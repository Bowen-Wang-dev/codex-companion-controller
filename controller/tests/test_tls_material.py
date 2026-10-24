import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'bridge'))
from tls_material import certificate_is_named_p256, create_certificate


class CertificateTests(unittest.TestCase):
    def test_named_curve_generation_permissions_and_trust(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            create_certificate(p, '192.0.2.10')
            cert = p / 'bridge-cert.pem'
            self.assertTrue(certificate_is_named_p256(cert))
            for name in ['bridge-cert.pem', 'bridge-key.pem']:
                self.assertEqual((p / name).stat().st_mode & 0o777, 0o600)
            subprocess.run(['openssl', 'verify', '-CAfile', str(cert), str(cert)],
                           check=True, capture_output=True)
            # The optional probe is built from IDF's actual Mbed TLS sources.
            probe = os.environ.get('PASSPORT_MBEDTLS_CERT_PROBE')
            if probe:
                result = subprocess.run([probe, str(cert), '192.0.2.10'],
                                        check=True, capture_output=True, text=True)
                self.assertIn('flags: 0x00000000', result.stdout)
                wrong = subprocess.run([probe, str(cert), '192.0.2.11'], capture_output=True)
                self.assertNotEqual(wrong.returncode, 0)

    def test_detect_explicit_curve_and_regenerate(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            create_certificate(p, '192.0.2.10')
            subprocess.run(['openssl', 'req', '-x509', '-newkey', 'ec', '-pkeyopt',
                            'ec_paramgen_curve:P-256', '-pkeyopt', 'ec_param_enc:explicit',
                            '-nodes', '-days', '1', '-keyout', str(p / 'bridge-key.pem'),
                            '-out', str(p / 'bridge-cert.pem'), '-config', str(p / 'cert.cnf')],
                           check=True, capture_output=True)
            self.assertFalse(certificate_is_named_p256(p / 'bridge-cert.pem'))
            probe = os.environ.get('PASSPORT_MBEDTLS_CERT_PROBE')
            if probe:
                result = subprocess.run([probe, str(p / 'bridge-cert.pem'), '192.0.2.10'], capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'-0x3d00', result.stdout)
            create_certificate(p, '192.0.2.10')
            self.assertTrue(certificate_is_named_p256(p / 'bridge-cert.pem'))

    def test_missing_and_malformed_certificates_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'cert.pem'
            self.assertFalse(certificate_is_named_p256(p))
            p.write_text('not a certificate')
            self.assertFalse(certificate_is_named_p256(p))


if __name__ == '__main__':
    unittest.main()
