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

import json
import logging
import requests
import urlparse
import yaml

from keystoneclient.v2_0 import Client as keystoneclient

from octane.handlers.backup_restore import base
from octane import magic_consts
from octane.util import helpers
from octane.util import subprocess

LOG = logging.getLogger(__name__)


class ReleaseArchivator(base.Base):
    def backup(self):
        pass

    def restore(self):
        with open(magic_consts.OPENSTACK_FIXTURES) as f:
            fixtures = yaml.load(f)
        releases = self.extend_fixtures(fixtures)
        for release in releases:
            self.__post_data_to_nailgun(
                "/api/v1/releases/",
                release,
                self.context.user,
                self.context.password)
        subprocess.call(
            [
                "fuel",
                "release",
                "--sync-deployment-tasks",
                "--dir",
                "/etc/puppet/",
            ],
            env=self.context.get_credentials_env())

    @staticmethod
    def extend_fixtures(fixtures):
        def extend(obj):
            if 'extend' in obj:
                obj['extend'] = extend(obj['extend'])
                return helpers.merge_dicts(obj['extend'], obj)
            return obj

        for fixture in fixtures:
            if "pk" not in fixture or fixture["pk"] is None:
                continue
            yield extend(fixture)["fields"]

    def __post_data_to_nailgun(self, url, data, user, password):
        ksclient = keystoneclient(
            auth_url=magic_consts.KEYSTONE_API_URL,
            username=user,
            password=password,
            tenant_name=magic_consts.KEYSTONE_TENANT_NAME,
        )
        resp = requests.post(
            urlparse.urljoin(magic_consts.NAILGUN_URL, url),
            json.dumps(data),
            headers={
                "X-Auth-Token": ksclient.auth_token,
                "Content-Type": "application/json",
            })
        LOG.debug(resp.content)
        return resp
