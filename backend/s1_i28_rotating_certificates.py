"""S1-002/I28: PKI rotativa SOMENTE para CI descartavel.

Gera segunda identidade gateway assinada pela CA efemera do I27.
Nunca escrever material de chave no Git, em logs ou no Supabase hospedado.
"""
from pathlib import Path
import os
import subprocess

from backend.s1_i27_ephemeral_certificates import create_local_certificates, certificate_fingerprint


def create_rotating_certificates(directory):
    root = Path(directory)
    result = create_local_certificates(directory)
    for name, cn in (("gateway_next", "prumo-i28-gateway-next"),
                     ("gateway_rogue", "prumo-i28-other-client")):
        def openssl(*arguments):
            subprocess.run(["openssl", *arguments], check=True, cwd=str(root),
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15)
        openssl("ecparam", "-name", "prime256v1", "-genkey", "-noout",
                "-out", name + ".key")
        os.chmod(root / (name + ".key"), 0o600)
        openssl("req", "-new", "-sha256", "-key", name + ".key",
                "-out", name + ".csr", "-subj", "/CN=" + cn)
        (root / (name + ".ext")).write_text(
            "basicConstraints=critical,CA:FALSE\n"
            "keyUsage=critical,digitalSignature\n"
            "extendedKeyUsage=clientAuth\n", encoding="ascii")
        openssl("x509", "-req", "-sha256", "-in", name + ".csr",
                "-CA", "ca.crt", "-CAkey", "ca.key", "-CAcreateserial",
                "-out", name + ".crt", "-days", "1", "-extfile", name + ".ext")
        result[name] = {"cert": str(root / (name + ".crt")),
                        "key": str(root / (name + ".key"))}
    return result


__all__ = ["create_rotating_certificates", "certificate_fingerprint"]
