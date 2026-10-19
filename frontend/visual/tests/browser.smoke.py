"""FV-UI-013. Ensaio opcional REAL com Playwright/Chromium em checkout completo.
Sem rede/API de negócio: HTML/CSS/JS locais são injetados no navegador real.
O roteiro não prova autenticação, backend ou execução quando apenas versionado.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import os
import re

base = Path(__file__).resolve().parents[1]
html = (base / 'index.html').read_text(encoding='utf-8')
css = (base / 'styles.css').read_text(encoding='utf-8')
css_link = '<link rel="stylesheet" href="./styles.css">'
module_tag = '<script type="module" src="./app.mjs"></script>'
assert html.count(css_link) == 1, 'Link CSS duplicado ou inexistente'
assert html.count(module_tag) == 1, 'Script de entrada duplicado ou inexistente'
html = html.replace(css_link, '<style>'+css+'</style>')
html = html.replace(module_tag, '')
script = '\n'.join((base / name).read_text(encoding='utf-8') for name in ('fixtures.mjs','view-model.mjs','cf-op-02.mjs','registration-view.mjs','bank-view.mjs','postmark-view.mjs','team-operations.mjs','team-monitor.mjs','team-monitoring.mjs','batch-monitor.mjs','app.mjs'))
script = re.sub(r'(?ms)^import \{.*?\} from ["\']\./[^"\']+["\'];\s*', '', script)
script = re.sub(r'(?m)^export ', '', script)
assert 'import {' not in script and 'export ' not in script, 'Módulo não concatenado com segurança'
assert html.count('id="team-monitor"') == 1
assert html.count('id="team-batches"') == 1

with sync_playwright() as p:
    exe = os.getenv('CHROMIUM_EXECUTABLE', '').strip()
    if not exe and Path('/usr/bin/chromium').is_file(): exe='/usr/bin/chromium'
    browser_kwargs = {'headless': True, 'args': ['--no-sandbox']}
    if exe: browser_kwargs['executable_path'] = exe
    browser = p.chromium.launch(**browser_kwargs)
    for width, height in ((1440,900),(900,780),(390,844),(320,640)):
        page = browser.new_page(viewport={'width':width,'height':height})
        page.set_default_timeout(4500)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.set_content(html)
        page.add_script_tag(content=script)
        assert page.locator('.conversation-card').count() == 8
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
        assert not errors, 'Erros JavaScript durante jornada: '+repr(errors)
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), 'Overflow horizontal após interação'
        print(f'FV-UI-002 {width}x{height}: PASS')
        page.close()
    page = browser.new_page(viewport={'width':1366,'height':768})
    errors_main = []
    page.on('pageerror', lambda error: errors_main.append(str(error)))
    page.set_content(html); page.add_script_tag(content=script)
    assert not errors_main, 'Erro JavaScript no bootstrap da gestão'
    page.locator('#actor-select').select_option('marina')
    assert page.locator('.conversation-card').count() == 11
    page.locator('#team-nav').click()
    assert page.locator('#team-list .team-member').count() == 2
    page.locator('#team-show-monitor').click()
    assert page.locator('#team-monitor').is_visible()
    assert 'G3 · MONITORAMENTO DA PRÓPRIA EQUIPE' in page.locator('#team-monitor').inner_text()
    assert 'Caso A-112' in page.locator('#team-monitor').inner_text()
    assert 'Caso A-103' not in page.locator('#team-monitor').inner_text()
    assert 'Monitoramento operacional da equipe' in page.locator('#team-monitor').inner_text()
    assert 'Etapas comerciais canônicas' in page.locator('#team-monitor').inner_text()
    assert 'Prazos de espera e atrasos reais: NÃO VERIFICADOS' in page.locator('#team-monitor').inner_text()
    assert 'Bianca Rocha' not in page.locator('#team-monitor').inner_text()
    assert 'Cliente Exemplo' not in page.locator('#team-monitor').inner_text()
    page.locator('#team-show-members').click()
    assert page.locator('#team-list').is_visible()
    page.locator('#team-show-batches').click()
    assert page.locator('#team-batches').is_visible()
    assert 'L-G4-01' in page.locator('#team-batches').inner_text()
    assert 'L-G4-03' not in page.locator('#team-batches').inner_text()
    assert 'Contagens não confirmadas' in page.locator('#team-batches').inner_text()
    page.locator('#team-show-members').click()
    assert 'Rafael Lima' in page.locator('#team-list').inner_text()
    assert 'Bianca Rocha' not in page.locator('#team-list').inner_text()
    page.get_by_role('button',name='Solicitar pausa de novos leads para Rafael Lima',exact=False).click()
    assert 'SOLICITADO LOCALMENTE' in page.locator('#team-list').inner_text()
    page.locator('#team-close').click()
    page.locator('#actor-select').select_option('daniel')
    assert page.locator('.conversation-card').count() == 1
    page.locator('#team-nav').click()
    assert 'Bianca Rocha' in page.locator('#team-list').inner_text()
    assert 'Rafael Lima' not in page.locator('#team-list').inner_text()
    page.get_by_role('button',name='Solicitar retomada de novos leads para Bianca Rocha',exact=False).click()
    assert 'SOLICITADO LOCALMENTE' in page.locator('#team-list').inner_text()
    page.locator('#team-close').click()
    page.locator('#actor-select').select_option('marina')
    page.locator('#shop-select').select_option('horizonte')
    assert page.locator('.conversation-card').count() == 2
    page.locator('#status-filter').select_option('em atendimento pelo operador')
    assert page.locator('.conversation-card').count() == 1
    # O3: profissional atribuído enxerga apenas dados aplicados na projeção fictícia.
    page.locator('#actor-select').select_option('rafael')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 09',exact=False).click()
    page.locator('.detail-tab',has_text='Extração').click()
    assert 'Valor fictício confirmado' in page.locator('#detail-content').inner_text()
    assert 'Somente proposta' not in page.locator('#detail-content').inner_text()
    # Supervisora não autoatribuída vê resumo, mas não D3 nem fontes.
    page.locator('#actor-select').select_option('marina')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 09',exact=False).click()
    page.locator('.detail-tab',has_text='Extração').click()
    assert 'Detalhes restritos ao responsável' in page.locator('#detail-content').inner_text()
    assert 'Valor fictício confirmado' not in page.locator('#detail-content').inner_text()
    # O4: remessa e retorno sem inferir decisão; supervisora sem dados D4.
    page.locator('#actor-select').select_option('rafael')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 05',exact=False).click()
    page.locator('.detail-tab',has_text='Banco').click()
    assert 'bank-demo-v1' in page.locator('#detail-content').inner_text()
    assert 'Decisão bancária não confirmada' in page.locator('#detail-content').inner_text()
    page.locator('#actor-select').select_option('marina')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 05',exact=False).click()
    page.locator('.detail-tab',has_text='Banco').click()
    assert 'Acompanhamento bancário · resumo' in page.locator('#detail-content').inner_text()
    assert 'bank-demo-v1' not in page.locator('#detail-content').inner_text()
    page.locator('#actor-select').select_option('rafael')
    assert page.locator('#team-nav').is_hidden()
    assert page.locator('#team-nav-mobile').is_hidden()
    assert not page.locator('#team-dialog').is_visible()
    # FV-03: a janela expirada não permite texto livre, mas mantém o caso pendente.
    page.locator('[data-inbox="active"]').click()
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 08',exact=False).click()
    assert page.locator('#message-input').is_disabled()
    assert page.get_by_role('button',name='Selecionar e solicitar template aprovado').count()==1
    assert page.get_by_role('button',name='Solicitar cadeia de tentativas à IA').count()==1
    page.get_by_role('button',name='Selecionar e solicitar template aprovado').click()
    assert page.locator('#template-dialog').is_visible()
    # Escape cancela sem reutilizar confirmação antiga.
    page.keyboard.press('Escape')
    assert not page.locator('#template-dialog').is_visible()
    assert 'Pedido simulado' not in page.locator('#workflow-bar').inner_text()
    page.get_by_role('button',name='Selecionar e solicitar template aprovado').click()
    page.locator('#template-form button[value="confirm"]').click()
    assert page.locator('#message-input').is_disabled()
    assert 'Pedido simulado' in page.locator('#workflow-bar').inner_text()
    page.locator('[data-inbox="history"]').click()
    assert page.locator('.conversation-card').count()==3
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 12',exact=False).click()
    assert page.locator('#message-input').is_disabled()
    assert 'perdido' in page.locator('#workflow-bar').inner_text()
    # O5: vínculo S0 fictício permite navegar, sem mutar o marco anterior.
    page.locator('[data-inbox="active"]').click()
    page.get_by_role('button', name='Abrir conversa Cliente Exemplo 05', exact=False).click()
    page.locator('.detail-tab',has_text='Novo contato').click()
    page.get_by_role('button',name='Abrir novo atendimento humano').click()
    assert 'Caso A-114' in page.locator('#thread-meta').inner_text()
    assert page.locator('#message-input').is_enabled()
    page.get_by_role('button',name='Consultar atendimento de origem').click()
    assert 'Caso A-105' in page.locator('#thread-meta').inner_text()
    assert page.locator('#message-input').is_disabled()
    page.locator('[data-inbox="history"]').click()
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 16',exact=False).click()
    page.locator('.detail-tab',has_text='Novo contato').click()
    page.get_by_role('button',name='Abrir novo atendimento humano').click()
    assert 'Caso A-116' in page.locator('#thread-meta').inner_text()
    assert page.locator('#message-input').is_enabled()
    print('FV-UI-009 O5 pós-marco banco e venda: PASS')
    print('FV-03 janela, template e histórico: PASS')
    assert not errors_main, 'Erros JavaScript na gestão: '+repr(errors_main)
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), 'Overflow horizontal na gestão'
    print('FV-UI-002 gestor/escopo: PASS')
    page.close()

    mobile = browser.new_page(viewport={'width':390,'height':844})
    errors_mobile = []
    mobile.on('pageerror', lambda error: errors_mobile.append(str(error)))
    mobile.set_content(html)
    mobile.add_script_tag(content=script)
    assert mobile.locator('#team-nav-mobile').is_hidden()
    mobile.locator('#actor-select').select_option('marina')
    assert mobile.locator('#team-nav-mobile').is_visible()
    mobile.locator('#team-nav-mobile').click()
    assert mobile.locator('#team-dialog').is_visible()
    assert mobile.locator('#team-list .team-member').count() == 2
    mobile.keyboard.press('Escape')
    assert not mobile.locator('#team-dialog').is_visible()
    mobile.locator('#actor-select').select_option('otavio')
    assert mobile.locator('.conversation-card').count() == 0
    assert mobile.locator('#team-nav-mobile').is_hidden()
    assert 'Sem acesso demonstrativo' in mobile.locator('#conversation-items').inner_text()
    assert not errors_mobile, 'Erros JavaScript em gestão mobile: '+repr(errors_mobile)
    assert not mobile.evaluate('document.documentElement.scrollWidth > innerWidth'), 'Overflow mobile'
    print('FV-UI-004 acesso suspenso / equipe no celular: PASS')
    mobile.close()
    browser.close()
