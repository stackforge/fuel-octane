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
import os
import urlparse

from octane.handlers.backup_restore import base

from octane.util import docker
from octane.util import helpers
from octane.util import subprocess


class NaigunWWWBackup(base.PathArchivator):
    path = "/var/www/nailgun/"
    db = "nailgun"
    name = None
    sql = None

    def _get_values_list(self, data):
        raise NotImplementedError

    def backup(self):
        ipaddr = helpers.get_astute_dict()["ADMIN_NETWORK"]["ipaddress"]
        results, _ = docker.run_in_container(
            "postgres",
            [
                "sudo",
                "-u",
                "postgres",
                "psql",
                self.db,
                "--tuples-only",
                "-c",
                self.sql
            ],
            stdout=subprocess.PIPE)
        results = results.strip()
        if not results:
            return
        rows = results.split("\n")
        already_backuped = set()
        for line in rows:
            data = json.loads(line)
            for value in self._get_values_list(data):
                if ipaddr in value['uri']:
                    path = urlparse.urlsplit(value['uri']).path
                    dir_name = path.lstrip("/").split('/', 1)[0]
                    if dir_name in already_backuped:
                        continue
                    already_backuped.add(dir_name)
                    path = os.path.join(self.path, dir_name)
                    self.archive.add(path, os.path.join(self.name, dir_name))


class MirrorsBackup(NaigunWWWBackup):

    name = "mirrors"
    sql = "select editable from attributes;"

    def _get_values_list(self, data):
        return data['repo_setup']['repos']['value']


class RepoBackup(NaigunWWWBackup):

    name = "repos"
    sql = "select generated from attributes;"

    def _get_values_list(self, data):
        return data['provision']['image_data'].values()


class FullMirrorsBackup(base.PathArchivator):

    path = "/var/www/nailgun/"
    sql = "select array_to_json(array_agg(distinct version)) from releases;"
    name = "mirrors"
    db = "nailgun"

    def _get_mirrors(self):
        results, _ = docker.run_in_container(
            "postgres",
            [
                "sudo",
                "-u",
                "postgres",
                "psql",
                self.db,
                "--tuples-only",
                "-c",
                self.sql
            ],
            stdout=subprocess.PIPE)
        results = results.strip().splitlines()
        releases = ["mos-ubuntu", ]
        for line in results:
            releases.extend(json.loads(line))
        return releases

    def backup(self):
        for dir_name in self._get_mirrors():
            path = os.path.join(self.path, dir_name)
            self.archive.add(path, os.path.join(self.name, dir_name))


class FullRepoBackup(base.PathArchivator):
    name = 'repos/targetimages'
    path = '/var/www/nailgun/targetimages'
