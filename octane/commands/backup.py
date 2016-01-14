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
import logging
import sys
import tarfile

from cliff import command

from octane.handlers import backup_restore

LOG = logging.getLogger(__name__)


def backup_admin_node(path_to_backup):
    if path_to_backup:
        backup_format = path_to_backup.rsplit(".", 1)[-1]
        if backup_format not in ["gz", "bz2"]:
            backup_format = ""
        tar_obj = tarfile.open(path_to_backup, "w|{0}".format(backup_format))
    else:
        tar_obj = tarfile.open(fileobj=sys.stdout, mode="w|")
    with contextlib.closing(tar_obj) as archive:
        for manager in backup_restore.ARCHIVATORS:
            manager(archive).backup()


class BackupCommand(command.Command):

    def get_parser(self, *args, **kwargs):
        parser = super(BackupCommand, self).get_parser(*args, **kwargs)
        parser.add_argument(
            "--to",
            type=str,
            action="store",
            dest="path",
            required=False,
            help="path to backup dir")
        return parser

    def take_action(self, parsed_args):
        backup_admin_node(parsed_args.path)
