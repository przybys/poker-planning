#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import httplib2

from apiclient import discovery
from oauth2client import appengine
from google.appengine.api import memcache

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), '../client_secrets.json')

http = httplib2.Http(memcache)
service = discovery.build("plus", "v1", http=http)
decorator = appengine.oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/plus.me'
)
