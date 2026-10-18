"""FV-UI-002. Ensaio opcional com Chromium/Playwright, sem acesso HTTP ou APIs.
Requer Python, playwright e Chromium instalados; não é CI ou aceite de produção.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import re

base = Path(__file__).resolve().parents[1]
html = (base / 'index.html').read_text(encoding='utf-8')
css = (base / 'styles.css').read_text(encoding='utf-8')
html = html.replace('<link rel="stylesheet" href="./styles.css">', '<style>'+css+'</style>')
html = html.replace('<script type="module" src="./app.mjs"></script>', '')
script = '\n'.join((base / name).read_text(encoding='utf-8') for name in ('fixtures.mjs','view-model.mjs','app.mjs'))
script = re.sub(r'(?ms)^import \{.*?\} from ["\']\./[^"\']+["\'];\s*', '', script)
script = re.sub(r'(?m)^export ', '', script)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    for width, height in ((1440,900),(900,780),(390,844),(320,640)):
        page = browser.new_page(viewport={'width':width,'height':height})
        page.set_default_timeout(4500)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content(html)
        page.add_script_tag(content=script)
        assert page.locator('.conversation-card').count() == 2
        assert not errors
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        page.locator('.conversation-card').first.click()
        if width<=1040: page.locator('#detail-toggle').click()
        if width<=760: assert page.locator('#visual-app').get_attribute('data-mobile-view') == 'detail'
        page.locator('.detail-tab', has_text='Notas').click()
        page.locator('#note-text').fill('Nota interna fictícia de ensaio')
        page.locator('#internal-note-form button').click()
        assert page.locator('.detail-row').filter(has_text='Nota interna fictícia').count() == 1
        page.locator('.detail-tab', has_text='Histórico').click()
        assert page.locator('.activity-item').count() > 3
        if width<=760: page.locator('#detail-back').click()
        elif width<=1040: page.locator('#detail-close').click()
        page.locator('#request-completion').click()
        page.locator('#completion-form button[value=confirm]').click()
        if width<=1040: page.locator('#detail-toggle').click()
        assert page.locator('.detail-tab.active').inner_text() == 'Extração'
        page.get_by_role('button',name='Retorno parcial').click()
        page.locator('.detail-tab',has_text='Histórico').click()
        assert 'extração' in page.locator('.activity-item').first.inner_text().lower()
        print(f'FV-UI-002 {width}x{height}: PASS')
        page.close()
    page = browser.new_page(viewport={'width':1366,'height':768})
    page.set_content(html); page.add_script_tag(content=script)
    page.locator('#actor-select').select_option('marina')
    assert page.locator('.conversation-card').count() == 5
    page.locator('#team-nav').click()
    assert page.locator('#team-list .team-member').count() == 3
    page.locator('#team-close').click()
    page.locator('#shop-select').select_option('horizonte')
    assert page.locator('.conversation-card').count() == 2
    page.locator('#status-filter').select_option('em atendimento pelo operador')
    assert page.locator('.conversation-card').count() == 1
    page.locator('#actor-select').select_option('rafael')
    page.locator('#team-nav').click()
    assert not page.locator('#team-dialog').is_visible()
    print('FV-UI-002 gestor/escopo: PASS')
    browser.close()
