# Fedora spec file for php-pecl-amqp
#
# Copyright (c) 2012-2021 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/4.0/
#
# Please, preserve the changelog entries
#

# we don't want -z defs linker flag
%undefine _strict_symbol_defs_build

%define _debugsource_template %{nil}
%define debug_package %{nil}

%global pecl_name   amqp
%global with_zts    0%{!?_without_zts:%{?__ztsphp:1}}
%global with_tests  0%{!?_without_tests:1}
%global ini_name    40-%{pecl_name}.ini
#global prever      beta4

Summary:       Communicate with any AMQP compliant server
Name:          php-pecl-amqp
Version:       1.10.2
Release:       4%{?dist}
License:       PHP
URL:           https://pecl.php.net/package/amqp
Source0:       https://pecl.php.net/get/%{pecl_name}-%{version}%{?prever}.tgz

Patch0:        https://github.com/php-amqp/php-amqp/commit/96cd5cb5eddd3db2faaa3643dad2fe4677d7c438.patch
Patch1:        https://patch-diff.githubusercontent.com/raw/php-amqp/php-amqp/pull/383.patch

BuildRequires: make
BuildRequires: gcc
BuildRequires: php-devel > 5.6
BuildRequires: php-pear
BuildRequires: pkgconfig(librabbitmq) >= 0.7.1
%if %{with_tests}
BuildRequires: rabbitmq-server
%endif

Requires:      php(zend-abi) = %{php_zend_api}
Requires:      php(api) = %{php_core_api}

Provides:      php-%{pecl_name}               = %{version}
Provides:      php-%{pecl_name}%{?_isa}       = %{version}
Provides:      php-pecl(%{pecl_name})         = %{version}
Provides:      php-pecl(%{pecl_name})%{?_isa} = %{version}


%description
This extension can communicate with any AMQP spec 0-9-1 compatible server,
such as RabbitMQ, OpenAMQP and Qpid, giving you the ability to create and
delete exchanges and queues, as well as publish to any exchange and consume
from any queue.


%prep
%setup -q -c

# Don't install/register tests
sed -e 's/role="test"/role="src"/' \
    -e '/LICENSE/s/role="doc"/role="src"/' \
    -i package.xml

mv %{pecl_name}-%{version}%{?prever} NTS
cd NTS
%patch0 -p1 -b .up
%patch1 -p1 -b .pr383

sed -e 's/CFLAGS="-I/CFLAGS="$CFLAGS -I/' -i config.m4

# Upstream often forget to change this
extver=$(sed -n '/#define PHP_AMQP_VERSION/{s/.* "//;s/".*$//;p}' php_amqp.h)
if test "x${extver}" != "x%{version}%{?prever}"; then
   : Error: Upstream version is ${extver}, expecting %{version}%{?prever}.
   exit 1
fi
cd ..

cat > %{ini_name} << 'EOF'
; Enable %{pecl_name} extension module
extension = %{pecl_name}.so

; Whether calls to AMQPQueue::get() and AMQPQueue::consume()
; should require that the client explicitly acknowledge messages.
; Setting this value to 1 will pass in the AMQP_AUTOACK flag to
; the above method calls if the flags field is omitted.
;amqp.auto_ack = 0

; The host to which to connect.
;amqp.host = localhost

; The login to use while connecting to the broker.
;amqp.login = guest

; The password to use while connecting to the broker.
;amqp.password = guest

; The port on which to connect.
;amqp.port = 5672

; The number of messages to prefect from the server during a
; call to AMQPQueue::get() or AMQPQueue::consume() during which
; the AMQP_AUTOACK flag is not set.
;amqp.prefetch_count = 3
;amqp.prefetch_size = 0
;amqp.global_prefetch_count =0
;amqp.global_prefetch_size =0

; The virtual host on the broker to which to connect.
;amqp.vhost = /

; Timeout
;amqp.timeout =
;amqp.read_timeout = 0
;amqp.write_timeout = 0
;amqp.connect_timeout = 0
;amqp.rpc_timeout = 0

;amqp.channel_max = 256
;amqp.frame_max = 131072
;amqp.heartbeat = 0

;amqp.cacert = ''
;amqp.cert = ''
;amqp.key = ''
;amqp.verify = ''
;amqp.sasl_method = 0
EOF

%if %{with_zts}
cp -pr NTS ZTS
%endif


