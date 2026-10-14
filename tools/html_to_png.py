#!/usr/bin/env python3
"""Pārvērš lokālu HTML failu PNG attēlā ar Playwright (Chromium). Lieto docs/ekranu-karte.png atjaunošanai."""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("png", type=Path)
    parser.add_argument("--selector", default="#page", help="Elements, kuru nofotografēt")
    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1800, "height": 1200}, device_scale_factor=2)
        page.goto(args.html.resolve().as_uri())
        page.locator(args.selector).screenshot(path=str(args.png))
        browser.close()
    print(f"OK: {args.png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
