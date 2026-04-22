# LinkedIn_Scraper.spec
# PyInstaller spec file — run with:
#   .venv\Scripts\pyinstaller.exe LinkedIn_Scraper.spec

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# ── Collect packages that need special handling ──────────────────────────
uc_datas,    uc_binaries,    uc_hiddenimports    = collect_all('undetected_chromedriver')
hc_datas,    hc_binaries,    hc_hiddenimports    = collect_all('humancursor')
flask_datas, flask_binaries, flask_hiddenimports = collect_all('flask')
bs4_datas,   bs4_binaries,   bs4_hiddenimports   = collect_all('bs4')

selenium_datas, selenium_binaries, selenium_hiddenimports = collect_all('selenium')

# ── Analysis ──────────────────────────────────────────────────────────────
a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=(
        uc_binaries + hc_binaries + flask_binaries +
        bs4_binaries + selenium_binaries
    ),
    datas=(
        # Flask app resources
        [('templates', 'templates'),
         ('static',    'static'),
         ('linkd.py',  '.'),]
        # Collected package data
        + uc_datas + hc_datas + flask_datas + bs4_datas + selenium_datas
        + flask_datas
    ),
    hiddenimports=(
        uc_hiddenimports + hc_hiddenimports + flask_hiddenimports +
        bs4_hiddenimports + selenium_hiddenimports +
        [
            'flask',
            'flask.templating',
            'jinja2',
            'jinja2.ext',
            'werkzeug',
            'werkzeug.serving',
            'werkzeug.routing',
            'werkzeug.middleware',
            'werkzeug.middleware.proxy_fix',
            'click',
            'itsdangerous',
            'bs4',
            'lxml',
            'html.parser',
            'selenium',
            'selenium.webdriver',
            'selenium.webdriver.chrome',
            'selenium.webdriver.chrome.options',
            'selenium.webdriver.common.by',
            'selenium.webdriver.support.ui',
            'selenium.webdriver.support.expected_conditions',
            'undetected_chromedriver',
            'humancursor',
            'humancursor.web_cursor',
            'humancursor.system_cursor',
            'pkg_resources',
            'importlib.metadata',
            'email.mime.text',
            'email.mime.multipart',
        ]
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'PIL', 'cv2',
              'PyQt5', 'PyQt6', 'wx', 'gi'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── PYZ (Python archive) ──────────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE ───────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LinkedIn_Scraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,              # Keep console window so server logs are visible
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# ── COLLECT (one-folder bundle) ───────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LinkedIn_Scraper',
)
