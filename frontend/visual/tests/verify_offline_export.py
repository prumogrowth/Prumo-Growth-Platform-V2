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

MANIFEST = json.loads("{\"source_head\":\"edb85ab28f8f5201c2731649fd296d3ea278f352\",\"source_branch\":\"feat/frontend-plataforma-visual\",\"files\":{\"frontend/visual/app.mjs\":{\"sha\":\"9525299a0e7cc2394565579ce5734491c5c18431\",\"size\":78842},\"frontend/visual/bank-view.mjs\":{\"sha\":\"fbd482cea1ca748093406554bb83a5515bfb6a87\",\"size\":4156},\"frontend/visual/batch-monitor.mjs\":{\"sha\":\"9ba7b1e0d1e6e141681059de33ef07adb7e99302\",\"size\":3882},\"frontend/visual/cf-op-02.mjs\":{\"sha\":\"28e99c8f4b021afb3f7c2dde3cdbccc6188c0f9b\",\"size\":18233},\"frontend/visual/conversation-attention.mjs\":{\"sha\":\"de26aa325fc05818447ce9475c4b5446ee2a4e01\",\"size\":2709},\"frontend/visual/distribution-view.mjs\":{\"sha\":\"793ffdd6a412419265df1b32cccc0d018e68148b\",\"size\":4872},\"frontend/visual/fixtures.mjs\":{\"sha\":\"23d5a9a1ffe8e9eee4f47c4505c3790eccbf0997\",\"size\":9684},\"frontend/visual/human-cycle-view.mjs\":{\"sha\":\"d9ebf146079547801bee3bb49ac47842e8363336\",\"size\":6548},\"frontend/visual/index.html\":{\"sha\":\"41b4b191ebed8d1934ead5c87278af0f1051f716\",\"size\":15478},\"frontend/visual/integration-gate-view.mjs\":{\"sha\":\"3515816bc6ea974178bb8c2474f7b46ddf4320ec\",\"size\":3023},\"frontend/visual/operation-feedback.mjs\":{\"sha\":\"1c997c303576366be501f9f43fdfa7f67400ba8e\",\"size\":3159},\"frontend/visual/postmark-view.mjs\":{\"sha\":\"9479e521aba815dc3537ed84c5ba929c23d4d786\",\"size\":5606},\"frontend/visual/README.md\":{\"sha\":\"712601990065ca0b065a819df75611a8d1c504a6\",\"size\":37844},\"frontend/visual/registration-view.mjs\":{\"sha\":\"da8f41bcd1584f7c14b1b04382491fe8e561353b\",\"size\":4638},\"frontend/visual/s0-command-result.mjs\":{\"sha\":\"044cfb95fee6eb8916dadf7de6f77aecdd3d2471\",\"size\":3543},\"frontend/visual/s0-read-contract.mjs\":{\"sha\":\"f764c045326c1740ed702fe7bcfe45b2f58f8267\",\"size\":2857},\"frontend/visual/styles.css\":{\"sha\":\"0f79cf4628caa970b116e6b73c51c0fabff6e8f8\",\"size\":48372},\"frontend/visual/team-monitor.mjs\":{\"sha\":\"1ebc701d2fbc245c0d39db8df50c8d041f5faf45\",\"size\":3377},\"frontend/visual/team-monitoring.mjs\":{\"sha\":\"ff013eb8f6c020715f5166257913c49dd6d6a90b\",\"size\":4236},\"frontend/visual/team-operations.mjs\":{\"sha\":\"a497207a97633a99cc77f3fa57d4d74c1b7bc9bd\",\"size\":2236},\"frontend/visual/team-pause-preview.mjs\":{\"sha\":\"1612c54e75e16431b337cbebeebb37432a74a065\",\"size\":4907},\"frontend/visual/tests/acceptance-matrix.json\":{\"sha\":\"15c550cd456286904c09ac84abe35a3726f28d56\",\"size\":3245},\"frontend/visual/tests/acceptance-matrix.test.mjs\":{\"sha\":\"6f2a5599be1c5cd29653a79b7434b720d20deb50\",\"size\":1622},\"frontend/visual/tests/app.dom.test.mjs\":{\"sha\":\"0db70e84632111f00f48ee4d4ca5b8cf26a1e6df\",\"size\":50556},\"frontend/visual/tests/app.mobile.dom.test.mjs\":{\"sha\":\"371778852c472fefa4ba58de6feb636edfeac935\",\"size\":10376},\"frontend/visual/tests/app.tablet.dom.test.mjs\":{\"sha\":\"69be75b16e37dcbe212180b58c76d3d992541267\",\"size\":2070},\"frontend/visual/tests/attention-integration.test.mjs\":{\"sha\":\"51518b8e41855c0a8d138d736d1d3d7902d43379\",\"size\":3792},\"frontend/visual/tests/bank-view.test.mjs\":{\"sha\":\"d9ee25e929674326adeae3db6d7ac868e4e13106\",\"size\":4626},\"frontend/visual/tests/batch-monitor.test.mjs\":{\"sha\":\"ca61ff3031662fcfdb7f07fafd9a251b131ee358\",\"size\":3895},\"frontend/visual/tests/browser.smoke.py\":{\"sha\":\"648ab6f6a8afcbc79ee208af223cd0fd8f170d15\",\"size\":91032},\"frontend/visual/tests/cf-op-02.test.mjs\":{\"sha\":\"f39ce909e01d568f6644b2e804de4f472c31068f\",\"size\":11206},\"frontend/visual/tests/conversation-attention.test.mjs\":{\"sha\":\"ff13cbe4e35400af9f441fe8c2fe5a6be4e56a0c\",\"size\":2712},\"frontend/visual/tests/distribution-view.test.mjs\":{\"sha\":\"b56d24082161d2e4a44cb6893af1d95c8e81aa87\",\"size\":6473},\"frontend/visual/tests/dom-fixture.mjs\":{\"sha\":\"00917a398123d228d566927382a9b8a8bad85a25\",\"size\":7287},\"frontend/visual/tests/fixtures.test.mjs\":{\"sha\":\"9547b1dfd1cf9107a897eb85f3d4cecddc3d900d\",\"size\":4550},\"frontend/visual/tests/human-cycle-view.test.mjs\":{\"sha\":\"e5a324284b0b9815e830c516064d8c070f6be0af\",\"size\":6430},\"frontend/visual/tests/integration-gate-view.test.mjs\":{\"sha\":\"4fc9d631b4c5f5b02ef62074bb5f29cb2dc9aac3\",\"size\":5363},\"frontend/visual/tests/offline-export-manifest.test.mjs\":{\"sha\":\"c3a2935d57fb260efe87bc5a23e90b693381a1c3\",\"size\":3781},\"frontend/visual/tests/operation-feedback.test.mjs\":{\"sha\":\"6610eb89aa8680a30bf8c9490cb2497674cf9bca\",\"size\":2438},\"frontend/visual/tests/postmark-view.test.mjs\":{\"sha\":\"0e30c18de7b7dfcfd877d36af588dd63ad0503ac\",\"size\":7318},\"frontend/visual/tests/registration-view.test.mjs\":{\"sha\":\"7ef6143fe0f4b07dca507ec2473beeac55c73add\",\"size\":5917},\"frontend/visual/tests/run_acceptance.py\":{\"sha\":\"f652ea1238b02bb0616ad7c32ab526a932f8dc74\",\"size\":15455},\"frontend/visual/tests/run_validation_layers.mjs\":{\"sha\":\"91cc5157c635368a6953272b1127d4697a34c52a\",\"size\":2466},\"frontend/visual/tests/s0-command-result.test.mjs\":{\"sha\":\"26a5e349af91ac6ece3871db31a2abad0f68a9d8\",\"size\":5177},\"frontend/visual/tests/s0-read-contract.test.mjs\":{\"sha\":\"394841eed32bed7f2f63756a7900094e2530a44a\",\"size\":4310},\"frontend/visual/tests/source-contract.test.mjs\":{\"sha\":\"a376da9244027a3039cefdc9fd9a6bd71d7c15d2\",\"size\":39345},\"frontend/visual/tests/source-module-graph.test.mjs\":{\"sha\":\"ea6a38966c2ab1a71f66ae34c16d33ab050a7446\",\"size\":5030},\"frontend/visual/tests/team-monitor.test.mjs\":{\"sha\":\"e231c9513d6e78a9ae5877e023cb6b09f6171829\",\"size\":6255},\"frontend/visual/tests/team-monitoring.test.mjs\":{\"sha\":\"a54ca19c3cb1190f9471e7054a8711ecf9d3da3e\",\"size\":5565},\"frontend/visual/tests/team-operations.test.mjs\":{\"sha\":\"c4e72a12e2dd1de10d5a2f56b51d43aeb4f86904\",\"size\":4413},\"frontend/visual/tests/team-pause-preview.test.mjs\":{\"sha\":\"762b2c76b06994238da636c95cc93a83dfed4d72\",\"size\":5059},\"frontend/visual/tests/test_offline_export.py\":{\"sha\":\"9bdfdfce2b12d2cf2cdc1a46a700bc1c6b47ab7e\",\"size\":14202},\"frontend/visual/tests/transport-state-view.test.mjs\":{\"sha\":\"d10f5710b80bf6f7c8030df2668df23b4f085768\",\"size\":4604},\"frontend/visual/tests/validation-layers.json\":{\"sha\":\"f105d5b036c938b308a831123a8a8c10deb2611c\",\"size\":2021},\"frontend/visual/tests/validation-layers.test.mjs\":{\"sha\":\"802fe7d22de902305bda3f69dfcdb7a118d6908e\",\"size\":2670},\"frontend/visual/tests/view-model.test.mjs\":{\"sha\":\"3b71b90cb2d77455977490e22d50bceae2f9c827\",\"size\":4086},\"frontend/visual/transport-state-view.mjs\":{\"sha\":\"a064c9ed2691c9bf670a58442957e63fea0f1537\",\"size\":3069},\"frontend/visual/view-model.mjs\":{\"sha\":\"27e1a85fe58ad644727415d47839637784a81098\",\"size\":4450}}}")

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
