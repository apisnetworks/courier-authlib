#
# Copyright 1998 - 2010 Double Precision, Inc.  See COPYING for
# distribution information.

# No dist tag from mock; detect mandrake, redhat, etc. the old fashioned way
%if 0%{!?dist:1}
%define courier_release %(test -e /etc/mandrake-release -o -e /etc/mandriva-release && release="mdk" ; if test $? != 0; then release="`rpm -q --queryformat='.rh%{VERSION}' redhat-release 2>/dev/null`" ; if test $? != 0 ; then release="`rpm -q --queryformat='.fc%{VERSION}' fedora-release 2>/dev/null`" ; if test $? != 0 ; then release="" ; fi ; fi ; fi ; echo "$release")
%else
%define courier_release %{nil}
%endif

# --define 'pg_version 9.3' to build for version 9.3 from pgdg
%define pglib %{?pg_version:-L/usr/pgsql-%{pg_version}/lib}

%define using_systemd %(test -d /etc/systemd && echo 1 || echo 0)

################################################################################

Name:           courier-authlib
Version:        0.71.5
Release:        2%{?dist}%{?courier_release}
Summary:        Courier authentication library

Group:          System Environment/Daemons
License:        GPLv3
URL:            http://www.courier-mta.org

################################################################################

Source:         http://dl.sourceforge.net/courier/%{name}-%{version}.tar.bz2
Patch0:		preserve-username.patch
Patch1:		subsys-removal.patch 
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

################################################################################
BuildRequires:      libtool
BuildRequires:      openldap-devel
BuildRequires:      mysql-devel zlib-devel sqlite-devel
BuildRequires:      postgresql-devel
BuildRequires:      gdbm-devel
BuildRequires:      pam-devel
BuildRequires:      expect
BuildRequires:      gcc-c++
BuildRequires:	    redhat-rpm-config
BuildRequires:      courier-unicode-devel >= 2.0

BuildRequires:      %{_includedir}/ltdl.h

%if 0%(rpm -q redhat-release >/dev/null 2>&1 || rpm -q fedora-release >/dev/null 2>&1 || exit 0; echo "1")
BuildRequires:      redhat-rpm-config
%endif

Requires:						courier-unicode >= 2.0

%if %using_systemd
Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):    systemd
%else
Requires(post):     /sbin/chkconfig
Requires(preun):    /sbin/chkconfig
%endif

%define need_perl_generators %(if rpm -q fedora-release >/dev/null 2>/dev/null; then echo "1"; exit 0; fi; echo "1"; exit 1)

%if %need_perl_generators
BuildRequires: perl-generators
%endif

################################################################################

%description
The Courier authentication library provides authentication services for
other Courier applications.

################################################################################

%package devel
Summary:    Development libraries for the Courier authentication library
Group:      Development/Libraries
Requires:   courier-authlib = 0:%{version}-%{release}

%description devel
This package contains the development libraries and files needed to compile
Courier packages that use this authentication library.  Install this
package in order to build the rest of the Courier packages.  After they are
built and installed this package can be removed.  Files in this package
are not needed at runtime.

################################################################################

%package userdb

Summary:    Userdb support for the Courier authentication library
Group:      System Environment/Daemons
Requires:   courier-authlib = 0:%{version}-%{release}

%description userdb
This package installs the userdb support for the Courier authentication
library.  Userdb is a simple way to manage virtual mail accounts using
a GDBM-based database file.
Install this package in order to be able to authenticate with userdb.

################################################################################

%package ldap

Summary:    LDAP support for the Courier authentication library
Group:      System Environment/Daemons
Requires:   courier-authlib = 0:%{version}-%{release}

%description ldap
This package installs LDAP support for the Courier authentication library.
Install this package in order to be able to authenticate using LDAP.

################################################################################

%package mysql

Summary:    MySQL support for the Courier authentication library
Group:      System Environment/Daemons
Requires:   courier-authlib = 0:%{version}-%{release}

%description mysql
This package installs MySQL support for the Courier authentication library.
Install this package in order to be able to authenticate using MySQL.

%package sqlite

Summary:    SQLite support for the Courier authentication library
Group:      System Environment/Daemons
Requires:   courier-authlib = 0:%{version}-%{release}

