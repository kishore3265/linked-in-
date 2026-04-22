"""
app.py — Flask web application for LinkedIn Sales Navigator scraping.

Run:
    python app.py

Then open http://localhost:5000 in your browser.
"""

import csv
import glob
import json
import os
import re
import sys
import threading
import uuid
from datetime import datetime

from flask import (
    Flask,
    jsonify,
    render_template,
    redirect,
    request,
    send_file,
    url_for,
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
# When running as a PyInstaller .exe, __file__ points to the temp extraction
# dir (_MEIPASS).  We keep two separate roots:
#   BUNDLE_DIR  — where templates/static/linkd.py live (inside the bundle)
#   DATA_DIR    — where runtime files live (cookies, output CSVs, next to .exe)

if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS                          # bundled resources
    DATA_DIR   = os.path.dirname(sys.executable)      # beside the .exe
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR   = BUNDLE_DIR

BASE_DIR = DATA_DIR   # keep existing references working (cookies, outputs)

app = Flask(
    __name__,
    template_folder=os.path.join(BUNDLE_DIR, 'templates'),
    static_folder=os.path.join(BUNDLE_DIR, 'static'),
)
app.secret_key = os.urandom(24)  # needed so flash/session work if added later

# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_SALES_NAV_RE = re.compile(
    r"https://www\.linkedin\.com/sales/search/[^\s<>\"']+"
)

