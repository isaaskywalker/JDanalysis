#!/bin/bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${JOB_PARSER_PYTHON:-python3}"
if ! "$PYTHON_BIN" -c 'import sys; assert sys.version_info >= (3,10)' 2>/dev/null; then
  echo 'Python 3.10 이상이 필요합니다. 예: JOB_PARSER_PYTHON=python3.12 bash install.sh'
  exit 1
fi
"$PYTHON_BIN" -m venv "$PROJECT_DIR/.venv"
"$PROJECT_DIR/.venv/bin/python" -m pip install -r "$PROJECT_DIR/requirements.txt"
"$PROJECT_DIR/.venv/bin/python" -m playwright install chromium
"$PROJECT_DIR/.venv/bin/python" - <<'PY'
import asyncio
from playwright.async_api import async_playwright
async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content('<main>browser check</main>')
        assert await page.inner_text('main') == 'browser check'
        await browser.close()
asyncio.run(check())
print('브라우저 실행 확인 완료')
PY
echo "설치 완료. 로컬 Codex에서 이 폴더를 열어 주세요: $PROJECT_DIR"
