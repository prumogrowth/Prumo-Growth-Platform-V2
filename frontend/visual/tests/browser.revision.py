"""FV-REV-01 Etapa 1: Chromium matrix and synthetic capability boundaries.
No real backend, dispatch, F02, account authentication or publication.
"""
from pathlib import Path
import sys
import os
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'preview'))
from collect_visual_review import offline_page_source


CONTRAST=r"""e=>{
  const rgb=s=>s.match(/\d+(?:\.\d+)?/g).slice(0,3).map(Number);
  const lum=v=>{const c=v.map(n=>n/255).map(n=>n<=.04045?n/12.92:((n+.055)/1.055)**2.4);return .2126*c[0]+.7152*c[1]+.0722*c[2]};
  const a=lum(rgb(getComputedStyle(e).color));let background=null;
  for(let node=e;node;node=node.parentElement){
    const color=getComputedStyle(node).backgroundColor,parts=color.match(/\d+(?:\.\d+)?/g).map(Number);
    if(parts.length===3 || parts[3]===1){background=rgb(color);break;}
  }
  if(!background)return 0;const b=lum(background);
  return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
}"""

def green_control(locator):
    color=locator.evaluate('e=>getComputedStyle(e).backgroundColor')
    import re
    r,g,b=map(float,re.findall(r'[\d.]+',color)[:3])
    assert g>r+10 and g>b+10,color
    assert locator.evaluate(CONTRAST)>=4.5


def no_composition(page):
    for selector in ('#composer','#message-input','#emoji-toggle','#audio-record','.send-button','#communication-tools'):
        expect(page.locator(selector)).to_be_hidden()
        assert page.locator(selector).bounding_box() is None,selector


