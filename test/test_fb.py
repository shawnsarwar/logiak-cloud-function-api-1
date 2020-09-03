#!/usr/bin/env python

# Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

from flask import Response
import json
import pytest


from test.app.cloud.auth import requires_auth
from test.app.cloud.utils import escape_email

from . import (  # noqa
    LOG,
    check_local_firebase_readyness,
    cfs,
    rtdb,
    fb_app,
    MockAuthHandler,
    MockPostRequest,
    rtdb_options,
    sample_project,
    TestSession
)


TEST_USER = 'aboubacar.douno@ehealthnigeria.org'


@pytest.mark.integration
def test__setup_emulator(sample_project):  # noqa  # import static -> emulator
    assert(True)


@pytest.mark.integration
def test__auth_has_app(MockAuthHandler):  # noqa
    assert(MockAuthHandler.sign_in_with_email_and_password('a', 'b') is True)


@pytest.mark.parametrize('email,res', [
    (
        TEST_USER,
        True),
    (
        'fake.person@ehealthnigeria.org',
        False)
])
@pytest.mark.integration
def test__auth_has_app(MockAuthHandler, email, res):  # noqa
    assert(MockAuthHandler.user_has_app_access(email) is res)


@pytest.mark.integration
def test__session(MockAuthHandler, rtdb):  # noqa
    session = MockAuthHandler.create_session(TEST_USER)
    assert(TEST_USER in session)
    session = session[TEST_USER]
    session_key = session['session_key']
    assert(MockAuthHandler._session_is_valid(session))
    assert(MockAuthHandler.verify_session(TEST_USER, session_key))

    # invalidate the token
    key = escape_email(TEST_USER)
    session_obj_ref = f'{MockAuthHandler.session_path}/{key}/{session_key}'
    expiry_ref = f'{session_obj_ref}/session_length'
    rtdb.reference(expiry_ref).set(0)
    assert(MockAuthHandler.verify_session(TEST_USER, session_key) is False)
    MockAuthHandler._remove_expired_sessions(TEST_USER)
    assert(rtdb.reference(session_obj_ref).get() is None)


@pytest.mark.integration
def test__bad_session(MockAuthHandler, rtdb):  # noqa
    assert(MockAuthHandler.verify_session('bad-user', 'bad-token') is False)
    MockAuthHandler._remove_expired_sessions('bad-user')
    assert(MockAuthHandler._session_is_valid({'a': 'bad_session'}) is False)


@pytest.mark.integration
def test__requires_auth(MockAuthHandler, TestSession):  # noqa

    @requires_auth(MockAuthHandler)
    def _fn(*args, **kwargs):
        return True

    session = TestSession(TEST_USER)
    session_key = session[TEST_USER]['session_key']
    good_headers = {'Logiak-User-Id': TEST_USER, 'Logiak-Session-Key': session_key}
    request = MockPostRequest(headers=good_headers)
    assert(_fn(request) is True)

    bad_headers = {'Logiak-User-Id': TEST_USER, 'Logiak-Session-Key': 'bad-key'}
    request = MockPostRequest(headers=bad_headers)
    res = _fn(request)
    assert(isinstance(res, Response))
    assert(res.status_code == 401)

    bad_headers = {'Missing ID': TEST_USER, 'Logiak-Session-Key': 'bad-key'}
    request = MockPostRequest(headers=bad_headers)
    res = _fn(request)
    assert(isinstance(res, Response))
    assert(res.status_code == 400)
