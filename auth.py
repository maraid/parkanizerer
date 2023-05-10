import requests
import re
from urllib.parse import urlparse
from urllib.parse import parse_qs


POLICY = "B2C_1A_Parkanizer_Login"
PARKANIZER_LOGIN_URI = "https://login.parkanizer.com/loginparkanizer.onmicrosoft.com/" + POLICY
PARKANIZER_SHARE_URI = "https://share.parkanizer.com"
PARKANIZER_CALLBACK_URI = "https://share.parkanizer.com/callback"


def get_token(username, password):
    session = requests.Session()

    authorize_response = session.get(
        PARKANIZER_SHARE_URI + "/api/auth0/authorize",
        params={
            "callbackUri": PARKANIZER_CALLBACK_URI,
            "emailHint": ""
        }
    )
    authorize_response.raise_for_status()

    state_properties = re.findall(
        r'"transId":"(StateProperties=[^"]*)"', authorize_response.text)[0]
    csrf = authorize_response.cookies["x-ms-cpim-csrf"]

    auth_params = {
        "tx": state_properties,
        "p": POLICY
    }

    self_asserted_response = session.post(
        PARKANIZER_LOGIN_URI + "/SelfAsserted",
        params=auth_params,
        data={
            "request_type": "RESPONSE",
            "signInName": username
        },
        headers={
            "X-CSRF-TOKEN": csrf
        }
    )
    self_asserted_response.raise_for_status()

    confirm_response = session.get(
        PARKANIZER_LOGIN_URI + "/api/CombinedSigninAndSignup/confirmed",
        params=dict(auth_params, **{"csrf_token": csrf})
    )
    confirm_response.raise_for_status()

    csrf2 = confirm_response.cookies['x-ms-cpim-csrf']

    self_asserted2_response = session.post(
        PARKANIZER_LOGIN_URI + "/SelfAsserted",
        params=auth_params,
        data={
            "request_type": "RESPONSE",
            "signInName": username,
            "password": password
        },
        headers={
            "X-CSRF-TOKEN": csrf2
        }
    )
    self_asserted2_response.raise_for_status()

    confirm2_response = session.get(
        PARKANIZER_LOGIN_URI + "/api/CombinedSigninAndSignup/confirmed",
        params=dict(auth_params, **{"csrf_token": csrf2})
    )
    confirm2_response.raise_for_status()

    confirm2_params = parse_qs(urlparse(confirm2_response.url).query)

    get_token_response = session.post(
        PARKANIZER_SHARE_URI + "/api/auth0/get-token",
        json={
            "code": confirm2_params['code'][0],
            "redirectUri": PARKANIZER_CALLBACK_URI,
            "state": confirm2_params['state'][0]
        }
    )
    get_token_response.raise_for_status()

    return "Bearer " + get_token_response.json()["accessToken"]
