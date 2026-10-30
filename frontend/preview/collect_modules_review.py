"""FV-REV-01/2: capturas do runtime integral, somente após gate certificado.
Nenhum deploy, dados reais, contrato externo ou efeito operacional.
"""
import argparse
import hashlib
import json
import os
import subprocess
from html import escape
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from collect_visual_review import local_preview_server


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[2]
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip()
    captures=[]
    with local_preview_server() as origin, sync_playwright() as p:
        options={'headless':True,'args':['--no-sandbox']}
        exe=os.getenv('CHROMIUM_EXECUTABLE') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').is_file() else None)
        if exe:options['executable_path']=exe
        browser=p.chromium.launch(**options)
        for width,height in ((1440,900),(900,780),(390,844)):
            for actor in ('rafael','marina'):
                for theme in ('light','dark'):
                    scenes=['resumo-ias','historico','notas','banco-ficha','banco-versoes','banco-remessa','continuidade','recontatos-realizados','recontatos']
                    if actor=='marina':scenes+=['gestao-equipe','gestao-monitoramento','gestao-lotes','gestao-fila']
                    for scene in scenes:
                        page=browser.new_page(viewport={'width':width,'height':height},color_scheme=theme)
                        page.set_default_timeout(7000);errors=[];external=[]
                        page.on('pageerror',lambda e:errors.append(str(e)))
                        def route(r):
                            if r.request.url.startswith(origin+'/'):r.continue_()
                            else:external.append(r.request.url);r.abort()
                        page.route('**/*',route)
                        page.goto(origin+('/?perfil=gestor' if actor=='marina' else '/'))
                        expect(page.locator('.conversation-card')).to_have_count(15 if actor=='marina' else 11)
                        if scene.startswith('gestao'):
                            page.locator('#team-nav-mobile' if width<=760 else '#team-nav').click()
                            panel={'gestao-equipe':'members','gestao-monitoramento':'monitor','gestao-lotes':'batches','gestao-fila':'queue'}[scene]
                            page.locator('#team-show-'+panel).click()
                            expect(page.locator('#team-dialog')).to_be_visible()
                        elif scene.startswith('banco'):
                            page.locator('#bank-nav-mobile' if width<=760 else '#bank-nav').click()
                            page.locator('#bank-case-select').select_option('A-114' if scene in ('banco-ficha','banco-versoes') else 'A-105')
                            expect(page.locator('#bank-dialog')).to_be_visible()
                            assert page.locator('#bank-content input,#bank-content textarea').count()==0
                        else:
                            number={'resumo-ias':'09','historico':'09','notas':'02','continuidade':'05','recontatos':'11','recontatos-realizados':'11'}[scene]
                            page.get_by_role('button',name='Abrir conversa Cliente Exemplo '+number,exact=False).click()
                            page.locator('#thread-title').click()
                            expect(page.locator('.detail-tab')).to_have_count(3)
                            tab='overview' if scene=='resumo-ias' else 'notes' if scene=='notas' else 'activity'
                            page.locator('#case-tab-'+tab).click()
                            if scene=='resumo-ias':
                                for summary in page.locator('.ai-communication summary').all():summary.click()
                            if scene=='notas' and actor=='rafael':page.locator('#note-text').fill('Rascunho interno não submetido')
                            if scene=='recontatos':
                                expect(page.locator('#future-attempts .activity-item')).to_have_count(3)
                                assert page.locator('#future-attempts [data-state=cancelled]').count()==0
                        assert not errors and not external,(errors,external)
                        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                        # Capture the top of the independently scrollable surface, with a second
                        # scroll position for recontact planning so future and past are both reviewable.
                        if scene=='recontatos':page.locator('#future-attempts').scroll_into_view_if_needed()
                        if scene=='banco-versoes' and actor=='rafael':page.locator('#bank-content .detail-label').filter(has_text='FICHA VIVA POR').scroll_into_view_if_needed()
                        name=f'{width}x{height}-{actor}-{theme}-{scene}.png'
                        page.screenshot(path=str(output/name),full_page=True,animations='disabled')
                        captures.append({'file':name,'width':width,'height':height,'role':actor,'theme':theme,'scene':scene,
                            'head':head,'sha256':hashlib.sha256((output/name).read_bytes()).hexdigest()})
                        page.close()
        browser.close()
    index={'head':head,'branch':branch,'base':'17336799ddf4c8575c790f09eb64570d6460733c',
        'synthetic_only':True,'published':False,'captures':captures}
    (output/'INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    figures=''.join('<figure><a href="'+escape(c['file'])+'"><img loading="lazy" src="'+escape(c['file'])+'" alt="'+escape(c['scene'])+'"></a><figcaption>'+escape(c['file'])+'</figcaption></figure>' for c in captures)
    (output/'INDEX.html').write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Prumo · Etapa 2</title><style>body{font:16px system-ui;background:#eee;color:#222;margin:24px}main{display:flex;flex-wrap:wrap;gap:20px}figure{margin:0;max-width:420px}img{max-width:100%;max-height:600px}figcaption{font-size:12px;margin:8px 0;overflow-wrap:anywhere}</style><h1>FV-REV-01 · Etapa 2</h1><p>Dados fictícios. Commit '+head+'</p><main>'+figures+'</main></html>')
    print(f'FV-REV-01/2 screenshots: PASS ({len(captures)}); HEAD {head}',flush=True)
    return len(captures)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    main(parser.parse_args().output)
