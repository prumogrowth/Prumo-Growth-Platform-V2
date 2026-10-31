"""FV-UI-013. Ensaio opcional REAL com Playwright/Chromium em checkout completo.
Sem rede/API de negócio: HTML/CSS/JS locais são injetados no navegador real.
O roteiro não prova autenticação, backend ou execução quando apenas versionado.
"""
from playwright.sync_api import sync_playwright, expect
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
script = '\n'.join((base / name).read_text(encoding='utf-8') for name in ('fixtures.mjs','view-model.mjs','cf-op-02.mjs','registration-view.mjs','human-cycle-view.mjs','operation-feedback.mjs','bank-view.mjs','postmark-view.mjs','team-operations.mjs','team-pause-preview.mjs','team-monitor.mjs','team-monitoring.mjs','batch-monitor.mjs','distribution-view.mjs','transport-state-view.mjs','conversation-attention.mjs','local-audio.mjs','communication-composer.mjs','revision-fixtures.mjs','relationship-view.mjs','app.mjs'))
script = re.sub(r'(?ms)^import \{.*?\} from ["\']\./[^"\']+["\'];\s*', '', script)
script = re.sub(r'(?m)^export ', '', script)
assert 'import {' not in script and 'export ' not in script, 'Módulo não concatenado com segurança'
assert html.count('id="team-monitor"') == 1
assert html.count('id="team-batches"') == 1

# FV-REV-01/2: jornadas antigas usam os destinos reais das abas realocadas.
def leave_bank(page):
    if page.locator('#bank-dialog').is_visible():page.locator('#bank-close').click()

def case_content(page):
    return page.locator('#bank-content' if page.locator('#bank-dialog').is_visible() else '#detail-content')

