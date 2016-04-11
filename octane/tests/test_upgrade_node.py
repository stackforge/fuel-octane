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

import copy
import pytest


@pytest.mark.parametrize('cmd,env,nodes,provision,roles', [
    (["upgrade-node", "--isolated", "1", "2", "3"], 1, [2, 3], True, None),
    (["upgrade-node", "--isolated", "--no-provision", "4", "5"], 4, [5], False,
     None),
    (["upgrade-node", "--isolated", "--roles=role-a,role-b", "6", "7"], 6, [7],
     True, ["role-a", "role-b"]),
    (["upgrade-node", "--isolated", "--no-provision", "--roles=role-c,role-d",
      "8", "9"], 8, [9], False, ["role-c", "role-d"]),
])
@pytest.mark.parametrize('no_live_migration', [True, False])
def test_parser(mocker, octane_app, cmd, env, nodes, provision, roles,
                no_live_migration):
    run_cmd = copy.copy(cmd)
    if no_live_migration:
        run_cmd.append("--no-live-migration")
    m = mocker.patch('octane.commands.upgrade_node.upgrade_node')
    octane_app.run(run_cmd)
    assert not octane_app.stdout.getvalue()
    assert not octane_app.stderr.getvalue()
    m.assert_called_once_with(env, nodes, isolated=True, network_template=None,
                              provision=provision, roles=roles,
                              no_live_migration=no_live_migration)
