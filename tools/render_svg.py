from pathlib import Path
from playwright.sync_api import sync_playwright

svg = Path(r"F:\html\ads-weekly-report-kit-v0.1\assets\github-hero.svg")
out = Path(r"F:\html\ads-weekly-report-kit-v0.1\assets\github-hero-check.png")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 800})
    page.goto(svg.as_uri(), wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1280, "height": 720}, timeout=60000)
    browser.close()
print(f"Saved: {out}")