%build
cd NTS
%{_bindir}/phpize
%configure --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}

%if %{with_zts}
cd ../ZTS
%{_bindir}/zts-phpize
%configure --with-php-config=%{_bindir}/zts-php-config
make %{?_smp_mflags}
%endif


%install
make -C NTS install INSTALL_ROOT=%{buildroot}

# Drop in the bit of configuration
install -Dpm 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

# Install XML package description
install -Dpm 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

%if %{with_zts}
make -C ZTS install INSTALL_ROOT=%{buildroot}
install -Dpm 644 %{ini_name} %{buildroot}%{php_ztsinidir}/%{ini_name}
%endif

# Documentation
cd NTS
for i in $(grep 'role="doc"' ../package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 $i %{buildroot}%{pecl_docdir}/%{pecl_name}/$i
done


%check
: Minimal load test for NTS extension
%{__php} --no-php-ini \
    --define extension=NTS/modules/%{pecl_name}.so \
    -m | grep %{pecl_name}

%if %{with_zts}
: Minimal load test for ZTS extension
%{__ztsphp} --no-php-ini \
    --define extension=ZTS/modules/%{pecl_name}.so \
    -m | grep %{pecl_name}
%endif

%if %{with_tests}
mkdir log run base
: Launch the RabbitMQ service
export RABBITMQ_PID_FILE=$PWD/run/pid
export RABBITMQ_LOG_BASE=$PWD/log
export RABBITMQ_MNESIA_BASE=$PWD/base
/usr/lib/rabbitmq/bin/rabbitmq-server &>log/output &
/usr/lib/rabbitmq/bin/rabbitmqctl wait $RABBITMQ_PID_FILE

ret=0
pushd NTS
: Run the upstream test Suite for NTS extension
TEST_PHP_EXECUTABLE=%{__php} \
TEST_PHP_ARGS="-n -d extension=$PWD/modules/%{pecl_name}.so -d error_reporting=1" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__php} -n run-tests.php --show-diff || ret=1
popd

%if %{with_zts}
pushd ZTS
: Run the upstream test Suite for ZTS extension
TEST_PHP_EXECUTABLE=%{__ztsphp} \
TEST_PHP_ARGS="-n -d extension=$PWD/modules/%{pecl_name}.so -d error_reporting=1" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{__ztsphp} -n run-tests.php --show-diff || ret=1
popd
%endif

: Cleanup
if [ -s $RABBITMQ_PID_FILE ]; then
   kill $(cat $RABBITMQ_PID_FILE)
fi
rm -rf log run base

exit $ret
%endif


%files
%license NTS/LICENSE
%doc %{pecl_docdir}/%{pecl_name}
%{pecl_xmldir}/%{name}.xml

%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{pecl_name}.so

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/%{ini_name}
%{php_ztsextdir}/%{pecl_name}.so
%endif


%changelog
* Thu Mar  4 2021 Remi Collet <remi@remirepo.net> - 1.10.2-4
- rebuild for https://fedoraproject.org/wiki/Changes/php80
- add patches for PHP 8 from upstream and
  https://github.com/php-amqp/php-amqp/pull/383

* Mon Apr  6 2020 Remi Collet <remi@remirepo.net> - 1.10.2-1
- update to 1.10.2

* Fri Jul 26 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.9.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.9.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Wed Jan  2 2019 Remi Collet <remi@remirepo.net> - 1.9.4-1
- update to 1.9.4
- drop patch merged upstream
- raise minimal PHP version to 5.6
  and open https://github.com/pdezwart/php-amqp/pull/338

* Thu Oct 11 2018 Remi Collet <remi@remirepo.net> - 1.9.3-5
- Rebuild for https://fedoraproject.org/wiki/Changes/php73
- add patch for PHP 7.3 from
  https://github.com/pdezwart/php-amqp/pull/323

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.9.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.9.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Jan 26 2018 Remi Collet <remi@remirepo.net> - 1.9.3-2
- undefine _strict_symbol_defs_build

* Thu Oct 19 2017 Remi Collet <remi@remirepo.net> - 1.9.3-1
- Update to 1.9.3 (stable)

* Tue Oct 03 2017 Remi Collet <remi@fedoraproject.org> - 1.9.1-4
- rebuild for https://fedoraproject.org/wiki/Changes/php72

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.9.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.9.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Jun 12 2017 Remi Collet <remi@remirepo.net> - 1.9.1-1
- Update to 1.9.1 (stable)

