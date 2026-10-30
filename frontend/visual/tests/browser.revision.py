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
                    page.locator('#list-extra summary').click()
                    expect(page.locator('#shop-select')).to_be_visible()
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
                        expect(field).to_be_disabled()
                        if width<=760:page.locator('#thread-back').click()
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                    assert not errors,errors
                    print(f'FV-REV-01 {width}x{height} {theme} {actor}: PASS',flush=True)
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
            expect(page.locator('#workflow-bar button')).to_have_count(count)
            expect(page.locator('#message-input')).to_be_disabled()
            if count==0:expect(page.locator('#composer-availability')).to_contain_text('indisponível')
        page.locator('#demo-open').click()
        page.locator('#demo-list-state').select_option('loading')
        page.locator('#demo-close').click()
        expect(page.locator('#conversation-items')).to_have_attribute('aria-busy','true')
        expect(page.locator('.conversation-card')).to_have_count(0)
        # Supervisor opening does not acknowledge on behalf of the assignee.
        page.evaluate("changeActor('marina')")
        card=page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False)
        expect(card.locator('.attention-unread')).to_have_text('2');card.click()
        expect(card.locator('.attention-unread')).to_have_text('2')
        expect(page.locator('#message-input')).to_be_disabled()
        page.close();browser.close()
        print('FV-REV-01 composer 0/1/2, unknown/blocked/open and supervisor: PASS',flush=True)

if __name__=='__main__':main()
