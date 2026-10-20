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
from zipfile import ZipFile, BadZipFile

MANIFEST = json.loads("{\"source_head\":\"e873463eaf36c6683477d30acb330bbe716e6660\",\"source_branch\":\"feat/frontend-plataforma-visual\",\"files\":{\"frontend/visual/README.md\":{\"sha\":\"95daebbd7ca17df4d123c5283763e6e4efc5f060\",\"size\":15822},\"frontend/visual/app.mjs\":{\"sha\":\"85b505d7029fc67eac565f1c93b6ad64e05b36b4\",\"size\":48014},\"frontend/visual/bank-view.mjs\":{\"sha\":\"588871c042e5a10d608726c65dcb88f26da68ae9\",\"size\":4155},\"frontend/visual/batch-monitor.mjs\":{\"sha\":\"9ba7b1e0d1e6e141681059de33ef07adb7e99302\",\"size\":3882},\"frontend/visual/cf-op-02.mjs\":{\"sha\":\"fbbfa5affcb10165d806382cfa6bf1ef86223170\",\"size\":14336},\"frontend/visual/fixtures.mjs\":{\"sha\":\"22264f84947c5f8ea4a1a52adf038dcd1ac27d4b\",\"size\":7466},\"frontend/visual/index.html\":{\"sha\":\"c80279c9df1112b30e23ddb393a14f3125ec8c02\",\"size\":11402},\"frontend/visual/postmark-view.mjs\":{\"sha\":\"1e7b395a5abca0ace4204800079ba8f161a52a45\",\"size\":5626},\"frontend/visual/registration-view.mjs\":{\"sha\":\"2b637a3268fb9da503f28cca8ea0e4b2d72b11b0\",\"size\":4700},\"frontend/visual/styles.css\":{\"sha\":\"24cb10a3abe814c2675d5f664eb43c4b5282326f\",\"size\":22706},\"frontend/visual/team-monitor.mjs\":{\"sha\":\"1ebc701d2fbc245c0d39db8df50c8d041f5faf45\",\"size\":3377},\"frontend/visual/team-monitoring.mjs\":{\"sha\":\"9e7ef19aabe5b53bdbfce88c0ea8eb3d95d66443\",\"size\":4111},\"frontend/visual/team-operations.mjs\":{\"sha\":\"9db41b31742fd7152d0ec2330007cfe17d774e57\",\"size\":2237},\"frontend/visual/tests/app.dom.test.mjs\":{\"sha\":\"8b5f52e2d3e98e897bfc9398f1827d733c003e86\",\"size\":23492},\"frontend/visual/tests/app.mobile.dom.test.mjs\":{\"sha\":\"c86f65cc4e5ae5f2b3a98cc4b36e33614ff0441f\",\"size\":6761},\"frontend/visual/tests/bank-view.test.mjs\":{\"sha\":\"d9ee25e929674326adeae3db6d7ac868e4e13106\",\"size\":4626},\"frontend/visual/tests/batch-monitor.test.mjs\":{\"sha\":\"ca61ff3031662fcfdb7f07fafd9a251b131ee358\",\"size\":3895},\"frontend/visual/tests/browser.smoke.py\":{\"sha\":\"b6aec358df62c98a08c0e4ef4eaa2bfb49e87f41\",\"size\":14485},\"frontend/visual/tests/cf-op-02.test.mjs\":{\"sha\":\"c59a4945e5c2c8da53f5a1158c2cc5eb6f281f62\",\"size\":9255},\"frontend/visual/tests/dom-fixture.mjs\":{\"sha\":\"56a4e332b8577cbc510ef660b395617a8b3ed266\",\"size\":5532},\"frontend/visual/tests/fixtures.test.mjs\":{\"sha\":\"9547b1dfd1cf9107a897eb85f3d4cecddc3d900d\",\"size\":4550},\"frontend/visual/tests/postmark-view.test.mjs\":{\"sha\":\"0e30c18de7b7dfcfd877d36af588dd63ad0503ac\",\"size\":7318},\"frontend/visual/tests/registration-view.test.mjs\":{\"sha\":\"7ef6143fe0f4b07dca507ec2473beeac55c73add\",\"size\":5917},\"frontend/visual/tests/run_acceptance.py\":{\"sha\":\"7c7f21ceb05a7a71b771b6b45ed7673db5629a2d\",\"size\":8302},\"frontend/visual/tests/source-contract.test.mjs\":{\"sha\":\"1a019f3cfb9f780a7afa7d08de958e6e3a51edcf\",\"size\":11608},\"frontend/visual/tests/source-module-graph.test.mjs\":{\"sha\":\"ccd6dba82aa8a3cec97199adb199876506fce0e9\",\"size\":4871},\"frontend/visual/tests/team-monitor.test.mjs\":{\"sha\":\"e231c9513d6e78a9ae5877e023cb6b09f6171829\",\"size\":6255},\"frontend/visual/tests/team-monitoring.test.mjs\":{\"sha\":\"4838d32609d018564cd87cf0baf8e553ba42f7fc\",\"size\":5498},\"frontend/visual/tests/team-operations.test.mjs\":{\"sha\":\"c4e72a12e2dd1de10d5a2f56b51d43aeb4f86904\",\"size\":4413},\"frontend/visual/tests/view-model.test.mjs\":{\"sha\":\"78fbb626fffc81ccd1be59c8e08123eae52959e0\",\"size\":2946},\"frontend/visual/view-model.mjs\":{\"sha\":\"dca44b9dbdcf944c75e98760955bed48b46dab3e\",\"size\":4020}}}")

def blob_sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()

def load_verified(archive):
    required = MANIFEST["files"]
    data = {}
    with ZipFile(archive) as z:
        names = [item.filename for item in z.infolist() if not item.is_dir()]
        prefixes = {name.partition("frontend/visual/")[0] for name in names
                    if "frontend/visual/" in name}
        if len(prefixes) != 1:
            raise ValueError("ZIP must contain exactly one frontend/visual root")
        prefix = prefixes.pop()
        for name in names:
            if name.startswith("/") or ".." in PurePosixPath(name).parts or "\\" in name:
                raise ValueError("Unsafe path in ZIP: "+name)
        for rel, info in required.items():
            path=prefix+rel
            if names.count(path)!=1:
                raise ValueError("Missing or duplicated file: "+rel)
            raw=z.read(path)
            if len(raw)!=info["size"] or blob_sha(raw)!=info["sha"]:
                raise ValueError("Git blob hash mismatch: "+rel)
            data[rel]=raw
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
        report["verified_blob_count"]=len(files)
        print("Verified",len(files),"GitHub source blobs against",MANIFEST["source_head"])
        if a.run_native:
            with tempfile.TemporaryDirectory(prefix="fv-ui-013-export-") as tmp:
                root=Path(tmp)
                for name,raw in files.items():
                    dest=root/name
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    dest.write_bytes(raw)
                visual=root/"frontend"/"visual"
                tests=sorted(str(f) for f in (visual/"tests").glob("*.test.mjs"))
                report["runs"]["node"]=execute(["node","--test",*tests],visual)
                report["runs"]["chromium"]=execute(
                    [sys.executable,str(visual/"tests"/"browser.smoke.py")],visual)
                report["native_snapshot_pass"]=all(
                    result["executed"] and result["passed"]
                    for result in report["runs"].values())
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
