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

import mock
import pytest


from octane.util import docker


class TestException(Exception):
    pass


@pytest.mark.parametrize("container", ["container_name"])
@pytest.mark.parametrize("prefix", ["prefix_name"])
@pytest.mark.parametrize("patches", [["patch_1"], ["patch_1", "patch_2"]])
def test_applied_patches(mocker, container, prefix, patches):
    apply_patches = mocker.patch("octane.util.docker.apply_patches")
    with docker.applied_patches(container, prefix, *patches):
        pass
    assert [
        mock.call(container, prefix, *patches),
        mock.call(container, prefix, *patches, revert=True)
    ] == apply_patches.call_args_list


@pytest.mark.parametrize("is_exception", [True, False])
@pytest.mark.parametrize("container", ["container"])
@pytest.mark.parametrize("patches", [("patch_1", ), ("patch_1", "patch_2")])
@pytest.mark.parametrize("service", ["service_1"])
@pytest.mark.parametrize("prefix ", ["prefix_1", "prefix_2", None])
def test_applied_docker_context_manager(
        mocker, patches, container, is_exception, service, prefix):
    patch_mock = mocker.patch("octane.util.docker.applied_patches")
    docker_run_mock = mocker.patch("octane.util.docker.run_in_container")

    if is_exception:
        with pytest.raises(TestException):
            with docker.patch_container_service(
                    container, service, prefix, *patches):
                raise TestException
    else:
        with docker.patch_container_service(
                container, service, prefix, *patches):
            pass

    assert [
        mock.call(container, ["service", service, "restart"]),
        mock.call(container, ["service", service, "restart"])
    ] == docker_run_mock.call_args_list
    patch_mock.assert_called_once_with(container, prefix, *patches)
