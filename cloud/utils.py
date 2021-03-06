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

from typing import List


def escape_email(s):
    s = s.replace('.', '-dot-')
    s = s.replace('@', '-at-')
    return s


def escape_version(s):
    return s.replace('.', '-')


def missing_required(d, required):
    if not d:
        return required
    return [k for k in required if k not in d]


def path_stripper(to_exclude: List):

    def _fn(path_parts: List) -> List:
        for rm in to_exclude:
            try:
                idx = path_parts.index(rm)
                path_parts.pop(idx)
            except ValueError:
                pass
        return path_parts

    return _fn


def chunk(obj, size):
    n = max(1, size)
    return (
        obj[i:i + size] for i in range(0, len(obj), n)
    )
