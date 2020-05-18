ARG centos=7
ARG image=php-7.1

FROM aursu/pearbuild:${centos}-${image}

# yum install --enablerepo=PowerTools "pkgconfig(librabbitmq)"

RUN yum -y install \
        rabbitmq-server \
        librabbitmq-devel \
    && yum clean all && rm -rf /var/cache/yum

COPY SOURCES ${BUILD_TOPDIR}/SOURCES
COPY SPECS ${BUILD_TOPDIR}/SPECS

RUN chown -R $BUILD_USER ${BUILD_TOPDIR}/{SOURCES,SPECS}

USER $BUILD_USER

ENTRYPOINT ["/usr/bin/rpmbuild", "php-pecl-amqp.spec"]
CMD ["-ba"]
