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

from distutils import version

from octane.util import subprocess


def get_version():
    _, stderr = subprocess.call(["fuel", "--version"], stderr=subprocess.PIPE)
    return stderr.strip().rsplit("\n", 1)[-1]


def equal_to(version_name):
    return version.StrictVersion(version_name) == get_version()
