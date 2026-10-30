"""FV-REV-01 Etapa 1: source runtime screenshots, no deploy or external endpoints."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
from html import escape
from playwright.sync_api import sync_playwright, expect
from collect_visual_review import local_preview_server


def main(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    repo=Path(__file__).resolve().parents[2]
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=repo,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain','--','frontend/visual','frontend/preview'],cwd=repo,text=True).strip():
        raise ValueError('Capture requires clean committed runtime and preview tools')
    captures=[]
    with local_preview_server() as origin,sync_playwright() as p:
        options={'headless':True,'args':['--no-sandbox']}
        exe=os.getenv('CHROMIUM_EXECUTABLE') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').is_file() else None)
        if exe:options['executable_path']=exe
        browser=p.chromium.launch(**options)
        for width,height in ((1440,900),(900,780),(390,844)):
            for theme in ('light','dark'):
                for role in ('consultor','gestor'):
                    for scene in ('lista','filtros','conversa','composicao','janela-expirada','vendido','perdido','painel-aberto','painel-fechado'):
                        page=browser.new_page(viewport={'width':width,'height':height},color_scheme=theme)
                        page.set_default_timeout(7000)
                        errors=[];external=[]
                        page.on('pageerror',lambda e:errors.append(str(e)))
                        def route(r):
                            if r.request.url.startswith(origin+'/'):r.continue_()
                            else:external.append(r.request.url);r.abort()
                        page.route('**/*',route)
                        page.goto(origin+'/?perfil='+role)
                        expect(page.locator('.conversation-card')).to_have_count(11 if role=='consultor' else 15)
                        if scene=='filtros':page.locator('#list-extra summary').click()
                        elif scene!='lista':
                            number={'janela-expirada':'08','vendido':'16','perdido':'12'}.get(scene,'02' if role=='consultor' else '06')
                            page.get_by_role('button',name='Abrir conversa Cliente Exemplo '+number,exact=False).click()
                            if scene=='composicao':
                                page.locator('#message-input').fill('Podemos conversar sobre as próximas etapas? ')
                                page.locator('#emoji-toggle').click()
                            elif scene in ('painel-aberto','painel-fechado'):
                                page.locator('#thread-title').click()
                                page.locator('#case-tab-notes').click()
                                page.locator('#note-text').fill('Rascunho interno não submetido')
                                if scene=='painel-fechado':page.locator('#detail-close').click()
                        if errors or external:raise AssertionError({'errors':errors,'external':external})
                        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
                        name=f'{width}x{height}-{role}-{theme}-{scene}.png'
                        page.screenshot(path=str(output/name),full_page=True,animations='disabled')
                        captures.append({'file':name,'width':width,'height':height,'role':role,'theme':theme,'scene':scene,
                                         'sha256':hashlib.sha256((output/name).read_bytes()).hexdigest()})
                        page.close()
        browser.close()
    index={'head':head,'branch':branch,'base':'2926d349e32c979dda68182b56bfd50ac6cf6212','synthetic_only':True,'published':False,'captures':captures}
    (output/'INDEX.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
    figures=''.join('<figure><a href="'+escape(c['file'])+'"><img loading="lazy" src="'+escape(c['file'])+'" alt="'+escape(c['scene'])+'"></a><figcaption>'+escape(c['file'])+'</figcaption></figure>' for c in captures)
    (output/'INDEX.html').write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Prumo · FV-REV-01 Etapa 1</title><style>body{font:16px system-ui;margin:24px;background:#eee;color:#222}main{display:flex;flex-wrap:wrap;gap:20px}figure{margin:0;max-width:420px}img{max-width:100%;max-height:600px}figcaption{font-size:12px;margin:8px 0;overflow-wrap:anywhere}</style><h1>FV-REV-01 · Etapa 1</h1><p>Dados sintéticos · sem publicação. Commit '+head+'</p><main>'+figures+'</main></html>')
    print(f'FV-REV-01 screenshots: PASS ({len(captures)}); HEAD {head}',flush=True)
    return len(captures)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    main(parser.parse_args().output)
