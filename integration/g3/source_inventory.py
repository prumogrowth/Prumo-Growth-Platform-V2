"""Traceable lexical index of pinned Git objects, NOT an authorization proof.

The effective SQL catalog is produced separately by run_local.py. This index
includes fixtures, test helpers and references; a match is never a deployed
table, route, bucket, grant or consumer certification.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[2]
REFS={
 'main':'dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a',
 's0-foundation':'75095fe9b6050c704df37c663bb92595bc6513b6',
 's0-pr4':'060b472b03e9e7b89f5b3d7e19b72b98836f106d',
 's1-i75c':'e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe',
 's0-pr9':'ff623482fca0eb1857a64b51959e3716bc0216d7',
 'ui-pr11':'ddec1b80444bfde871d43a02d0ee94b9ed7cde11',
 'meta-pr7':'450dcd645f35d4c8bf93e974e75d3b09467965a7',
 'meta-pr8':'cb7fc3e2eacdaad9b8d47ffca1284759ca3357a3',
 'f03-pr1':'a7ba0136ae7c7907cc5b7f9ad0ee6b6ae499125e',
 'frontend':'e44a14dbc89e8c443bed08ea06c20a1f16f4ac12',
 's2':'ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c',
}
TABLE=re.compile(r'^\s*create\s+(?:unlogged\s+)?table\s+(?:if\s+not\s+exists\s+)?([a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*)',re.I|re.M)
WATCH=re.compile(r'\b(?:leads_loja|ciclos_comerciais|casos_humanos|atribuicoes_humanas|conversas|mensagens|itens_lote|reencontros_lote|eventos_status_comercial|canais_loja|lotes_importacao|cfi01_f03_\w+)\b')
MEDIA=re.compile(r'storage\.(?:objects|buckets|from)|createSignedUrl|create_signed_url|signed.?url|download|media_attestation|message_modalities|form_fields_local|\b(?:D2|D3|D4)\b',re.I)


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out={'scope':'lexical tracked files only; no production discovery; comments and tests may match','snapshots':{}}
    for label,ref in REFS.items():
        files=[];declarations=[];references=[];media=[]
        with tarfile.open(fileobj=io.BytesIO(git('archive',ref))) as archive:
            for member in archive.getmembers():
                if not member.isfile():continue
                data=archive.extractfile(member).read();path=member.name
                files.append({'path':path,'git_blob':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),
                              'sha256':hashlib.sha256(data).hexdigest()})
                if not path.endswith(('.sql','.py','.mjs','.js','.ts','.toml')):continue
                text=data.decode('utf-8')
                if path.endswith('.sql'):
                    declarations.extend({'object':m[1],'path':path,'line':text[:m.start()].count('\n')+1,
                                         'stage':'migration-source' if '/migrations/' in path else 'isolated-fixture'} for m in TABLE.finditer(text))
                for line_no,line in enumerate(text.splitlines(),1):
                    hits=sorted(set(WATCH.findall(line)))
                    if hits:references.append({'path':path,'line':line_no,'objects':hits,'excerpt':line.strip()[:220]})
                    if MEDIA.search(line):media.append({'path':path,'line':line_no,'excerpt':line.strip()[:220]})
        out['snapshots'][label]={'sha':ref,'tree':git('rev-parse',ref+'^{tree}').decode().strip(),
          'file_count':len(files),'files':files,'table_declarations':declarations,
          'lexical_references':references,'media_data_mentions':media}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print({k:{'files':v['file_count'],'table_declarations':len(v['table_declarations'])} for k,v in out['snapshots'].items()})


if __name__=='__main__':main()
