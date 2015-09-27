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
from cliff import command as cmd
from fuelclient.objects import environment as environment_obj

from octane.util import env as env_util
from octane.util import maintenance
from octane.util import ssh


def update_neutron_config(orig_env, seed_env):
    controllers = list(env_util.get_controllers(seed_env))
    tenant_id = env_util.cache_service_tenant_id(orig_env)
    sed_script = 's/^(nova_admin_tenant_id )=.*/\\1 = %s/' % (tenant_id,)
    for node in controllers:
        ssh.call(['sed', '-re', sed_script, '-i', '/etc/neutron/neutron.conf'],
                 node=node)


def upgrade_control_plane(orig_id, seed_id):
    orig_env = environment_obj.Environment(orig_id)
    seed_env = environment_obj.Environment(seed_id)
    # enable all services on seed env
    maintenance.start_corosync_services(seed_env)
    maintenance.start_upstart_services(seed_env)
    # disable cluster services on orig env
    maintenance.stop_services(env_util.get_cluster_services(orig_env),
                              orig_env)
    # switch networks to seed env
    env_util.disconnect_networks(orig_env)
    env_util.delete_overlay_networks(seed_env)
    env_util.connect_to_networks(seed_env)


class UpgradeControlPlaneCommand(cmd.Command):
    """Switch control plane to the seed environment"""

    def get_parser(self, prog_name):
        parser = super(UpgradeControlPlaneCommand, self).get_parser(prog_name)
        parser.add_argument(
            'orig_id', type=int, metavar='ORIG_ID',
            help="ID of original environment")
        parser.add_argument(
            'seed_id', type=int, metavar='SEED_ID',
            help="ID of seed environment")
        return parser

    def take_action(self, parsed_args):
        upgrade_control_plane(parsed_args.orig_id, parsed_args.seed_id)
