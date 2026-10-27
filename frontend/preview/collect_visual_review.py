"""FVB-01. Capture synthetic interactive UI for consolidated visual review.

No business APIs, no real users, no publishing. Browser + local in-memory HTML/CSS/JS.
This intentionally mirrors the loader used by the certified browser.smoke.py.
Screenshots are evidence for HUMAN review, never an automatic aesthetic approval.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

VISUAL = Path(__file__).resolve().parents[1] / "visual"
MODULES = (
    'fixtures.mjs', 'view-model.mjs', 'cf-op-02.mjs',
    'registration-view.mjs', 'human-cycle-view.mjs',
    'operation-feedback.mjs', 'bank-view.mjs', 'postmark-view.mjs',
    'team-operations.mjs', 'team-pause-preview.mjs',
    'team-monitor.mjs', 'team-monitoring.mjs', 'batch-monitor.mjs',
    'distribution-view.mjs', 'transport-state-view.mjs',
    'conversation-attention.mjs', 'app.mjs'
)


def offline_page_source():
    html = (VISUAL / "index.html").read_text(encoding="utf-8")
    css = (VISUAL / "styles.css").read_text(encoding="utf-8")
    link = '<link rel="stylesheet" href="./styles.css">'
    script_tag = '<script type="module" src="./app.mjs"></script>'
    if html.count(link) != 1 or html.count(script_tag) != 1:
        raise ValueError("Unexpected HTML runtime entry")
    html = html.replace(link, "<style>" + css + "</style>").replace(script_tag, "")
    js = "\n".join((VISUAL / name).read_text(encoding="utf-8") for name in MODULES)
    js = re.sub(r'(?ms)^import \{.*?\} from ["\']\./[^"\']+["\'];\s*', '', js)
    js = re.sub(r'(?m)^export ', '', js)
    if "import {" in js or "export " in js:
        raise ValueError("Unresolved local module linkage")
    if "Dados fictícios" not in html:
        raise ValueError("Demo warning missing")
    return html, js


def main(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    html, js = offline_page_source()
    captures = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        for width, height, theme, actor, scene in (
            (1440, 900, 'light', 'rafael', 'list'),
            (1440, 900, 'dark', 'rafael', 'thread'),
            (1366, 768, 'light', 'marina', 'team'),
            (1366, 768, 'dark', 'rafael', 'extraction'),
            (390, 844, 'light', 'rafael', 'list'),
            (390, 844, 'light', 'rafael', 'thread'),
            (390, 844, 'dark', 'rafael', 'details'),
            (320, 640, 'light', 'rafael', 'list'),
            (320, 640, 'dark', 'rafael', 'thread'),
        ):
            page = browser.new_page(viewport={'width': width, 'height': height},
                                    color_scheme='light', device_scale_factor=1)
            page.set_default_timeout(9000)
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))
            page.set_content(html)
            page.add_script_tag(content=js)
            expect(page.locator('#visual-app')).to_have_attribute('data-theme', 'light')
            if theme == 'dark':
                page.locator('#ui-settings').evaluate('e => e.open = true')
                page.locator('#theme-dark').click()
                page.locator('#ui-settings').evaluate('e => e.open = false')
            expect(page.locator('#visual-app')).to_have_attribute('data-theme', theme)
            if actor != 'rafael':
                page.locator('#ui-settings').evaluate('e => e.open = true')
                page.locator('#actor-select').select_option(actor)
                page.locator('#ui-settings').evaluate('e => e.open = false')

            if scene in ('thread', 'details', 'extraction'):
                page.get_by_role('button', name='Abrir conversa Cliente Exemplo 02',
                                 exact=False).click()
                if scene in ('details', 'extraction') and width <= 1040:
                    page.locator('#detail-toggle').click()
                if scene == 'extraction':
                    page.locator('.detail-tab', has_text='Extração').click()
                    expect(page.locator('#case-tab-extraction')).to_have_attribute(
                        'aria-selected', 'true')
            elif scene == 'team':
                page.locator('#team-nav').click()
                expect(page.locator('#team-dialog')).to_be_visible()

            if errors:
                raise RuntimeError("JavaScript error on screenshot scene: " + repr(errors))
            if page.evaluate('document.documentElement.scrollWidth > innerWidth'):
                raise RuntimeError(f"Horizontal overflow at {width}px ({scene})")
            filename = f"{width}x{height}-{theme}-{actor}-{scene}.png"
            page.screenshot(path=str(output / filename), full_page=True,
                            animations='disabled')
            captures.append({'file': filename, 'width': width, 'height': height,
                             'theme': theme, 'actor': actor, 'scene': scene,
                             'synthetic': True})
            page.close()
        browser.close()

    index = {
        'title': 'Prumo — FVB-01 consolidated visual evidence',
        'purpose': 'For human visual review only — not a production approval',
        'synthetic': True,
        'captures': captures,
        'notes': [
            'Screens are synthetic; profile selectors are not authenticated.',
            'A screenshot cannot certify touch, accessibility, S0 or ChatGPT Sites.',
            'Assess mobile list/thread/detail, desktop team/extraction and both themes.',
            'No files or screen images were published by this script.'
        ]
    }
    (output / 'INDEX.json').write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')
    print(f'FVB-01 screenshot evidence: PASS ({len(captures)} scenes)')
    return len(captures)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='fv-visual-review')
    args = parser.parse_args()
    main(args.output)
