ARG os=8.7.20221112
ARG image=php-7.4

FROM aursu/pearbuild:${os}-${image}

RUN dnf -y install \
        centos-release-rabbitmq-38 \
    && dnf clean all && rm -rf /var/cache/dnf

RUN dnf -y install \
        rabbitmq-server \
        librabbitmq-devel \
    && dnf clean all && rm -rf /var/cache/dnf \
    && usermod -G rabbitmq centos \
    && chmod 770 /var/lib/rabbitmq

COPY SOURCES ${BUILD_TOPDIR}/SOURCES
COPY SPECS ${BUILD_TOPDIR}/SPECS

RUN chown -R $BUILD_USER ${BUILD_TOPDIR}/{SOURCES,SPECS}

USER $BUILD_USER

ENTRYPOINT ["/usr/bin/rpmbuild", "php-pecl-amqp.spec"]
CMD ["-ba"]
