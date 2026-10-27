import os
from integration.i83.provision_local import install
from scripts.test_s0_cfi01_auth_rest_local import local_env

if __name__=='__main__':
    install(local_env()['DB_URL'])
    print('I83 dedicated role disabled/passwordless and private custody installed; no credentials generated',flush=True)
