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

import re
import time
from xml.etree import ElementTree

from octane import magic_consts
from octane.util import env as env_util
from octane.util import ssh
from octane.util import subprocess


def disable_apis(env):
    controllers = list(env_util.get_controllers(env))
    maintenance_line = 'backend maintenance'
    stats_socket_re = re.compile('stats\s+socket\s+/var/lib/haproxy/stats'
                                 '(?!.*level admin)')
    mode_tcp_re = re.compile('mode\s+tcp')
    use_backend_line = '  use_backend maintenance if TRUE'
    for node in controllers:
        sftp = ssh.sftp(node)
        sftp.chdir('/etc/haproxy')
        with ssh.update_file(sftp, 'haproxy.cfg') as (old, new):
            found_maint_line = False
            for line in old:
                if maintenance_line in line:
                    found_maint_line = True
                line = stats_socket_re.sub(r'\g<0> level admin', line)
                new.write(line)
            if not found_maint_line:
                new.write(maintenance_line)
        sftp.chdir('/etc/haproxy/conf.d')
        for f in sftp.listdir():
            with ssh.update_file(sftp, f) as (old, new):
                contents = old.read()
                if not mode_tcp_re.search(contents):
                    raise ssh.DontUpdateException
                new.write(contents)
                if not contents.endswith('\n'):
                    new.write('\n')
                new.write(use_backend_line)
        ssh.call(['crm', 'resource', 'restart', 'p_haproxy'], node=node)


def enable_apis(env):
    controllers = list(env_util.get_controllers(env))
    maintenance_line = 'backend maintenance'
    use_backend_line = '  use_backend maintenance if TRUE'
    for node in controllers:
        sftp = ssh.sftp(node)
        sftp.chdir('/etc/haproxy')
        with ssh.update_file(sftp, 'haproxy.cfg') as (old, new):
            for line in old:
                if maintenance_line in line:
                    continue
                new.write(line)
        sftp.chdir('/etc/haproxy/conf.d')
        for f in sftp.listdir():
            with ssh.update_file(sftp, f) as (old, new):
                for line in old:
                    if use_backend_line in line:
                        continue
                    new.write(line)
        ssh.call(['crm', 'resource', 'restart', 'p_haproxy'], node=node)


_default_exclude_services = ('p_mysql', 'p_haproxy', 'p_dns', 'p_ntp', 'vip',
                             'p_conntrackd', 'p_rabbitmq-server',
                             'clone_p_vrouter')


def get_crm_services(status_out, exclude=_default_exclude_services):
    data = ElementTree.fromstring(status_out)
    for resource in data:
        name = resource.get('id')
        if any(service in name for service in exclude):
            continue
        yield name


def stop_corosync_services(env):
    node = env_util.get_one_controller(env)
    status_out = ssh.call_output(['cibadmin', '--query', '--scope',
                                  'resources'], node=node)
    for service in get_crm_services(status_out):
        while True:
            try:
                ssh.call(['crm', 'resource', 'stop', service],
                         node=node)
            except subprocess.CalledProcessError:
                pass
            else:
                break
    time.sleep(60)


def wait_for_corosync_services_sync(env, timeout=720, check_freq=20):
    node = env_util.get_one_controller(env)
    started_at = time.time()
    db_status = ssh.call_output(['cibadmin', '--query', '--scope',
                                 'resources'], node=node)
    while True:
        real_status = ssh.call_output(['crm_mon', '--as-xml'], node=node)
        if is_resources_synced(db_status, real_status):
            return
        if time.time() - started_at >= timeout:
            raise Exception("Timeout waiting for corosync cluster for env %s"
                            " to be synced" % env.id)
        time.sleep(check_freq)


def is_resources_synced(db_status, real_status):
    pass


def stop_upstart_services(env):
    controllers = list(env_util.get_controllers(env))
    service_re = re.compile("^((?:%s)[^\s]*).*start/running" %
                            ("|".join(magic_consts.OS_SERVICES),),
                            re.MULTILINE)
    for node in controllers:
        sftp = ssh.sftp(node)
        try:
            svc_file = sftp.open('/root/services_list')
        except IOError:
            with sftp.open('/root/services_list.tmp', 'w') as svc_file:
                initctl_out = ssh.call_output(['initctl', 'list'], node=node)
                to_stop = []
                for match in service_re.finditer(initctl_out):
                    service = match.group(1)
                    to_stop.append(service)
                    svc_file.write(service + '\n')
            sftp.rename('/root/services_list.tmp', '/root/services_list')
        else:
            with svc_file:
                to_stop = svc_file.read().splitlines()
        for service in to_stop:
            ssh.call(['stop', service], node=node)


def start_corosync_services(env):
    node = next(env_util.get_controllers(env))
    status_out = ssh.call_output(['cibadmin', '--query', '--scope',
                                  'resources'], node=node)
    for service in get_crm_services(status_out):
        while True:
            try:
                ssh.call(['crm', 'resource', 'start', service],
                         node=node)
            except subprocess.CalledProcessError:
                pass
            else:
                break
    time.sleep(180)


def start_upstart_services(env):
    controllers = list(env_util.get_controllers(env))
    for node in controllers:
        sftp = ssh.sftp(node)
        try:
            svc_file = sftp.open('/root/services_list')
        except IOError:
            raise
        else:
            with svc_file:
                to_start = svc_file.read().splitlines()
        for service in to_start:
            ssh.call(['start', service], node=node)


def stop_services(services, env):
    controllers = list(env_util.get_controllers(env))
    for node in controllers:
        for service in services:
            ssh.call(['service', service, 'stop'], node=node)


def get_cluster_stop_actions():
    return [['pcs', 'cluster', 'kill']]


def get_cluster_start_actions(env):
    major_version = env.data['fuel_version'].split('.')[0]
    if int(major_version) < 6:
        return [['service', 'corosync', 'start']]
    return [['pcs', 'cluster', 'start']]