def open_area(page, title):
    if title in ('Extração','Banco'):
        if not page.locator('#detail-pane').is_visible():page.locator('#thread-title').click()
        page.locator('#case-tab-overview').click()
        page.locator('#open-bank-case').click()
        expect(page.locator('#bank-dialog')).to_be_visible()
    else:
        page.locator('#case-tab-activity' if title in ('Novo contato','Recontatos') else '#case-tab-'+{'Resumo':'overview','Histórico':'activity','Notas':'notes'}[title]).click()

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
        page.evaluate("state.inboxView='active';renderList()")
        page.locator('#list-extra').evaluate('e=>e.open=true')
        assert page.locator('.conversation-card').count() == 8
        expect(page.locator('#visual-app')).to_have_attribute('data-theme', 'light')
        light_workspace = page.locator('.workspace').evaluate("node => getComputedStyle(node).backgroundColor")
        light_message = page.locator('.message').first.evaluate("node => getComputedStyle(node).backgroundColor")
        leave_bank(page)
        page.locator('#list-extra').evaluate('e=>e.open=false')
        page.locator('#ui-settings').evaluate('e => e.open = true')
        page.locator('#theme-dark').click()
        page.locator('#ui-settings').evaluate('e => e.open = false')
        expect(page.locator('#visual-app')).to_have_attribute('data-theme', 'dark')
        expect(page.locator('#theme-dark')).to_have_attribute('aria-pressed','true')
        dark_workspace = page.locator('.workspace').evaluate("node => getComputedStyle(node).backgroundColor")
        dark_message = page.locator('.message').first.evaluate("node => getComputedStyle(node).backgroundColor")
        assert light_workspace != dark_workspace
        assert light_message != dark_message
        leave_bank(page)
        page.locator('#list-extra').evaluate('e=>e.open=false')
        page.locator('#ui-settings').evaluate('e => e.open = true')
        page.locator('#theme-light').click()
        page.locator('#ui-settings').evaluate('e => e.open = false')
        expect(page.locator('#visual-app')).to_have_attribute('data-theme', 'light')
        expect(page.locator('#theme-light')).to_have_attribute('aria-pressed','true')
        # Um único indicador: numérico sem leitura, sem número após leitura por titular.
        assert page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).locator('.attention-unread').inner_text() == '2'
        assert not errors
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        # Selecionar caso estável, não depender de ordenação de conversas.
        leave_bank(page)
        page.locator('#list-extra').evaluate('e=>e.open=false')
        page.get_by_role('button', name='Abrir conversa Cliente Exemplo 02', exact=False).click()
        assert page.locator('.conversation-card').filter(has_text='Cliente Exemplo 02').locator('.attention-pending').count() == 1
        if width<=1040: page.locator('#thread-title').click()
        if width<=760: assert page.locator('#visual-app').get_attribute('data-mobile-view') == 'detail'
        page.locator('.detail-tab', has_text='Notas').click()
        page.locator('#note-text').fill('Nota interna fictícia de ensaio')
        page.locator('#internal-note-form button').click()
        # FV-UI-031: foco não deve cair no BODY quando a nota recria o formulário.
        expect(page.locator('#note-text')).to_be_focused()
        assert page.locator('.detail-row').filter(has_text='Nota interna fictícia').count() == 1
        page.locator('.detail-tab', has_text='Histórico').click()
        assert page.locator('.activity-item').count() > 3
        if width<=760: page.locator('#detail-back').click()
        elif width<=1040: page.locator('#detail-close').click()
        # FV-UI-017: prévia de autoria, confirmação APENAS local e alerta não resolvido.
        page.locator('#message-input').fill('Resposta em demonstração')
        page.locator('#composer .send-button').click()
        expect(page.locator('#message-preview-dialog')).to_be_visible()
        assert page.locator('#message-preview-body').inner_text().startswith('Consultor Rafael Lima:')
        page.locator('#message-preview-form button[value=confirm]').click()
        assert page.locator('#message-preview-dialog').is_hidden()
        assert 'NÃO ENVIADA' in page.locator('.message-send-state').last.inner_text()
        assert page.locator('.conversation-card').filter(has_text='Cliente Exemplo 02').locator('.attention-pending').count() == 1
        page.locator('#request-completion').click()
        page.locator('#completion-form button[value=confirm]').click()
        expect(page.locator('#bank-dialog')).to_be_visible()
        page.get_by_role('button',name='Retorno parcial').click()
        # FV-UI-032: resultado recria o DOM; aba persistente retoma o foco.
        expect(page.locator('#bank-case-select')).to_be_focused()
        assert 'Resultado técnico fictício Retorno parcial' in page.locator('#context-announcement').inner_text()
        leave_bank(page)
        if not page.locator('#detail-pane').is_visible():page.locator('#thread-title').click()
        page.locator('.detail-tab',has_text='Histórico').click()
        assert page.locator('.activity-item').filter(has_text=re.compile('extração',re.I)).count()==1
        assert not errors, 'Erros JavaScript durante jornada: '+repr(errors)
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), 'Overflow horizontal após interação'
        print(f'FV-UI-002 {width}x{height}: PASS')
        print('FV-UI-036 tema claro/escuro e superfícies neutras: PASS')
        page.close()
    dark_preference=browser.new_page(viewport={'width':1366,'height':768}, color_scheme='dark')
    dark_preference.set_content(html)
    dark_preference.add_script_tag(content=script)
    dark_preference.evaluate("state.inboxView='active';renderList()")
    dark_preference.locator('#list-extra').evaluate('e=>e.open=true')
    expect(dark_preference.locator('#visual-app')).to_have_attribute('data-theme','dark')
    expect(dark_preference.locator('body')).to_have_attribute('data-theme','dark')
    leave_bank(dark_preference)
    dark_preference.locator('#list-extra').evaluate('e=>e.open=false')
    dark_preference.locator('#ui-settings').evaluate('e => e.open = true')
    dark_preference.locator('#demo-dialog').evaluate('e=>e.showModal()')
    dark_preference.locator('#actor-select').select_option('marina')
    dark_preference.evaluate("state.inboxView='active';renderList()")
    dark_preference.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(dark_preference.locator('#demo-open')).to_be_focused()
    dark_preference.locator('#ui-settings').evaluate('e => e.open = false')
    dark_preference.locator('#team-nav').click()
    modal_surface=dark_preference.locator('#team-dialog').evaluate("node => getComputedStyle(node).backgroundColor")
    assert modal_surface=='rgb(29, 29, 29)',modal_surface
    dark_preference.locator('#team-close').click()
    leave_bank(dark_preference)
    dark_preference.locator('#list-extra').evaluate('e=>e.open=false')
    dark_preference.locator('#ui-settings').evaluate('e => e.open = true')
    dark_preference.locator('#theme-light').click()
    dark_preference.locator('#ui-settings').evaluate('e => e.open = false')
    expect(dark_preference.locator('body')).to_have_attribute('data-theme','light')
    dark_preference.close()
    print('FV-UI-036 preferência nativa escura e modais externos: PASS')
    page = browser.new_page(viewport={'width':1366,'height':768})
    errors_main = []
    page.on('pageerror', lambda error: errors_main.append(str(error)))
    page.set_content(html); page.add_script_tag(content=script)
    page.evaluate("state.inboxView='active';renderList()")
    assert not errors_main, 'Erro JavaScript no bootstrap da gestão'
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.locator('#ui-settings').evaluate('e => e.open = true')
    page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    page.locator('#actor-select').select_option('marina')
    page.evaluate("state.inboxView='active';renderList()")
    page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(page.locator('#demo-open')).to_be_focused()
    page.locator('#ui-settings').evaluate('e => e.open = false')
    assert page.locator('.conversation-card').count() == 12  # A-117 da equipe Marina, case-only da Lia
    # Supervisor acessa D2 sem zerar as não lidas do operador.
    assert page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).locator('.attention-unread').inner_text() == '2'
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    assert page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).locator('.attention-unread').inner_text() == '2'
    page.locator('#team-nav').click()
    assert page.locator('#team-list .team-member').count() == 2
    assert page.locator('.team-pause-preview').count() == 2
    page.locator('.team-pause-preview summary').first.click()
    assert 'Sem substituto na equipe' in page.locator('.team-pause-preview').first.inner_text()
    assert 'Somente prévia fictícia' in page.locator('.team-pause-preview').first.inner_text()
    page.locator('.team-pause-preview summary').first.click()
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
    assert page.locator('#intake-dialog').is_visible()
    assert 'SOLICITADO LOCALMENTE' not in page.locator('#team-list').inner_text()
    page.locator('#intake-form button[value=cancel]').click()
    assert 'SOLICITADO LOCALMENTE' not in page.locator('#team-list').inner_text()
    page.get_by_role('button',name='Solicitar pausa de novos leads para Rafael Lima',exact=False).click()
    page.locator('#intake-form button[value=confirm]').click()
    expect(page.locator('#team-list')).to_contain_text('SOLICITADO LOCALMENTE')
    page.locator('#team-close').click()
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.locator('#ui-settings').evaluate('e => e.open = true')
    page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    page.locator('#actor-select').select_option('daniel')
    page.evaluate("state.inboxView='active';renderList()")
    page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(page.locator('#demo-open')).to_be_focused()
    page.locator('#ui-settings').evaluate('e => e.open = false')
    assert page.locator('.conversation-card').count() == 1
    page.locator('#team-nav').click()
    assert 'Bianca Rocha' in page.locator('#team-list').inner_text()
    assert 'Rafael Lima' not in page.locator('#team-list').inner_text()
    page.get_by_role('button',name='Solicitar retomada de novos leads para Bianca Rocha',exact=False).click()
    page.locator('#intake-form button[value=confirm]').click()
    expect(page.locator('#team-list')).to_contain_text('SOLICITADO LOCALMENTE')
    page.locator('#team-close').click()
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.locator('#ui-settings').evaluate('e => e.open = true')
    page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    page.locator('#actor-select').select_option('marina')
    page.evaluate("state.inboxView='active';renderList()")
    page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(page.locator('#demo-open')).to_be_focused()
    page.locator('#ui-settings').evaluate('e => e.open = false')
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.locator('#ui-settings').evaluate('e => e.open = true')
    page.locator('#list-extra').evaluate('e=>e.open=true')
    page.locator('#shop-select').select_option('horizonte')
    page.evaluate("state.inboxView='active';renderList()")
    page.locator('#ui-settings').evaluate('e => e.open = false')
    assert page.locator('.conversation-card').count() == 2
    page.locator('#list-extra').evaluate('e => e.open = true')
    page.locator('#list-extra').evaluate('e=>e.open=true')
    page.locator('#status-filter').select_option('em atendimento pelo operador')
    assert page.locator('.conversation-card').count() == 1
    # O3: profissional atribuído enxerga apenas dados aplicados na projeção fictícia.
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.locator('#ui-settings').evaluate('e => e.open = true')
    page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    page.locator('#actor-select').select_option('rafael')
    page.evaluate("state.inboxView='active';renderList()")
    page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(page.locator('#demo-open')).to_be_focused()
    page.locator('#ui-settings').evaluate('e => e.open = false')
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 09',exact=False).click()
    open_area(page, 'Extração')
    assert 'Valor fictício confirmado' in case_content(page).inner_text()
    assert 'Somente proposta' not in case_content(page).inner_text()
    # Supervisora não autoatribuída vê resumo, mas não D3 nem fontes.
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.locator('#ui-settings').evaluate('e => e.open = true')
    page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    page.locator('#actor-select').select_option('marina')
    page.evaluate("state.inboxView='active';renderList()")
    page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(page.locator('#demo-open')).to_be_focused()
    page.locator('#ui-settings').evaluate('e => e.open = false')
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 09',exact=False).click()
    open_area(page, 'Extração')
    assert 'Detalhes restritos ao responsável' in case_content(page).inner_text()
    assert 'Valor fictício confirmado' not in case_content(page).inner_text()
    # O4: remessa e retorno sem inferir decisão; supervisora sem dados D4.
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.locator('#ui-settings').evaluate('e => e.open = true')
    page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    page.locator('#actor-select').select_option('rafael')
    page.evaluate("state.inboxView='active';renderList()")
    page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(page.locator('#demo-open')).to_be_focused()
    page.locator('#ui-settings').evaluate('e => e.open = false')
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 05',exact=False).click()
    open_area(page, 'Banco')
    assert 'bank-demo-v1' in case_content(page).inner_text()
    assert 'Decisão bancária não confirmada' in case_content(page).inner_text()
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.locator('#ui-settings').evaluate('e => e.open = true')
    page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    page.locator('#actor-select').select_option('marina')
    page.evaluate("state.inboxView='active';renderList()")
    page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(page.locator('#demo-open')).to_be_focused()
    page.locator('#ui-settings').evaluate('e => e.open = false')
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 05',exact=False).click()
    open_area(page, 'Banco')
    assert 'Acompanhamento bancário · resumo' in case_content(page).inner_text()
    assert 'bank-demo-v1' not in case_content(page).inner_text()
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.locator('#ui-settings').evaluate('e => e.open = true')
    page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    page.locator('#actor-select').select_option('rafael')
    page.evaluate("state.inboxView='active';renderList()")
    page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(page.locator('#demo-open')).to_be_focused()
    page.locator('#ui-settings').evaluate('e => e.open = false')
    assert page.locator('#team-nav').is_hidden()
    assert page.locator('#team-nav-mobile').is_hidden()
    assert not page.locator('#team-dialog').is_visible()
    # FV-03: a janela expirada não permite texto livre, mas mantém o caso pendente.
    page.locator('#list-extra').evaluate('e=>e.open=true')
    page.locator('[data-inbox="active"]').click()
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 08',exact=False).click()
    assert page.locator('#message-input').is_disabled()
    assert page.get_by_role('button',name='Enviar template').count()==1
    assert page.get_by_role('button',name='Cadeia por IA').count()==1
    page.get_by_role('button',name='Enviar template').click()
    assert page.locator('#template-dialog').is_visible()
    # Escape cancela sem reutilizar confirmação antiga.
    page.keyboard.press('Escape')
    assert not page.locator('#template-dialog').is_visible()
    assert 'Pedido simulado' not in page.locator('#workflow-bar').inner_text()
    page.get_by_role('button',name='Enviar template').click()
    page.locator('#template-form button[value="confirm"]').click()
    assert page.locator('#message-input').is_disabled()
    expect(page.locator('#workflow-bar')).to_contain_text('Pedido simulado')
    page.locator('#list-extra').evaluate('e=>e.open=true')
    page.locator('[data-inbox="history"]').click()
    assert page.locator('.conversation-card').count()==3
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 12',exact=False).click()
    assert page.locator('#message-input').is_disabled()
    assert 'Perdido' in page.locator('#terminal-banner').inner_text()
    # O5: vínculo S0 fictício permite navegar, sem mutar o marco anterior.
    page.locator('#list-extra').evaluate('e=>e.open=true')
    page.locator('[data-inbox="active"]').click()
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.get_by_role('button', name='Abrir conversa Cliente Exemplo 05', exact=False).click()
    open_area(page, 'Novo contato')
    page.get_by_role('button',name='Abrir novo atendimento humano').click()
    # FV-UI-032: botão do vínculo deixa o DOM; foco alcança região de destino.
    expect(page.locator('#thread-pane')).to_be_focused()
    assert 'Caso A-114 aberto por vínculo fictício autorizado' in page.locator('#context-announcement').inner_text()
    assert 'Caso A-114' in page.locator('#thread-meta').inner_text()
    assert page.locator('#message-input').is_enabled()
    page.get_by_role('button',name='Consultar atendimento de origem').click()
    assert 'Caso A-105' in page.locator('#thread-meta').inner_text()
    assert page.locator('#message-input').is_disabled()
    page.locator('#list-extra').evaluate('e=>e.open=true')
    page.locator('[data-inbox="history"]').click()
    leave_bank(page)
    page.locator('#list-extra').evaluate('e=>e.open=false')
    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 16',exact=False).click()
    open_area(page, 'Novo contato')
    page.get_by_role('button',name='Abrir novo atendimento humano').click()
    assert 'Caso A-116' in page.locator('#thread-meta').inner_text()
    assert page.locator('#message-input').is_enabled()
    print('FV-UI-009 O5 pós-marco banco e venda: PASS')
    print('FV-03 janela, template e histórico: PASS')
    assert not errors_main, 'Erros JavaScript na gestão: '+repr(errors_main)
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth'), 'Overflow horizontal na gestão'
    print('FV-UI-002 gestor/escopo: PASS')
    page.close()

    for mobile_width,mobile_height in ((390,844),(320,640)):
        mobile = browser.new_page(viewport={'width':mobile_width,'height':mobile_height})
        errors_mobile = []
        mobile.on('pageerror', lambda error: errors_mobile.append(str(error)))
        mobile.set_content(html)
        mobile.add_script_tag(content=script)
        mobile.evaluate("state.inboxView='active';renderList()")
        mobile.locator('#list-extra').evaluate('e=>e.open=true')
        assert mobile.locator('#team-nav-mobile').is_hidden()
        leave_bank(mobile)
        mobile.locator('#list-extra').evaluate('e=>e.open=false')
        mobile.locator('#ui-settings').evaluate('e => e.open = true')
        mobile.locator('#demo-dialog').evaluate('e=>e.showModal()')
        mobile.locator('#actor-select').select_option('marina')
        mobile.evaluate("state.inboxView='active';renderList()")
        mobile.locator('#demo-dialog').evaluate('e=>e.close()')
        expect(mobile.locator('#demo-open')).to_be_focused()
        mobile.locator('#ui-settings').evaluate('e => e.open = false')
        assert mobile.locator('#team-nav-mobile').is_visible()
        mobile.locator('#team-nav-mobile').click()
        assert mobile.locator('#team-dialog').is_visible()
        assert mobile.locator('#team-list .team-member').count() == 2
        # FV-UI-013: exercitar G3 e G4 também com navegação real no celular.
        assert mobile.locator('.team-help').evaluate('(e) => !e.open'), 'Explicação deve iniciar recolhida'
        mobile.locator('.team-help summary').click()
        assert mobile.locator('.team-help').evaluate('(e) => e.open'), 'Ajuda deve abrir via toque'
        assert 'S0/S1-002' in mobile.locator('.team-help').inner_text()
        mobile.locator('.team-help summary').click()
        mobile.locator('.team-help summary').focus()
        mobile.keyboard.press('Enter')
        assert mobile.locator('.team-help').evaluate('(e) => e.open'), 'Ajuda acessível via teclado'
        mobile.keyboard.press('Enter')
        assert mobile.locator('.team-help').evaluate('(e) => !e.open'), 'Ajuda recolhe via teclado'
        mobile.locator('#team-show-monitor').click()
        assert mobile.locator('#team-monitor').is_visible()
        # A primeira métrica deve estar dentro da altura visível do diálogo.
        assert mobile.locator('#team-monitor > .team-monitor-metrics').count() == 1
        assert mobile.evaluate('''() => {
            const d=document.querySelector('#team-dialog').getBoundingClientRect();
            const m=document.querySelector('#team-monitor .team-monitor-metric');
            return m.getBoundingClientRect().bottom <= d.bottom &&
                m.getBoundingClientRect().top >= d.top;
        }'''), 'Indicadores G3 devem ficar acessíveis sem rolar o diálogo'
        assert all(mobile.locator('#team-dialog .team-mode button').nth(i).evaluate('(e) => e.getBoundingClientRect().height >= 44') for i in range(3))

        monitor_mobile = mobile.locator('#team-monitor').inner_text()
        assert 'G3 · MONITORAMENTO DA PRÓPRIA EQUIPE' in monitor_mobile
        assert 'Monitoramento operacional da equipe' in monitor_mobile
        assert 'Caso A-112' in monitor_mobile
        assert 'Caso A-103' not in monitor_mobile
        assert 'Bianca Rocha' not in monitor_mobile
        mobile.locator('#team-show-batches').click()
        assert mobile.locator('#team-batches').is_visible()
        batches_mobile = mobile.locator('#team-batches').inner_text()
        assert 'L-G4-01' in batches_mobile
        assert 'L-G4-03' not in batches_mobile
        mobile.locator('#team-show-members').click()
        assert mobile.locator('#team-list').is_visible()
        assert 'Rafael Lima' in mobile.locator('#team-list').inner_text()
        assert 'Bianca Rocha' not in mobile.locator('#team-list').inner_text()
        assert not mobile.evaluate('document.documentElement.scrollWidth > innerWidth'), 'Overflow mobile em G3/G4'
        mobile.keyboard.press('Escape')
        assert not mobile.locator('#team-dialog').is_visible()
        leave_bank(mobile)
        mobile.locator('#list-extra').evaluate('e=>e.open=false')
        mobile.locator('#ui-settings').evaluate('e => e.open = true')
        mobile.locator('#demo-dialog').evaluate('e=>e.showModal()')
        mobile.locator('#actor-select').select_option('otavio')
        mobile.evaluate("state.inboxView='active';renderList()")
        mobile.locator('#demo-dialog').evaluate('e=>e.close()')
        expect(mobile.locator('#demo-open')).to_be_focused()
        mobile.locator('#ui-settings').evaluate('e => e.open = false')
        assert mobile.locator('.conversation-card').count() == 0
        assert mobile.locator('#team-nav-mobile').is_hidden()
        assert 'Sem acesso demonstrativo' in mobile.locator('#conversation-items').inner_text()
        assert not errors_mobile, 'Erros JavaScript em gestão mobile: '+repr(errors_mobile)
        assert not mobile.evaluate('document.documentElement.scrollWidth > innerWidth'), 'Overflow mobile'
        print('FV-UI-004 acesso suspenso / equipe no celular: PASS')
        mobile.close()
    # FV-UI-018: fila de gestores e caso excepcional somente-caso (não backend).
    queue_page=browser.new_page(viewport={'width':1366,'height':800})
    queue_page.set_content(html)
    queue_page.add_script_tag(content=script)
    queue_page.evaluate("state.inboxView='active';renderList()")
    queue_page.locator('#list-extra').evaluate('e=>e.open=true')
    leave_bank(queue_page)
    queue_page.locator('#list-extra').evaluate('e=>e.open=false')
    queue_page.locator('#ui-settings').evaluate('e => e.open = true')
    queue_page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    queue_page.locator('#actor-select').select_option('marina')
    queue_page.evaluate("state.inboxView='active';renderList()")
    queue_page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(queue_page.locator('#demo-open')).to_be_focused()
    queue_page.locator('#ui-settings').evaluate('e => e.open = false')
    queue_page.locator('#team-nav').click()
    queue_page.locator('#team-show-queue').click()
    assert 'FILA-A-01' in queue_page.locator('#team-queue').inner_text()
    queue_page.locator('#team-queue').get_by_role('button',name='Solicitar assunção').first.click()
    assert queue_page.locator('#queue-action-dialog').is_visible()
    queue_page.locator('#queue-action-form button[value=confirm]').click()
    expect(queue_page.locator('#queue-action-dialog')).to_be_hidden()
    expect(queue_page.locator('#team-queue')).to_contain_text('NÃO ATRIBUÍDO')
    queue_page.locator('#team-close').click()
    leave_bank(queue_page)
    queue_page.locator('#list-extra').evaluate('e=>e.open=false')
    queue_page.locator('#ui-settings').evaluate('e => e.open = true')
    queue_page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    queue_page.locator('#actor-select').select_option('daniel')
    queue_page.evaluate("state.inboxView='active';renderList()")
    queue_page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(queue_page.locator('#demo-open')).to_be_focused()
    queue_page.locator('#ui-settings').evaluate('e => e.open = false')
    queue_page.locator('#team-nav').click()
    queue_page.locator('#team-show-queue').click()
    assert 'FILA-A-01' in queue_page.locator('#team-queue').inner_text()
    queue_page.locator('#team-close').click()
    leave_bank(queue_page)
    queue_page.locator('#list-extra').evaluate('e=>e.open=false')
    queue_page.locator('#ui-settings').evaluate('e => e.open = true')
    queue_page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    queue_page.locator('#actor-select').select_option('lia')
    queue_page.evaluate("state.inboxView='active';renderList()")
    queue_page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(queue_page.locator('#demo-open')).to_be_focused()
    queue_page.locator('#ui-settings').evaluate('e => e.open = false')
    leave_bank(queue_page)
    queue_page.locator('#list-extra').evaluate('e=>e.open=false')
    queue_page.locator('#ui-settings').evaluate('e => e.open = true')
    queue_page.locator('#list-extra').evaluate('e=>e.open=true')
    queue_page.locator('#shop-select').select_option('aurora')
    queue_page.evaluate("state.inboxView='active';renderList()")
    queue_page.locator('#ui-settings').evaluate('e => e.open = false')
    assert queue_page.locator('.conversation-card').count()==1
    assert 'Cliente Exemplo 19' in queue_page.locator('#conversation-items').inner_text()
    assert 'Cliente Exemplo 02' not in queue_page.locator('#conversation-items').inner_text()
    queue_page.close()
    print('FV-UI-018 fila compartilhada e caso excepcional sintéticos: PASS')
    # FV-UI-019: dois cutoffs S0 da fixture; nova solicitação continua NÃO confirmada.
    cycle_page=browser.new_page(viewport={'width':1366,'height':800})
    cycle_page.set_content(html)
    cycle_page.add_script_tag(content=script)
    cycle_page.evaluate("state.inboxView='active';renderList()")
    cycle_page.locator('#list-extra').evaluate('e=>e.open=true')
    leave_bank(cycle_page)
    cycle_page.locator('#list-extra').evaluate('e=>e.open=false')
    cycle_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 09',exact=False).click()
    open_area(cycle_page, 'Extração')
    assert 'f03-a108-1' in case_content(cycle_page).inner_text()
    assert 'f03-a108-2' in case_content(cycle_page).inner_text()
    cycle_page.locator('#show-clarification-demo').click()
    # FV-UI-032: esclarecimento recriado mantém foco na aba.
    expect(cycle_page.locator('#bank-case-select')).to_be_focused()
    assert 'Cenário de esclarecimento fictício' in cycle_page.locator('#context-announcement').inner_text()
    assert 'CENÁRIO ALTERNATIVO' in cycle_page.locator('#workflow-bar').inner_text()
    leave_bank(cycle_page)
    cycle_page.locator('#request-completion').click()
    cycle_page.locator('#completion-form button[value=confirm]').click()
    expect(cycle_page.locator('#completion-dialog')).to_be_hidden()
    # O evento close nativo abre Banco; não escolher um locator do painel anterior
    # enquanto o callback de conclusão ainda está na fila de eventos.
    expect(cycle_page.locator('#bank-dialog')).to_be_visible()
    expect(case_content(cycle_page)).to_contain_text('a108-3')
    expect(case_content(cycle_page)).to_contain_text(re.compile('corte apenas candidato',re.I))
    details=case_content(cycle_page).inner_text()
    assert 'v1-ficticia' in details
    leave_bank(cycle_page)
    cycle_page.locator('#list-extra').evaluate('e=>e.open=false')
    cycle_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 15',exact=False).click()
    open_area(cycle_page, 'Extração')
    dossier=case_content(cycle_page).inner_text()
    assert 'live-form-v2-demo' in dossier and 'bank-demo-v1' in dossier
    leave_bank(cycle_page)
    cycle_page.locator('#list-extra').evaluate('e=>e.open=false')
    cycle_page.locator('#ui-settings').evaluate('e => e.open = true')
    cycle_page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    cycle_page.locator('#actor-select').select_option('marina')
    cycle_page.evaluate("state.inboxView='active';renderList()")
    cycle_page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(cycle_page.locator('#demo-open')).to_be_focused()
    cycle_page.locator('#ui-settings').evaluate('e => e.open = false')
    leave_bank(cycle_page)
    cycle_page.locator('#list-extra').evaluate('e=>e.open=false')
    cycle_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 09',exact=False).click()
    open_area(cycle_page, 'Extração')
    assert 'f03-a108-1' not in case_content(cycle_page).inner_text()
    cycle_page.close()
    # FV-UI-032: a navegação O5 móvel orienta no botão de retorno.
    mobile_link=browser.new_page(viewport={'width':390,'height':844})
    mobile_link.set_content(html)
    mobile_link.add_script_tag(content=script)
    mobile_link.evaluate("state.inboxView='active';renderList()")
    mobile_link.locator('#list-extra').evaluate('e=>e.open=true')
    leave_bank(mobile_link)
    mobile_link.locator('#list-extra').evaluate('e=>e.open=false')
    mobile_link.get_by_role('button',name='Abrir conversa Cliente Exemplo 05',exact=False).click()
    mobile_link.locator('#thread-title').click()
    open_area(mobile_link, 'Novo contato')
    mobile_link.get_by_role('button',name='Abrir novo atendimento humano').click()
    expect(mobile_link.locator('#thread-back')).to_be_focused()
    assert mobile_link.locator('#visual-app').get_attribute('data-mobile-view')=='thread'
    assert 'Caso A-114' in mobile_link.locator('#thread-meta').inner_text()
    mobile_link.close()
    print('FV-UI-019 histórico F03, reextração candidata e snapshot preservado: PASS')
    # FV-UI-020: ACK incerto não equivale a envio; prova sintética não altera comércio.
    technical=browser.new_page(viewport={'width':900,'height':780})
    technical.set_content(html)
    technical.add_script_tag(content=script)
    technical.evaluate("state.inboxView='active';renderList()")
    technical.locator('#list-extra').evaluate('e=>e.open=true')
    leave_bank(technical)
    technical.locator('#list-extra').evaluate('e=>e.open=false')
    technical.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    assert 'API aceitou · envio NÃO comprovado' in technical.locator('#thread-body').inner_text()
    assert 'Não tentar reenvio automático' in technical.locator('#thread-body').inner_text()
    leave_bank(technical)
    technical.locator('#list-extra').evaluate('e=>e.open=false')
    technical.get_by_role('button',name='Abrir conversa Cliente Exemplo 05',exact=False).click()
    assert 'Envio comprovado · fixture' in technical.locator('#thread-body').inner_text()
    leave_bank(technical)
    technical.locator('#list-extra').evaluate('e=>e.open=false')
    technical.locator('#ui-settings').evaluate('e => e.open = true')
    technical.locator('#demo-dialog').evaluate('e=>e.showModal()')
    technical.locator('#actor-select').select_option('marina')
    technical.evaluate("state.inboxView='active';renderList()")
    technical.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(technical.locator('#demo-open')).to_be_focused()
    technical.locator('#ui-settings').evaluate('e => e.open = false')
    leave_bank(technical)
    technical.locator('#list-extra').evaluate('e=>e.open=false')
    technical.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    assert 'API aceitou · envio NÃO comprovado' not in technical.locator('#thread-body').inner_text()
    technical.close()
    print('FV-UI-020 fronteira de transporte e supervisão: PASS')
    # FV-UI-021: foco, anúncio acessível, Home/End e viewport baixa; sem S0.
    access_page=browser.new_page(viewport={'width':390,'height':844})
    access_page.set_default_timeout(4500)
    access_page.set_content(html)
    access_page.add_script_tag(content=script)
    access_page.evaluate("state.inboxView='active';renderList()")
    access_page.locator('#list-extra').evaluate('e=>e.open=true')
    assert 'Consultor fictício' in access_page.locator('#context-announcement').inner_text()
    leave_bank(access_page)
    access_page.locator('#list-extra').evaluate('e=>e.open=false')
    access_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    assert 'Caso A-102 aberto' in access_page.locator('#context-announcement').inner_text()
    assert access_page.evaluate('document.activeElement.id') == 'thread-back'
    access_page.locator('#thread-title').click()
    assert access_page.evaluate('document.activeElement.id') == 'detail-back'
    access_page.locator('.detail-tab[role=tab]').first.focus()
    access_page.keyboard.press('End')
    assert access_page.locator('.detail-tab[aria-selected=true]').inner_text() == 'Notas'
    access_page.keyboard.press('Home')
    assert access_page.locator('.detail-tab[aria-selected=true]').inner_text() == 'Resumo'
    access_page.locator('#detail-back').click()
    assert access_page.evaluate('document.activeElement.id') == 'thread-title'
    access_page.locator('#thread-back').click()
    assert access_page.evaluate('document.activeElement.id') == 'search-input'
    leave_bank(access_page)
    access_page.locator('#list-extra').evaluate('e=>e.open=false')
    access_page.locator('#ui-settings').evaluate('e => e.open = true')
    access_page.locator('#demo-dialog').evaluate('e=>e.showModal()')
    access_page.locator('#actor-select').select_option('marina')
    access_page.evaluate("state.inboxView='active';renderList()")
    access_page.locator('#demo-dialog').evaluate('e=>e.close()')
    expect(access_page.locator('#demo-open')).to_be_focused()
    access_page.locator('#ui-settings').evaluate('e => e.open = false')
    assert 'Gestor fictício' in access_page.locator('#context-announcement').inner_text()
    assert 'A-102' not in access_page.locator('#context-announcement').inner_text()
    access_page.close()
    short_page=browser.new_page(viewport={'width':900,'height':480})
    short_page.set_content(html)
    short_page.add_script_tag(content=script)
    short_page.evaluate("state.inboxView='active';renderList()")
    short_page.locator('#list-extra').evaluate('e=>e.open=true')
    assert not short_page.evaluate('document.documentElement.scrollWidth > innerWidth')
    assert short_page.evaluate('document.querySelector(".visual-app").getBoundingClientRect().height <= innerHeight')
    short_page.close()
    print('FV-UI-021 foco móvel, anúncio, Home End e viewport baixa: PASS')
    # FV-UI-022: Escape move foco ao painel visível; cancelar mensagem não envia.
    focus_page=browser.new_page(viewport={'width':390,'height':844})
    focus_page.set_content(html)
    focus_page.add_script_tag(content=script)
    focus_page.evaluate("state.inboxView='active';renderList()")
    focus_page.locator('#list-extra').evaluate('e=>e.open=true')
    leave_bank(focus_page)
    focus_page.locator('#list-extra').evaluate('e=>e.open=false')
    focus_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    focus_page.locator('#message-input').fill('Rascunho de teste não enviado')
    focus_page.locator('#composer .send-button').click()
    assert focus_page.locator('#message-preview-dialog').is_visible()
    focus_page.keyboard.press('Escape')
    assert focus_page.locator('#message-preview-dialog').is_hidden()
    assert focus_page.locator('#message-input').input_value() == 'Rascunho de teste não enviado'
    expect(focus_page.locator('#message-input')).to_be_focused()
    assert 'Rascunho de teste não enviado' not in focus_page.locator('#thread-body').inner_text()
    focus_page.locator('#thread-back').focus()
    focus_page.keyboard.press('Escape')
    assert focus_page.locator('#visual-app').get_attribute('data-mobile-view') == 'list'
    assert focus_page.evaluate('document.activeElement.id') == 'search-input'
    leave_bank(focus_page)
    focus_page.locator('#list-extra').evaluate('e=>e.open=false')
    focus_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    assert focus_page.locator('#message-input').input_value() == ''
    focus_page.locator('#thread-title').click()
    focus_page.locator('#detail-back').focus()
    focus_page.keyboard.press('Escape')
    assert focus_page.locator('#visual-app').get_attribute('data-mobile-view') == 'thread'
    assert focus_page.evaluate('document.activeElement.id') == 'thread-title'
    focus_page.close()
    print('FV-UI-022 Escape mobile, contexto de mensagem e foco: PASS')
    # FV-UI-027: equivalente em viewport CSS de reflow sob zoom 200/400%.
    # Não substitui testes manuais de zoom real nem de leitores de tela.
    for zoom_label, zoom_width, zoom_height in (
        ('reflow-200', 720, 850), ('reflow-400-short', 360, 500),
        ('reflow-narrow', 320, 640)
    ):
        zoom_page=browser.new_page(
            viewport={'width':zoom_width,'height':zoom_height},
            reduced_motion='reduce')
        zoom_errors=[]
        zoom_page.on('pageerror',lambda error: zoom_errors.append(str(error)))
        zoom_page.set_content(html)
        zoom_page.add_script_tag(content=script)
        zoom_page.evaluate("state.inboxView='active';renderList()")
        zoom_page.locator('#list-extra').evaluate('e=>e.open=true')
        assert not zoom_page.evaluate('document.documentElement.scrollWidth > innerWidth'), zoom_label
        assert zoom_page.locator('.conversation-card').count()==8
        assert zoom_page.locator('.conversation-card').first.evaluate(
            '(e) => getComputedStyle(e).transitionDuration') == '0s', zoom_label
        if zoom_height<=700:
            assert zoom_page.locator('.list-pane').evaluate(
                '(e)=>e.scrollHeight > e.clientHeight'), zoom_label + ' sem rolagem vertical acessível'
            assert zoom_page.locator('.conversation-items').evaluate(
                '(e)=>e.getBoundingClientRect().height >= 170'), zoom_label + ' lista colapsada'
            zoom_page.locator('.conversation-card').last.scroll_into_view_if_needed()
            assert zoom_page.locator('.conversation-card').last.is_visible(), zoom_label
            zoom_page.locator('.list-footer').scroll_into_view_if_needed()
            footer=zoom_page.locator('.list-footer').bounding_box()
            assert footer is not None and 0 <= footer['y'] and footer['y']+footer['height'] <= zoom_height+1, zoom_label
        leave_bank(zoom_page)
        zoom_page.locator('#list-extra').evaluate('e=>e.open=false')
        zoom_page.get_by_role('button', name='Abrir conversa Cliente Exemplo 02', exact=False).click()
        assert zoom_page.locator('#visual-app').get_attribute('data-mobile-view')=='thread'
        assert zoom_page.locator('#message-input').is_visible()
        assert zoom_page.evaluate('document.activeElement.id')=='thread-back'
        zoom_page.locator('#thread-title').click()
        assert zoom_page.locator('#visual-app').get_attribute('data-mobile-view')=='detail'
        zoom_page.locator('#detail-back').click()
        assert zoom_page.evaluate('document.activeElement.id')=='thread-title'
        assert not zoom_page.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not zoom_errors, zoom_label + ': ' + repr(zoom_errors)
        zoom_page.close()
    # FV-UI-033: a mudança de breakpoint é diferente de abrir caso em viewport já estreito.
    # Teste real de reflow em Chromium (CSS pixels equivalentes a 200/400%).
    dynamic=browser.new_page(viewport={'width':1440,'height':900})
    dynamic.set_default_timeout(4500)
    dynamic_errors=[]
    dynamic.on('pageerror',lambda error:dynamic_errors.append(str(error)))
    dynamic.set_content(html);dynamic.add_script_tag(content=script)
    dynamic.evaluate("state.inboxView='active';renderList()")
    leave_bank(dynamic)
    dynamic.locator('#list-extra').evaluate('e=>e.open=false')
    dynamic.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    detail_tab=dynamic.locator('#case-tab-overview')
    detail_tab.focus()
    expect(detail_tab).to_be_focused()
    dynamic.set_viewport_size({'width':360,'height':500})
    expect(dynamic.locator('#visual-app')).to_have_attribute('data-mobile-view','detail')
    expect(detail_tab).to_be_visible()
    expect(detail_tab).to_be_focused()
    assert not dynamic.evaluate('document.documentElement.scrollWidth > innerWidth')
    dynamic.keyboard.press('End')
    expect(dynamic.locator('#case-tab-notes')).to_be_focused()
    dynamic.keyboard.press('Home')
    expect(detail_tab).to_be_focused()
    dynamic.set_viewport_size({'width':1440,'height':900})
    expect(detail_tab).to_be_visible()
    expect(detail_tab).to_be_focused()
    assert dynamic.locator('#thread-title').get_attribute('aria-expanded')=='true'
    assert not dynamic_errors,repr(dynamic_errors)
    dynamic.close()

    # Caso inverso: aba Detalhes iniciada em 400%-equivalente (320px) não
    # pode desaparecer quando a viewport volta ao modo desktop em zoom 100%.
    narrow=browser.new_page(viewport={'width':320,'height':480})
    narrow.set_content(html);narrow.add_script_tag(content=script)
    narrow.evaluate("state.inboxView='active';renderList()")
    leave_bank(narrow)
    narrow.locator('#list-extra').evaluate('e=>e.open=false')
    narrow.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    narrow.locator('#thread-title').click()
    narrow.locator('#case-tab-overview').focus()
    narrow.set_viewport_size({'width':1440,'height':900})
    expect(narrow.locator('#case-tab-overview')).to_be_visible()
    expect(narrow.locator('#case-tab-overview')).to_be_focused()
    assert narrow.locator('#thread-title').get_attribute('aria-expanded')=='true'
    narrow.close()

    # A lista e o compositor não devem saltar arbitrariamente para outra aba
    # quando o usuário altera o zoom sem abrir Detalhes.
    for source,target in [('list','list'),('thread','thread')]:
        responsive=browser.new_page(viewport={'width':1440,'height':900})
        responsive.set_content(html);responsive.add_script_tag(content=script)
        responsive.evaluate("state.inboxView='active';renderList()")
        if source=='thread':
            leave_bank(responsive)
            responsive.locator('#list-extra').evaluate('e=>e.open=false')
            responsive.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
            responsive.locator('#message-input').focus()
        else: responsive.locator('#search-input').focus()
        responsive.set_viewport_size({'width':320,'height':480})
        expect(responsive.locator('#visual-app')).to_have_attribute('data-mobile-view',target)
        expect(responsive.locator('#message-input' if target=='thread' else '#search-input')).to_be_focused()
        assert not responsive.evaluate('document.documentElement.scrollWidth > innerWidth')
        responsive.close()
    # FV-UI-035: o botão Voltar existe só no layout mobile. Quando a viewport
    # aumenta, o foco não deve desaparecer nem ficar no BODY/controle oculto.
    for destination_width in (900,1440):
        for view in ('thread','detail'):
            backflow=browser.new_page(viewport={'width':390,'height':844})
            backflow.set_default_timeout(4500)
            backflow_errors=[]
            backflow.on('pageerror',lambda error:backflow_errors.append(str(error)))
            backflow.set_content(html);backflow.add_script_tag(content=script)
            backflow.evaluate("state.inboxView='active';renderList()")
            leave_bank(backflow)
            backflow.locator('#list-extra').evaluate('e=>e.open=false')
            backflow.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
            if view=='detail':backflow.locator('#thread-title').click()
            backflow.locator('#'+view+'-back').focus()
            expect(backflow.locator('#'+view+'-back')).to_be_focused()
            backflow.set_viewport_size({'width':destination_width,'height':780})
            target='#thread-pane' if view=='thread' else '#case-tab-overview'
            expect(backflow.locator(target)).to_be_focused()
            expect(backflow.locator(target)).to_be_visible()
            assert 'Caso A-102' in backflow.locator('#thread-meta').inner_text()
            assert not backflow.evaluate('document.documentElement.scrollWidth > innerWidth')
            assert not backflow_errors,repr(backflow_errors)
            backflow.close()
    print('FV-UI-035 retorno de foco ao ampliar mobile para desktop/tablet: PASS')

    print('FV-UI-033 foco e reflow na transição de breakpoints: PASS')

    # FV-UI-034: Escape e Fechar no overlay de 761..1040 px não podem
    # deixar o teclado sobre controle invisível nem interferir no compositor.
    for width in (900,1024):
        overlay=browser.new_page(viewport={'width':width,'height':780})
        overlay.set_default_timeout(4500)
        overlay_errors=[]
        overlay.on('pageerror',lambda error:overlay_errors.append(str(error)))
        overlay.set_content(html);overlay.add_script_tag(content=script)
        overlay.evaluate("state.inboxView='active';renderList()")
        leave_bank(overlay)
        overlay.locator('#list-extra').evaluate('e=>e.open=false')
        overlay.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
        overlay.locator('#thread-title').click()
        expect(overlay.locator('#detail-pane')).to_be_visible()
        overlay.locator('#detail-close').focus()
        overlay.keyboard.press('Enter')
        expect(overlay.locator('#detail-pane')).to_be_hidden()
        expect(overlay.locator('#thread-title')).to_be_focused()
        expect(overlay.locator('#thread-title')).to_have_attribute('aria-expanded','false')
        assert 'Caso A-102' in overlay.locator('#thread-meta').inner_text()
        overlay.locator('#thread-title').click()
        overlay.locator('#case-tab-overview').focus()
        overlay.keyboard.press('Escape')
        expect(overlay.locator('#detail-pane')).to_be_hidden()
        expect(overlay.locator('#thread-title')).to_be_focused()
        overlay.locator('#thread-title').click()
        overlay.locator('#case-tab-notes').click()
        overlay.locator('#note-text').fill('Rascunho de nota local')
        overlay.keyboard.press('Escape')
        expect(overlay.locator('#detail-pane')).to_be_visible()
        expect(overlay.locator('#note-text')).to_be_focused()
        assert 'Rascunho de nota local' == overlay.locator('#note-text').input_value()
        assert not overlay.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not overlay_errors,repr(overlay_errors)
        overlay.close()
    print('FV-UI-034 Escape tablet e foco ao fechar detalhes: PASS')

    print('FV-UI-027 reflow responsivo, rolagem e movimento reduzido: PASS')
    # FV-UI-028: aria-expanded acompanha o painel visível; foco de teclado contrastante.
    for viewport in ({'width':390,'height':844},{'width':320,'height':640}):
        aria_page=browser.new_page(viewport=viewport)
        aria_page.set_default_timeout(4500)
        aria_errors=[]
        aria_page.on('pageerror',lambda e:aria_errors.append(str(e)))
        aria_page.set_content(html)
        aria_page.add_script_tag(content=script)
        aria_page.evaluate("state.inboxView='active';renderList()")
        aria_page.locator('#list-extra').evaluate('e=>e.open=true')
        toggler=aria_page.locator('#thread-title')
        expect(toggler).to_have_attribute('aria-expanded','false')
        leave_bank(aria_page)
        aria_page.locator('#list-extra').evaluate('e=>e.open=false')
        aria_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
        expect(toggler).to_have_attribute('aria-expanded','false')
        toggler.click()
        expect(toggler).to_have_attribute('aria-expanded','true')
        assert aria_page.locator('#detail-pane').is_visible()
        aria_page.keyboard.press('Escape')
        expect(toggler).to_have_attribute('aria-expanded','false')
        assert aria_page.locator('#thread-pane').is_visible()
        toggler.click()
        expect(toggler).to_have_attribute('aria-expanded','true')
        aria_page.locator('#detail-back').click()
        expect(toggler).to_have_attribute('aria-expanded','false')
        aria_page.locator('#thread-back').click()
        leave_bank(aria_page)
        aria_page.locator('#list-extra').evaluate('e=>e.open=false')
        aria_page.locator('#ui-settings').evaluate('e => e.open = true')
        aria_page.locator('#demo-dialog').evaluate('e=>e.showModal()')
        aria_page.locator('#actor-select').select_option('marina')
        aria_page.evaluate("state.inboxView='active';renderList()")
        aria_page.locator('#demo-dialog').evaluate('e=>e.close()')
        expect(aria_page.locator('#demo-open')).to_be_focused()
        aria_page.locator('#ui-settings').evaluate('e => e.open = false')
        expect(toggler).to_have_attribute('aria-expanded','false')
        assert aria_page.locator('#visual-app').get_attribute('data-mobile-view')=='list'
        # COR-01: o filtro precede Configurações e Busca na ordem do cabeçalho.
        leave_bank(aria_page)
        aria_page.locator('#list-extra').evaluate('e=>e.open=false')
        aria_page.locator('#search-input').focus()
        aria_page.keyboard.press('Shift+Tab')
        aria_page.keyboard.press('Shift+Tab')
        focus=aria_page.evaluate("""()=>({tag:document.activeElement?.tagName,
            outline:getComputedStyle(document.activeElement).outlineColor,
            width:getComputedStyle(document.activeElement).outlineWidth})""")
        assert focus['tag']=='SUMMARY',focus
        assert focus['width']=='3px' and focus['outline']=='rgb(92, 92, 92)',focus
        assert not aria_page.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not aria_errors,aria_errors
        aria_page.close()
    print('FV-UI-028 acessibilidade teclado, painel e foco: PASS')
    # FV-UI-029: após confirmar ação aninhada, o gatilho foi re-renderizado.
    # O foco deve ficar numa aba ESTÁVEL dentro do modal maior, nunca no BODY.
    for width,height in ((390,844),(1366,768)):
        focus_team=browser.new_page(viewport={'width':width,'height':height})
        focus_team.set_default_timeout(4500)
        focus_team.set_content(html)
        focus_team.add_script_tag(content=script)
        focus_team.evaluate("state.inboxView='active';renderList()")
        focus_team.locator('#list-extra').evaluate('e=>e.open=true')
        leave_bank(focus_team)
        focus_team.locator('#list-extra').evaluate('e=>e.open=false')
        focus_team.locator('#ui-settings').evaluate('e => e.open = true')
        focus_team.locator('#demo-dialog').evaluate('e=>e.showModal()')
        focus_team.locator('#actor-select').select_option('marina')
        focus_team.evaluate("state.inboxView='active';renderList()")
        focus_team.locator('#demo-dialog').evaluate('e=>e.close()')
        expect(focus_team.locator('#demo-open')).to_be_focused()
        focus_team.locator('#ui-settings').evaluate('e => e.open = false')
        focus_team.locator('#team-nav-mobile' if width<=760 else '#team-nav').click()
        expect(focus_team.locator('#team-dialog')).to_be_visible()
        focus_team.locator('#team-list .team-member button').first.click()
        expect(focus_team.locator('#intake-dialog')).to_be_visible()
        focus_team.locator('#intake-form button[value=confirm]').click()
        expect(focus_team.locator('#intake-dialog')).to_be_hidden()
        expect(focus_team.locator('#team-show-members')).to_be_focused()
        expect(focus_team.locator('#team-action-announcement')).to_contain_text('não aplicada no S0/S1')
        focus_team.locator('#team-show-queue').click()
        focus_team.locator('#team-queue button').first.click()
        expect(focus_team.locator('#queue-action-dialog')).to_be_visible()
        focus_team.locator('#queue-action-form button[value=confirm]').click()
        expect(focus_team.locator('#queue-action-dialog')).to_be_hidden()
        expect(focus_team.locator('#team-show-queue')).to_be_focused()
        expect(focus_team.locator('#team-action-announcement')).to_contain_text('Nenhuma atribuição')
        assert focus_team.locator('#team-dialog').is_visible()
        assert not focus_team.evaluate('document.documentElement.scrollWidth > innerWidth')
        focus_team.close()
    print('FV-UI-029 confirmação, anúncio e retorno do foco: PASS')
    # FV-UI-037: preferência do SO ao vivo até escolha manual.
    follow_system=browser.new_page(viewport={'width':390,'height':844},color_scheme='light')
    follow_system.set_content(html);follow_system.add_script_tag(content=script)
    follow_system.evaluate("state.inboxView='active';renderList()")
    expect(follow_system.locator('#visual-app')).to_have_attribute('data-theme','light')
    follow_system.emulate_media(color_scheme='dark')
    expect(follow_system.locator('#visual-app')).to_have_attribute('data-theme','dark')
    expect(follow_system.locator('body')).to_have_attribute('data-theme','dark')
    follow_system.emulate_media(color_scheme='light')
    expect(follow_system.locator('#visual-app')).to_have_attribute('data-theme','light')
    leave_bank(follow_system)
    follow_system.locator('#list-extra').evaluate('e=>e.open=false')
    follow_system.locator('#ui-settings').evaluate('e => e.open = true')
    follow_system.locator('#theme-light').click()
    follow_system.locator('#ui-settings').evaluate('e => e.open = false')
    follow_system.emulate_media(color_scheme='dark')
    expect(follow_system.locator('#visual-app')).to_have_attribute('data-theme','light')
    expect(follow_system.locator('#theme-light')).to_have_attribute('aria-pressed','true')
    assert not follow_system.evaluate('document.documentElement.scrollWidth > innerWidth')
    follow_system.close()
    print('FV-UI-037 sistema e escolha manual: PASS')

    # FV-UI-038: contraste real em diálogos gerenciais do tema escuro.
    # Testar textos pequenos em lotes, monitoramento e fila, não dados comerciais.
    for manager_width in (1366,390):
        manager_dark=browser.new_page(viewport={'width':manager_width,'height':800},color_scheme='dark')
        manager_dark.set_default_timeout(4500)
        manager_errors=[]
        manager_dark.on('pageerror',lambda error:manager_errors.append(str(error)))
        manager_dark.set_content(html);manager_dark.add_script_tag(content=script)
        manager_dark.evaluate("state.inboxView='active';renderList()")
        expect(manager_dark.locator('body')).to_have_attribute('data-theme','dark')
        leave_bank(manager_dark)
        manager_dark.locator('#list-extra').evaluate('e=>e.open=false')
        manager_dark.locator('#ui-settings').evaluate('e => e.open = true')
        manager_dark.locator('#demo-dialog').evaluate('e=>e.showModal()')
        manager_dark.locator('#actor-select').select_option('marina')
        manager_dark.evaluate("state.inboxView='active';renderList()")
        manager_dark.locator('#demo-dialog').evaluate('e=>e.close()')
        expect(manager_dark.locator('#demo-open')).to_be_focused()
        manager_dark.locator('#ui-settings').evaluate('e => e.open = false')
        manager_dark.locator('#team-nav-mobile' if manager_width<=760 else '#team-nav').click()
        contrast_js="""selector => {
          const el=document.querySelector(selector);
          if(!el) return null;
          const rgb=value=>{const match=value.match(/rgba?\\(([^)]+)\\)/);
            return match ? match[1].split(',').slice(0,3).map(Number) : null;};
          const lum=v=>{const xs=v.map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);
            return .2126*xs[0]+.7152*xs[1]+.0722*xs[2];};
          const fg=rgb(getComputedStyle(el).color);
          let element=el,bg=null;
          while(element){const raw=getComputedStyle(element).backgroundColor;
            if(raw && !raw.endsWith(', 0)') && raw!=='transparent'){bg=rgb(raw);break;}
            element=element.parentElement;}
          if(!fg||!bg)return null;
          const a=lum(fg),b=lum(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
        }"""
        manager_dark.locator('#team-show-batches').click()
        for selector in ('.team-batch-summary','.team-batch-card span','.team-help summary'):
            ratio=manager_dark.evaluate(contrast_js,selector)
            assert ratio is not None and ratio>=4.5,(manager_width,selector,ratio)
        manager_dark.locator('#team-show-monitor').click()
        for selector in ('.team-monitor-metric span','.team-monitor-stage'):
            ratio=manager_dark.evaluate(contrast_js,selector)
            assert ratio is not None and ratio>=4.5,(manager_width,selector,ratio)
        manager_dark.locator('#team-show-queue').click()
        ratio=manager_dark.evaluate(contrast_js,'.team-queue-item span')
        assert ratio is not None and ratio>=4.5,(manager_width,'team queue',ratio)
        assert not manager_dark.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not manager_errors,repr(manager_errors)
        manager_dark.close()
    print('FV-UI-038 contraste de painel gerencial em dark desktop e mobile: PASS')

    # FV-UI-039: ações claro/escuro devem ser tocáveis sem comprimir o cabeçalho.
    for theme_width in (320,390,900,1440):
        touch=browser.new_page(viewport={'width':theme_width,'height':640},color_scheme='light')
        touch.set_default_timeout(4500)
        touch_errors=[]
        touch.on('pageerror',lambda error:touch_errors.append(str(error)))
        touch.set_content(html);touch.add_script_tag(content=script)
        touch.evaluate("state.inboxView='active';renderList()")
        expect(touch.locator('#ui-settings > summary')).to_be_visible()
        assert touch.locator('#ui-settings > summary').bounding_box()['width']>=44
        leave_bank(touch)
        touch.locator('#list-extra').evaluate('e=>e.open=false')
        touch.locator('#ui-settings').evaluate('e => e.open = true')
        for theme in ('light','dark'):
            btn=touch.locator('#theme-'+theme)
            btn.click()
            expect(btn).to_have_attribute('aria-pressed','true')
            box=btn.bounding_box()
            assert box and box['width']>=44 and box['height']>=44,(theme_width,theme,box)
            assert touch.locator('#theme-light').is_visible() and touch.locator('#theme-dark').is_visible()
            assert not touch.evaluate('document.documentElement.scrollWidth > innerWidth')
        touch.locator('#ui-settings').evaluate('e => e.open = false')
        assert not touch.locator('#theme-light').is_visible()
        assert not touch_errors,repr(touch_errors)
        touch.close()
    print('FV-UI-039 botoes de tema 44px e reflow em quatro larguras: PASS')

    # FV-UI-040: hierarquia da fila em ambos os temas, com contraste e sem overflow.
    contrast_function="""selector => {
      const node=document.querySelector(selector);if(!node)return null;
      const parse=s=>{const m=s.match(/rgba?\(([^)]+)\)/);return m?m[1].split(',').map(Number):null};
      const luminance=v=>{const a=v.slice(0,3).map(n=>n/255).map(n=>n<=.04045?n/12.92:((n+.055)/1.055)**2.4);
        return .2126*a[0]+.7152*a[1]+.0722*a[2]};
      const foreground=parse(getComputedStyle(node).color);if(!foreground)return null;
      let target=node,background=null;
      while(target){const color=parse(getComputedStyle(target).backgroundColor);
        if(color && (color.length<4 || color[3]>=1)){background=color;break;}
        target=target.parentElement;}
      if(!background)return null;
      const x=luminance(foreground),y=luminance(background);
      return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
    }"""
    for queue_width in (320,390,900,1440):
        for queue_theme in ('light','dark'):
            queue_page=browser.new_page(viewport={'width':queue_width,'height':820},color_scheme=queue_theme)
            queue_page.set_default_timeout(4500)
            queue_page.set_content(html);queue_page.add_script_tag(content=script)
            queue_page.evaluate("state.inboxView='active';renderList()")
            expect(queue_page.locator('#visual-app')).to_have_attribute('data-theme',queue_theme)
            expect(queue_page.locator('.conversation-card.is-selected')).to_have_count(1)
            for selector,min_font in (('.conversation-card.is-selected .item-title',14),
                ('.conversation-card.is-selected .item-preview',12),
                ('.conversation-card.is-selected .item-time',11),
                ('.summary-tile span',11)):
                item=queue_page.locator(selector).first
                assert item.count()>0,(queue_width,queue_theme,selector)
                size=float(item.evaluate('node=>parseFloat(getComputedStyle(node).fontSize)'))
                assert size>=min_font,(queue_width,queue_theme,selector,size)
                ratio=queue_page.evaluate(contrast_function,selector)
                assert ratio is not None and ratio>=4.5,(queue_width,queue_theme,selector,ratio)
            assert queue_page.locator('.conversation-card .micro-tag').count()==0
            assert queue_page.locator('.conversation-card.is-selected').evaluate(
                'node=>getComputedStyle(node).boxShadow')!='none'
            assert not queue_page.evaluate('document.documentElement.scrollWidth > innerWidth')
            queue_page.close()
    print('FV-UI-040 hierarquia legivel da fila em 8 cenarios: PASS')

    # FV-UI-041: detalhes com tipografia legivel em claro/escuro e responsividade.
    for detail_width in (320,390,900,1440):
        for detail_theme in ('light','dark'):
            detail_page=browser.new_page(viewport={'width':detail_width,'height':820},color_scheme=detail_theme)
            detail_page.set_default_timeout(4500)
            detail_page.set_content(html);detail_page.add_script_tag(content=script)
            detail_page.evaluate("state.inboxView='active';renderList()")
            leave_bank(detail_page)
            detail_page.locator('#list-extra').evaluate('e=>e.open=false')
            detail_page.locator('#ui-settings').evaluate('e => e.open = true')
            detail_page.locator('#theme-'+detail_theme).click()
            detail_page.locator('#ui-settings').evaluate('e => e.open = false')
            if detail_width<=760:
                leave_bank(detail_page)
                detail_page.locator('#list-extra').evaluate('e=>e.open=false')
                detail_page.locator('.conversation-card').first.click()
                detail_page.locator('#thread-title').click()
            else:
                detail_page.locator('#thread-title').click() if not detail_page.locator('#detail-pane').is_visible() else None
            expect(detail_page.locator('#detail-pane')).to_be_visible()
            expect(detail_page.locator('#case-tab-overview')).to_have_attribute('aria-selected','true')
            for selector,min_font in (('.detail-pane .case-context',12),('.detail-pane .detail-label',11),('.detail-pane .property span',12),('.detail-pane .property strong',12),('.detail-pane .detail-tab.active',12)):
                node=detail_page.locator(selector).first
                assert node.count()>0,(detail_width,detail_theme,selector)
                size=float(node.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'))
                assert size>=min_font,(detail_width,detail_theme,selector,size)
            contrast_js = """selector => {
              const e=document.querySelector(selector);if(!e)return null;
              const rgb=x=>{const m=x.match(/rgba?\(([^)]+)\)/);return m?m[1].split(',').map(Number):null};
              const lum=x=>{const y=x.slice(0,3).map(z=>z/255).map(z=>z<=.04045?z/12.92:((z+.055)/1.055)**2.4);return .2126*y[0]+.7152*y[1]+.0722*y[2]};
              const fg=rgb(getComputedStyle(e).color);let node=e,bg=null;
              while(node){const computed=rgb(getComputedStyle(node).backgroundColor);
                if(computed && (computed.length<4 || computed[3]>=1)){bg=computed;break;}node=node.parentElement;}
              if(!fg||!bg)return null;const a=lum(fg),b=lum(bg);
              return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
            }"""
            for selector in ('.detail-pane .detail-label','.detail-pane .property span','.detail-pane .property strong','.detail-pane .detail-tab.active'):
                ratio=detail_page.evaluate(contrast_js,selector)
                assert ratio is not None and ratio>=4.5,(detail_width,detail_theme,selector,ratio)
            for tab in ('notes','overview'):
                detail_page.locator('#case-tab-'+tab).click()
                expect(detail_page.locator('#case-tab-'+tab)).to_have_attribute('aria-selected','true')
                if tab=='notes':
                    ratio=detail_page.evaluate(contrast_js,'.detail-pane .detail-callout')
                    assert ratio is not None and ratio>=4.5,(detail_width,detail_theme,'note callout',ratio)
            assert not detail_page.evaluate('document.documentElement.scrollWidth > innerWidth'),(detail_width,detail_theme)
            detail_page.close()
    print('FV-UI-041 detalhes legiveis em oito cenarios e abas preservadas: PASS')

    # FV-UI-042: legibilidade da conversa, ambas as cores e quatro larguras.
    for thread_width in (320,390,900,1440):
        for thread_theme in ('light','dark'):
            readable=browser.new_page(viewport={'width':thread_width,'height':820},color_scheme=thread_theme)
            readable.set_default_timeout(4500)
            errors_042=[]
            readable.on('pageerror',lambda error:errors_042.append(str(error)))
            readable.set_content(html);readable.add_script_tag(content=script)
            readable.evaluate("state.inboxView='active';renderList()")
            if thread_width<=760:
                leave_bank(readable)
                readable.locator('#list-extra').evaluate('e=>e.open=false')
                readable.locator('.conversation-card').first.click()
            expect(readable.locator('#thread-pane')).to_be_visible()
            expect(readable.locator('#visual-app')).to_have_attribute('data-theme',thread_theme)
            assert readable.locator('.thread-pane .message').count()>0
            for selector,minimum in (('.thread-pane .thread-name',14),
                ('.thread-pane .thread-meta',11),('.thread-pane .message',13),
                ('.thread-pane .message small',11),('.thread-pane .day-separator',11),
                ('.thread-pane .composer-note',11)):
                node=readable.locator(selector).first
                assert node.count()>0,(thread_width,thread_theme,selector)
                size=float(node.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'))
                assert size>=minimum,(thread_width,thread_theme,selector,size)
                ratio=readable.evaluate("""selector=>{
                  let e=document.querySelector(selector);if(!e)return null;
                  const rgb=t=>{const m=t.match(/rgba?\(([^)]+)\)/);return m?m[1].split(',').map(Number):null};
                  const lum=v=>{const a=v.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return a[0]*.2126+a[1]*.7152+a[2]*.0722};
                  const fg=rgb(getComputedStyle(e).color);let bg=null;
                  while(e){const c=rgb(getComputedStyle(e).backgroundColor);
                    if(c&&(c.length<4||c[3]>=1)){bg=c;break;}e=e.parentElement}
                  if(!fg||!bg)return null;
                  const x=lum(fg),y=lum(bg);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)
                }""",selector)
                assert ratio is not None and ratio>=4.5,(thread_width,thread_theme,selector,ratio)
            if readable.locator('.message-transport-hint').count():
                technical=readable.evaluate("""selector=>{
                  let e=document.querySelector(selector);const rgb=t=>{let m=t.match(/rgba?\(([^)]+)\)/);return m?m[1].split(',').map(Number):null};
                  const L=v=>{let a=v.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return a[0]*.2126+a[1]*.7152+a[2]*.0722};
                  let fg=rgb(getComputedStyle(e).color),bg=null;while(e){let c=rgb(getComputedStyle(e).backgroundColor);
                    if(c&&(c.length<4||c[3]>=1)){bg=c;break;}e=e.parentElement}
                  if(!fg||!bg)return null;let x=L(fg),y=L(bg);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)
                }""",'.message-transport-hint')
                assert technical is not None and technical>=4.5,(thread_width,thread_theme,'transport contrast',technical)
            assert not readable.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not errors_042,errors_042
            readable.close()
    print('FV-UI-042 conversa legivel 8 cenarios 4.5:1 PASS')

    # FV-UI-043: legibilidade, foco, toque e estados do rodape em claro/escuro.
    contrast_043="""selector=>{let e=document.querySelector(selector);if(!e)return null;
      const rgb=t=>{const m=t.match(/rgba?\(([^)]+)\)/);return m?m[1].split(',').map(Number):null};
      const L=v=>{const a=v.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return .2126*a[0]+.7152*a[1]+.0722*a[2]};
      const fg=rgb(getComputedStyle(e).color);let bg=null;
      while(e){const c=rgb(getComputedStyle(e).backgroundColor);
        if(c&&(c.length<4||c[3]>=1)){bg=c;break;}e=e.parentElement}
      if(!fg||!bg)return null;const x=L(fg),y=L(bg);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}"""
    for composer_width in (320,390,900,1440):
        for composer_theme in ('light','dark'):
            bottom_page=browser.new_page(viewport={'width':composer_width,'height':760},color_scheme=composer_theme)
            bottom_page.set_default_timeout(4500)
            bottom_errors=[]
            bottom_page.on('pageerror',lambda error:bottom_errors.append(str(error)))
            bottom_page.set_content(html);bottom_page.add_script_tag(content=script)
            bottom_page.evaluate("state.inboxView='active';renderList()")
            if composer_width<=760:
                leave_bank(bottom_page)
                bottom_page.locator('#list-extra').evaluate('e=>e.open=false')
                bottom_page.locator('.conversation-card').first.click()
            expect(bottom_page.locator('#thread-pane')).to_be_visible()
            expect(bottom_page.locator('#visual-app')).to_have_attribute('data-theme',composer_theme)
            input_043=bottom_page.locator('#message-input')
            send_043=bottom_page.locator('.send-button')
            assert input_043.bounding_box()['height']>=48
            assert send_043.bounding_box()['width']>=48 and send_043.bounding_box()['height']>=48
            assert float(input_043.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)')) >=(16 if composer_width<=760 else 14)
            for selector in ('#thread-actions .btn','.thread-pane .composer-note'):
                node=bottom_page.locator(selector).first
                assert node.count()>0,(composer_width,composer_theme,selector)
                assert float(node.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'))>=11
                ratio=bottom_page.evaluate(contrast_043,selector)
                assert ratio is not None and ratio>=4.5,(composer_width,composer_theme,selector,ratio)
            # Amostra controlada das cores dos tipos de estado, sem simular mutacao de negocio.
            bottom_page.evaluate("""()=>{
              const bar=document.querySelector('.thread-heading');
              const fixture=document.createElement('div');fixture.className='fixture-contrast';
              for(const kind of ['human','ai','bank','success','danger']){
                const badge=document.createElement('span');
                badge.className='status-indicator '+kind;badge.textContent='Estado fictício';
                fixture.append(badge);
              }
              bar.append(fixture);
            }""")
            for position in range(1,6):
                ratio=bottom_page.evaluate(contrast_043,'.fixture-contrast .status-indicator:nth-child('+str(position)+')')
                assert ratio is not None and ratio>=4.5,(composer_width,composer_theme,position,ratio)
            bottom_page.locator('.fixture-contrast').evaluate('e=>e.remove()')
            for action_043 in bottom_page.locator('.thread-pane .workflow-bar .btn').all():
                assert action_043.bounding_box()['height']>=44
            assert not bottom_page.evaluate('document.documentElement.scrollWidth > innerWidth')
            # Apenas inspecionar aparencia da desabilitacao; nao executar envio.
            input_043.evaluate('e=>e.disabled=true')
            send_043.evaluate('e=>e.disabled=true')
            assert send_043.evaluate('e=>getComputedStyle(e).backgroundColor')!='rgba(0, 0, 0, 0)'
            assert not bottom_errors,bottom_errors
            bottom_page.close()
    print('FV-UI-043 rodape operacional 8 cenarios e indicadores contrastantes: PASS')

    # FV-UI-044: Tab/Shift+Tab, foco visível e anel sem corte dentro do overflow.
    for focus_width in (320,390,900,1440):
        for focus_theme in ('light','dark'):
            focus_044=browser.new_page(viewport={'width':focus_width,'height':520 if focus_width<=390 else 760},color_scheme=focus_theme)
            focus_044.set_default_timeout(4500)
            focus_errors=[]
            focus_044.on('pageerror',lambda e:focus_errors.append(str(e)))
            focus_044.set_content(html);focus_044.add_script_tag(content=script)
            focus_044.evaluate("state.inboxView='active';renderList()")
            leave_bank(focus_044)
            focus_044.locator('#list-extra').evaluate('e=>e.open=false')
            if focus_width<=760:focus_044.locator('.conversation-card').first.click()
            expect(focus_044.locator('#thread-pane')).to_be_visible()
            expect(focus_044.locator('#visual-app')).to_have_attribute('data-theme',focus_theme)
            # Do painel para o primeiro controle de cabeçalho: foco de teclado percebido.
            focus_044.locator('#thread-pane').focus()
            focus_044.keyboard.press('Tab')
            assert focus_044.evaluate('getComputedStyle(document.activeElement).outlineWidth')=='3px'
            # Testa o retorno do campo para a ação anterior SEM clicar nem concluir.
            focus_044.locator('#message-input').focus()
            focus_044.keyboard.press('Shift+Tab')
            expect(focus_044.locator('#emoji-toggle')).to_be_focused()
            focus_044.keyboard.press('Shift+Tab')
            if focus_044.evaluate('document.activeElement.id')=='thread-body':
                focus_044.keyboard.press('Shift+Tab')
            # I03 removed the redundant i after Concluir. Native order is now
            # client name -> authorized completion -> message region/composer.
            expect(focus_044.locator('#request-completion')).to_be_focused()
            ring=focus_044.evaluate("""() => {
              const e=document.activeElement,bar=document.querySelector('.thread-heading');
              const r=e.getBoundingClientRect(),b=bar.getBoundingClientRect(),css=getComputedStyle(e);
              return {width:css.outlineWidth,style:css.outlineStyle,color:css.outlineColor,
                left:r.left-b.left,top:r.top-b.top,right:b.right-r.right,bottom:b.bottom-r.bottom};
            }""")
            assert ring['width']=='3px' and ring['style']=='solid',(focus_width,focus_theme,ring)
            assert ring['color']==('rgb(202, 202, 202)' if focus_theme=='dark' else 'rgb(92, 92, 92)')
            assert all(ring[side]>=5 for side in ('left','right','top','bottom')),(focus_width,focus_theme,ring)
            focus_044.keyboard.press('Shift+Tab')
            expect(focus_044.locator('#thread-title')).to_be_focused()
            assert focus_044.evaluate('getComputedStyle(document.activeElement).outlineWidth')=='3px'
            focus_044.keyboard.press('Tab')
            expect(focus_044.locator('#request-completion')).to_be_focused()
            focus_044.keyboard.press('Tab')
            if focus_044.evaluate('document.activeElement.id')=='thread-body':
                focus_044.keyboard.press('Tab')
            expect(focus_044.locator('#emoji-toggle')).to_be_focused()
            focus_044.keyboard.press('Tab')
            expect(focus_044.locator('#message-input')).to_be_focused()
            assert focus_044.locator('#message-input').evaluate('e=>getComputedStyle(e).outlineWidth')=='3px'
            focus_044.keyboard.press('Tab')
            expect(focus_044.locator('#audio-record')).to_be_focused()
            focus_044.keyboard.press('Tab')
            expect(focus_044.locator('.send-button')).to_be_focused()
            assert focus_044.locator('.send-button').evaluate('e=>getComputedStyle(e).outlineWidth')=='3px'
            assert not focus_044.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not focus_errors,focus_errors
            focus_044.close()
    print('FV-UI-044 foco teclado sem recorte em 8 cenarios: PASS')

    # FV-UI-047: botoes, filtros, contraste e foco da fila em claro/escuro.
    contrast_047="""selector=>{const e0=document.querySelector(selector);if(!e0)return null;
      const rgb=t=>{const m=t.match(/rgba?\(([^)]+)\)/);return m?m[1].split(',').map(Number):null};
      const L=v=>{const a=v.slice(0,3).map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return .2126*a[0]+.7152*a[1]+.0722*a[2]};
      const fg=rgb(getComputedStyle(e0).color);let e=e0,bg=null;
      while(e){const c=rgb(getComputedStyle(e).backgroundColor);
        if(c&&(c.length<4||c[3]>=1)){bg=c;break;}e=e.parentElement}
      if(!fg||!bg)return null;const x=L(fg),y=L(bg);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)}"""
    for queue_width in (320,390,900,1440):
        for queue_theme in ('light','dark'):
            queue_page=browser.new_page(viewport={'width':queue_width,'height':640 if queue_width<=390 else 820},color_scheme=queue_theme)
            queue_page.set_default_timeout(4500)
            errors_047=[]
            queue_page.on('pageerror',lambda e:errors_047.append(str(e)))
            queue_page.set_content(html);queue_page.add_script_tag(content=script)
            queue_page.evaluate("state.inboxView='active';renderList()")
            queue_page.evaluate("changeActor('marina')")
            queue_page.locator('#list-extra').evaluate('e=>e.open=true')
            expect(queue_page.locator('#conversation-list')).to_be_visible()
            expect(queue_page.locator('#visual-app')).to_have_attribute('data-theme',queue_theme)
            for selector in ('.list-pane .search-box','.list-pane .inbox-tab',
                             '.list-pane .filter-chip','.list-pane .advanced-filter select'):
                target=queue_page.locator(selector).first
                assert target.count()>0,(queue_width,queue_theme,selector)
                assert target.bounding_box()['height']>=44,(queue_width,queue_theme,selector)
            minimum=16 if queue_width<=760 else 14
            assert float(queue_page.locator('#search-input').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'))>=minimum
            for selector in ('.list-pane .inbox-tab:not(.selected)',
                             '.list-pane .filter-chip:not(.selected)',
                             '.list-pane .advanced-filter label',
                             '.list-pane .advanced-filter select'):
                ratio=queue_page.evaluate(contrast_047,selector)
                assert ratio is not None and ratio>=4.5,(queue_width,queue_theme,selector,ratio)
            leave_bank(queue_page)
            queue_page.locator('#list-extra').evaluate('e=>e.open=false')
            queue_page.locator('#search-input').focus()
            assert queue_page.locator('.search-box').evaluate('e=>getComputedStyle(e).outlineWidth')=='3px'
            queue_page.keyboard.press('Shift+Tab')
            queue_page.keyboard.press('Shift+Tab')
            expect(queue_page.locator('#list-extra summary')).to_be_focused()
            queue_page.keyboard.press('Enter')
            queue_page.keyboard.press('Tab')
            expect(queue_page.locator('#shop-select')).to_be_focused()
            queue_page.keyboard.press('Tab')
            queue_page.keyboard.press('Tab')
            expect(queue_page.locator('.inbox-tab[data-inbox="active"]')).to_be_focused()
            assert queue_page.locator('.inbox-tab[data-inbox="active"]').evaluate('e=>getComputedStyle(e).outlineWidth')=='3px'
            queue_page.locator('#list-extra').evaluate('e=>e.open=true')
            queue_page.locator('.inbox-tab[data-inbox="history"]').click()
            expect(queue_page.locator('.inbox-tab[data-inbox="history"]')).to_have_attribute('aria-pressed','true')
            queue_page.locator('#list-extra').evaluate('e=>e.open=true')
            queue_page.locator('.inbox-tab[data-inbox="active"]').click()
            expect(queue_page.locator('.inbox-tab[data-inbox="active"]')).to_have_attribute('aria-pressed','true')
            queue_page.locator('#list-extra').evaluate('e=>e.open=true')
            queue_page.locator('.filter-chip[data-filter="unread"]').click()
            expect(queue_page.locator('.filter-chip[data-filter="unread"]')).to_have_attribute('aria-pressed','true')
            queue_page.locator('#list-extra').evaluate('e=>e.open=true')
            queue_page.locator('.filter-chip[data-filter="all"]').click()
            expect(queue_page.locator('.filter-chip[data-filter="all"]')).to_have_attribute('aria-pressed','true')
            assert not queue_page.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not errors_047,errors_047
            queue_page.close()
    print('FV-UI-047 filtros da fila em oito cenarios, foco e contraste: PASS')

    # FV-UI-048: espaco e alcance na lista sem esconder a fila nem os avisos.
    for compact_width,compact_height in ((320,640),(390,844),(900,780),(1440,900)):
        for compact_theme in ('light','dark'):
            compact=browser.new_page(viewport={'width':compact_width,'height':compact_height},color_scheme=compact_theme)
            compact.set_default_timeout(4500)
            errors_048=[]
            compact.on('pageerror',lambda e:errors_048.append(str(e)))
            compact.set_content(html);compact.add_script_tag(content=script)
            compact.evaluate("state.inboxView='active';renderList()")
            expect(compact.locator('#conversation-list')).to_be_visible()
            expect(compact.locator('#visual-app')).to_have_attribute('data-theme',compact_theme)
            assert compact.locator('#queue-summary .summary-tile').count()>=1
            assert compact.locator('.conversation-card').count()>=1
            assert compact.locator('#list-count').inner_text().strip()
            # FV-REV-01: filters are centralized; the lab is explicitly separate.
            assert compact.locator('#search-input').is_visible()
            assert compact.locator('#list-extra summary').is_visible()
            assert not compact.locator('[data-inbox=active]').is_visible()
            assert not compact.locator('#actor-select').is_visible()
            assert not compact.locator('#status-filter').is_visible()
            compact.locator('#demo-open').click()
            assert compact.locator('#actor-select').is_visible()
            compact.locator('#demo-close').click()
            compact.locator('#list-extra').evaluate('e=>e.open=true')
            assert compact.locator('#shop-select').is_visible()
            assert not compact.locator('#status-filter').is_visible()
            if compact_width<=760:
                assert compact.locator('.list-heading').evaluate('e=>parseFloat(getComputedStyle(e).paddingTop)')<=15
                assert compact.locator('.list-topline').evaluate('e=>parseFloat(getComputedStyle(e).marginBottom)')<=12
                assert compact.locator('.queue-summary').evaluate('e=>parseFloat(getComputedStyle(e).marginTop)')<=9
                assert compact.locator('.filter-chip').first.bounding_box()['height']>=44
                if compact_height<=700:
                    assert compact.locator('#conversation-list').evaluate('e=>getComputedStyle(e).overflowY')=='auto'
                    assert compact.locator('#conversation-list').evaluate('e=>e.scrollHeight>e.clientHeight')
            leave_bank(compact)
            compact.locator('#list-extra').evaluate('e=>e.open=false')
            compact.locator('.conversation-card').first.scroll_into_view_if_needed()
            assert compact.locator('.conversation-card').first.is_visible()
            # A nota continua acessivel via aria-describedby, nao ocupa rodape.
            assert compact.locator('#list-demo-guidance').count()==1
            assert 'fictícios' in compact.locator('#list-demo-guidance').inner_text()
            assert compact.locator('#search-input').get_attribute('aria-describedby')=='list-demo-guidance'
            if compact_width<=760:
                assert compact.locator('.conversation-card').first.bounding_box()['y']<420
            assert not compact.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not errors_048,errors_048
            compact.close()
    print('FV-UI-048 lista compacta e conteudo acessivel em oito cenarios: PASS')

    # FV-UI-049: busca vazia, reset seguro e perfil suspenso em telas e temas distintos.
    for empty_width,empty_height in ((320,640),(390,844),(900,780),(1440,900)):
        for empty_theme in ('light','dark'):
            empty_page=browser.new_page(viewport={'width':empty_width,'height':empty_height},color_scheme=empty_theme)
            empty_page.set_default_timeout(4500)
            empty_errors=[]
            empty_page.on('pageerror',lambda error:empty_errors.append(str(error)))
            empty_page.set_content(html);empty_page.add_script_tag(content=script)
            empty_page.evaluate("state.inboxView='active';renderList()")
            expect(empty_page.locator('#conversation-list')).to_be_visible()
            expect(empty_page.locator('#visual-app')).to_have_attribute('data-theme',empty_theme)
            assert empty_page.locator('.conversation-card').count()>0
            profile_before=empty_page.locator('#actor-select').input_value()
            shop_before=empty_page.locator('#shop-select').input_value()
            empty_page.locator('#list-extra').evaluate('e=>e.open=true')
            empty_page.locator('.filter-chip[data-filter="unread"]').click()
            empty_page.locator('#search-input').fill('fv-ui-049-sem-correspondencia-xyzz')
            expect(empty_page.locator('.no-results strong')).to_have_text('Nenhuma conversa corresponde à busca')
            assert empty_page.locator('.no-results').get_attribute('role')=='status'
            assert empty_page.locator('#list-count').inner_text().startswith('0 de ')
            clear_button=empty_page.locator('.empty-reset')
            expect(clear_button).to_be_visible()
            assert clear_button.bounding_box()['height']>=44
            if empty_width<=390:
                clear_button.scroll_into_view_if_needed()
            leave_bank(empty_page)
            empty_page.locator('#list-extra').evaluate('e=>e.open=false')
            clear_button.click()
            expect(empty_page.locator('#search-input')).to_be_focused()
            assert empty_page.locator('#search-input').input_value()==''
            assert empty_page.locator('#status-filter').input_value()=='all'
            expect(empty_page.locator('.filter-chip[data-filter="all"]')).to_have_attribute('aria-pressed','true')
            assert empty_page.locator('.conversation-card').count()>0
            assert empty_page.locator('#actor-select').input_value()==profile_before
            assert empty_page.locator('#shop-select').input_value()==shop_before
            assert empty_page.locator('.empty-reset').count()==0
            leave_bank(empty_page)
            empty_page.locator('#list-extra').evaluate('e=>e.open=false')
            empty_page.locator('#ui-settings').evaluate('e => e.open = true')
            empty_page.locator('#demo-dialog').evaluate('e=>e.showModal()')
            empty_page.locator('#actor-select').select_option('otavio')
            empty_page.evaluate("state.inboxView='active';renderList()")
            empty_page.locator('#demo-dialog').evaluate('e=>e.close()')
            expect(empty_page.locator('#demo-open')).to_be_focused()
            empty_page.locator('#ui-settings').evaluate('e => e.open = false')
            expect(empty_page.locator('.no-results strong')).to_have_text('Sem acesso demonstrativo')
            assert empty_page.locator('.empty-reset').count()==0
            assert not empty_page.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not empty_errors,empty_errors
            empty_page.close()
    print('FV-UI-049 busca vazia, reset e suspensao em oito cenarios: PASS')

    # FV-UI-050: avisos de leitura acessivel, afastados do compositor nos 2 temas.
    for notice_width,notice_height in ((320,640),(390,844),(900,780),(1440,900)):
        for notice_theme in ('light','dark'):
            notice_page=browser.new_page(viewport={'width':notice_width,'height':notice_height},color_scheme=notice_theme)
            notice_page.set_default_timeout(4500)
            notice_errors=[]
            notice_page.on('pageerror',lambda e:notice_errors.append(str(e)))
            notice_page.set_content(html);notice_page.add_script_tag(content=script)
            notice_page.evaluate("state.inboxView='active';renderList()")
            expect(notice_page.locator('#visual-app')).to_have_attribute('data-theme',notice_theme)
            leave_bank(notice_page)
            notice_page.locator('#list-extra').evaluate('e=>e.open=false')
            if notice_width<=760:notice_page.locator('.conversation-card').first.click()
            expect(notice_page.locator('#thread-pane')).to_be_visible()
            notice_ms=notice_page.evaluate("""() => {
              const original=window.setTimeout; let delay=-1;
              window.setTimeout=(fn,ms)=>{delay=ms;return 4201};
              try { showToast('Aviso fictício extenso: nenhuma mensagem foi enviada, nenhuma API foi chamada e as informações desta central são apenas uma demonstração local.'); }
              finally { window.setTimeout=original }
              return delay;
            }""")
            assert 5000<=notice_ms<=9000,(notice_width,notice_theme,notice_ms)
            toast=notice_page.locator('#toast')
            expect(toast).to_be_visible()
            assert toast.get_attribute('role')=='status'
            assert toast.get_attribute('aria-live')=='polite'
            toast_rect=toast.bounding_box()
            composer_rect=notice_page.locator('.composer').bounding_box()
            assert toast_rect['y']+toast_rect['height']+12 < composer_rect['y'],(notice_width,notice_theme,toast_rect,composer_rect)
            assert toast_rect['x']>=0 and toast_rect['x']+toast_rect['width']<=notice_width
            assert float(toast.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'))>=13
            colors=toast.evaluate("""e=>({foreground:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor,
                bottom:getComputedStyle(e).bottom,events:getComputedStyle(e).pointerEvents})""")
            assert colors['foreground']=='rgb(255, 255, 255)' and colors['background']=='rgb(57, 57, 57)'
            # Chromium pode resolver bottom:auto em pixels; a geometria real foi validada acima.
            assert colors['events']=='none',(notice_width,notice_theme,colors)
            assert not notice_page.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not notice_errors,notice_errors
            notice_page.close()
    print('FV-UI-050 avisos acessiveis, tempo de leitura e compositor livre em 8 cenarios: PASS')

    # FV-UI-051: ajuda consistente em busca, composicao e detalhes (leitores de tela).
    for guide_width,guide_height in ((320,640),(390,844),(900,780),(1440,900)):
        for guide_theme in ('light','dark'):
            guide=browser.new_page(viewport={'width':guide_width,'height':guide_height},color_scheme=guide_theme)
            guide.set_default_timeout(4500)
            guide_errors=[]
            guide.on('pageerror',lambda e:guide_errors.append(str(e)))
            guide.set_content(html);guide.add_script_tag(content=script)
            guide.evaluate("state.inboxView='active';renderList()")
            expect(guide.locator('#conversation-list')).to_be_visible()
            expect(guide.locator('#visual-app')).to_have_attribute('data-theme',guide_theme)
            assert guide.locator('#search-input').get_attribute('aria-describedby')=='list-demo-guidance'
            list_note=guide.locator('#list-demo-guidance')
            assert list_note.count()==1 and list_note.get_attribute('role')=='note'
            assert 'Dados fictícios' in list_note.inner_text()
            leave_bank(guide)
            guide.locator('#list-extra').evaluate('e=>e.open=false')
            guide.locator('.conversation-card').first.click()
            expect(guide.locator('#thread-pane')).to_be_visible()
            assert guide.locator('#message-input').get_attribute('aria-describedby')=='composer-demo-guidance'
            message_note=guide.locator('#composer-demo-guidance')
            expect(message_note).to_be_visible()
            assert message_note.get_attribute('role')=='note'
            assert 'Dados fictícios' in message_note.inner_text()
            assert 'Dados fictícios · sem envios reais' in message_note.inner_text()
            if not guide.locator('#detail-pane').is_visible():
                guide.locator('#thread-title').click()
            expect(guide.locator('#detail-pane')).to_be_visible()
            detail_note=guide.locator('#case-demo-guidance')
            expect(detail_note).to_be_visible()
            assert detail_note.get_attribute('role')=='note'
            assert guide.locator('#case-tab-panel').get_attribute('aria-describedby')=='case-demo-guidance'
            assert 'Dados fictícios' in detail_note.inner_text()
            assert 'não executa operações externas' in detail_note.inner_text()
            assert float(detail_note.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'))>=12
            result_051=detail_note.evaluate("""e=>{
              const rgb=s=>s.match(/\d+(\.\d+)?/g).slice(0,3).map(Number);
              const l=v=>{const c=v.map(n=>n/255).map(n=>n<=0.04045?n/12.92:Math.pow((n+0.055)/1.055,2.4));
              return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]};
              const cs=getComputedStyle(e),fg=l(rgb(cs.color)),bg=l(rgb(cs.backgroundColor));
              return {contrast:(Math.max(fg,bg)+0.05)/(Math.min(fg,bg)+0.05),font:cs.fontSize};
            }""")
            assert result_051['contrast']>=4.5,(guide_width,guide_theme,result_051)
            assert not guide.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not guide_errors,guide_errors
            guide.close()
    print('FV-UI-051 orientacoes vinculadas e detalhes legiveis em 8 cenarios: PASS')

    # FV-UI-052: anúncio da contagem sem duplicar o estado vazio acessível.
    for results_width,results_height in ((320,640),(390,844),(900,780),(1440,900)):
        for results_theme in ('light','dark'):
            results=browser.new_page(viewport={'width':results_width,'height':results_height},color_scheme=results_theme)
            results.set_default_timeout(4500)
            errors_052=[]
            results.on('pageerror',lambda e:errors_052.append(str(e)))
            results.set_content(html);results.add_script_tag(content=script)
            results.evaluate("state.inboxView='active';renderList()")
            expect(results.locator('#conversation-list')).to_be_visible()
            expect(results.locator('#visual-app')).to_have_attribute('data-theme',results_theme)
            count=results.locator('#list-count')
            assert count.get_attribute('role')=='status'
            assert count.get_attribute('aria-atomic')=='true'
            assert count.get_attribute('aria-live')=='polite'
            assert results.locator('.conversation-card').count()>0
            original_actor=results.locator('#actor-select').input_value()
            original_shop=results.locator('#shop-select').input_value()
            results.locator('#search-input').fill('FV-UI-052-nenhum-caso-123xyz')
            assert count.get_attribute('aria-live')=='off'
            assert count.inner_text().strip().startswith('0 de ')
            assert results.locator('.no-results').count()==1
            assert results.locator('.no-results').get_attribute('role')=='status'
            assert results.locator('.no-results').get_attribute('aria-live')=='polite'
            clear=results.locator('.empty-reset')
            expect(clear).to_be_visible()
            clear.scroll_into_view_if_needed()
            leave_bank(results)
            results.locator('#list-extra').evaluate('e=>e.open=false')
            clear.click()
            expect(results.locator('#search-input')).to_be_focused()
            assert count.get_attribute('aria-live')=='polite'
            assert results.locator('.conversation-card').count()>0
            assert results.locator('.no-results').count()==0
            assert results.locator('#actor-select').input_value()==original_actor
            assert results.locator('#shop-select').input_value()==original_shop
            assert not results.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not errors_052,errors_052
            results.close()
    print('FV-UI-052 contador de resultados e estado vazio acessiveis em 8 cenarios: PASS')


    # FV-UI-053: atalho descobrivel, sem ocultar busca nem roubar area no celular.
    for shortcut_width, shortcut_height in ((320,640),(390,844),(900,780),(1440,900)):
        for shortcut_theme in ('light','dark'):
            shortcut_page=browser.new_page(viewport={'width':shortcut_width,'height':shortcut_height},color_scheme=shortcut_theme)
            shortcut_page.set_default_timeout(4500)
            shortcut_errors=[]
            shortcut_page.on('pageerror',lambda e:shortcut_errors.append(str(e)))
            shortcut_page.set_content(html);shortcut_page.add_script_tag(content=script)
            shortcut_page.evaluate("state.inboxView='active';renderList()")
            expect(shortcut_page.locator('#visual-app')).to_have_attribute('data-theme',shortcut_theme)
            shortcut_input=shortcut_page.locator('#search-input')
            assert shortcut_input.get_attribute('aria-keyshortcuts')=='Escape ArrowDown'
            assert shortcut_page.locator('.search-shortcut').count()==0
            initial_count=shortcut_page.locator('.conversation-card').count()
            shortcut_input.fill('Cliente')
            shortcut_input.focus()
            shortcut_page.keyboard.press('Control+k')
            # No application handler intercepts the removed shortcut.
            assert shortcut_page.locator('#search-input').input_value()=='Cliente'
            assert shortcut_page.locator('.conversation-card').count()==initial_count
            assert not shortcut_page.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not shortcut_errors,shortcut_errors
            shortcut_page.close()
    print('FV-REV-006 busca preservada sem atalho removido: PASS')


    # FV-UI-054: limpar filtros ativos, com ou sem resultados, preservando escopo.
    for reset_width,reset_height in ((320,640),(390,844),(900,780),(1440,900)):
        for reset_theme in ('light','dark'):
            reset_page=browser.new_page(viewport={'width':reset_width,'height':reset_height},color_scheme=reset_theme)
            reset_page.set_default_timeout(4500)
            errors_054=[]
            reset_page.on('pageerror',lambda e:errors_054.append(str(e)))
            reset_page.set_content(html);reset_page.add_script_tag(content=script)
            reset_page.evaluate("state.inboxView='active';renderList()")
            expect(reset_page.locator('#visual-app')).to_have_attribute('data-theme',reset_theme)
            reset_controls=reset_page.locator('#filter-reset-controls')
            expect(reset_controls).to_be_hidden()
            reset_page.evaluate("changeActor('marina');state.inboxView='active';renderList()")
            original_actor=reset_page.locator('#actor-select').input_value()
            original_shop=reset_page.locator('#shop-select').input_value()
            reset_page.locator('#search-input').fill('FV-UI-054-busca-sem-resultado-xxyy')
            reset_page.locator('#list-extra').evaluate('e => e.open = true')
            reset_page.locator('#list-extra').evaluate('e=>e.open=true')
            reset_page.locator('#status-filter').select_option(index=1)
            reset_page.locator('#list-extra').evaluate('e=>e.open=true')
            reset_page.locator('[data-filter="unread"]').click()
            expect(reset_controls).to_be_hidden()
            reset_button=reset_page.locator('.empty-reset')
            expect(reset_button).to_be_visible()
            assert reset_button.bounding_box()['height']>=44
            reset_button.scroll_into_view_if_needed()
            leave_bank(reset_page)
            reset_page.locator('#list-extra').evaluate('e=>e.open=false')
            reset_button.click()
            expect(reset_controls).to_be_hidden()
            expect(reset_page.locator('#search-input')).to_be_focused()
            assert reset_page.locator('#search-input').input_value()==''
            assert reset_page.locator('#status-filter').input_value()=='all'
            assert reset_page.locator('[data-filter="all"]').get_attribute('aria-pressed')=='true'
            assert reset_page.locator('[data-inbox="active"]').get_attribute('aria-pressed')=='true'
            assert reset_page.locator('#actor-select').input_value()==original_actor
            assert reset_page.locator('#shop-select').input_value()==original_shop
            assert reset_page.locator('.conversation-card').count()>0
            # FV-UI-055: com resultados, usar ação superior; lista vazia, apenas a ação contextual.
            reset_page.locator('#search-input').fill('Cliente Exemplo')
            assert reset_page.locator('.conversation-card').count()>0
            expect(reset_controls).to_be_visible()
            assert reset_page.locator('.empty-reset').count()==0
            assert reset_page.get_by_role('button',name='Limpar busca e filtros').count()==1
            reset_page.locator('#clear-list-filters').click()
            expect(reset_controls).to_be_hidden()
            expect(reset_page.locator('#search-input')).to_be_focused()
            reset_page.locator('#search-input').fill('FV-UI-055-sem-resultado-impossivel-xyzz')
            expect(reset_controls).to_be_hidden()
            assert reset_page.locator('.conversation-card').count()==0
            assert reset_page.locator('.empty-reset').count()==1
            assert reset_page.get_by_role('button',name='Limpar busca e filtros').count()==1
            reset_page.locator('.empty-reset').click()
            assert reset_page.locator('.conversation-card').count()>0
            assert reset_page.locator('#actor-select').input_value()==original_actor
            assert reset_page.locator('#shop-select').input_value()==original_shop
            expect(reset_page.locator('#search-input')).to_be_focused()
            assert not reset_page.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not errors_054,errors_054
            reset_page.close()
    print('FV-UI-054 limpeza de filtros com escopo preservado em 8 cenarios: PASS')
    print('FV-UI-055 limpeza unica por estado em 8 cenarios: PASS')

    # FV-UI-056: busca tolerante a acentos/espacos, sem alterar o isolamento por loja.
    for search_width,search_height in ((320,640),(390,844),(900,780),(1440,900)):
        for search_theme in ('light','dark'):
            search_page=browser.new_page(viewport={'width':search_width,'height':search_height},color_scheme=search_theme)
            search_page.set_default_timeout(4500)
            errors_056=[]
            search_page.on('pageerror',lambda e:errors_056.append(str(e)))
            search_page.set_content(html);search_page.add_script_tag(content=script)
            search_page.evaluate("state.inboxView='active';renderList()")
            expect(search_page.locator('#visual-app')).to_have_attribute('data-theme',search_theme)
            search_input=search_page.locator('#search-input')
            search_input.fill('  CLIENTE   EXÉMPLO   02  ')
            assert search_page.locator('.conversation-card').count()==1
            assert search_page.locator('.conversation-card').filter(has_text='Cliente Exemplo 02').count()==1
            search_input.fill('  CÁDASTRO    ENVIADO  AO BANCO ')
            assert search_page.locator('.conversation-card').count()==1
            assert search_page.locator('.conversation-card').filter(has_text='Cliente Exemplo 05').count()==1
            search_input.fill(' A-105 ')
            assert search_page.locator('.conversation-card').filter(has_text='Cliente Exemplo 05').count()==1
            leave_bank(search_page)
            search_page.locator('#list-extra').evaluate('e=>e.open=false')
            search_page.locator('#ui-settings').evaluate('e => e.open = true')
            search_page.locator('#demo-dialog').evaluate('e=>e.showModal()')
            search_page.locator('#actor-select').select_option('marina')
            search_page.evaluate("state.inboxView='active';renderList()")
            search_page.locator('#demo-dialog').evaluate('e=>e.close()')
            expect(search_page.locator('#demo-open')).to_be_focused()
            search_page.locator('#ui-settings').evaluate('e => e.open = false')
            leave_bank(search_page)
            search_page.locator('#list-extra').evaluate('e=>e.open=false')
            search_page.locator('#ui-settings').evaluate('e => e.open = true')
            search_page.locator('#list-extra').evaluate('e=>e.open=true')
            search_page.locator('#shop-select').select_option('horizonte')
            search_page.evaluate("state.inboxView='active';renderList()")
            search_page.locator('#ui-settings').evaluate('e => e.open = false')
            search_input.fill(' CLIENTE   EXÉMPLO   02 ')
            assert search_page.locator('.conversation-card').count()==0
            assert search_page.locator('.no-results').count()==1
            leave_bank(search_page)
            search_page.locator('#list-extra').evaluate('e=>e.open=false')
            search_page.locator('#ui-settings').evaluate('e => e.open = true')
            search_page.locator('#list-extra').evaluate('e=>e.open=true')
            search_page.locator('#shop-select').select_option('aurora')
            search_page.evaluate("state.inboxView='active';renderList()")
            search_page.locator('#ui-settings').evaluate('e => e.open = false')
            search_input.fill(' CLIENTE   EXÉMPLO   02 ')
            assert search_page.locator('.conversation-card').filter(has_text='Cliente Exemplo 02').count()==1
            assert not search_page.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not errors_056,errors_056
            search_page.close()
    print('FV-UI-056 busca normalizada e isolamento de loja em 8 cenarios: PASS')

    # FV-UI-057: Escape em busca com refinamentos preserva chips, escopo e foco.
    for esc_width,esc_height in ((320,640),(390,844),(900,780),(1440,900)):
        for esc_theme in ('light','dark'):
            esc_page=browser.new_page(viewport={'width':esc_width,'height':esc_height},color_scheme=esc_theme)
            esc_page.set_default_timeout(4500)
            errors_057=[]
            esc_page.on('pageerror',lambda e:errors_057.append(str(e)))
            esc_page.set_content(html);esc_page.add_script_tag(content=script)
            esc_page.evaluate("state.inboxView='active';renderList()")
            expect(esc_page.locator('#visual-app')).to_have_attribute('data-theme',esc_theme)
            input057=esc_page.locator('#search-input')
            assert input057.get_attribute('aria-keyshortcuts')=='Escape ArrowDown'
            assert 'Esc apaga somente o texto' in esc_page.locator('#list-demo-guidance').inner_text()
            actor057=esc_page.locator('#actor-select').input_value()
            shop057=esc_page.locator('#shop-select').input_value()
            esc_page.locator('#list-extra').evaluate('e=>e.open=true')
            esc_page.locator('[data-filter="unread"]').click()
            unread_count_057=esc_page.locator('.conversation-card').count()
            assert unread_count_057>0 and unread_count_057<8
            input057.fill('FV-UI-057-consulta-sem-resultados')
            assert esc_page.locator('.conversation-card').count()==0
            assert esc_page.locator('.empty-reset').count()==1
            input057.press('Escape')
            assert input057.input_value()==''
            expect(input057).to_be_focused()
            assert esc_page.locator('[data-filter="unread"]').get_attribute('aria-pressed')=='true'
            assert esc_page.locator('[data-inbox="active"]').get_attribute('aria-pressed')=='true'
            assert esc_page.locator('#actor-select').input_value()==actor057
            assert esc_page.locator('#shop-select').input_value()==shop057
            assert esc_page.locator('.conversation-card').count()==unread_count_057
            expect(esc_page.locator('#filter-reset-controls')).to_be_visible()
            esc_page.locator('#clear-list-filters').click()
            assert esc_page.locator('.conversation-card').count()==8

            # FV-UI-058: reaproveitar os mesmos oito navegadores da FV-UI-057.
            # Verificar transicao de foco sem assumir um caso inicial selecionado.
            nav_first=esc_page.locator('.conversation-card').first
            before_selected=nav_first.get_attribute('aria-pressed')
            before_thread=esc_page.locator('#thread-title').text_content()
            input057.focus()
            input057.press('ArrowDown')
            expect(nav_first).to_be_focused()
            assert nav_first.get_attribute('aria-pressed')==before_selected
            assert esc_page.locator('#thread-title').text_content()==before_thread
            if esc_width==320 and esc_theme=='light':
                input057.fill('FV-UI-058-nenhum-resultado-xyzz')
                assert esc_page.locator('.conversation-card').count()==0
                input057.press('ArrowDown')
                expect(input057).to_be_focused()
                assert esc_page.locator('.empty-reset').count()==1
            assert not esc_page.evaluate('document.documentElement.scrollWidth>innerWidth')
            assert not errors_057,errors_057
            esc_page.close()
    print('FV-UI-057 Esc limpa somente busca em 8 cenarios: PASS')
    print('FV-UI-058 foco do primeiro caso pela seta em 8 cenarios: PASS')

    browser.close()

# O mesmo gate obrigatório inclui agora carga ESM por HTTP e captura sintética real.
from runpy import run_path
run_path(str(base / 'tests' / 'browser.communication.py'), run_name='__main__')

run_path(str(base / 'tests' / 'browser.revision.py'), run_name='__main__')

run_path(str(base / 'tests' / 'browser.modules.py'), run_name='__main__')
