"""Package metadata evidence without business rows; gzip is deterministic."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import shutil


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--sources',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    for f in sorted(a.input.glob('*-catalog.json')):
        (a.output/(f.name+'.gz')).write_bytes(gzip.compress(f.read_bytes(),mtime=0))
    (a.output/'source-inventory.json.gz').write_bytes(gzip.compress(a.sources.read_bytes(),mtime=0))
    shutil.copyfile(a.input/'execution.json',a.output/'execution.json')
    for f in a.input.glob('*-negative.log'):shutil.copyfile(f,a.output/(f.stem+'.txt'))
    with (a.output/'columns.csv').open('w',newline='') as out:
        writer=csv.writer(out,lineterminator='\n')
        writer.writerow(['profile','schema','table','column','type','not_null','owner','rls','force_rls',
                         'anon_select','authenticated_select','authenticated_insert','authenticated_update','column_acl'])
        for f in sorted(a.input.glob('*-catalog.json')):
            d=json.loads(f.read_text())
            for r in d['relations']:
                for c in r['columns'] or []:
                    auth=c['privileges']['authenticated']
                    writer.writerow([f.name.removesuffix('-catalog.json'),r['schema'],r['name'],c['name'],c['type'],c['not_null'],
                        r['owner'],r['rls'],r['force_rls'],c['privileges']['anon']['select'],auth['select'],auth['insert'],auth['update'],c['acl']])
    manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(a.output.iterdir()) if f.name!='SHA256.json'}
    (a.output/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(manifest)


if __name__=='__main__':main()
