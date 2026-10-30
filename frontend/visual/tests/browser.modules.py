"""FV-REV-01/2: navegação, consulta, histórico e gestão em Chromium REAL.
Somente HTTP loopback/fixtures sintéticas; sem APIs, persistência ou integrações.
"""
from pathlib import Path
import os
import sys
from playwright.sync_api import sync_playwright, expect
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'preview'))
from collect_visual_review import local_preview_server, offline_page_source


CONTRAST=r"""e=>{
 const rgb=s=>s.match(/\d+(?:\.\d+)?/g).slice(0,3).map(Number);
 const lum=v=>{const c=v.map(n=>n/255).map(n=>n<=.04045?n/12.92:((n+.055)/1.055)**2.4);return .2126*c[0]+.7152*c[1]+.0722*c[2]};
 const a=lum(rgb(getComputedStyle(e).color));let background=null;
 for(let node=e;node;node=node.parentElement){const color=getComputedStyle(node).backgroundColor,parts=color.match(/\d+(?:\.\d+)?/g).map(Number);if(parts.length===3 || parts[3]===1){background=rgb(color);break;}}
 if(!background)return 0;const b=lum(background);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
}"""

def open_conversation(page, number, width):
    if page.locator('#bank-dialog').is_visible():page.locator('#bank-close').click()
    if width<=760:
        if page.locator('#visual-app').get_attribute('data-mobile-view')=='detail':page.locator('#detail-close').click()
        if page.locator('#visual-app').get_attribute('data-mobile-view')=='thread':page.locator('#thread-back').click()
    elif width<=1040 and page.locator('#detail-pane').is_visible():page.locator('#detail-close').click()
    target=page.get_by_role('button',name='Abrir conversa Cliente Exemplo '+number,exact=False)
    if target.count()==0:
        page.locator('#filter-toggle').click();page.locator('[data-inbox=all]').click();page.locator('#filter-toggle').click()
    target.click()
    page.locator('#thread-title').click()
    expect(page.locator('#detail-pane')).to_be_visible()


