%define name fuel-octane
%{!?version: %define version 1}
%{!?release: %define release 1}

Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
Summary: Fuel upgrade tool
URL:     http://mirantis.com
License: Apache
Group: Applications/System
BuildRoot: %{_tmppath}/%{name}-%{version}-buildroot
Prefix: %{_prefix}
BuildRequires:  git
BuildRequires: python-setuptools
BuildRequires: python-pbr
BuildArch: noarch

Requires:    python
Requires:    patch
Requires:    tar
Requires:    pssh

%description
Project is aimed to validate if more or less simple upgrade of MOS 5.1+

%prep
%setup -cq -n %{name}-%{version}

%build
export OSLO_PACKAGE_VERSION=1 # XXX workaround hack
cd %{_builddir}/%{name}-%{version} && python setup.py build

%install
cd %{_builddir}/%{name}-%{version} 
# stub
install -d -m 755 %{buildroot}%{_sysconfdir}/octane

%clean
rm -rf $RPM_BUILD_ROOT
