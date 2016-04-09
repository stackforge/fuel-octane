# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import contextlib

import fuelclient
from fuelclient import client
from fuelclient import fuelclient_settings


@contextlib.contextmanager
def set_auth_context(auth_context):
    auth_cm = set_auth_context_80
    # NOTE(akscram): The 9.0.0 release for fuelclient is not yet
    # available on PyPI but to test it on master nodes with the 9.0
    # release some workaround is needed.
    if fuelclient.__version__ == "9.0.0":
        auth_cm = set_auth_context_90
    with auth_cm(auth_context):
        yield


@contextlib.contextmanager
def set_auth_context_80(auth_context):
    old_credentials = (client.APIClient.user, client.APIClient.password)
    client.APIClient.user = auth_context.user
    client.APIClient.password = auth_context.password
    client.APIClient._session = client.APIClient._keystone_client = None
    try:
        yield
    finally:
        (client.APIClient.user, client.APIClient.password) = old_credentials
        client.APIClient._session = client.APIClient._keystone_client = None


@contextlib.contextmanager
def set_auth_context_90(auth_context):
    config = fuelclient_settings._SETTINGS.config
    old_credentials = (config['OS_USERNAME'], config['OS_PASSWORD'])
    config['OS_USERNAME'] = auth_context.user
    config['OS_PASSWORD'] = auth_context.password
    client.APIClient._session = client.APIClient._keystone_client = None
    try:
        yield
    finally:
        (config['OS_USERNAME'], config['OS_PASSWORD']) = old_credentials
        client.APIClient._session = client.APIClient._keystone_client = None
