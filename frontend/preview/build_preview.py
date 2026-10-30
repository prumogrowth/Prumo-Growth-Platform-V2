"""Prepare a static, source-verified, synthetic Prumo frontend preview for local review.

No deploy. No external requests. No real customer data. Python stdlib only.
Serve the extracted ZIP over localhost for review. Publication is a separate action
and is not performed or authorized by this builder.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

ROOT = Path(__file__).resolve().parents[2]
VISUAL = ROOT / "frontend" / "visual"
VERIFIER = VISUAL / "tests" / "verify_offline_export.py"
PREVIEW = ROOT / "frontend" / "preview"
ALLOWED_SUFFIXES = {".mjs", ".css", ".html"}
ENTRY = {"index.html", "styles.css", "app.mjs"}


def pinned_manifest():
    """Read the pinned provenance declaration as a literal, without exec."""
    root = ast.parse(VERIFIER.read_text(encoding="utf-8"), filename=str(VERIFIER))
    for stmt in root.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "MANIFEST"
                   for target in stmt.targets):
            continue
        value = stmt.value
        if (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and value.func.attr == "loads"
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id == "json" and len(value.args) == 1
                and isinstance(value.args[0], ast.Constant)
                and isinstance(value.args[0].value, str)):
            manifest = json.loads(value.args[0].value)
            if manifest.get("source_branch") not in {"feat/frontend-plataforma-visual", "codex/fv-ux-01-comunicacao-20261027", "codex/fv-rev-01-conversas-20261030"}:
                raise ValueError("Unrecognized source branch")
            return manifest
    raise ValueError("No valid pinned manifest")


def git_blob_hash(data):
    """Git SHA1 includes the Git blob header; do not confuse with raw SHA1."""
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") +
                        b"\0" + data).hexdigest()


def collect_assets():
    """Fail closed on any unpinned, modified, or unsafe runtime asset."""
    manifest = pinned_manifest()
    assets = {}
    for path in sorted(VISUAL.iterdir()):
        if path.is_symlink():
            raise ValueError("Symlink rejected: " + path.name)
        if path.is_file() and path.suffix in ALLOWED_SUFFIXES:
            if path.name != "index.html" and path.suffix == ".html":
                raise ValueError("Unexpected extra HTML")
            data = path.read_bytes()
            origin = "frontend/visual/" + path.name
            pin = manifest["files"].get(origin)
            if not isinstance(pin, dict) or pin.get("size") != len(data):
                raise ValueError("Unpinned runtime asset: " + origin)
            if pin.get("sha") != git_blob_hash(data):
                raise ValueError("Runtime asset differs from certified manifest: " + origin)
            assets[path.name] = data
    if not ENTRY.issubset(assets):
        raise ValueError("Required entry assets missing")
    html = assets["index.html"].decode("utf-8")
    if ('src="./app.mjs"' not in html or
            'href="./styles.css"' not in html or
            "Dados fictícios" not in html):
        raise ValueError("Demo entry contract differs from reviewed source")

    # All relative module imports must point to files inside the export.
    import re
    for name, data in assets.items():
        if not name.endswith(".mjs"):
            continue
        text = data.decode("utf-8")
        for target in re.findall(r'''(?:\bfrom\s*|\bimport\s*)['"](\.[^'"]+)['"]''', text):
            if target.startswith("./") and target[2:] not in assets:
                raise ValueError("Unresolved module " + target + " in " + name)
            if not target.startswith("./"):
                raise ValueError("Unsafe relative module specifier in " + name)
    return assets, manifest


def make_archive(output):
    assets, manifest = collect_assets()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    runtime_hashes = {name: hashlib.sha256(contents).hexdigest()
                      for name, contents in sorted(assets.items())}
    info = {
        "kind": "Prumo visual evaluation only",
        "source_branch": manifest["source_branch"],
        "source_head": manifest["source_head"],
        "synthetic_data_only": True,
        "backend_calls": False,
        "production_authorization": False,
        "runtime_files_sha256": runtime_hashes,
        "notice": "Synthetic local review only. No authentication, upload or business services. Publication requires a separate instruction."
    }
    # noindex is a crawl request, NOT access control.
    extras = {
        "robots.txt": b"User-agent: *\nDisallow: /\n",
        "_headers": b"/*\n  X-Robots-Tag: noindex, nofollow\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n",
        "PREVIEW_BUILD_MANIFEST.json": (json.dumps(info, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    }
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted({**assets, **extras}.items()):
            # Deterministic metadata; no local paths or filesystem metadata embedded.
            entry = ZipInfo(name, date_time=(2026, 10, 26, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, content, compress_type=ZIP_DEFLATED, compresslevel=9)
    print(f"Preview ZIP prepared: {output} ({len(assets)} certified runtime files; no deploy)")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="out/prumo-demo-visual.zip")
    args = parser.parse_args()
    make_archive(args.output)
