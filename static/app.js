/* app.js — Dashboard polling + scrape form logic */

'use strict';

// ── Helpers ──────────────────────────────────────────────────────────────

function statusBadge(status) {
  const map = {
    queued:  ['bg-secondary', 'bi-hourglass',        'Queued'],
    running: ['bg-primary',   'bi-arrow-repeat spin', 'Running'],
    done:    ['bg-success',   'bi-check-circle',      'Done'],
    error:   ['bg-danger',    'bi-x-circle',          'Error'],
  };
  const [bg, icon, label] = map[status] || ['bg-secondary', 'bi-question', status];
  return `<span class="badge ${bg} status-badge">
            <i class="bi ${icon} me-1"></i>${label}
          </span>`;
}

function makeViewLinks(outputFile) {
  if (!outputFile) return '—';
  const dl  = `/results/${encodeURIComponent(outputFile)}/download`;
  const view = `/results/${encodeURIComponent(outputFile)}/view`;
  return `
    <a href="${dl}"   class="btn btn-sm btn-outline-secondary py-0 px-1" title="Download JSON">
      <i class="bi bi-download"></i>
    </a>
    <a href="${view}" class="btn btn-sm btn-outline-primary py-0 px-1 ms-1" title="View in browser">
      <i class="bi bi-eye"></i>
    </a>`;
}

function now() {
  return new Date().toLocaleTimeString();
}

// ── Active Jobs Polling ───────────────────────────────────────────────────

const activeJobs = new Set();  // job IDs currently being polled
let pollTimer = null;

function addJobRow(job) {
  const tbody = document.getElementById('jobsBody');

  // Remove "no jobs" placeholder row if present
  const placeholder = document.getElementById('noJobsRow');
  if (placeholder) placeholder.remove();

  const tr = document.createElement('tr');
  tr.id = `job-${job.job_id}`;
  tr.innerHTML = `
    <td><code>${job.job_id}</code></td>
    <td class="text-truncate" style="max-width:260px;" title="${escapeHtml(job.url_snippet)}">${escapeHtml(job.url_snippet)}</td>
    <td>${job.max_pages}</td>
    <td class="job-status">${statusBadge(job.status)}</td>
    <td class="lead-count">${job.lead_count}</td>
    <td class="text-muted small">${job.started}</td>
    <td class="job-links">${makeViewLinks(job.output_file)}</td>
  `;
  tbody.prepend(tr);
}

function updateJobRow(job) {
  const tr = document.getElementById(`job-${job.job_id}`);
  if (!tr) {
    addJobRow(job);
    return;
  }
  tr.querySelector('.job-status').innerHTML  = statusBadge(job.status);
  tr.querySelector('.lead-count').textContent = job.lead_count;
  if (job.output_file) {
    tr.querySelector('.job-links').innerHTML = makeViewLinks(job.output_file);
  }
  if (job.status === 'error') {
    tr.classList.add('table-danger');
  }
}

async function pollJob(jobId) {
  try {
    const res  = await fetch(`/api/scrape/status/${jobId}`);
    const data = await res.json();
    updateJobRow(data);

    // Stop polling finished jobs
    if (data.status === 'done' || data.status === 'error') {
      activeJobs.delete(jobId);
      if (data.status === 'done') {
        // Reload results table to show newly saved file
        await refreshResultsTable();
      }
    }
  } catch (_) {
    // Network blip — keep polling
  }
}

function startPolling() {
  if (pollTimer) return;           // already running
  pollTimer = setInterval(async () => {
    if (activeJobs.size === 0) {
      clearInterval(pollTimer);
      pollTimer = null;
      return;
    }
    for (const id of [...activeJobs]) {
      await pollJob(id);
    }
    const el = document.getElementById('lastRefreshed');
    if (el) el.textContent = `Last refreshed: ${now()}`;
  }, 3000);
}

// ── Results Table Refresh ─────────────────────────────────────────────────

