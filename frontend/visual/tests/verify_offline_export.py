"""FV-UI-013. Offline snapshot verifier for GitHub branch ZIP (NOT a Git checkout).

Manifest is pinned to a GitHub commit; re-create when app/test sources change.
Runs Node/Chromium only after every required source blob SHA-1 matches.
This validates the synthetic frontend, NOT Supabase/S0 or production.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import stat
from zipfile import ZipFile, BadZipFile

MANIFEST = json.loads("{\"source_head\":\"7f6188957ef2fd05880e2f2499fc699af73d8e80\",\"source_branch\":\"fix/fv-coe-01-coerencia-20261031\",\"files\":{\"frontend/visual/README.md\":{\"sha\":\"4bf20aad7afc23f540fd3ee8eff9191a58e4fa67\",\"size\":41569},\"frontend/visual/app.mjs\":{\"sha\":\"1bcfa9481d557daa7c53f6e1ba7b88b01a506141\",\"size\":92221},\"frontend/visual/bank-view.mjs\":{\"sha\":\"87741e59204555f21c1a1ca6bab091f8bb76dfc8\",\"size\":4903},\"frontend/visual/batch-monitor.mjs\":{\"sha\":\"9ba7b1e0d1e6e141681059de33ef07adb7e99302\",\"size\":3882},\"frontend/visual/cf-op-02.mjs\":{\"sha\":\"28e99c8f4b021afb3f7c2dde3cdbccc6188c0f9b\",\"size\":18233},\"frontend/visual/communication-composer.mjs\":{\"sha\":\"4a84bf1d2966fedf5d09e089f4f048bb2cb3253f\",\"size\":7785},\"frontend/visual/conversation-attention.mjs\":{\"sha\":\"0b19e9a8f4d372549656438eb8e17cc5e79d27da\",\"size\":5979},\"frontend/visual/distribution-view.mjs\":{\"sha\":\"793ffdd6a412419265df1b32cccc0d018e68148b\",\"size\":4872},\"frontend/visual/fixtures.mjs\":{\"sha\":\"23d5a9a1ffe8e9eee4f47c4505c3790eccbf0997\",\"size\":9684},\"frontend/visual/human-cycle-view.mjs\":{\"sha\":\"d9ebf146079547801bee3bb49ac47842e8363336\",\"size\":6548},\"frontend/visual/index.html\":{\"sha\":\"af5d26312292e38e0eb29331ac934c4ab6bdefe5\",\"size\":20622},\"frontend/visual/integration-gate-view.mjs\":{\"sha\":\"3515816bc6ea974178bb8c2474f7b46ddf4320ec\",\"size\":3023},\"frontend/visual/local-audio.mjs\":{\"sha\":\"642f4aaec24ee62dec953258936c8b2c1528ef6d\",\"size\":6702},\"frontend/visual/operation-feedback.mjs\":{\"sha\":\"1c997c303576366be501f9f43fdfa7f67400ba8e\",\"size\":3159},\"frontend/visual/postmark-view.mjs\":{\"sha\":\"be483aad2807ef1fce16ea41e6854e519aaf4d66\",\"size\":5778},\"frontend/visual/registration-view.mjs\":{\"sha\":\"da8f41bcd1584f7c14b1b04382491fe8e561353b\",\"size\":4638},\"frontend/visual/relationship-view.mjs\":{\"sha\":\"5495bb1828c006f7f6d1706039a976d15fff70f2\",\"size\":9376},\"frontend/visual/revision-fixtures.mjs\":{\"sha\":\"64ddddf69cab125538307757386e861758e20999\",\"size\":6256},\"frontend/visual/s0-command-result.mjs\":{\"sha\":\"044cfb95fee6eb8916dadf7de6f77aecdd3d2471\",\"size\":3543},\"frontend/visual/s0-read-contract.mjs\":{\"sha\":\"f764c045326c1740ed702fe7bcfe45b2f58f8267\",\"size\":2857},\"frontend/visual/styles.css\":{\"sha\":\"fdf896bd2c6a8a3f31908873c20670b4ac427834\",\"size\":68510},\"frontend/visual/team-monitor.mjs\":{\"sha\":\"1ebc701d2fbc245c0d39db8df50c8d041f5faf45\",\"size\":3377},\"frontend/visual/team-monitoring.mjs\":{\"sha\":\"481181ddbb3f26eebb55b9b93a7b92514068b013\",\"size\":4370},\"frontend/visual/team-operations.mjs\":{\"sha\":\"a497207a97633a99cc77f3fa57d4d74c1b7bc9bd\",\"size\":2236},\"frontend/visual/team-pause-preview.mjs\":{\"sha\":\"1612c54e75e16431b337cbebeebb37432a74a065\",\"size\":4907},\"frontend/visual/tests/acceptance-matrix.json\":{\"sha\":\"db8f50e15195a05beac92114f805f621600c0e37\",\"size\":3363},\"frontend/visual/tests/acceptance-matrix.test.mjs\":{\"sha\":\"6f2a5599be1c5cd29653a79b7434b720d20deb50\",\"size\":1622},\"frontend/visual/tests/app.dom.test.mjs\":{\"sha\":\"0d3e08a426cd77623d5df918a0915b9160ed705e\",\"size\":63490},\"frontend/visual/tests/app.mobile.dom.test.mjs\":{\"sha\":\"780038f493548bf4d59f3239f08f1d5c71d86eb1\",\"size\":10511},\"frontend/visual/tests/app.tablet.dom.test.mjs\":{\"sha\":\"455a5a3758e75ae069196ecd959b61a25f4d5365\",\"size\":2064},\"frontend/visual/tests/attention-integration.test.mjs\":{\"sha\":\"51518b8e41855c0a8d138d736d1d3d7902d43379\",\"size\":3792},\"frontend/visual/tests/bank-view.test.mjs\":{\"sha\":\"6570aa00d75270ced8ee63db2f7f30f49a1a4c97\",\"size\":5192},\"frontend/visual/tests/batch-monitor.test.mjs\":{\"sha\":\"ca61ff3031662fcfdb7f07fafd9a251b131ee358\",\"size\":3895},\"frontend/visual/tests/browser.communication.py\":{\"sha\":\"58ca7d6a5cebff1f695e07746c7791ee252d1dae\",\"size\":14394},\"frontend/visual/tests/browser.corrections.py\":{\"sha\":\"bcf77548dd823942c03da68bcc5d75d3720aa0d2\",\"size\":16356},\"frontend/visual/tests/browser.modules.py\":{\"sha\":\"2ccdffab72589fac887f02b87d3ea89fb1f37829\",\"size\":16069},\"frontend/visual/tests/browser.revision.py\":{\"sha\":\"fded04cf9f524ed2798cc98faa77d0bbbd65539b\",\"size\":15672},\"frontend/visual/tests/browser.smoke.py\":{\"sha\":\"a21924894412e37d772674db6b8533e6c80ca695\",\"size\":119914},\"frontend/visual/tests/cf-op-02.test.mjs\":{\"sha\":\"f39ce909e01d568f6644b2e804de4f472c31068f\",\"size\":11206},\"frontend/visual/tests/communication-composer.test.mjs\":{\"sha\":\"6fbca36f35b2e377fe7f21a5ef3f3f2273f87fdf\",\"size\":2249},\"frontend/visual/tests/conversation-attention.test.mjs\":{\"sha\":\"2528d95dc02dba53b7b88fa5ee7a4a6834e6de7d\",\"size\":6679},\"frontend/visual/tests/distribution-view.test.mjs\":{\"sha\":\"b56d24082161d2e4a44cb6893af1d95c8e81aa87\",\"size\":6473},\"frontend/visual/tests/dom-fixture.mjs\":{\"sha\":\"d714b066703ca693273e00c566dd2d75a0e49060\",\"size\":8718},\"frontend/visual/tests/fixtures.test.mjs\":{\"sha\":\"9547b1dfd1cf9107a897eb85f3d4cecddc3d900d\",\"size\":4550},\"frontend/visual/tests/human-cycle-view.test.mjs\":{\"sha\":\"e5a324284b0b9815e830c516064d8c070f6be0af\",\"size\":6430},\"frontend/visual/tests/integration-gate-view.test.mjs\":{\"sha\":\"4fc9d631b4c5f5b02ef62074bb5f29cb2dc9aac3\",\"size\":5363},\"frontend/visual/tests/local-audio.test.mjs\":{\"sha\":\"42864c8d1fd7f8f3819637f63ea03c71ea7a7f35\",\"size\":7153},\"frontend/visual/tests/modules.dom.test.mjs\":{\"sha\":\"48fb07642ca3f9ea5ee840588edfdf4ca29fc65f\",\"size\":6116},\"frontend/visual/tests/offline-export-manifest.test.mjs\":{\"sha\":\"a23eeacec97a0223465a5d6e764af5698564ad1b\",\"size\":4012},\"frontend/visual/tests/operation-feedback.test.mjs\":{\"sha\":\"6610eb89aa8680a30bf8c9490cb2497674cf9bca\",\"size\":2438},\"frontend/visual/tests/postmark-view.test.mjs\":{\"sha\":\"0e30c18de7b7dfcfd877d36af588dd63ad0503ac\",\"size\":7318},\"frontend/visual/tests/registration-view.test.mjs\":{\"sha\":\"7ef6143fe0f4b07dca507ec2473beeac55c73add\",\"size\":5917},\"frontend/visual/tests/relationship-view.test.mjs\":{\"sha\":\"e6af7e85bfd5c337974a8409961a86193b26a8d3\",\"size\":12670},\"frontend/visual/tests/revision-conversations.test.mjs\":{\"sha\":\"04be14fb6c3ba2abf977364e70721b8edc0fdf6f\",\"size\":11816},\"frontend/visual/tests/run_acceptance.py\":{\"sha\":\"8f3b0a255af3ce807822e5673823fa419e88a76f\",\"size\":16961},\"frontend/visual/tests/run_validation_layers.mjs\":{\"sha\":\"91cc5157c635368a6953272b1127d4697a34c52a\",\"size\":2466},\"frontend/visual/tests/s0-command-result.test.mjs\":{\"sha\":\"26a5e349af91ac6ece3871db31a2abad0f68a9d8\",\"size\":5177},\"frontend/visual/tests/s0-read-contract.test.mjs\":{\"sha\":\"394841eed32bed7f2f63756a7900094e2530a44a\",\"size\":4310},\"frontend/visual/tests/source-contract.test.mjs\":{\"sha\":\"8e2ee65e11ae6deb8a0783844e9cd907a6fac838\",\"size\":40773},\"frontend/visual/tests/source-module-graph.test.mjs\":{\"sha\":\"a1c627841aaca0db7addc570f56fce7f875fe7f6\",\"size\":5129},\"frontend/visual/tests/team-monitor.test.mjs\":{\"sha\":\"e231c9513d6e78a9ae5877e023cb6b09f6171829\",\"size\":6255},\"frontend/visual/tests/team-monitoring.test.mjs\":{\"sha\":\"375fc901abbd586a2346546993cd54f9e553422c\",\"size\":6245},\"frontend/visual/tests/team-operations.test.mjs\":{\"sha\":\"c4e72a12e2dd1de10d5a2f56b51d43aeb4f86904\",\"size\":4413},\"frontend/visual/tests/team-pause-preview.test.mjs\":{\"sha\":\"762b2c76b06994238da636c95cc93a83dfed4d72\",\"size\":5059},\"frontend/visual/tests/test_offline_export.py\":{\"sha\":\"677fb3c1dfe1fdeb60772986c1d486add9c9e118\",\"size\":14810},\"frontend/visual/tests/transport-state-view.test.mjs\":{\"sha\":\"7bf46954a513e1d251fdd61bfbf30da97aa1f5c5\",\"size\":5705},\"frontend/visual/tests/validation-layers.json\":{\"sha\":\"8d225d0eb45e325eb4e90c3ddf67ab2f59a8feff\",\"size\":2209},\"frontend/visual/tests/validation-layers.test.mjs\":{\"sha\":\"802fe7d22de902305bda3f69dfcdb7a118d6908e\",\"size\":2670},\"frontend/visual/tests/view-model.test.mjs\":{\"sha\":\"8292adee20ed8bcc28dfaa0ca8aaf7a0985581ff\",\"size\":4044},\"frontend/visual/transport-state-view.mjs\":{\"sha\":\"4e3ba3064db9c0d3a52e5a9a47342bf7910173e2\",\"size\":3968},\"frontend/visual/view-model.mjs\":{\"sha\":\"3ac47b5528ae70b210c436cbd7d95b4bc85bce65\",\"size\":4283}}}")

def blob_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()

def load_verified(archive):
    required = MANIFEST["files"]
    data = {}
    with ZipFile(archive) as z:
        entries = z.infolist()
        if len(entries)>3000:
            raise ValueError("ZIP inventory exceeds offline verifier limit")
        names = [item.filename for item in entries if not item.is_dir()]
        if len(names)!=len(set(names)):
            raise ValueError("Duplicate file entries in ZIP")
        # Evita descompressão acumulada de centenas de entradas pequenas.
        if sum(item.file_size for item in entries if not item.is_dir() and
               "frontend/visual/" in item.filename) > 25_000_000:
            raise ValueError("ZIP frontend uncompressed budget exceeded")
        for item in entries:
            mode=item.external_attr>>16
            if stat.S_ISLNK(mode):
                raise ValueError("Symbolic links are not allowed in ZIP")
            if item.file_size>25_000_000:
                raise ValueError("ZIP member too large: "+item.filename)
        prefixes = {name.partition("frontend/visual/")[0] for name in names
                    if "frontend/visual/" in name}
        if len(prefixes) != 1:
            raise ValueError("ZIP must contain exactly one frontend/visual root")
        prefix = prefixes.pop()
        for name in names:
            if name.startswith("/") or ".." in PurePosixPath(name).parts or "\\" in name:
                raise ValueError("Unsafe path in ZIP: "+name)
        # Não aceitar código/testes extras invisíveis ao manifesto pinado.
        verifier="frontend/visual/tests/verify_offline_export.py"
        expected_paths=set(required)|{verifier}
        exported_paths={name[len(prefix):] for name in names
                        if name.startswith(prefix+"frontend/visual/")}
        if exported_paths!=expected_paths:
            raise ValueError("Unpinned or missing frontend/visual file in ZIP")
        verifier_path=prefix+verifier
        archived_verifier=z.read(verifier_path)
        if archived_verifier!=Path(__file__).read_bytes():
            raise ValueError("Offline verifier differs from the ZIP version")
        for rel, info in required.items():
            path=prefix+rel
            if names.count(path)!=1:
                raise ValueError("Missing or duplicated file: "+rel)
            raw=z.read(path)
            if len(raw)!=info["size"] or blob_sha(raw)!=info["sha"]:
                raise ValueError("Git blob hash mismatch: "+rel)
            data[rel]=raw
        # Cópia já comparada byte a byte: necessária ao teste Node do manifesto,
        # mas excluída do hash-pinning para evitar autodependência circular.
        data[verifier]=archived_verifier
    return data

def execute(cmd,cwd):
    try:
        r=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,check=False,timeout=180)
        return {"executed":True,"passed":r.returncode==0,"exit_code":r.returncode,
                "stdout":r.stdout[-15000:],"stderr":r.stderr[-4000:]}
    except (OSError,subprocess.TimeoutExpired) as e:
        return {"executed":False,"passed":False,"error":str(e)}

def main():
    p=argparse.ArgumentParser(description="Check GitHub ZIP bytes against pinned Git blobs")
    p.add_argument("--archive",type=Path,required=True)
    p.add_argument("--run-native",action="store_true",help="Node and Chromium on verified snapshot")
    p.add_argument("--json-report",type=Path)
    a=p.parse_args()
    report={"kind":"FV-UI-013-verified-ZIP-diagnostic",
            "source_head":MANIFEST["source_head"],"source_branch":MANIFEST["source_branch"],
            "snapshot_verified":False,"git_checkout_verified":False,
            "full_acceptance":False,"runs":{}}
    try:
        files=load_verified(a.archive)
        report["snapshot_verified"]=True
        report["verified_blob_count"]=len(files)-1
        report["verifier_matched_archive"]=True
        report["extra_files_accepted"]=False
        print("Verified",len(files)-1,"GitHub source blobs against",MANIFEST["source_head"])
        if a.run_native:
            with tempfile.TemporaryDirectory(prefix="fv-ui-013-export-") as tmp:
                root=Path(tmp)
                for name,raw in files.items():
                    dest=root/name
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    dest.write_bytes(raw)
                visual=root/"frontend"/"visual"
                tests=sorted(str(f) for f in (visual/"tests").glob("*.test.mjs"))
                security=execute(
                    [sys.executable,"-B","-m","unittest","discover",
                     "-s",str(visual/"tests"),"-p","test_offline_export.py"],
                    visual)
                report["runs"]["zip_security_python"]=security
                if security["executed"] and security["passed"]:
                    node_step=execute(["node","--test",*tests],visual)
                    report["runs"]["node"]=node_step
                    if node_step["executed"] and node_step["passed"]:
                        report["runs"]["chromium"]=execute(
                            [sys.executable,str(visual/"tests"/"browser.smoke.py")],
                            visual)
                    else:
                        report["runs"]["chromium"]={
                            "executed":False,"passed":False,
                            "error":"blocked by Node ESM regression"
                        }
                else:
                    # Não iniciar código JS/browser depois de falha na prova
                    # adversarial do próprio verificador.
                    for gate in ("node","chromium"):
                        report["runs"][gate]={
                            "executed":False,"passed":False,
                            "error":"blocked by ZIP verifier security regression"
                        }
                report["native_snapshot_pass"]=all(
                    report["runs"][gate]["executed"] and report["runs"][gate]["passed"]
                    for gate in ("zip_security_python","node","chromium"))
                print("Native verified-ZIP diagnostic:",
                      "PASS" if report["native_snapshot_pass"] else "FAIL")
        else:
            print("Integrity PASS; native tests not run.")
    except (OSError,ValueError,KeyError,BadZipFile) as error:
        report["error"]=str(error)
        print("Integrity FAIL:",error,file=sys.stderr)
    if a.json_report:
        a.json_report.parent.mkdir(parents=True,exist_ok=True)
        a.json_report.write_text(json.dumps(report,ensure_ascii=False,indent=2),
                                 encoding="utf-8")
    return 0 if report["snapshot_verified"] and (
        not a.run_native or report.get("native_snapshot_pass",False)) else 1

if __name__=="__main__":
    sys.exit(main())
