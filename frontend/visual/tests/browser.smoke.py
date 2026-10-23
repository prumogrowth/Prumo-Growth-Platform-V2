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
script = '\n'.join((base / name).read_text(encoding='utf-8') for name in ('fixtures.mjs','view-model.mjs','cf-op-02.mjs','registration-view.mjs','human-cycle-view.mjs','operation-feedback.mjs','bank-view.mjs','postmark-view.mjs','team-operations.mjs','team-pause-preview.mjs','team-monitor.mjs','team-monitoring.mjs','batch-monitor.mjs','distribution-view.mjs','transport-state-view.mjs','conversation-attention.mjs','app.mjs'))
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
        # Um único indicador: numérico sem leitura, sem número após leitura por titular.
        assert page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).locator('.attention-unread').inner_text() == '2'
        assert not errors
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        # Selecionar caso estável, não depender de ordenação de conversas.
        page.get_by_role('button', name='Abrir conversa Cliente Exemplo 02', exact=False).click()
        assert page.locator('.conversation-card').filter(has_text='Cliente Exemplo 02').locator('.attention-pending').count() == 1
        if width<=1040: page.locator('#detail-toggle').click()
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
        page.locator('#composer button').click()
        expect(page.locator('#message-preview-dialog')).to_be_visible()
        assert page.locator('#message-preview-body').inner_text().startswith('Consultor Rafael Lima:')
        page.locator('#message-preview-form button[value=confirm]').click()
        assert page.locator('#message-preview-dialog').is_hidden()
        assert 'NÃO ENVIADA' in page.locator('.message-send-state').last.inner_text()
        assert page.locator('.conversation-card').filter(has_text='Cliente Exemplo 02').locator('.attention-pending').count() == 1
        page.locator('#request-completion').click()
        page.locator('#completion-form button[value=confirm]').click()
        if width<=1040: page.locator('#detail-toggle').click()
        expect(page.locator('.detail-tab.active')).to_have_text('Extração')
        page.get_by_role('button',name='Retorno parcial').click()
        # FV-UI-032: resultado recria o DOM; aba persistente retoma o foco.
        expect(page.locator('#case-tab-extraction')).to_be_focused()
        assert 'Resultado técnico fictício Retorno parcial' in page.locator('#context-announcement').inner_text()
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
    assert page.locator('.conversation-card').count() == 12  # A-117 da equipe Marina, case-only da Lia
    # Supervisor acessa D2 sem zerar as não lidas do operador.
    assert page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).locator('.attention-unread').inner_text() == '2'
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
    page.locator('#actor-select').select_option('daniel')
    assert page.locator('.conversation-card').count() == 1
    page.locator('#team-nav').click()
    assert 'Bianca Rocha' in page.locator('#team-list').inner_text()
    assert 'Rafael Lima' not in page.locator('#team-list').inner_text()
    page.get_by_role('button',name='Solicitar retomada de novos leads para Bianca Rocha',exact=False).click()
    page.locator('#intake-form button[value=confirm]').click()
    expect(page.locator('#team-list')).to_contain_text('SOLICITADO LOCALMENTE')
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
    expect(page.locator('#workflow-bar')).to_contain_text('Pedido simulado')
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
    # FV-UI-032: botão do vínculo deixa o DOM; foco alcança região de destino.
    expect(page.locator('#thread-pane')).to_be_focused()
    assert 'Caso A-114 aberto por vínculo fictício autorizado' in page.locator('#context-announcement').inner_text()
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

    for mobile_width,mobile_height in ((390,844),(320,640)):
        mobile = browser.new_page(viewport={'width':mobile_width,'height':mobile_height})
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
        mobile.locator('#actor-select').select_option('otavio')
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
    queue_page.locator('#actor-select').select_option('marina')
    queue_page.locator('#team-nav').click()
    queue_page.locator('#team-show-queue').click()
    assert 'FILA-A-01' in queue_page.locator('#team-queue').inner_text()
    queue_page.locator('#team-queue').get_by_role('button',name='Solicitar assunção').first.click()
    assert queue_page.locator('#queue-action-dialog').is_visible()
    queue_page.locator('#queue-action-form button[value=confirm]').click()
    expect(queue_page.locator('#queue-action-dialog')).to_be_hidden()
    expect(queue_page.locator('#team-queue')).to_contain_text('NÃO ATRIBUÍDO')
    queue_page.locator('#team-close').click()
    queue_page.locator('#actor-select').select_option('daniel')
    queue_page.locator('#team-nav').click()
    queue_page.locator('#team-show-queue').click()
    assert 'FILA-A-01' in queue_page.locator('#team-queue').inner_text()
    queue_page.locator('#team-close').click()
    queue_page.locator('#actor-select').select_option('lia')
    queue_page.locator('#shop-select').select_option('aurora')
    assert queue_page.locator('.conversation-card').count()==1
    assert 'Cliente Exemplo 19' in queue_page.locator('#conversation-items').inner_text()
    assert 'Cliente Exemplo 02' not in queue_page.locator('#conversation-items').inner_text()
    queue_page.close()
    print('FV-UI-018 fila compartilhada e caso excepcional sintéticos: PASS')
    # FV-UI-019: dois cutoffs S0 da fixture; nova solicitação continua NÃO confirmada.
    cycle_page=browser.new_page(viewport={'width':1366,'height':800})
    cycle_page.set_content(html)
    cycle_page.add_script_tag(content=script)
    cycle_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 09',exact=False).click()
    cycle_page.locator('.detail-tab',has_text='Extração').click()
    assert 'f03-a108-1' in cycle_page.locator('#detail-content').inner_text()
    assert 'f03-a108-2' in cycle_page.locator('#detail-content').inner_text()
    cycle_page.locator('#show-clarification-demo').click()
    # FV-UI-032: esclarecimento recriado mantém foco na aba.
    expect(cycle_page.locator('#case-tab-extraction')).to_be_focused()
    assert 'Cenário de esclarecimento fictício' in cycle_page.locator('#context-announcement').inner_text()
    assert 'CENÁRIO ALTERNATIVO' in cycle_page.locator('#workflow-bar').inner_text()
    cycle_page.locator('#request-completion').click()
    cycle_page.locator('#completion-form button[value=confirm]').click()
    expect(cycle_page.locator('#completion-dialog')).to_be_hidden()
    expect(cycle_page.locator('#detail-content')).to_contain_text('a108-3')
    expect(cycle_page.locator('#detail-content')).to_contain_text(re.compile('corte apenas candidato',re.I))
    details=cycle_page.locator('#detail-content').inner_text()
    assert 'v1-ficticia' in details
    cycle_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 15',exact=False).click()
    cycle_page.locator('.detail-tab',has_text='Extração').click()
    dossier=cycle_page.locator('#detail-content').inner_text()
    assert 'live-form-v2-demo' in dossier and 'bank-demo-v1' in dossier
    cycle_page.locator('#actor-select').select_option('marina')
    cycle_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 09',exact=False).click()
    cycle_page.locator('.detail-tab',has_text='Extração').click()
    assert 'f03-a108-1' not in cycle_page.locator('#detail-content').inner_text()
    cycle_page.close()
    # FV-UI-032: a navegação O5 móvel orienta no botão de retorno.
    mobile_link=browser.new_page(viewport={'width':390,'height':844})
    mobile_link.set_content(html)
    mobile_link.add_script_tag(content=script)
    mobile_link.get_by_role('button',name='Abrir conversa Cliente Exemplo 05',exact=False).click()
    mobile_link.locator('#detail-toggle').click()
    mobile_link.locator('.detail-tab',has_text='Novo contato').click()
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
    technical.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    assert 'API aceitou · envio NÃO comprovado' in technical.locator('#thread-body').inner_text()
    assert 'Não tentar reenvio automático' in technical.locator('#thread-body').inner_text()
    technical.get_by_role('button',name='Abrir conversa Cliente Exemplo 05',exact=False).click()
    assert 'Envio comprovado · fixture' in technical.locator('#thread-body').inner_text()
    technical.locator('#actor-select').select_option('marina')
    technical.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    assert 'API aceitou · envio NÃO comprovado' not in technical.locator('#thread-body').inner_text()
    technical.close()
    print('FV-UI-020 fronteira de transporte e supervisão: PASS')
    # FV-UI-021: foco, anúncio acessível, Home/End e viewport baixa; sem S0.
    access_page=browser.new_page(viewport={'width':390,'height':844})
    access_page.set_default_timeout(4500)
    access_page.set_content(html)
    access_page.add_script_tag(content=script)
    assert 'Consultor fictício' in access_page.locator('#context-announcement').inner_text()
    access_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    assert 'Caso A-102 aberto' in access_page.locator('#context-announcement').inner_text()
    assert access_page.evaluate('document.activeElement.id') == 'thread-back'
    access_page.locator('#detail-toggle').click()
    assert access_page.evaluate('document.activeElement.id') == 'detail-back'
    access_page.locator('.detail-tab[role=tab]').first.focus()
    access_page.keyboard.press('End')
    assert access_page.locator('.detail-tab[aria-selected=true]').inner_text() == 'Recontatos'
    access_page.keyboard.press('Home')
    assert access_page.locator('.detail-tab[aria-selected=true]').inner_text() == 'Resumo'
    access_page.locator('#detail-back').click()
    assert access_page.evaluate('document.activeElement.id') == 'detail-toggle'
    access_page.locator('#thread-back').click()
    assert access_page.evaluate('document.activeElement.id') == 'search-input'
    access_page.locator('#actor-select').select_option('marina')
    assert 'Gestor fictício' in access_page.locator('#context-announcement').inner_text()
    assert 'A-102' not in access_page.locator('#context-announcement').inner_text()
    access_page.close()
    short_page=browser.new_page(viewport={'width':900,'height':480})
    short_page.set_content(html)
    short_page.add_script_tag(content=script)
    assert not short_page.evaluate('document.documentElement.scrollWidth > innerWidth')
    assert short_page.evaluate('document.querySelector(".visual-app").getBoundingClientRect().height <= innerHeight')
    short_page.close()
    print('FV-UI-021 foco móvel, anúncio, Home End e viewport baixa: PASS')
    # FV-UI-022: Escape move foco ao painel visível; cancelar mensagem não envia.
    focus_page=browser.new_page(viewport={'width':390,'height':844})
    focus_page.set_content(html)
    focus_page.add_script_tag(content=script)
    focus_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    focus_page.locator('#message-input').fill('Rascunho de teste não enviado')
    focus_page.locator('#composer button').click()
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
    focus_page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
    assert focus_page.locator('#message-input').input_value() == ''
    focus_page.locator('#detail-toggle').click()
    focus_page.locator('#detail-back').focus()
    focus_page.keyboard.press('Escape')
    assert focus_page.locator('#visual-app').get_attribute('data-mobile-view') == 'thread'
    assert focus_page.evaluate('document.activeElement.id') == 'detail-toggle'
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
        zoom_page.get_by_role('button', name='Abrir conversa Cliente Exemplo 02', exact=False).click()
        assert zoom_page.locator('#visual-app').get_attribute('data-mobile-view')=='thread'
        assert zoom_page.locator('#message-input').is_visible()
        assert zoom_page.evaluate('document.activeElement.id')=='thread-back'
        zoom_page.locator('#detail-toggle').click()
        assert zoom_page.locator('#visual-app').get_attribute('data-mobile-view')=='detail'
        zoom_page.locator('#detail-back').click()
        assert zoom_page.evaluate('document.activeElement.id')=='detail-toggle'
        assert not zoom_page.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not zoom_errors, zoom_label + ': ' + repr(zoom_errors)
        zoom_page.close()
    print('FV-UI-027 reflow responsivo, rolagem e movimento reduzido: PASS')
    # FV-UI-028: aria-expanded acompanha o painel visível; foco de teclado contrastante.
    for viewport in ({'width':390,'height':844},{'width':320,'height':640}):
        aria_page=browser.new_page(viewport=viewport)
        aria_page.set_default_timeout(4500)
        aria_errors=[]
        aria_page.on('pageerror',lambda e:aria_errors.append(str(e)))
        aria_page.set_content(html)
        aria_page.add_script_tag(content=script)
        toggler=aria_page.locator('#detail-toggle')
        expect(toggler).to_have_attribute('aria-expanded','false')
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
        aria_page.locator('#actor-select').select_option('marina')
        expect(toggler).to_have_attribute('aria-expanded','false')
        assert aria_page.locator('#visual-app').get_attribute('data-mobile-view')=='list'
        # De um campo de busca, Tab deixa foco perceptível no botão seguinte.
        aria_page.locator('#search-input').focus()
        aria_page.keyboard.press('Tab')
        focus=aria_page.evaluate("""()=>({tag:document.activeElement?.tagName,
            outline:getComputedStyle(document.activeElement).outlineColor,
            width:getComputedStyle(document.activeElement).outlineWidth})""")
        assert focus['tag']=='BUTTON',focus
        assert focus['width']=='3px' and focus['outline']=='rgb(17, 104, 93)',focus
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
        focus_team.locator('#actor-select').select_option('marina')
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
    browser.close()