async function refreshResultsTable() {
  try {
    const res   = await fetch('/api/results');
    const files = await res.json();

    // Re-render results tbody
    const tbody = document.querySelector('.card:last-child tbody');
    if (!tbody) return;

    if (files.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">No results yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = files.map(f => `
      <tr>
        <td><code class="text-muted" style="font-size:.8rem;">${escapeHtml(f.filename)}</code></td>
        <td class="text-muted small">${escapeHtml(f.modified)}</td>
        <td><strong>${f.lead_count}</strong></td>
        <td class="d-flex gap-1">
          <a href="/results/${encodeURIComponent(f.filename)}/view"
             class="btn btn-sm btn-outline-primary">
            <i class="bi bi-eye me-1"></i>View
          </a>
          <a href="/results/${encodeURIComponent(f.filename)}/download"
             class="btn btn-sm btn-outline-secondary">
            <i class="bi bi-filetype-json me-1"></i>JSON
          </a>
          <a href="/results/${encodeURIComponent(f.filename)}/download/csv"
             class="btn btn-sm btn-outline-success">
            <i class="bi bi-filetype-csv me-1"></i>CSV
          </a>
        </td>
      </tr>
    `).join('');
  } catch (_) { /* ignore */ }
}

// ── Scrape Form Submission ────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const form     = document.getElementById('scrapeForm');
  const errorBox = document.getElementById('startError');
  const startBtn = document.getElementById('startBtn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorBox.classList.add('d-none');
    errorBox.textContent = '';

    const url      = document.getElementById('scrapeUrl').value.trim();
    const maxPages = parseInt(document.getElementById('maxPages').value, 10);

    // Client-side URL check
    if (!url.includes('linkedin.com/sales/search/')) {
      errorBox.textContent = 'Please enter a valid Sales Navigator search URL.';
      errorBox.classList.remove('d-none');
      return;
    }

    startBtn.disabled = true;
    startBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Starting…';

    try {
      const res  = await fetch('/api/scrape/start', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ url, max_pages: maxPages }),
      });
      const data = await res.json();

      if (!res.ok) {
        errorBox.textContent = data.error || 'Failed to start scrape.';
        errorBox.classList.remove('d-none');
        return;
      }

      // Add row and start polling
      activeJobs.add(data.job_id);
      addJobRow({
        job_id:      data.job_id,
        url_snippet: url.slice(0, 80) + (url.length > 80 ? '…' : ''),
        max_pages:   maxPages,
        status:      'queued',
        lead_count:  0,
        started:     new Date().toLocaleString(),
        output_file: null,
      });
      startPolling();

      // Clear form
      document.getElementById('scrapeUrl').value = '';

    } catch (err) {
      errorBox.textContent = `Network error: ${err.message}`;
      errorBox.classList.remove('d-none');
    } finally {
      startBtn.disabled = false;
      startBtn.innerHTML = '<i class="bi bi-play-fill me-1"></i>Start';
    }
  });

  // Resume polling for any rows already visible on page load (e.g. after refresh)
  document.querySelectorAll('#jobsBody tr[id^="job-"]').forEach(tr => {
    const statusText = tr.querySelector('.job-status')?.textContent?.trim().toLowerCase() || '';
    if (statusText.includes('running') || statusText.includes('queued')) {
      const jobId = tr.id.replace('job-', '');
      activeJobs.add(jobId);
    }
  });
  if (activeJobs.size > 0) startPolling();
});

// ── Cookie Manager ────────────────────────────────────────────────────────

function showCookieAlert(message, type /* 'success'|'danger'|'warning' */) {
  const el = document.getElementById('cookieAlert');
  if (!el) return;
  el.className     = `alert alert-${type}`;
  el.innerHTML     = message;
  el.classList.remove('d-none');
  setTimeout(() => el.classList.add('d-none'), 6000);
}

function updateCookieUI(detail) {
  // Update status badge
  const badge = document.getElementById('cookieStatusBadge');
  if (badge) {
    const map = {
      ok:      ['bg-success',             'bi-shield-check',       'Valid'],
      partial: ['bg-warning text-dark',   'bi-shield-exclamation', 'Partial'],
      invalid: ['bg-danger',              'bi-shield-x',           'Invalid'],
      missing: ['bg-danger',              'bi-shield-x',           'Missing'],
    };
    const [bg, icon, label] = map[detail.status] || ['bg-secondary', 'bi-shield', detail.status];
    badge.innerHTML = `<span class="badge ${bg}"><i class="bi ${icon} me-1"></i>${label}</span>`;
  }

  // Update message
  const msg = document.getElementById('cookieMsg');
  if (msg) {
    const cls = { ok: 'text-success', partial: 'text-warning' }[detail.status] || 'text-danger';
    msg.className = `mb-3 small ${cls}`;
    const updated = detail.updated ? `<span class="text-muted ms-2">· Last updated: ${escapeHtml(detail.updated)}</span>` : '';
    msg.innerHTML = `<i class="bi bi-info-circle me-1"></i>${escapeHtml(detail.message)}${updated}`;
  }

  // Update navbar cookie indicator
  const navBadges = document.querySelectorAll('.cookie-ok, .cookie-partial, .cookie-invalid, .cookie-missing');
  navBadges.forEach(el => {
    el.className = `cookie-${detail.status} small`;
    const icon = detail.status === 'ok' ? 'bi-shield-check' : detail.status === 'partial' ? 'bi-shield-exclamation' : 'bi-shield-x';
    const label = detail.status === 'ok' ? 'Cookies OK' : detail.status === 'partial' ? 'Partial Cookies' : 'No Cookies';
    el.innerHTML = `<i class="bi ${icon}"></i> ${label}`;
  });
}

async function submitCookies(payload /* FormData or JSON string */) {
  const uploadBtn = document.getElementById('uploadFileBtn');
  const pasteBtn  = document.getElementById('pasteCookieBtn');
  [uploadBtn, pasteBtn].forEach(b => { if (b) b.disabled = true; });

  try {
    let res;
    if (payload instanceof FormData) {
      res = await fetch('/api/cookies/upload', { method: 'POST', body: payload });
    } else {
      res = await fetch('/api/cookies/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
      });
    }

    const data = await res.json();
    if (!res.ok || data.error) {
      showCookieAlert(`<i class="bi bi-x-circle me-1"></i>${escapeHtml(data.error || 'Upload failed.')}`, 'danger');
    } else {
      showCookieAlert('<i class="bi bi-check-circle me-1"></i>Cookies saved successfully!', 'success');
      if (data.detail) updateCookieUI(data.detail);
      // Clear the textarea and file input
      const paste = document.getElementById('cookiePaste');
      const file  = document.getElementById('cookieFile');
      if (paste) paste.value = '';
      if (file)  file.value  = '';
    }
  } catch (err) {
    showCookieAlert(`<i class="bi bi-x-circle me-1"></i>Network error: ${escapeHtml(err.message)}`, 'danger');
  } finally {
    [uploadBtn, pasteBtn].forEach(b => { if (b) b.disabled = false; });
  }
}

document.addEventListener('DOMContentLoaded', () => {

  // File upload button
  const uploadBtn = document.getElementById('uploadFileBtn');
  if (uploadBtn) {
    uploadBtn.addEventListener('click', () => {
      const fileInput = document.getElementById('cookieFile');
      if (!fileInput || !fileInput.files.length) {
        showCookieAlert('<i class="bi bi-info-circle me-1"></i>Please select a JSON file first.', 'warning');
        return;
      }
      const fd = new FormData();
      fd.append('file', fileInput.files[0]);
      submitCookies(fd);
    });
  }

  // Paste / save button
  const pasteBtn = document.getElementById('pasteCookieBtn');
  if (pasteBtn) {
    pasteBtn.addEventListener('click', () => {
      const raw = (document.getElementById('cookiePaste')?.value || '').trim();
      if (!raw) {
        showCookieAlert('<i class="bi bi-info-circle me-1"></i>Please paste cookie JSON into the text box first.', 'warning');
        return;
      }
      // Validate JSON client-side before sending
      try {
        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) throw new Error('Must be a JSON array.');
      } catch (e) {
        showCookieAlert(`<i class="bi bi-x-circle me-1"></i>Invalid JSON: ${escapeHtml(e.message)}`, 'danger');
        return;
      }
      submitCookies(raw);
    });
  }

});

// ── Spin animation for running icon ──────────────────────────────────────

const style = document.createElement('style');
style.textContent = `
  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { display: inline-block; animation: spin 1s linear infinite; }
`;
document.head.appendChild(style);

// ── XSS-safe escaping ────────────────────────────────────────────────────

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