* Tue Mar 21 2017 Remi Collet <remi@remirepo.net> - 1.9.0-1
- update to 1.9.0 (stable)

* Fri Feb 17 2017 Remi Collet <remi@remirepo.net> - 1.8.0-1
- update to 1.8.0 (stable)

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.7.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Nov 14 2016 Remi Collet <remi@fedoraproject.org> - 1.7.1-2
- rebuild for https://fedoraproject.org/wiki/Changes/php71

* Mon Jul 11 2016 Remi Collet <remi@fedoraproject.org> - 1.7.1-1
- update to 1.7.1 (php 5 and 7, stable)

* Mon Jun 27 2016 Remi Collet <remi@fedoraproject.org> - 1.7.0-2
- rebuild for https://fedoraproject.org/wiki/Changes/php70

* Tue Apr 26 2016 Remi Collet <remi@fedoraproject.org> - 1.7.0-1
- update to 1.7.0 (php 5 and 7, stable)

* Wed Feb 10 2016 Remi Collet <remi@fedoraproject.org> - 1.6.1-2
- drop scriptlets (replaced file triggers in php-pear)

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.6.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Nov 26 2015 Remi Collet <remi@fedoraproject.org> - 1.6.1-1
- update to 1.6.1 (stable)

* Tue Nov  3 2015 Remi Collet <remi@fedoraproject.org> - 1.6.0-1
- update to 1.6.0 (stable)
- fix typo in config file

* Fri Sep 18 2015 Remi Collet <remi@fedoraproject.org> - 1.6.0-0.4.beta4
- update to 1.6.0beta4
- open https://github.com/pdezwart/php-amqp/pull/178 - librabbitmq 0.5
- open https://github.com/pdezwart/php-amqp/pull/179 --with-libdir

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.0-0.2.beta3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Apr 20 2015 Remi Collet <remi@fedoraproject.org> - 1.6.0-0.1.beta3
- update to 1.6.0beta3
* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jun 19 2014 Remi Collet <rcollet@redhat.com> - 1.4.0-4
- rebuild for https://fedoraproject.org/wiki/Changes/Php56

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Apr 23 2014 Remi Collet <remi@fedoraproject.org> - 1.4.0-2
- add numerical prefix to extension configuration file

* Tue Apr 15 2014 Remi Collet <remi@fedoraproject.org> - 1.4.0-1
- update to 1.6.0 (stable)
- install doc in pecl doc_dir
- install tests in pecl test_dir (in devel)
- add --with tests option to run upstream tests during build
- build ZTS extension

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu May 30 2013 Remi Collet <remi@fedoraproject.org> - 1.2.0-1
- Update to 1.2.0

* Fri Mar 22 2013 Remi Collet <rcollet@redhat.com> - 1.0.9-4
- rebuild for http://fedoraproject.org/wiki/Features/Php55

* Wed Mar 13 2013 Remi Collet <remi@fedoraproject.org> - 1.0.9-3
- rebuild for new librabbitmq

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Nov 13 2012 Remi Collet <remi@fedoraproject.org> - 1.0.9-1
- update to 1.0.9
- cleanups

* Wed Sep 12 2012 Remi Collet <remi@fedoraproject.org> - 1.0.7-1
- update to 1.0.7

* Mon Aug 27 2012 Remi Collet <remi@fedoraproject.org> - 1.0.5-1
- update to 1.0.5
- LICENSE now provided in upstream tarball

* Wed Aug 01 2012 Remi Collet <remi@fedoraproject.org> - 1.0.4-1
- update to 1.0.4

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat May 19 2012 Remi Collet <remi@fedoraproject.org> - 1.0.3-1
- update to 1.0.3
- add extension version check (and fix)

* Mon Mar 19 2012 Remi Collet <remi@fedoraproject.org> - 1.0.1-3
- clean EL-5 stuff as requires php 5.2.0, https://bugs.php.net/61351

* Sat Mar 10 2012 Remi Collet <remi@fedoraproject.org> - 1.0.1-2
- rebuild for PHP 5.4

* Sat Mar 10 2012 Remi Collet <remi@fedoraproject.org> - 1.0.1-1
- Initial RPM release without ZTS extension
- open request for LICENSE file https://bugs.php.net/61337

