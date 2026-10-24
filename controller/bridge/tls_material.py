"""Generate the named-curve P-256 certificates accepted by the device TLS stack."""
import base64
import binascii
import os
from pathlib import Path
import subprocess
import tempfile

# DER SubjectPublicKeyInfo: id-ecPublicKey + prime256v1 OIDs, followed by
# the BIT STRING containing an uncompressed P-256 point. This checks only
# the bridge's one supported key format, not a general certificate parser.
P256_SPKI_PREFIX = bytes.fromhex('3059301306072a8648ce3d020106082a8648ce3d03010703420004')


def certificate_is_named_p256(path):
    try:
        result = subprocess.run(['openssl', 'x509', '-in', str(path), '-pubkey', '-noout'],
                                check=True, capture_output=True)
        pem = result.stdout
        if not pem.startswith(b'-----BEGIN PUBLIC KEY-----'):
            return False
        encoded = b''.join(pem.splitlines()[1:-1])
        der = base64.b64decode(encoded, validate=True)
        return len(der) == 91 and der.startswith(P256_SPKI_PREFIX)
    except (OSError, ValueError, binascii.Error, subprocess.CalledProcessError):
        return False


def create_certificate(private, ip):
    private = Path(private)
    # Stage both files privately; validate the actual encoding before replacing
    # the old pair. Calling this requires an explicit USB re-pairing workflow.
    with tempfile.TemporaryDirectory(prefix='tls-', dir=private) as directory:
        stage = Path(directory)
        cfg = stage / 'cert.cnf'
        cfg.write_text(f'[req]\ndistinguished_name=dn\nx509_extensions=ext\nprompt=no\n[dn]\nCN=Passport Bridge\n[ext]\nsubjectAltName=IP:{ip},IP:127.0.0.1\nbasicConstraints=critical,CA:TRUE\nkeyUsage=critical,digitalSignature,keyCertSign\nextendedKeyUsage=serverAuth\n')
        key, cert = stage / 'bridge-key.pem', stage / 'bridge-cert.pem'
        # macOS LibreSSL can default to explicit parameters, unlike modern
        # OpenSSL. Specify the encoding instead of relying on either default.
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'ec', '-pkeyopt',
                        'ec_paramgen_curve:P-256', '-pkeyopt', 'ec_param_enc:named_curve',
                        '-sha256', '-nodes', '-days', '3650', '-keyout', str(key),
                        '-out', str(cert), '-config', str(cfg)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not certificate_is_named_p256(cert):
            raise ValueError('新证书不是设备支持的命名曲线 P-256 格式，未替换原证书。')
        for source in (key, cert, cfg):
            os.chmod(source, 0o600)
            os.replace(source, private / source.name)
