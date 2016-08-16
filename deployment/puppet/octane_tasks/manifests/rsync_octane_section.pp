
# == Class: octane_tasks::rsync_octane_section
#
# This class adds a section to rsyncd.conf for Octane with r/w support.
# It also restarts Rsyncd if it's necessary.
#
class octane_tasks::rsync_octane_section {
  augeas { 'rsync_octane_section_code' :
    context => '/files/etc/rsyncd.conf/octane_code',
    notify  => Service['rsyncd'],
    changes => [
      'set path /var/www/nailgun/octane_code',
      'set read\ only true',
      'set uid 0',
      'set gid 0',
      'set use\ chroot no',
    ]
  }

  augeas { 'rsync_octane_section_data' :
    context => '/files/etc/rsyncd.conf/octane_data',
    notify  => Service['rsyncd'],
    changes => [
      'set path /var/www/nailgun/octane_data',
      'set read\ only false',
      'set uid 0',
      'set gid 0',
      'set use\ chroot no',
    ]
  }

  service { 'rsyncd': }
}
