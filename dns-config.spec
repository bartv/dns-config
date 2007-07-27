%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           dns-config
Version:        0.3
Release:        1%{?dist}
Summary:        Tool to generate dns configuration from ldap

Group:          System/tools
License:        MIT
URL:            http://bart.ulyssis.org/hg/dns-config
Source0:        dns-config-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python-setuptools
Requires:       python-ldap 
Requires:       python-ldapobject
Requires:       bind
BuildArch:      noarch

%description

%prep
%setup -q -n %{name}-%{hg_tag}

%build
%{__python} setup.py build 

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --root $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{_datadir}/dns-config/templates
install -pm 0644 templates/*.py  $RPM_BUILD_ROOT%{_datadir}/dns-config/templates/
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}
install -pm 0644 dnsconfig.conf $RPM_BUILD_ROOT%{_sysconfdir}/
mkdir -p $RPM_BUILD_ROOT%{_bindir}
install -pm 0755 dnsconfig $RPM_BUILD_ROOT%{_bindir}/

mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/dnsconfig
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/cache/dnsconfig

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc
%{python_sitelib}/dnsconfig/*.py*
# egg stuff
%{python_sitelib}/dns_config-*/*
%{_datadir}/dns-config/templates/*
%config %{_sysconfdir}/dnsconfig.conf
%{_bindir}/dnsconfig
%{_localstatedir}/log/dnsconfig
%{_localstatedir}/cache/dnsconfig

%changelog
* Fri 27 2007 Bart Vanbrabant <bart@ulyssis.org> 0.3-1
- Update to 0.3

* Wed Jan 26 2007 Bart Vanbrabant <bart@ulyssis.org> 0.2-3
- Update snapshot

* Sun Jan 22 2007 Bart Vanbrabant <bart@ulyssis.org> 0.2-1
- Initial packaging