%description sqlite
This package installs SQLite support for the Courier authentication library.
Install this package in order to be able to authenticate using an SQLite-based
database file.

################################################################################

%package pgsql

Summary:    PostgreSQL support for the Courier authentication library
Group:      System Environment/Daemons
Requires:   courier-authlib = 0:%{version}-%{release}

%description pgsql
This package installs PostgreSQL support for the Courier authentication
library.
Install this package in order to be able to authenticate using PostgreSQL.

################################################################################

%package pipe

Summary:    External authentication module that communicates via pipes
Group:      System Environment/Daemons
Requires:   courier-authlib = 0:%{version}-%{release}

%description pipe
This package installs the authpipe module, which is a generic plugin
that enables authentication requests to be serviced by an external
program, then communicates through messages on stdin and stdout.

################################################################################

%prep
%setup -q
%patch0 -p1
%patch1 -p1

%build
env PATH=/usr/bin:$PATH CFLAGS="%{pglib}" CXXFLAGS="%{pglib}" %configure -C --with-redhat
%{__make} -s %{_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
MAKEFLAGS= %{__make} install DESTDIR=$RPM_BUILD_ROOT
%{__rm} -f $RPM_BUILD_ROOT%{_libdir}/courier-authlib/*.a
%{__install} -m 555 sysconftool $RPM_BUILD_ROOT%{_libexecdir}/courier-authlib

./courierauthconfig --configfiles >configtmp
. ./configtmp

d=`pwd`
cd $RPM_BUILD_ROOT%{_localstatedir}/spool/authdaemon || exit 1
$d/authmksock ./socket || exit 1
cd $d || exit 1
touch $RPM_BUILD_ROOT%{_localstatedir}/spool/authdaemon/pid.lock || exit 1
touch $RPM_BUILD_ROOT%{_localstatedir}/spool/authdaemon/pid || exit 1
%{__chmod} 777 $RPM_BUILD_ROOT%{_localstatedir}/spool/authdaemon/socket || exit 1

cat >configfiles.base <<EOF
%defattr(-,$mailuser,$mailgroup,-)
%{_sysconfdir}/authlib
%{_libexecdir}/courier-authlib
%dir %{_libdir}/courier-authlib
%dir %attr(750,$mailuser,$mailgroup) %{_localstatedir}/spool/authdaemon
EOF

echo "%defattr(-,$mailuser,$mailgroup,-)" >configfiles.mysql
echo "%defattr(-,$mailuser,$mailgroup,-)" >configfiles.sqlite
echo "%defattr(-,$mailuser,$mailgroup,-)" >configfiles.ldap
echo "%defattr(-,$mailuser,$mailgroup,-)" >configfiles.pgsql
echo "%defattr(-,$mailuser,$mailgroup,-)" >configfiles.userdb
echo "%defattr(-,$mailuser,$mailgroup,-)" >configfiles.pipe
echo "%defattr(-,$mailuser,$mailgroup,-)" >configfiles.devel

for f in $RPM_BUILD_ROOT%{_sbindir}/*
do
	fn=`basename $f`
	case "$fn" in
	*userdb*)
		echo "%{_sbindir}/$fn" >>configfiles.userdb
		;;
	*)
		echo "%{_sbindir}/$fn" >>configfiles.base
		;;
	esac
done

for f in $RPM_BUILD_ROOT%{_libdir}/courier-authlib/*
do
	fn=`basename $f`

	# Remove *.la for authentication modules, keep the ones
	# for client libraries. Do this before we sort them into buckets,
	# below.

	case "$fn" in
	*.la)
		case "$fn" in
		libcourierauth*)
			;;
		*)
			rm -f "$f"
			;;
		esac
		continue
		;;
	esac

	case "$fn" in
	libauthpipe*)
		echo "%{_libdir}/courier-authlib/$fn" >>configfiles.pipe
		;;
	libauthldap*)
		echo "%{_libdir}/courier-authlib/$fn" >>configfiles.ldap
		;;
	libauthmysql*)
		echo "%{_libdir}/courier-authlib/$fn" >>configfiles.mysql
		;;
	libauthsqlite*)
		echo "%{_libdir}/courier-authlib/$fn" >>configfiles.sqlite
		;;
	libauthpgsql*)
		echo "%{_libdir}/courier-authlib/$fn" >>configfiles.pgsql
		;;
	libauthldap*)
		echo "%{_libdir}/courier-authlib/$fn" >>configfiles.ldap
		;;
	libauthuserdb*)
		echo "%{_libdir}/courier-authlib/$fn" >>configfiles.userdb
		;;
	*)
		echo "%{_libdir}/courier-authlib/$fn" >>configfiles.base
		;;
	esac
done
%if %using_systemd
%{__mkdir_p} $RPM_BUILD_ROOT%{_datadir}
# Hardcoded path
sed -e 's!/usr/share!'%{_libexecdir}'!g' courier-authlib.sysvinit
%{__install} -m 555 courier-authlib.sysvinit $RPM_BUILD_ROOT%{_libexecdir}/courier-authlib

%{__mkdir_p} $RPM_BUILD_ROOT/lib/systemd/system
%{__install} -m 644 courier-authlib.service $RPM_BUILD_ROOT/lib/systemd/system
%else
%{__mkdir_p} $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d
%{__install} -m 555 courier-authlib.sysvinit \
        $RPM_BUILD_ROOT%{_sysconfdir}/rc.d/init.d/courier-authlib
%endif

%post
%{_libexecdir}/courier-authlib/sysconftool -n %{_sysconfdir}/authlib/*.dist >/dev/null
%if %using_systemd
if test -f /etc/init.d/courier-authlib
then
# Upgrade to systemd

        /sbin/chkconfig --del courier-authlib
        /bin/systemctl stop courier-authlib.service || :
fi
%systemd_post courier-authlib.service
%else
/sbin/chkconfig --del courier-authlib
/sbin/chkconfig --add courier-authlib
%endif
%preun
if test -x %{_sbindir}/authdaemond
then
	%{_sbindir}/authdaemond stop >/dev/null 2>&1 || /bin/true
fi

if test "$1" = "0"
then
%if %using_systemd
%systemd_preun courier-authlib.service
%else
        /sbin/chkconfig --del courier-authlib
%endif
fi

%postun
%if %using_systemd
%systemd_postun_with_restart courier-authlib.service
%endif

%clean
rm -rf $RPM_BUILD_ROOT


%files -f configfiles.base
%defattr(-,root,root,-)
%doc README README*html README.authmysql.myownquery README.ldap
%doc NEWS COPYING* AUTHORS ChangeLog
%if %using_systemd
/lib/systemd/system/*
%attr(755, bin, bin) %{_libexecdir}/courier-authlib/courier-authlib.sysvinit
%else
/etc/rc.d/init.d/*
%endif
%ghost %attr(600, root, root) %{_localstatedir}/spool/authdaemon/pid.lock
%ghost %attr(644, root, root) %{_localstatedir}/spool/authdaemon/pid
%ghost %attr(-, root, root) %{_localstatedir}/spool/authdaemon/socket
%{_mandir}/man1/*

%files -f configfiles.userdb userdb
%{_mandir}/man8/*userdb*

%files -f configfiles.devel devel
%defattr(-,root,root,-)
%{_bindir}/courierauthconfig
%{_includedir}/*
%{_mandir}/man3/*
%{_libdir}/courier-authlib/*.la
%doc authlib.html auth_*.html

%files -f configfiles.ldap ldap
%defattr(-,root,root,-)
%doc authldap.schema authldap.ldif

%files -f configfiles.mysql mysql

%files -f configfiles.sqlite sqlite

%files -f configfiles.pgsql pgsql

%files -f configfiles.pipe pipe

%changelog

* Thu Sep  7 2006 Chris Petersen <rpm@forevermore.net>                  0.58-2
- Make the spec a little prettier
- Replace BuildPreReq with BuildRequires
- Remove period from summaries (rpmlint)
- Fix release tag to use %{?dist} macro if it's present
- Change distro-detection to use "rh" and "fc" for version detection, and add support for mandriva

* Sun Oct  3 2004 Mr. Sam <sam@email-scan.com>                          0.50-1
- Initial build.

