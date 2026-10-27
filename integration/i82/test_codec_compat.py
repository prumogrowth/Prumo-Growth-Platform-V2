"""Compare persisted synthetic wire/HMAC vectors against unchanged Python ports."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import UUID
from backend.identity_boundary import Principal
from backend import s1_professionals_local as i79
from backend import s1_legacy_regularization_local as i80

class CodecCompatibility(unittest.TestCase):
    def test_original_python_ports_match_all_http_vectors(self):
        f=json.loads(Path('integration/i82/compat_vectors.json').read_text())
        for v in f['vectors']:
            with self.subTest(action=v['command']['action'],family=v['family']):
                module=i79 if v['family']=='i79' else i80
                cls=module.S1ProfessionalsLocal if v['family']=='i79' else module.S1LegacyRegularizationLocal
                adapter=object.__new__(cls)
                adapter.gateway=SimpleNamespace(_key_id=UUID(f['key_id']),_secret=bytes.fromhex(f['secret_hex']))
                dto=v['command'].copy()
                if v['family']=='i79':dto['expected_relationship_id']=int(dto['expected_relationship_id'])
                p=module.command(dto)
                principal=Principal(UUID(f['principal']['actor']),UUID(f['principal']['session']))
                with patch.object(module.time,'time',return_value=f['issued']),patch.object(module,'uuid4',return_value=UUID(f['nonce'])):
                    args=adapter.proof(principal,p)
                self.assertEqual(args[-1],v['mac'])

if __name__=='__main__':unittest.main(verbosity=2)
