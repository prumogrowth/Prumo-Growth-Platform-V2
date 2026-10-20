"""S1-002/I27: gerar PKI efemera para ENSAIOS CI. Nunca gera arquivos persistentes.

CA privada, certificado do assinador e identidades gateway/intruso distintos.
openssl local; sem internet, Vault, KMS, ACME ou chaves operacionais.
"""
from __future__ import annotations

from pathlib import Path
import ssl
import subprocess


def create_local_certificates(directory):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)

    def openssl(*args):
        subprocess.run(["openssl", *args], cwd=str(root), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                       timeout=15)

    openssl("ecparam", "-name", "prime256v1", "-genkey", "-noout",
            "-out", "ca.key")
    openssl("req", "-x509", "-new", "-sha256", "-key", "ca.key",
            "-out", "ca.crt", "-days", "1", "-subj", "/CN=Prumo-I27-Local-CA",
            "-addext", "basicConstraints=critical,CA:TRUE",
            "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    certificates = {}
    for label, common_name, eku in (
        ("signer", "localhost", "serverAuth"),
        ("gateway", "prumo-i27-gateway", "clientAuth"),
        ("intruder", "prumo-i27-intruder", "clientAuth"),
    ):
        key = label + ".key"
        crt = label + ".crt"
        openssl("ecparam", "-name", "prime256v1", "-genkey", "-noout",
                "-out", key)
        openssl("req", "-new", "-sha256", "-key", key,
                "-out", label + ".csr", "-subj", "/CN=" + common_name)
        extension = ("basicConstraints=critical,CA:FALSE\n"
                     "keyUsage=critical,digitalSignature\n"
                     "extendedKeyUsage=" + eku + "\n")
        if label == "signer":
            extension += "subjectAltName=DNS:localhost,IP:127.0.0.1\n"
        (root / (label + ".ext")).write_text(extension, encoding="ascii")
        openssl("x509", "-req", "-sha256", "-in", label + ".csr",
                "-CA", "ca.crt", "-CAkey", "ca.key", "-CAcreateserial",
                "-out", crt, "-days", "1", "-extfile", label + ".ext")
        certificates[label] = {"cert": str(root / crt), "key": str(root / key)}
    return {"ca": str(root / "ca.crt"), **certificates}


def certificate_fingerprint(cert_path):
    pem=Path(cert_path).read_text(encoding="ascii")
    import hashlib
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()
