"""FV-COR-07: independent FV-AUD-03 reproductions in ESM and integral HTML.
No source edits/real services. Optional outputs must be outside the checkout.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
import json, os, sys, hashlib, subprocess, tempfile
from playwright.sync_api import sync_playwright, expect
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'preview'))
from build_standalone_preview import build as build_integral_preview
VISUAL=Path(__file__).resolve().parents[1]
OUTPUT=Path(os.environ['FV_COR07_OUTPUT']).resolve() if os.environ.get('FV_COR07_OUTPUT') else None
if OUTPUT:
    checkout=VISUAL.parents[1]
    if OUTPUT==checkout or checkout in OUTPUT.parents:raise ValueError('Evidence must stay outside the checkout')
    OUTPUT.mkdir(parents=True,exist_ok=True)
results=[]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(VISUAL)))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start();origin=f'http://127.0.0.1:{server.server_port}'
    # Exact source-pinned exporter, not a hand-written alternative bundle.
    temp=tempfile.TemporaryDirectory(prefix='fv-cor07-preview-')
    integral_path=Path(temp.name)/'prumo-preview-integral.html'
    try:
        build_integral_preview(integral_path)
        integral=integral_path.read_text(encoding='utf-8')
    except Exception:
        server.shutdown();server.server_close();thread.join(5);temp.cleanup()
        raise
    try:
        with sync_playwright() as p:
            options={'headless':True,'args':['--no-sandbox','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']}
            exe=os.environ.get('CHROMIUM_EXECUTABLE') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None)
            if exe:options['executable_path']=exe
            browser=p.chromium.launch(**options)
            cells=[('module',1440,900,'light')] if os.environ.get('FV_COR07_QUICK')=='1' else [(fmt,w,h,t) for fmt in ('module','html') for w,h in ((1440,900),(900,780),(390,844)) for t in ('light','dark')]
            for fmt,width,height,theme in cells:
                for scenario in ('R01','R01-recording','R01-requesting','N02','N03','N04','N05','I01-empty','I01-blank','I02','I03','OBS01'):
                    actor='marina' if scenario=='I02' else 'rafael'
                    context=browser.new_context(viewport={'width':width,'height':height},color_scheme=theme,has_touch=width<=760,is_mobile=width<=760,permissions=['microphone'])
                    external=[];errors=[]
                    context.add_init_script('''window.__drops=[];window.__streams=[];
                    const drop=URL.revokeObjectURL.bind(URL);URL.revokeObjectURL=u=>{__drops.push(u);drop(u)};
                    const gum=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
                    navigator.mediaDevices.getUserMedia=async c=>{const s=await gum(c);__streams.push(s);return s;};''')
                    patch=None
                    if scenario.startswith('I01-'):
                        messages=[] if scenario=='I01-empty' else [{'id':'blank','side':'in','body':' \n\t','time':'T1'}]
                        patch='const r=rows.find(r=>r.id==="A-102");r.messages='+json.dumps(messages)+';r.unread=0;return rows;'
                    def route(r):
                        if not r.request.url.startswith(origin+'/'):
                            external.append(r.request.url);r.abort();return
                        is_html=r.request.url.split('?')[0].endswith('/audit-integral.html')
                        if is_html or (patch and r.request.url.split('?')[0].endswith('/cf-op-02.mjs')):
                            body=integral if is_html else r.fetch().text()
                            if patch:
                                body=body.replace('function copyCFDemoFixtures()', 'function corOriginalCopyCFDemoFixtures()',1)
                                wrapper='function copyCFDemoFixtures(){const rows=corOriginalCopyCFDemoFixtures();'+patch+'}'
                                body=body.replace('</script>',wrapper+'</script>',1) if is_html else body+'\nexport '+wrapper
                            r.fulfill(status=200,content_type='text/html' if is_html else 'text/javascript',body=body)
                        else:r.continue_()
                    context.route('**/*',route)
                    page=context.new_page();page.set_default_timeout(7000);page.on('pageerror',lambda e:errors.append(str(e)))
                    result={'scenario':scenario,'format':fmt,'width':width,'theme':theme,'actor':actor,'pass':False}
                    def open_case(number):
                        if page.locator('#bank-dialog').is_visible():page.locator('#bank-close').click()
                        if width<=760:
                            if page.locator('#visual-app').get_attribute('data-mobile-view')=='detail':page.locator('#detail-close').click()
                            if page.locator('#visual-app').get_attribute('data-mobile-view')=='thread':page.locator('#thread-back').click()
                        elif width<=1040 and page.locator('#detail-pane').is_visible():page.locator('#detail-close').click()
                        page.get_by_role('button',name='Abrir conversa Cliente Exemplo '+number,exact=False).click()
                    def details():
                        page.locator('#thread-title').focus();page.keyboard.press('Enter');expect(page.locator('#detail-pane')).to_be_visible()
                    def bank_from_case():
                        details();page.locator('#open-bank-case').click();expect(page.locator('#bank-dialog')).to_be_visible()
                    def ready_audio():
                        page.locator('#audio-record').click();expect(page.locator('#audio-status')).to_have_text('Gravando áudio')
                        expect(page.locator('#audio-duration')).not_to_have_text('0:00')
                        page.locator('#audio-stop').click();expect(page.locator('#audio-status')).to_have_text('Áudio pronto para ouvir')
                        return page.locator('#audio-preview').get_attribute('src')
                    try:
                        url=origin+('/audit-integral.html' if fmt=='html' else '/')+('?perfil=gestor' if actor=='marina' else '')
                        page.goto(url);expect(page.locator('.conversation-card')).to_have_count(15 if actor=='marina' else 11)
                        if scenario in ('R01','R01-recording','R01-requesting','N02'):
                            open_case('02');field=page.locator('#message-input');field.fill('Rascunho da conversa A 🙂')
                            if scenario=='R01-requesting':
                                page.evaluate('''()=>{const gum=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
                                  navigator.mediaDevices.getUserMedia=()=>new Promise(resolve=>{window.__lateResolve=async()=>resolve(await gum({audio:true}))})}''')
                                page.locator('#audio-record').click();expect(page.locator('#audio-status')).to_contain_text('Aguardando permissão')
                                audio=None
                            elif scenario=='R01-recording':
                                page.locator('#audio-record').click();expect(page.locator('#audio-status')).to_have_text('Gravando áudio')
                                expect(page.locator('#audio-duration')).not_to_have_text('0:00');audio=None
                            else:audio=ready_audio()
                            bank_from_case()
                            if scenario=='N02':
                                page.locator('#bank-case-select').select_option('A-108');page.locator('#show-clarification-demo').click()
                            page.locator('#bank-close').click()
                            if width<=1040:page.locator('#detail-close').click()
                            expect(field).to_have_value('Rascunho da conversa A 🙂')
                            expect(page.locator('#thread-meta')).to_contain_text('Caso A-102')
                            if scenario=='R01-requesting':
                                page.evaluate('async()=>await window.__lateResolve()')
                                page.wait_for_function('__streams.every(s=>s.getTracks().every(t=>t.readyState==="ended"))')
                                expect(page.locator('#audio-draft')).to_be_hidden()
                            else:
                                expect(page.locator('#audio-status')).to_have_text('Áudio pronto para ouvir')
                                expect(page.locator('#audio-preview')).to_be_visible()
                                if audio:assert page.locator('#audio-preview').get_attribute('src')==audio
                                else:audio=page.locator('#audio-preview').get_attribute('src')
                            if OUTPUT:page.screenshot(path=str(OUTPUT/f'{scenario}-{fmt}-{width}-{theme}-preserved.png'),full_page=True)
                            if audio:assert not page.evaluate('u=>__drops.includes(u)',audio)
                            assert page.evaluate('__streams.every(s=>s.getTracks().every(t=>t.readyState==="ended"))')
                            # A real case change still invalidates both drafts and URLs.
                            open_case('08')
                            if audio:assert page.evaluate('u=>__drops.includes(u)',audio)
                            expect(field).to_have_value('');expect(page.locator('#audio-draft')).to_be_hidden()
                        elif scenario=='N03':
                            open_case('12');details();page.locator('#case-tab-activity').click()
                            kinds=page.locator('.timeline-events .activity-item').evaluate_all('ns=>ns.map(n=>({kind:n.dataset.kind,state:n.dataset.state}))')
                            assert next(i for i,x in enumerate(kinds) if x['state']=='sent_confirmed')<next(i for i,x in enumerate(kinds) if x['kind']=='lost'),kinds
                            expect(page.locator('.timeline-events [data-kind=lost]')).to_be_visible()
                        elif scenario in ('N04','N05'):
                            open_case('15');details()
                            if scenario=='N04':
                                page.locator('#case-tab-activity').click();event=page.locator('.activity-item[data-kind=registration]')
                                event.scroll_into_view_if_needed();expect(event).to_be_visible();expect(event).to_contain_text('live-form-v2-demo')
                            else:
                                summary=page.locator('.ai-communication[data-source=F03] summary');summary.click()
                                expect(page.locator('.ai-communication[data-source=F03] p')).to_be_visible()
                        elif scenario.startswith('I01-'):
                            open_case('02');expect(page.locator('.attention-pending')).to_have_count(0)
                            expect(page.locator('.message')).to_have_count(0)
                            expect(page.locator('#thread-body')).to_contain_text('Nenhuma mensagem' if scenario=='I01-empty' else 'sem conteúdo legível')
                            details();page.locator('#case-tab-notes').click();page.locator('#case-tab-activity').click();page.locator('#detail-close').click()
                            open_case('05');expect(page.locator('.conversation-card').filter(has_text='Cliente Exemplo 02').locator('.attention-pending')).to_have_count(0)
                        elif scenario=='I02':
                            open_case('02');label=page.locator('.message-transport-state').first
                            expect(label).to_be_visible();expect(label).to_contain_text('Transporte não confirmado')
                            expect(page.locator('.message-transport-hint').first).to_be_visible()
                            expect(page.locator('#thread-body')).not_to_contain_text('ack-a102');expect(page.locator('#composer')).to_be_hidden()
                            if width<=760:page.locator('#thread-back').click()
                            expect(page.locator('.conversation-card').filter(has_text='Cliente Exemplo 02').locator('.attention-unread')).to_have_text('2')
                        elif scenario=='I03':
                            open_case('02');expect(page.locator('#detail-toggle')).to_have_count(0)
                            details();page.locator('#detail-close').focus();page.keyboard.press('Enter')
                            expect(page.locator('#detail-pane')).to_be_hidden();expect(page.locator('#thread-title')).to_be_focused()
                            details();page.keyboard.press('Escape');expect(page.locator('#detail-pane')).to_be_hidden();expect(page.locator('#thread-title')).to_be_focused()
                        else:
                            page.locator('#filter-toggle').click()
                            for mode,count in (('all','11'),('active','8'),('history','3')):
                                page.locator('[data-inbox='+mode+']').click();expect(page.locator('#list-count')).to_contain_text(count)
                                expect(page.locator('#queue-summary')).to_have_attribute('aria-label','Indicadores fictícios dos atendimentos ativos autorizados')
                                expect(page.locator('#queue-summary')).to_contain_text('Total de ativos')
                        assert not errors,errors;assert not external,external
                        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                        result['pass']=True
                    except Exception as e:result['error']=str(e)
                    finally:
                        if OUTPUT:
                            if scenario in ('N03','N04','N05'):
                                # Keep current view so the evidence shows the actual asserted state.
                                pass
                            name=f'{scenario}-{fmt}-{width}-{theme}'
                            page.screenshot(path=str(OUTPUT/(name+'.png')),full_page=True)
                        result['js_errors']=errors;result['external_requests']=external;results.append(result)
                        if OUTPUT:(OUTPUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
                        print('FV-COR-07',scenario,fmt,width,theme,'PASS' if result['pass'] else 'FAIL',flush=True)
                        context.close()
            browser.close()
    finally:
        server.shutdown();server.server_close();thread.join(5)
        if OUTPUT:
            (OUTPUT/'prumo-preview-integral.html').write_text(integral,encoding='utf-8')
            head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=VISUAL,text=True).strip()
            branch=subprocess.check_output(['git','branch','--show-current'],cwd=VISUAL,text=True).strip()
            clean=not subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=VISUAL,text=True).strip()
            provenance={'head':head,'branch':branch,'clean_worktree':clean,'synthetic_only':True,
                'published':False,'protocol':'HTTP loopback','physical_devices':False,
                'html_sha256':hashlib.sha256(integral.encode()).hexdigest(),
                'overlay_scenarios':['I01-empty','I01-blank'],
                'sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUTPUT.iterdir() if f.is_file() and f.name!='PROVENIENCIA.json'}}
            (OUTPUT/'PROVENIENCIA.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
        temp.cleanup()
    failed=[r for r in results if not r['pass']]
    assert not failed,json.dumps(failed,ensure_ascii=False,indent=2)

if __name__=='__main__':main()
