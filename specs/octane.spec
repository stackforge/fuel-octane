%define name fuel-octane
%{!?version: %define version 9.0.0}
%{!?release: %define release 1}

Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
Summary: Fuel/MOS upgrade tool
URL:     https://github.com/openstack/fuel-octane
License: Apache
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: /opt
BuildRequires: git
BuildRequires: python-setuptools
BuildRequires: python-pbr
BuildArch: noarch

Requires:    git
Requires:    patch
Requires:    python
Requires:    python-setuptools
Requires:    python-paramiko
Requires:    python-stevedore
Requires:    python-fuelclient
Requires:    python-cliff

%description
Project is aimed to provide tools to upgrade the Fuel Admin node and OpenStack
installations to version 9.0.

%prep
%setup -cq -n %{name}-%{version}

%build
ip a ; traceroute 172.18.184.28 ; cd %{_builddir}/%{name}-%{version} && OSLO_PACKAGE_VERSION=%{version} %{__python2} setup.py egg_info && cp octane.egg-info/PKG-INFO . && %{__python2} setup.py build

%install
ip a ; traceroute 172.18.184.28 ; cd %{_builddir}/%{name}-%{version} && %{__python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=%{_builddir}/%{name}-%{version}/INSTALLED_FILES
cp -vr %{_builddir}/%{name}-%{version}/octane/patches ${RPM_BUILD_ROOT}/%{python2_sitelib}/octane/

%files -f %{_builddir}/%{name}-%{version}/INSTALLED_FILES
%{python2_sitelib}/octane/patches/*
%defattr(-,root,root)


%clean
rm -rf $RPM_BUILD_ROOT
