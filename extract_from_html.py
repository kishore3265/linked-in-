"""
extract_from_html.py
---------------------
Reads every search_page_*.html file saved in the linkedin/ folder and
extracts the key company data that is present directly on the search
result cards (no extra HTTP requests needed).

Fields extracted per company
-----------------------------
  page            – which HTML page the record came from
  company_name    – display name of the company
  linkedin_url    – full Sales Navigator company profile URL
  industry        – industry label from the card
  employee_count  – raw text e.g. "160 employees"
  employees_num   – numeric value only (int)
  revenue         – revenue range shown on the card e.g. "$1M - $2.5M"
  about           – first ~300 chars of the company blurb

Output
------
  linkedin/extracted_leads_<timestamp>.csv
"""

import csv
import os
import re
import time
from bs4 import BeautifulSoup

# ── Configuration ──────────────────────────────────────────────────────────────
HTML_FOLDER  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkedin')
TIMESTAMP    = time.strftime('%Y%m%d_%H%M%S')
OUTPUT_CSV   = os.path.join(HTML_FOLDER, f'extracted_leads_{TIMESTAMP}.csv')

FIELDNAMES = [
    'page',
    'company_name',
    'linkedin_url',
    'industry',
    'employee_count',
    'employees_num',
    'revenue',
    'about',
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _natural_sort_key(filename: str):
    """Sort filenames so search_page_2.html comes before search_page_10.html."""
    parts = re.split(r'(\d+)', filename)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def extract_employees_num(raw: str) -> int | str:
    """Pull the first integer out of a string like '160 employees on LinkedIn'."""
    m = re.search(r'[\d,]+', raw)
    if m:
        return int(m.group().replace(',', ''))
    return ''


def extract_page(soup: BeautifulSoup, page_num: int) -> list[dict]:
    """
    Parse one page's BeautifulSoup tree and return a list of record dicts.
    """
    records = []

    company_links = soup.find_all(
        'a', attrs={'data-control-name': 'view_company_via_result_name'}
    )

    for lnk in company_links:
        name = lnk.get_text(strip=True)
        href = lnk.get('href', '').split('?')[0]          # strip tracking params
        url  = (
            f'https://www.linkedin.com{href}'
            if href.startswith('/')
            else href
        )

        # Walk up to the closest card / list-item container
        card = (
            lnk.find_parent(class_=lambda c: c and 'result-lockup'            in c)
            or lnk.find_parent(class_=lambda c: c and 'search-results__result-item' in c)
            or lnk.find_parent('li')
        )
        scope = card if card else soup

        # ── Industry ──────────────────────────────────────────────────────────
        industry_el = scope.find(attrs={'data-anonymize': 'industry'})
        industry    = industry_el.get_text(strip=True) if industry_el else ''

        # ── Employee count ────────────────────────────────────────────────────
        emp_el   = scope.find('a', attrs={'data-anonymize': 'company-size'})
        emp_text = emp_el.get_text(strip=True) if emp_el else ''
        # Remove the trailing "on LinkedIn" part if present
        emp_text = re.sub(r'\s*on LinkedIn.*', '', emp_text, flags=re.IGNORECASE).strip()

        # ── Revenue ───────────────────────────────────────────────────────────
        rev_el  = scope.find(attrs={'data-anonymize': 'revenue'})
        revenue = rev_el.get_text(strip=True) if rev_el else ''

        # ── About blurb ───────────────────────────────────────────────────────
        about_el = scope.find(attrs={'data-anonymize': 'person-blurb'})
        if not about_el:
            about_el = scope.find('div', attrs={'data-anonymize': 'person-blurb'})
        about_raw = about_el.get_text(separator=' ', strip=True) if about_el else ''
        about     = ' '.join(about_raw.split())[:300]      # normalise whitespace, cap at 300 chars

        records.append({
            'page'          : page_num,
            'company_name'  : name,
            'linkedin_url'  : url,
            'industry'      : industry,
            'employee_count': emp_text,
            'employees_num' : extract_employees_num(emp_text),
            'revenue'       : revenue,
            'about'         : about,
        })

    return records


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print('=' * 60)
    print(f' HTML → CSV extractor')
    print(f' Source folder : {HTML_FOLDER}')
    print(f' Output CSV    : {OUTPUT_CSV}')
    print('=' * 60)

    # Find all search_page_*.html files
    html_files = sorted(
        [f for f in os.listdir(HTML_FOLDER) if re.match(r'search_page_\d+\.html$', f)],
        key=_natural_sort_key,
    )

    if not html_files:
        print('\n No search_page_*.html files found in the linkedin/ folder.')
        print(' Run linkd.py first to generate them.')
        return

    print(f'\n Found {len(html_files)} HTML file(s): {html_files[0]}  …  {html_files[-1]}')

    all_records   = []
    seen_urls     = set()          # deduplicate across pages
    duplicate_cnt = 0

    for filename in html_files:
        # Extract page number from filename (search_page_7.html → 7)
        page_num = int(re.search(r'(\d+)', filename).group(1))
        filepath = os.path.join(HTML_FOLDER, filename)

        print(f'\n  Parsing {filename} ...', end=' ', flush=True)
        with open(filepath, encoding='utf-8', errors='ignore') as fh:
            soup = BeautifulSoup(fh, 'html.parser')

        records = extract_page(soup, page_num)

        new_records = []
        for r in records:
            if r['linkedin_url'] in seen_urls:
                duplicate_cnt += 1
                continue
            seen_urls.add(r['linkedin_url'])
            new_records.append(r)

        all_records.extend(new_records)
        print(f'{len(new_records)} companies extracted  ({len(records) - len(new_records)} dupes skipped)')

    # Write CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as cf:   # utf-8-sig = BOM for Excel
        writer = csv.DictWriter(cf, fieldnames=FIELDNAMES, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_records)

    print('\n' + '=' * 60)
    print(f' DONE')
    print(f'  Pages processed : {len(html_files)}')
    print(f'  Total companies : {len(all_records)}')
    print(f'  Duplicates skip : {duplicate_cnt}')
    print(f'  CSV saved to    : {OUTPUT_CSV}')
    print('=' * 60)


if __name__ == '__main__':
    main()
