class octane_tasks::dbsync (
) inherits octane_tasks::params {

  include ::nova::db::sync
  include ::glance::db::sync
  include ::neutron::db::sync
  include ::cinder::db::sync
  include ::heat::db::sync

  if $murano_enabled {
    include ::murano::db::sync
  }

  if $sahara_enabled {
    include ::sahara::db::sync
  }

  # All db sync classes have "refreshonly => true" by default
  Exec <||> {
    refreshonly => false
  }
}
