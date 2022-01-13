import os

import requests
from django.conf import settings

if settings.USE_IPB:
    SITE_URL = os.environ.get('SITE_URL')
    CLIENT_ID = os.environ.get('OAUTH_CLIENT_ID')
    # OAUTH_LINK = f'{SITE_URL}/oauth/authorize/?client_id={CLIENT_ID}&response_type=code'
    OAUTH_ACCESS_TOKEN_URL = SITE_URL + os.environ.get('OAUTH_ACCESS_TOKEN_ENDPOINT')
    CLIENT_SECRET = os.environ.get('OAUTH_CLIENT_SECRET')
    SCOPE = os.environ.get('OAUTH_SCOPE')
    BENLOTUS_API_KEY = os.environ.get("BENLOTUS_API_KEY")

    f_params = {'key': BENLOTUS_API_KEY}
    assert SITE_URL
    assert CLIENT_SECRET
    assert CLIENT_ID
    assert SCOPE
    assert BENLOTUS_API_KEY


def ipb_oauth_authenticate(username: str, password: str) -> (bool, str):
    payload = {'grant_type': 'password',
               'username': username,
               'password': password,
               'scope': 'movie',
               'client_id': CLIENT_ID,
               'client_secret': CLIENT_SECRET}
    try:
        response = requests.request("POST", OAUTH_ACCESS_TOKEN_URL, data=payload)
        if response.status_code == 200 and response.json().get('access_token'):
            return True, response.json().get('access_token')
    except Exception as e:
        print(e)
    return False, ''