def main():
    with local_preview_server() as origin, sync_playwright() as p:
        options={'headless':True,'args':['--no-sandbox']}
        exe=os.getenv('CHROMIUM_EXECUTABLE') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').is_file() else None)
        if exe:options['executable_path']=exe
        browser=p.chromium.launch(**options)
        for width,height in ((1440,900),(900,780),(390,844),(320,640),(740,390)):
            for theme in ('light','dark'):
                for actor in ('rafael','marina'):
                    context=browser.new_context(viewport={'width':width,'height':height},color_scheme=theme)
                    external=[]
                    def route(r):
                        if r.request.url.startswith(origin+'/'):r.continue_()
                        else:external.append(r.request.url);r.abort()
                    context.route('**/*',route)
                    page=context.new_page();page.set_default_timeout(6500)
                    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                    page.goto(origin+('/?perfil=gestor' if actor=='marina' else '/'))
                    expect(page.locator('.conversation-card')).to_have_count(15 if actor=='marina' else 11)
                    title=page.locator('#thread-title').inner_text()
                    card=page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False)
                    expect(card.locator('.attention-unread')).to_have_text('2')
                    nav=page.locator('#bank-nav-mobile' if width<=760 else '#bank-nav')
                    nav.focus();page.keyboard.press('Enter')
                    expect(page.locator('#bank-case-select')).to_be_focused()
                    page.locator('#bank-case-select').select_option('A-108')
                    content=page.locator('#bank-content');expect(content).to_be_visible()
                    box=page.locator('#bank-dialog').bounding_box()
                    assert box['x']>=0 and box['x']+box['width']<=width
                    assert box['y']>=0 and box['y']+box['height']<=height
                    assert content.locator('input,textarea,[contenteditable=true]').count()==0
                    for selector in ('.bank-guidance','.bank-context','#bank-case-select','.bank-content .detail-label','.bank-content .detail-small'):
                        assert page.locator(selector).first.evaluate(CONTRAST)>=4.5,(theme,selector)
                    assert page.locator('#thread-title').inner_text()==title
                    expect(card.locator('.attention-unread')).to_have_text('2')
                    if actor=='rafael':
                        for text in ('Valor fictício confirmado','v1-ficticia','INFORMAÇÕES AUSENTES','CONTRADIÇÕES','f03-a108-1','f03-a108-2'):
                            expect(content).to_contain_text(text)
                        expect(content).not_to_contain_text('Somente proposta')
                    else:
                        expect(content).to_contain_text('Detalhes restritos ao responsável')
                        for text in ('Valor fictício confirmado','v1-ficticia','a108-1','f03-a108-1'):
                            expect(content).not_to_contain_text(text)
                    page.locator('#bank-case-select').select_option('A-114')
                    if actor=='rafael':
                        for text in ('F01 · coleta inicial','F03 · atualização confirmada','live-form-v1-demo','live-form-v2-demo','snapshot preservado','Confirmada apenas na fixture · sem remessa iniciada'):
                            expect(content).to_contain_text(text)
                    else:
                        for text in ('Valor sintético','bank-demo-v1','live-form-v2-demo'):
                            expect(content).not_to_contain_text(text)
                    page.locator('#bank-case-select').select_option('A-105')
                    expect(content).to_contain_text('Decisão bancária não confirmada' if actor=='rafael' else 'Acompanhamento bancário · resumo')
                    assert content.locator('button').count()==0
                    # Native Escape closes only Bank and restores its actual navigation opener.
                    page.keyboard.press('Escape');expect(page.locator('#bank-dialog')).to_be_hidden();expect(nav).to_be_focused()
                    open_conversation(page,'09',width)
                    expect(page.locator('.detail-tab')).to_have_count(3)
                    assert page.locator('.detail-tab').all_inner_texts()==['Resumo','Histórico','Notas']
                    assert page.locator('.profile-detail').count()==0
                    expect(page.locator('#detail-content')).not_to_contain_text('Cliente Exemplo 09')
                    expect(page.locator('#detail-content')).not_to_contain_text('REGRAS DA EXPERIÊNCIA')
                    comm=page.locator('.ai-communication')
                    expect(comm).to_have_count(5 if actor=='rafael' else 3)
                    for i in range(comm.count()):
                        summary=comm.nth(i).locator('summary');summary.focus();page.keyboard.press('Enter')
                        expect(comm.nth(i).locator('p')).to_be_visible()
                        assert summary.bounding_box()['height']>=44
                    assert page.locator('.ai-communication[data-source=F03]').count()==(2 if actor=='rafael' else 0)
                    page.locator('#case-tab-overview').focus();page.keyboard.press('ArrowRight')
                    expect(page.locator('#case-tab-activity')).to_be_focused()
                    expect(page.locator('.timeline-events')).to_be_visible()
                    assert page.locator('.activity-item[data-kind=message]').count()==0
                    assert page.locator('.activity-item[data-kind=registration]').count()==(2 if actor=='rafael' else 0)
                    page.locator('#case-tab-notes').click()
                    expect(page.locator('#note-text')).to_be_visible() if actor=='rafael' else expect(page.locator('#note-text')).to_be_hidden()
                    # Recontatos: cancelado é histórico, futuro tem grupo e círculos próprios.
                    open_conversation(page,'11',width);page.locator('#case-tab-activity').click()
                    expect(page.locator('#future-attempts .activity-item')).to_have_count(3)
                    assert page.locator('#future-attempts [data-state=cancelled]').count()==0
                    for state in ('sent_confirmed','executing','failed','uncertain','cancelled'):
                        event=page.locator('.timeline-events [data-state='+state+']')
                        event.scroll_into_view_if_needed();expect(event).to_be_visible()
                    future=page.locator('#future-attempts .activity-item').first
                    assert future.evaluate('e=>getComputedStyle(e).borderLeftWidth')=='0px'
                    assert future.evaluate('e=>getComputedStyle(e,"::before").borderRadius')=='50%'
                    future.scroll_into_view_if_needed();expect(future).to_be_visible()
                    assert future.locator('strong').evaluate(CONTRAST)>=4.5
                    assert future.locator('.event-state').evaluate(CONTRAST)>=4.5
                    # Navegação autorizada entre ciclos pós-remessa e pós-venda.
                    for origin_number,destination in (('05','A-114'),('16','A-116')):
                        open_conversation(page,origin_number,width);page.locator('#case-tab-activity').click()
                        if origin_number=='16':
                            sale=page.locator('.timeline-events [data-kind=sold] strong');sale.scroll_into_view_if_needed();expect(sale).to_be_visible()
                            color=sale.evaluate('e=>getComputedStyle(e).color');import re
                            r,g,b=map(float,re.findall(r'[\d.]+',color)[:3]);assert g>r+10 and g>b+10
                            assert sale.evaluate(CONTRAST)>=4.5
                        page.get_by_role('button',name='Abrir novo atendimento humano').click()
                        expect(page.locator('#thread-meta')).to_contain_text(destination)
                        expect(page.locator('#message-input')).to_be_enabled() if actor=='rafael' else expect(page.locator('#message-input')).to_be_disabled()
                        if width<=760:page.locator('#thread-title').click()
                        expect(page.locator('#detail-content')).to_contain_text('Silenciada definitivamente')
                        page.get_by_role('button',name='Consultar atendimento de origem').click()
                        expect(page.locator('#message-input')).to_be_disabled()
                    open_conversation(page,'12',width);page.locator('#case-tab-activity').click()
                    loss=page.locator('.timeline-events [data-kind=lost] strong');loss.scroll_into_view_if_needed();expect(loss).to_be_visible()
                    color=loss.evaluate('e=>getComputedStyle(e).color');import re
                    r,g,b=map(float,re.findall(r'[\d.]+',color)[:3]);assert r>g+10 and r>b+10
                    assert loss.evaluate(CONTRAST)>=4.5
                    open_conversation(page,'02',width)
                    page.locator('#case-tab-notes').click()
                    if actor=='rafael':
                        page.locator('#note-text').fill('Rascunho interno preservado')
                        page.locator('#detail-close').click()
                        field=page.locator('#message-input');field.fill('Mensagem 🙂 preservada')
                        page.locator('#thread-title').click();page.locator('#case-tab-overview').click()
                        page.locator('#open-bank-case').click();expect(page.locator('#bank-dialog')).to_be_visible()
                        page.locator('#bank-close').click();expect(page.locator('#open-bank-case')).to_be_focused()
                        page.locator('#case-tab-notes').click();expect(page.locator('#note-text')).to_have_value('Rascunho interno preservado')
                        expect(field).to_have_value('Mensagem 🙂 preservada')
                        assert page.locator('.detail-row').filter(has_text='Rascunho interno preservado').count()==0
                    else:expect(page.locator('#note-text')).to_be_hidden()
                    page.locator('#detail-close').click()
                    if width<=760:page.locator('#thread-back').click()
                    if actor=='marina':
                        team_nav=page.locator('#team-nav-mobile' if width<=760 else '#team-nav')
                        team_nav.click();expect(page.locator('#team-dialog')).to_be_visible()
                        for panel in ('members','monitor','batches','queue'):
                            page.locator('#team-show-'+panel).click()
                            expect(page.locator({'members':'#team-list','monitor':'#team-monitor','batches':'#team-batches','queue':'#team-queue'}[panel])).to_be_visible()
                        page.locator('#team-close').click()
                    else:expect(page.locator('#team-nav-mobile' if width<=760 else '#team-nav')).to_be_hidden()
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                    assert not errors and not external,(errors,external)
                    print(f'FV-REV-01/2 {width} {theme} {actor}: PASS',flush=True)
                    context.close()
        # Estados bancários sem prova e cancelamento projetado: fixtures injetadas
        # no mesmo runtime, como as regressões de capacidades do gate anterior.
        html,script=offline_page_source()
        negative=browser.new_page(viewport={'width':900,'height':780},color_scheme='dark')
        negative.set_default_timeout(6500);negative.set_content(html);negative.add_script_tag(content=script)
        negative.locator('#bank-nav').click();negative.locator('#bank-case-select').select_option('A-105')
        for phase,label in (('not_submitted','Evidência bancária não confirmada'),
                            ('submission_requested','Solicitação de remessa · não confirmada'),
                            ('unverified','Evidência bancária não confirmada'),
                            ('reply_verified','Evidência bancária não confirmada')):
            negative.evaluate("phase=>{const row=state.cases.find(r=>r.id==='A-105');row.bankProjection={phase,submissionProofState:'unverified',submittedByAuthorizedHuman:false};renderBank()}",phase)
            expect(negative.locator('#bank-content')).to_contain_text(label)
            expect(negative.locator('#bank-content')).not_to_contain_text('Remessa confirmada apenas na fixture')
            expect(negative.locator('#bank-content')).not_to_contain_text('Retorno do banco confirmado apenas na fixture')
        negative.evaluate("()=>{const row=state.cases.find(r=>r.id==='A-105');row.bankProjection={phase:'reply_verified',submissionProofState:'verified',submittedByAuthorizedHuman:true,submissionVersionRef:'bank-negative-v1-demo',replyProofState:'verified',replyRecordedByHuman:true,replyVersionRef:'reply-negative-v1-demo'};renderBank()}")
        expect(negative.locator('#bank-content')).to_contain_text('Retorno do banco confirmado apenas na fixture')
        expect(negative.locator('#bank-content')).to_contain_text('cadastro enviado ao banco')
        negative.locator('#bank-close').click()
        open_conversation(negative,'11',900);negative.locator('#case-tab-activity').click()
        expect(negative.locator('#future-attempts .activity-item')).to_have_count(3)
        negative.evaluate("()=>{state.cases.find(r=>r.id==='A-110').followupProjection.state='cancelled';renderDetails()}")
        expect(negative.locator('#future-attempts')).to_be_hidden()
        expect(negative.locator('.timeline-events [data-state=cancelled]')).to_have_count(4)
        expect(negative.locator('.timeline-events [data-state=sent_confirmed]')).to_have_count(1)
        negative.close()
        print('FV-REV-01/2 negative bank evidence and confirmed cancellation: PASS',flush=True)
        browser.close()

if __name__=='__main__':main()
