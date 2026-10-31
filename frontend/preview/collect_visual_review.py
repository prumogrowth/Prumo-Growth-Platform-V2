"""FVB-01. Capture synthetic interactive UI for consolidated visual review.

No business APIs, no real users, no publishing. Browser + localhost HTTP, with source-derived standalone support.
This intentionally mirrors the loader used by the certified browser.smoke.py.
Screenshots are evidence for HUMAN review, never an automatic aesthetic approval.
"""
from __future__ import annotations

import argparse
import json
import re
import os
from contextlib import contextmanager
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
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
    'conversation-attention.mjs', 'local-audio.mjs', 'communication-composer.mjs', 'revision-fixtures.mjs', 'relationship-view.mjs', 'app.mjs'
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


@contextmanager
def local_preview_server():
    class QuietFiles(SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietFiles, directory=str(VISUAL)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)


def main(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    offline_page_source()  # Validate the same module order used by standalone and smoke.
    captures = []

    with local_preview_server() as origin, sync_playwright() as p:
        options = {'headless': True, 'args': ['--no-sandbox','--use-fake-device-for-media-stream']}
        exe = os.getenv('CHROMIUM_EXECUTABLE', '').strip()
        if not exe and Path('/usr/bin/chromium').is_file():
            exe = '/usr/bin/chromium'
        if exe:
            options['executable_path'] = exe
        browser = p.chromium.launch(**options)
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
            (390, 844, 'dark', 'rafael', 'emoji'),
            (320, 640, 'light', 'rafael', 'audio'),
            (1440, 900, 'dark', 'rafael', 'audio-message'),
            (390, 844, 'light', 'rafael', 'expired'),
            (390, 844, 'dark', 'rafael', 'unknown'),
            (390, 844, 'light', 'rafael', 'notes'),
            (1440, 900, 'light', 'rafael', 'history'),
            (390, 844, 'dark', 'rafael', 'bank'),
            (390, 844, 'light', 'rafael', 'continuation'),
            (390, 844, 'dark', 'marina', 'team'),
            (320, 640, 'light', 'marina', 'monitor'),
            (1440, 900, 'dark', 'marina', 'batches'),
            (390, 844, 'light', 'marina', 'queue'),
        ):
            page = browser.new_page(viewport={'width': width, 'height': height},
                                    color_scheme='light', device_scale_factor=1, permissions=['microphone'])
            page.set_default_timeout(9000)
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))
            page.goto(origin + ('/?perfil=gestor' if actor == 'marina' else '/'))
            page.wait_for_selector('.conversation-card')
            expect(page.locator('#visual-app')).to_have_attribute('data-theme', 'light')
            if theme == 'dark':
                page.locator('#list-extra').evaluate('e=>e.open=false')
                page.locator('#ui-settings').evaluate('e => e.open = true')
                page.locator('#theme-dark').click()
                page.locator('#ui-settings').evaluate('e => e.open = false')
            expect(page.locator('#visual-app')).to_have_attribute('data-theme', theme)
            if scene in ('team','monitor','batches','queue'):
                page.locator('#team-nav-mobile' if width <= 760 else '#team-nav').click()
                if scene != 'team':
                    page.locator('#team-show-'+scene).click()
                expect(page.locator('#team-dialog')).to_be_visible()
            elif scene != 'list':
                number = '08' if scene == 'expired' else '05' if scene in ('unknown','bank','continuation') else '02'
                page.get_by_role('button', name='Abrir conversa Cliente Exemplo '+number, exact=False).click()
                if scene in ('details','extraction','notes','history','bank','continuation'):
                    if width <= 1040:
                        page.locator('#thread-title').click()
                    if scene in ('extraction','bank'):
                        page.locator('#open-bank-case').click()
                        expect(page.locator('#bank-dialog')).to_be_visible()
                    else:
                        tab = {'notes':'Notas','history':'Histórico','continuation':'Histórico'}.get(scene)
                        if tab:page.locator('.detail-tab', has_text=tab).click()
                elif scene == 'emoji':
                    page.locator('#message-input').fill('Podemos conversar? ')
                    page.locator('#emoji-toggle').click()
                elif scene in ('audio','audio-message'):
                    page.locator('#audio-record').click()
                    expect(page.locator('#audio-status')).to_have_text('Gravando áudio')
                    expect(page.locator('#audio-duration')).not_to_have_text('0:00')
                    page.locator('#audio-stop').click()
                    expect(page.locator('#audio-attach')).to_be_visible()
                    if scene == 'audio-message':
                        page.locator('#audio-attach').click()
                        expect(page.locator('.local-audio-message')).to_be_visible()

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
    from html import escape
    items = ''.join('<figure><a href="'+escape(c['file'])+'"><img loading="lazy" src="'+escape(c['file'])+'" alt="'+escape(c['scene'])+'"></a><figcaption>'+escape(c['file'])+'</figcaption></figure>' for c in captures)
    (output / 'INDEX.html').write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Prumo · revisão visual</title><style>body{font:16px system-ui;margin:24px;background:#eee;color:#222}main{display:flex;flex-wrap:wrap;gap:20px}figure{margin:0;max-width:420px}img{max-width:100%;max-height:600px}figcaption{font-size:12px;margin:8px 0}</style><h1>Prumo · revisão visual</h1><p>Dados fictícios. Capturas para avaliação humana, sem aceite automático ou publicação.</p><main>'+items+'</main></html>',encoding='utf-8')
    print(f'FVB-01 screenshot evidence: PASS ({len(captures)} scenes)')
    return len(captures)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='fv-visual-review')
    args = parser.parse_args()
    main(args.output)
