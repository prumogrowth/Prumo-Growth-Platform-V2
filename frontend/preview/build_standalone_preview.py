"""Cópia integral do runtime pinado em um HTML local. Não publica nem integra serviços.
A concatenação é a mesma exercitada pelo smoke Chromium existente.
"""
import argparse
from pathlib import Path
from build_preview import collect_assets
from collect_visual_review import offline_page_source


def build(output):
    assets, manifest = collect_assets()  # Falha se houver bytes fora do manifesto.
    html, script = offline_page_source()
    html = html.replace('<head>', '<head>\n<!-- Prumo: '+manifest['source_branch']+' @ '+manifest['source_head']+'; synthetic local preview, no deploy. -->')
    # Impede encerramento do elemento script por literais de texto no código-fonte.
    script = script.replace('</script', '<\\/script')
    html = html.replace('</body>', '<script>\n'+script+'\n</script></body>')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html,encoding='utf-8')
    print(f'Prévia integral local: {output}; fonte {manifest["source_head"]}; {len(assets)} assets incorporados, sem deploy')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    build(parser.parse_args().output)
