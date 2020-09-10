#!/usr/bin/env python

# Copyright (C) 2020 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import logging
import os

import firebase_admin
from firebase_admin.credentials import ApplicationDefault
from flask import Response
from google.auth.credentials import AnonymousCredentials
from google.cloud.firestore_v1.client import Client as CFS_Client

try:
    from .auth import AuthHandler, auth_request, require_auth
except ImportError:
    from test.app.cloud.auth import AuthHandler, auth_request, require_auth

from . import data, fb_utils, meta, utils

LOG = logging.getLogger('EP')
LOG.setLevel(logging.DEBUG)

ROOT_PATH = os.environ.get('ROOT_PATH')
_STRIP = utils.path_stripper([ROOT_PATH, ''])


SCHEMAS = {}

if (local_fb_uri := os.environ.get('FIREBASE_DATABASE_EMULATOR_HOST', False)):
    LOG.debug('Connecting to Local Emulator')
    _local = 'local'
    uri = f'http://{local_fb_uri}/?ns={_local}'
    APP = firebase_admin.initialize_app(
        name=_local,
        credential=ApplicationDefault(),
        options={
            'databaseURL': uri,
            'projectId': _local
        })
    CFS = fb_utils.Firestore(
        instance=CFS_Client(
            _local,
            credentials=AnonymousCredentials()
        ))
else:
    LOG.debug('Connecting to Firebase')
    APP = firebase_admin.initialize_app(options={
        'databaseURL': os.environ.get('FIREBASE_URL')
    })
    CFS = fb_utils.Firestore(APP)


RTDB = fb_utils.RTDB(APP)
AUTH_HANDLER = AuthHandler(RTDB)


# actual request handlers


# route all from base path (usually APP_ID, name or alias)
def handle_all(request):
    path = request.path.split('/')
    root = _STRIP(path)[0]
    if root == 'auth':
        return handle_auth(request)
    elif root == 'meta':
        return handle_meta(request)
    elif root == 'data':
        return handle_data(request)
    return Response(f'Not Found @ {path}', 404)


def handle_auth(request):
    data = request.get_json(force=True, silent=True)
    return auth_request(data, AUTH_HANDLER)


@require_auth(AUTH_HANDLER)
def handle_meta(request):
    path = request.path.split('/')
    return meta.resolve(path, RTDB)


@require_auth(AUTH_HANDLER)
def handle_data(request):
    user_id = request.headers.get('Logiak-User-Id')
    path = request.path.split('/')
    return data.resolve(user_id, path, CFS)
