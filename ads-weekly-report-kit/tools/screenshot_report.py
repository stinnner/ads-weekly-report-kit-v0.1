"""Take a full-page screenshot of the weekly report HTML using Playwright."""
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

HTML_PATH = Path(__file__).resolve().parent.parent / "outputs" / "weekly_report.html"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "outputs" / "weekly_report_preview.png"

def main():
    url = HTML_PATH.as_uri()
    print(f"Capturing: {HTML_PATH}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(url, wait_until="networkidle")
        # Extra wait for KaTeX rendering
        page.wait_for_timeout(3000)
        page.screenshot(path=str(OUTPUT_PATH), full_page=True)
        browser.close()
    
    print(f"Saved: {OUTPUT_PATH}")
    return OUTPUT_PATH

if __name__ == "__main__":
    main()
