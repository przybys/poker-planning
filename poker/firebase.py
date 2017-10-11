#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import base64
try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache
import json
import time
import httplib2

from google.appengine.api import app_identity
from oauth2client.client import GoogleCredentials

FIREBASE_DATABASE_URL = 'https://poker-planning-a8ba9.firebaseio.com'

IDENTITY_ENDPOINT = ('https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit')

FIREBASE_SCOPES = [
    'https://www.googleapis.com/auth/firebase.database',
    'https://www.googleapis.com/auth/userinfo.email',
]

@lru_cache()
def get_http():
    http = httplib2.Http()
    creds = GoogleCredentials.get_application_default().create_scoped(FIREBASE_SCOPES)
    creds.authorize(http)
    return http

def send_firebase_message(uid, message=None):
    url = '{}/channels/{}.json'.format(FIREBASE_DATABASE_URL, uid)
    if message:
        return get_http().request(url, 'PATCH', body=message)
    else:
        return get_http().request(url, 'DELETE')

def create_custom_token(uid, valid_minutes=60):
    client_email = app_identity.get_service_account_name()
    now = int(time.time())
    body = {
        'iss': client_email,
        'sub': client_email,
        'aud': IDENTITY_ENDPOINT,
        'uid': uid,
        'iat': now,
        'exp': now + (valid_minutes * 60),
    }
    payload = base64.b64encode(json.dumps(body))
    header = base64.b64encode(json.dumps({'typ': 'JWT', 'alg': 'RS256'}))
    to_sign = '{}.{}'.format(header, payload)
    return '{}.{}'.format(to_sign, base64.b64encode(app_identity.sign_blob(to_sign)[1]))