CSV_FIELDS = [
    "company_name",
    "company_url",
    "industry",
    "city",
    "state",
    "country",
    "employee_count",
    "revenue",
    "website",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job_output_path(job: dict) -> str | None:
    """Return the absolute path to the job's JSON output file, or None."""
    fname = job.get("output_file")
    if not fname:
        return None
    return os.path.join(BASE_DIR, fname)


def _poll_lead_count(job: dict) -> int:
    """
    Read the JSON output file that linkd.py writes page-by-page and return
    how many leads are currently in it.  Returns 0 on any error.
    """
    path = _job_output_path(job)
    if not path or not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return len(data) if isinstance(data, list) else 0
    except Exception:
        return 0


def _get_cookie_detail() -> dict:
    """
    Return a detailed status dict about the current linkedin_cookies.json.
    """
    cookie_path = os.path.join(DATA_DIR, "linkedin_cookies.json")
    if not os.path.exists(cookie_path):
        return {"status": "missing", "message": "linkedin_cookies.json not found.", "count": 0, "names": []}

    try:
        with open(cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        if not isinstance(cookies, list):
            return {"status": "invalid", "message": "File is not a JSON array.", "count": 0, "names": []}
    except Exception as exc:
        return {"status": "invalid", "message": f"Cannot parse JSON: {exc}", "count": 0, "names": []}

    names = [c.get("name", "") for c in cookies if c.get("name")]
    has_li_at  = "li_at"               in names
    has_li_a   = "li_a"                in names
    has_li_ep  = "li_ep_auth_context"  in names

    if has_li_at and has_li_a:
        status  = "ok"
        message = "Sales Navigator cookies are present and look valid."
    elif has_li_at:
        status  = "partial"
        message = "Regular LinkedIn cookie (li_at) found, but Sales Navigator cookies (li_a, li_ep_auth_context) are missing. Re-export cookies from Sales Navigator."
    else:
        status  = "invalid"
        message = "Critical cookie li_at is missing. Please re-export cookies from LinkedIn."

    mtime = datetime.fromtimestamp(os.path.getmtime(cookie_path)).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "status":    status,
        "message":   message,
        "count":     len(cookies),
        "names":     names,
        "has_li_at": has_li_at,
        "has_li_a":  has_li_a,
        "has_li_ep": has_li_ep,
        "updated":   mtime,
    }


def _list_result_files() -> list[dict]:
    """
    Return metadata for every scraped_leads_*.json in BASE_DIR, newest first.
    """
    pattern = os.path.join(BASE_DIR, "scraped_leads_*.json")
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    results = []
    for fpath in files:
        fname = os.path.basename(fpath)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            count = len(data) if isinstance(data, list) else 0
        except Exception:
            count = 0
        mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        results.append(
            {
                "filename": fname,
                "lead_count": count,
                "modified": mtime,
            }
        )
    return results


def _build_job_response(job_id: str) -> dict:
    """Return a JSON-serialisable dict describing a single job."""
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return {"error": "job not found"}

    # Refresh live lead count from file while job is running
    if job["status"] == "running":
        job["lead_count"] = _poll_lead_count(job)

    return {
        "job_id": job_id,
        "status": job["status"],
        "url_snippet": job["url"][:80] + ("…" if len(job["url"]) > 80 else ""),
        "max_pages": job["max_pages"],
        "lead_count": job["lead_count"],
        "error": job.get("error"),
        "output_file": job.get("output_file"),
        "started": job["started"],
    }


# ---------------------------------------------------------------------------
# Background scrape worker
# ---------------------------------------------------------------------------

def _scrape_worker(job_id: str, url: str, max_pages: int):
    """Run in a daemon thread — launches Chrome, scrapes, updates JOBS."""
    try:
        # When frozen, BUNDLE_DIR is on sys.path via the spec file.
        # When running normally, the source directory is already on sys.path.
        if getattr(sys, 'frozen', False) and BUNDLE_DIR not in sys.path:
            sys.path.insert(0, BUNDLE_DIR)
        from linkd import SalesNavigatorScraper  # noqa: PLC0415
    except ImportError as exc:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = f"Cannot import scraper: {exc}"
        return

    try:
        cookie_file = os.path.join(DATA_DIR, "linkedin_cookies.json")
        scraper = SalesNavigatorScraper(cookie_file=cookie_file)

        # Tell the job what output file to watch before scraping starts.
        # linkd.py  picks the timestamp AFTER scrape_search_results is called,
        # so we peek at the newest file after scrape to grab the filename.
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "running"

        scraper.run_continuation(continuation_url=url, max_pages=max_pages)

        # Find the newest scraped_leads_*.json written during this run
        pattern = os.path.join(BASE_DIR, "scraped_leads_*.json")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        output_file = os.path.basename(files[0]) if files else None

        final_count = 0
        if output_file:
            try:
                with open(os.path.join(BASE_DIR, output_file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                final_count = len(data) if isinstance(data, list) else 0
            except Exception:
                pass

        with JOBS_LOCK:
            JOBS[job_id]["status"] = "done"
            JOBS[job_id]["output_file"] = output_file
            JOBS[job_id]["lead_count"] = final_count

    except Exception as exc:
        with JOBS_LOCK:
            JOBS[job_id]["status"] = "error"
            JOBS[job_id]["error"] = str(exc)


# ---------------------------------------------------------------------------
# Routes — Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    with JOBS_LOCK:
        jobs = [_build_job_response(jid) for jid in JOBS]
    return render_template("index.html", jobs=jobs, results=_list_result_files(), cookie_detail=_get_cookie_detail())


@app.route("/results/<filename>/view")
def view_results(filename: str):
    # Validate filename — only allow scraped_leads_*.json
    if not re.match(r"^scraped_leads_[\w]+\.json$", filename):
        return "Invalid filename", 400

    fpath = os.path.join(BASE_DIR, filename)
    if not os.path.exists(fpath):
        return "File not found", 404

    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        leads = data if isinstance(data, list) else []
    except Exception as exc:
        return f"Error reading file: {exc}", 500

    # Simple server-side pagination
    page = request.args.get("page", 1, type=int)
    per_page = 50
    total = len(leads)
    start = (page - 1) * per_page
    end = start + per_page
    page_leads = leads[start:end]
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "view_results.html",
        filename=filename,
        leads=page_leads,
        page=page,
        total_pages=total_pages,
        total=total,
        fields=CSV_FIELDS,
    )


# ---------------------------------------------------------------------------
# Routes — API
# ---------------------------------------------------------------------------

@app.route("/api/scrape/start", methods=["POST"])
def api_scrape_start():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    max_pages = int(data.get("max_pages", 5))

    # Validate URL
    if not _SALES_NAV_RE.match(url):
        return jsonify({"error": "URL must be a LinkedIn Sales Navigator search URL."}), 400

    # Clamp pages
    max_pages = max(1, min(max_pages, 100))

    job_id = str(uuid.uuid4())[:8]
    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": "queued",
            "url": url,
            "max_pages": max_pages,
            "lead_count": 0,
            "output_file": None,
            "error": None,
            "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    t = threading.Thread(
        target=_scrape_worker,
        args=(job_id, url, max_pages),
        daemon=True,
    )
    t.start()

    return jsonify({"job_id": job_id}), 202


@app.route("/api/scrape/status/<job_id>")
def api_scrape_status(job_id: str):
    with JOBS_LOCK:
        if job_id not in JOBS:
            return jsonify({"error": "Job not found"}), 404
    return jsonify(_build_job_response(job_id))


@app.route("/api/cookies/status")
def api_cookies_status():
    return jsonify(_get_cookie_detail())


@app.route("/api/cookies/upload", methods=["POST"])
def api_cookies_upload():
    """
    Accept cookies via:
      - JSON body: { "cookies": [ ... ] }
      - File upload: multipart field named "file" (linkedin_cookies.json)
      - Raw JSON text body (Content-Type: text/plain or application/json array)
    Validates the array, then writes to linkedin_cookies.json next to the exe.
    """
    cookies = None

    # ── Try multipart file upload first ──────────────────────────────────
    if "file" in request.files:
        f = request.files["file"]
        if not f.filename:
            return jsonify({"error": "No file selected."}), 400
        try:
            raw = f.read().decode("utf-8")
            cookies = json.loads(raw)
        except Exception as exc:
            return jsonify({"error": f"Cannot parse uploaded file: {exc}"}), 400

    # ── Try JSON body: { "cookies": [...] } or plain array ───────────────
    if cookies is None:
        data = request.get_json(silent=True, force=True)
        if isinstance(data, list):
            cookies = data
        elif isinstance(data, dict) and isinstance(data.get("cookies"), list):
            cookies = data["cookies"]

    # ── Try raw text body (user pasted JSON into a textarea) ─────────────
    if cookies is None:
        try:
            raw = request.get_data(as_text=True).strip()
            if raw:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    cookies = parsed
                elif isinstance(parsed, dict) and isinstance(parsed.get("cookies"), list):
                    cookies = parsed["cookies"]
        except Exception:
            pass

    if cookies is None:
        return jsonify({"error": "No valid cookie data received. Provide a JSON array."}), 400

    if not isinstance(cookies, list) or len(cookies) == 0:
        return jsonify({"error": "Cookies must be a non-empty JSON array."}), 400

    # Basic structure check — each item should at least have name + value
    for item in cookies[:5]:   # spot-check first 5
        if not isinstance(item, dict) or "name" not in item or "value" not in item:
            return jsonify({"error": "Each cookie must be an object with 'name' and 'value' fields."}), 400

    # Save to disk
    cookie_path = os.path.join(DATA_DIR, "linkedin_cookies.json")
    try:
        with open(cookie_path, "w", encoding="utf-8") as out:
            json.dump(cookies, out, indent=2, ensure_ascii=False)
    except Exception as exc:
        return jsonify({"error": f"Could not save cookies: {exc}"}), 500

    detail = _get_cookie_detail()
    return jsonify({"success": True, "detail": detail}), 200


@app.route("/api/results")
def api_results():
    return jsonify(_list_result_files())


@app.route("/results/<filename>/download")
def download_result(filename: str):
    # Validate filename — only allow scraped_leads_*.json or *.csv
    if not re.match(r"^scraped_leads_[\w]+\.(json|csv)$", filename):
        return "Invalid filename", 400

    fpath = os.path.join(BASE_DIR, filename)
    if not os.path.exists(fpath):
        return "File not found", 404

    return send_file(fpath, as_attachment=True, download_name=filename)


@app.route("/results/<filename>/download/csv")
def download_csv(filename: str):
    """
    If the user clicks download CSV but only the JSON exists,
    convert on-the-fly and serve.
    """
    if not re.match(r"^scraped_leads_[\w]+\.json$", filename):
        return "Invalid filename", 400

    csv_name = filename.replace(".json", ".csv")
    csv_path = os.path.join(BASE_DIR, csv_name)

    # If CSV already exists, serve it directly
    if os.path.exists(csv_path):
        return send_file(csv_path, as_attachment=True, download_name=csv_name)

    # Otherwise convert from JSON
    json_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(json_path):
        return "File not found", 404

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        leads = data if isinstance(data, list) else []
    except Exception as exc:
        return f"Error reading JSON: {exc}", 500

    import io

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(leads)
    output.seek(0)

    from flask import Response

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{csv_name}"'},
    )


# ---------------------------------------------------------------------------
# Cookie status helper exposed to templates
# ---------------------------------------------------------------------------

@app.context_processor
def inject_cookie_status():
    """Inject cookie freshness info into every template context."""
    cookie_path = os.path.join(BASE_DIR, "linkedin_cookies.json")
    status = "missing"
    if os.path.exists(cookie_path):
        try:
            with open(cookie_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            names = [c.get("name") for c in cookies]
            has_li_at = "li_at" in names
            has_li_a = "li_a" in names
            if has_li_at and has_li_a:
                status = "ok"
            elif has_li_at:
                status = "partial"
            else:
                status = "invalid"
        except Exception:
            status = "invalid"
    return {"cookie_status": status}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import webbrowser
    print("=" * 60)
    print("  LinkedIn Scraper Web App")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60)
    # Auto-open browser after a short delay so Flask is ready
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False, host="0.0.0.0", port=5001, threaded=True)