def main():
    html, script=offline_page_source()
    with sync_playwright() as p:
        options={'headless':True,'args':['--no-sandbox']}
        exe=os.getenv('CHROMIUM_EXECUTABLE') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').is_file() else None)
        if exe:options['executable_path']=exe
        browser=p.chromium.launch(**options)
        for width,height in ((1440,900),(900,780),(390,844),(320,640)):
            for theme in ('light','dark'):
                for actor in ('rafael','marina'):
                    page=browser.new_page(viewport={'width':width,'height':height},color_scheme=theme)
                    page.set_default_timeout(5000)
                    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                    page.set_content(html);page.add_script_tag(content=script)
                    if actor=='marina':
                        page.locator('#demo-open').click()
                        page.locator('#actor-select').select_option(actor)
                        page.locator('#demo-close').click()
                    expect(page.locator('.conversation-card')).to_have_count(11 if actor=='rafael' else 15)
                    assert page.locator('.avatar').count()==0
                    assert page.locator('.search-shortcut').count()==0
                    assert page.locator('#ui-settings #actor-select, #ui-settings #shop-select, #ui-settings #reset-app').count()==0
                    icon=page.locator('#filter-toggle');settings=page.locator('#ui-settings summary')
                    ib=icon.bounding_box();sb=settings.bounding_box();search=page.locator('#search-input').bounding_box()
                    assert ib['width']>=44 and ib['height']>=44
                    assert abs(ib['y']-sb['y'])<1 and 0<=sb['x']-(ib['x']+ib['width'])<=10
                    assert ib['y']+ib['height']<=search['y']
                    card=page.locator('.conversation-card').first
                    shop=card.locator('.item-shop');expect(shop).to_be_visible()
                    assert shop.inner_text()=='Aurora Motos' and shop.get_attribute('title')=='Aurora Motos'
                    assert card.locator('.item-center').evaluate('e=>e.children.length')==2
                    assert card.locator('.item-preview').bounding_box()['width']>=50
                    assert shop.evaluate(CONTRAST)>=4.5
                    sh=shop.bounding_box();pr=card.locator('.item-preview').bounding_box()
                    assert abs((sh['y']+sh['height']/2)-(pr['y']+pr['height']/2))<1
                    unread=card.locator('.attention-unread');green_control(unread)
                    assert unread.inner_text()=='2' and unread.get_attribute('aria-label')
                    icon.focus();icon.press('Enter')
                    expect(page.locator('#shop-select')).to_be_visible()
                    pb=page.locator('#filter-panel').bounding_box()
                    assert pb['x']>=0 and pb['x']+pb['width']<=width and pb['y']+pb['height']<=height
                    page.locator('#shop-select').focus();page.keyboard.press('Escape')
                    expect(icon).to_be_focused();expect(page.locator('#shop-select')).to_be_hidden()
                    icon.press('Enter')
                    assert page.locator('.shop-control label').evaluate(CONTRAST)>=4.5
                    assert page.locator('.rail-label').evaluate(CONTRAST)>=4.5
                    if actor=='rafael':expect(page.locator('#status-filter')).to_be_hidden()
                    else:expect(page.locator('#status-filter')).to_be_visible()
                    page.locator('[data-inbox=history]').click()
                    expect(page.locator('.conversation-card')).to_have_count(3)
                    page.locator('[data-filter=unread]').click()
                    expect(page.locator('.no-results')).to_be_visible()
                    page.locator('[data-filter=all]').click()
                    page.locator('[data-inbox=all]').click()
                    page.locator('#list-extra summary').click()
                    number='02' if actor=='rafael' else '06'
                    page.get_by_role('button',name='Abrir conversa Cliente Exemplo '+number,exact=False).click()
                    field=page.locator('#message-input');field.fill('Rascunho preservado 🙂')
                    expect(page.locator('#request-completion')).to_be_visible()
                    green_control(page.locator('#request-completion'))
                    expect(page.locator('#composer')).to_be_visible()
                    if width<=760:page.locator('#thread-back').click()
                    pending=page.get_by_role('button',name='Abrir conversa Cliente Exemplo '+number,exact=False).locator('.attention-pending')
                    expect(pending).to_be_visible()
                    warm=pending.evaluate('e=>getComputedStyle(e).color')
                    import re
                    r,g,b=map(float,re.findall(r'[\d.]+',warm)[:3]);assert r>g>b,warm
                    assert pending.evaluate(CONTRAST)>=4.5 and pending.get_attribute('aria-label')
                    if width<=760:
                        page.get_by_role('button',name='Abrir conversa Cliente Exemplo '+number,exact=False).click()
                        field.fill('Rascunho preservado 🙂')
                    assert page.locator('#thread-actions #request-completion').count()==1
                    page.locator('#thread-title').click()
                    expect(page.locator('#detail-pane')).to_be_visible()
                    page.locator('#case-tab-notes').click()
                    note=page.locator('#note-text');note.fill('Nota não submetida')
                    panel_width=page.locator('#detail-pane').bounding_box()['width']
                    page.locator('#detail-content').evaluate("e=>{e.style.height='120px';e.style.overflowY='scroll'}")
                    assert abs(page.locator('#detail-pane').bounding_box()['width']-panel_width)<1
                    page.locator('#detail-close').click()
                    expect(page.locator('#detail-pane')).to_be_hidden()
                    expect(page.locator('#thread-title')).to_be_focused()
                    expect(field).to_have_value('Rascunho preservado 🙂')
                    expect(page.locator('#thread-meta')).to_contain_text('A-102' if actor=='rafael' else 'A-106')
                    page.locator('#thread-title').press('Enter')
                    expect(note).to_have_value('Nota não submetida')
                    page.locator('#case-tab-notes').focus();page.keyboard.press('Escape')
                    expect(page.locator('#detail-pane')).to_be_hidden()
                    expect(page.locator('#thread-title')).to_be_focused()
                    # Pending simulated operation survives closing/reopening its panel.
                    page.locator('#request-completion').click()
                    page.locator('#completion-form button[value=confirm]').click()
                    page.locator('#thread-title').click()
                    expect(page.locator('#case-tab-extraction')).to_have_attribute('aria-selected','true')
                    before=page.locator('#case-tab-panel').inner_text()
                    page.locator('#detail-close').click();page.locator('#thread-title').click()
                    assert page.locator('#case-tab-panel').inner_text()==before
                    page.locator('#detail-close').click()
                    if width<=760:page.locator('#thread-back').click()
                    for number,label in (('16','Vendido'),('12','Perdido')):
                        page.get_by_role('button',name='Abrir conversa Cliente Exemplo '+number,exact=False).click()
                        expect(page.locator('#terminal-banner')).to_contain_text(label)
                        assert page.locator('#terminal-banner').evaluate(CONTRAST)>=4.5
                        expect(field).to_be_disabled();no_composition(page)
                        expect(page.locator('#composer-availability')).to_be_hidden()
                        expect(page.locator('#composer-demo-guidance')).to_be_hidden()
                        expect(page.locator('#thread-bottom')).to_be_hidden()
                        if width<=760:page.locator('#thread-back').click()
                    # COR-05: actual visibility and horizontal geometry for every capability subset.
                    for meta,allowed,count in (
                        ('expired',[],0),('expired',['single_template'],1),('expired',['request_chain'],1),
                        ('expired',['single_template','request_chain'],2),('unknown',['free_text','single_template','request_chain'],0),
                        ('blocked',['free_text','single_template','request_chain'],0),('open',[],0),('open',['free_text'],0)):
                        page.evaluate('''([actor,meta,allowed])=>{
                          state.processing={};state.followupRequests={};
                          const record=state.cases.find(r=>r.id===(actor==='rafael'?'A-102':'A-106'));
                          record.metaWindowProjection=meta;record.allowedActionsProjection=allowed;
                          record.eligibleTemplatesProjection=['modelo_continuidade_demo@v1-demo'];
                          state.selectedId=record.id;state.mobileView='thread';render();
                        }''',[actor,meta,allowed])
                        buttons=page.locator('#followup-actions button');expect(buttons).to_have_count(count)
                        if meta=='open' and 'free_text' in allowed:
                            expect(page.locator('#composer')).to_be_visible();expect(field).to_be_enabled()
                        else:
                            no_composition(page);expect(field).to_be_disabled()
                            expect(page.locator('#composer-availability')).to_be_visible()
                        for action in buttons.all():
                            expect(action).to_be_visible();assert action.bounding_box()['height']>=44
                        if count==2:
                            first,second=[n.bounding_box() for n in buttons.all()]
                            assert abs(first['y']-second['y'])<1 and first['x']+first['width']<=second['x']
                        if count==1:
                            expect(buttons).to_have_text(['Enviar template' if allowed[0]=='single_template' else 'Cadeia por IA'])
                        if count==0 and meta!='open':
                            expect(page.locator('#followup-actions')).to_be_hidden()
                            expect(page.locator('#composer-availability')).to_contain_text('indisponível')
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                    assert not errors,errors
                    print(f'FV-REV-01 COR-01..06 {width}x{height} {theme} {actor}: PASS',flush=True)
                    page.close()
        # Capability matrix with exact synthetic records; same UI projection as runtime.
        page=browser.new_page(viewport={'width':1440,'height':900})
        page.set_content(html);page.add_script_tag(content=script)
        for meta,capabilities,count in (
            ('expired',[],0),('expired',['single_template'],1),('expired',['request_chain'],1),
            ('expired',['single_template','request_chain'],2),('unknown',['single_template','request_chain'],0),
            ('blocked',['single_template','request_chain'],0),('open',['single_template','request_chain'],0)):
            page.evaluate("""([meta,actions])=>{
              const record=state.cases.find(r=>r.id==='A-107');
              record.metaWindowProjection=meta;record.allowedActionsProjection=actions;
              state.selectedId=record.id;render();
            }""",[meta,capabilities])
            expect(page.locator('#followup-actions button')).to_have_count(count)
            expect(page.locator('#message-input')).to_be_disabled()
            if count==0:expect(page.locator('#composer-availability')).to_contain_text('indisponível')
        page.locator('#demo-open').click()
        page.locator('#demo-list-state').select_option('loading')
        page.locator('#demo-close').click()
        expect(page.locator('#conversation-items')).to_have_attribute('aria-busy','true')
        expect(page.locator('.conversation-card')).to_have_count(0)
        # Supervisor opening does not acknowledge on behalf of the assignee.
        page.evaluate("const supervised=state.cases.find(r=>r.id==='A-102');supervised.metaWindowProjection='open';supervised.allowedActionsProjection=['free_text','complete'];changeActor('marina')")
        card=page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False)
        expect(card.locator('.attention-unread')).to_have_text('2');card.click()
        expect(card.locator('.attention-unread')).to_have_text('2')
        expect(page.locator('#message-input')).to_be_disabled();no_composition(page)
        expect(page.locator('#request-completion')).to_have_count(0)
        page.evaluate("const record=state.cases.find(r=>r.id==='A-102');record.metaWindowProjection='expired';record.allowedActionsProjection=['single_template','request_chain','complete'];render()")
        no_composition(page);expect(page.locator('#followup-actions')).to_be_hidden()
        expect(page.locator('#composer-availability')).to_be_visible()
        expect(page.locator('#request-completion')).to_have_count(0)
        page.close();browser.close()
        print('FV-REV-01 composer 0/1/2, unknown/blocked/open and supervisor: PASS',flush=True)

if __name__=='__main__':main()
