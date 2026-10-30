"""FV-UX-01: módulos ESM por HTTP local e MediaRecorder real com dispositivo sintético.
Sem endpoints de negócio, credenciais, storage, uploads ou publicação.
"""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread
import os
from playwright.sync_api import sync_playwright, expect

VISUAL = Path(__file__).resolve().parents[1]

class QuietFiles(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietFiles, directory=str(VISUAL)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            launch = {'headless': True, 'args': ['--no-sandbox', '--use-fake-device-for-media-stream']}
            exe = os.getenv('CHROMIUM_EXECUTABLE', '').strip()
            if not exe and Path('/usr/bin/chromium').is_file():
                exe = '/usr/bin/chromium'
            if exe:
                launch['executable_path'] = exe
            browser = p.chromium.launch(**launch)
            for width, height in ((320,640),(390,844),(900,780),(1440,900)):
                for theme in ('light','dark'):
                    context = browser.new_context(viewport={'width':width,'height':height}, color_scheme=theme,
                                                  permissions=['microphone'])
                    errors, external, assets = [], [], []
                    def route(request_route):
                        url = request_route.request.url
                        if url.startswith(origin + '/') or url.startswith('blob:'):
                            request_route.continue_()
                        else:
                            external.append(url)
                            request_route.abort()
                    context.route('**/*',route)
                    context.add_init_script("""
                      window.__urls = []; window.__dropped = []; window.__streams = [];
                      const gum=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
                      navigator.mediaDevices.getUserMedia=async constraints=>{
                        const stream=await gum(constraints);window.__streams.push(stream);return stream;
                      };
                      const make=URL.createObjectURL.bind(URL),drop=URL.revokeObjectURL.bind(URL);
                      URL.createObjectURL=blob=>{const url=make(blob);__urls.push(url);return url;};
                      URL.revokeObjectURL=url=>{__dropped.push(url);drop(url);};
                      window.fetch=()=>{throw Error('fetch proibido na demonstração');};
                      XMLHttpRequest.prototype.open=()=>{throw Error('XHR proibido');};
                      navigator.sendBeacon=()=>{throw Error('beacon proibido');};
                      Storage.prototype.setItem=()=>{throw Error('persistência proibida');};
                      indexedDB.open=()=>{throw Error('persistência proibida');};
                    """)
                    page=context.new_page();page.set_default_timeout(7000)
                    page.on('pageerror',lambda e:errors.append(str(e)))
                    page.on('response',lambda r:assets.append((r.url,r.status)))
                    page.goto(origin)
                    expect(page.locator('.conversation-card')).to_have_count(11)
                    first=page.locator('.conversation-card').first.bounding_box()
                    assert first['y'] < height * .55, (width,first)
                    assert not page.locator('#ui-settings').evaluate('e=>e.open')
                    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
                    expect(page.locator('#composer-availability')).to_be_hidden()
                    assert page.locator('.window-indicator.open').count()==0
                    field=page.locator('#message-input')
                    field.fill('Olá, cliente')
                    field.evaluate('e=>e.setSelectionRange(3,3)')
                    page.locator('#emoji-toggle').click()
                    expect(page.get_by_role('button',name='Sorriso',exact=True)).to_be_focused()
                    page.keyboard.press('ArrowRight'); page.keyboard.press('Enter')
                    expect(field).to_have_value('Olá😊, cliente')
                    assert field.evaluate('e=>e.selectionStart')==5
                    expect(field).to_be_focused()
                    expect(page.locator('#message-preview-dialog')).to_be_hidden()
                    field.fill('a'*499);page.locator('#emoji-toggle').click();page.keyboard.press('ArrowRight');page.keyboard.press('Enter')
                    expect(field).to_have_value('a'*499)
                    field.fill('Rascunho preservado')
                    page.locator('#emoji-toggle').click();page.keyboard.press('Escape')
                    expect(field).to_have_value('Rascunho preservado');expect(field).to_be_focused()
                    for selector in ('#emoji-toggle','#audio-record','.send-button'):
                        rect=page.locator(selector).bounding_box()
                        assert rect['width']>=44 and rect['height']>=44,(width,selector,rect)
                    # Gravação real com o dispositivo sintético do Chromium, sem bytes de usuário.
                    page.locator('#audio-record').click()
                    expect(page.locator('#audio-status')).to_have_text('Gravando áudio')
                    expect(page.locator('#audio-stop')).to_be_focused()
                    if width>760:
                        page.locator('#thread-title').click()
                        page.locator('#detail-close').click()
                        expect(page.locator('#audio-status')).to_have_text('Gravando áudio')
                        expect(field).to_have_value('Rascunho preservado')
                    expect(page.locator('#audio-duration')).not_to_have_text('0:00')
                    page.locator('#audio-stop').click()
                    expect(page.locator('#audio-status')).to_have_text('Áudio pronto para ouvir')
                    expect(page.locator('#thread-body .message').last).to_be_in_viewport()
                    assert page.evaluate('__streams.every(s=>s.getTracks().every(t=>t.readyState==="ended"))')
                    player=page.locator('#audio-preview')
                    player.evaluate('e=>e.play()')
                    expect(player).to_have_js_property('paused',False)
                    player.evaluate('e=>e.pause()')
                    draft_url=player.get_attribute('src')
                    page.locator('#audio-delete').click()
                    expect(page.locator('#audio-draft')).to_be_hidden();expect(field).to_have_value('Rascunho preservado')
                    assert page.evaluate('url=>__dropped.includes(url)',draft_url)
                    page.locator('#audio-record').click();expect(page.locator('#audio-status')).to_have_text('Gravando áudio')
                    expect(page.locator('#audio-duration')).not_to_have_text('0:00')
                    page.locator('#audio-stop').click();expect(page.locator('#audio-attach')).to_be_visible()
                    page.locator('#audio-attach').click()
                    expect(page.locator('.local-audio-message')).to_have_count(1)
                    assert 'NÃO ENVIADA' in page.locator('.message').last.inner_text()
                    expect(field).to_have_value('Rascunho preservado')
                    # Anexo local não comprova resposta humana nem limpa o DOT.
                    assert page.locator('.conversation-card').filter(has_text='Cliente Exemplo 02').locator('.attention-pending').count()==1
                    if width<=760:page.locator('#thread-back').click()
                    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 08',exact=False).click()
                    expect(page.locator('#composer-availability')).to_contain_text('Janela de conversa encerrada')
                    expect(page.locator('#audio-record')).to_be_disabled();expect(page.locator('#emoji-toggle')).to_be_disabled()
                    assert page.evaluate('__urls.every(u=>__dropped.includes(u))')
                    if width<=760:page.locator('#thread-back').click()
                    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
                    assert page.locator('.local-audio-message').count()==0
                    assert 'Prévia de áudio descartada' in page.locator('.message').last.inner_text()
                    # Conclusão local remove elegibilidade durante captura.
                    page.locator('#audio-record').click();expect(page.locator('#audio-status')).to_have_text('Gravando áudio')
                    page.locator('#request-completion').click();page.locator('#completion-form button[value=confirm]').click()
                    expect(page.locator('#audio-draft')).to_be_hidden();expect(page.locator('#audio-record')).to_be_disabled()
                    assert page.evaluate('__streams.every(s=>s.getTracks().every(t=>t.readyState==="ended"))')
                    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                    assert not external,external
                    assert all(status<400 for _,status in assets),assets
                    assert not errors,errors
                    context.close()
                    print(f'FV-UX-01 ESM HTTP, emoji, MediaRecorder, preview, exclusão, limpeza {width}px {theme}: PASS')
            # Negativas e autorização de supervisão.
            for scenario in ('denied','unsupported','pending','manager','pagehide','hidden','shop','actor','reset'):
                context=browser.new_context(permissions=['microphone'])
                context.add_init_script('''
                  window.__tracks=[];
                  const gum=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
                  navigator.mediaDevices.getUserMedia=async c=>{const s=await gum(c);__tracks.push(...s.getTracks());return s;};
                ''')
                page=context.new_page();page.set_default_timeout(7000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                if scenario=='denied':
                    page.add_init_script("navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('negada','NotAllowedError');}")
                elif scenario=='unsupported':
                    page.add_init_script('window.MediaRecorder=undefined;')
                elif scenario=='pending':
                    page.add_init_script("navigator.mediaDevices.getUserMedia=()=>new Promise(resolve=>{window.__resolve=()=>resolve({getTracks:()=>[{stop:()=>window.__stopped=true}]});});")
                page.goto(origin+('/?perfil=gestor' if scenario in ('manager','shop') else '/'))
                page.wait_for_selector('.conversation-card')
                if scenario=='manager':
                    page.get_by_role('button',name='Abrir conversa Cliente Exemplo 02',exact=False).click()
                    expect(page.locator('#audio-record')).to_be_disabled()
                    expect(page.locator('#composer-availability')).to_have_text('Envio indisponível no momento')
                    page.locator('#team-nav').click();expect(page.locator('#team-dialog')).to_be_visible()
                    for button,panel in [('members','list'),('monitor','monitor'),('batches','batches'),('queue','queue')]:
                        page.locator('#team-show-'+button).click();expect(page.locator('#team-'+panel)).to_be_visible()
                else:
                    if scenario=='shop':
                        page.get_by_role('button',name='Abrir conversa Cliente Exemplo 06',exact=False).click()
                    page.locator('#audio-record').click()
                    if scenario in ('denied','unsupported'):
                        expect(page.locator('#audio-draft')).to_have_attribute('data-phase','error')
                        assert ('negada' if scenario=='denied' else 'indisponível') in page.locator('#audio-status').inner_text()
                        assert page.locator('#audio-preview').get_attribute('src') is None
                    elif scenario=='pending':
                        expect(page.locator('#audio-status')).to_contain_text('Aguardando')
                        page.locator('#audio-delete').click();page.evaluate('__resolve()')
                        page.wait_for_function('window.__stopped===true')
                        expect(page.locator('#audio-draft')).to_be_hidden()
                    else:
                        expect(page.locator('#audio-status')).to_have_text('Gravando áudio')
                        if scenario=='pagehide':page.evaluate("window.dispatchEvent(new Event('pagehide'))")
                        elif scenario=='hidden':page.evaluate("Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))")
                        else:
                            if scenario=='shop':
                                page.locator('#list-extra').evaluate('e=>e.open=true')
                                page.locator('#shop-select').select_option('horizonte')
                            else:
                                page.locator('#demo-dialog').evaluate('e=>e.showModal()')
                                if scenario=='actor':page.locator('#actor-select').select_option('marina')
                                else:page.locator('#reset-app').click()
                                page.locator('#demo-dialog').evaluate('e=>e.close()')
                        expect(page.locator('#audio-draft')).to_be_hidden()
                        assert page.evaluate('__tracks.every(t=>t.readyState==="ended")')
                assert not errors,errors
                context.close();print(f'FV-UX-01 {scenario}: PASS')
            browser.close()
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)

if __name__=='__main__':
    main()
