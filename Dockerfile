ARG os=9.4.20240523
ARG image=php-8.3

FROM aursu/pearbuild:${os}-${image}

# https://www.rabbitmq.com/docs/install-rpm
COPY system/etc/yum.repos.d/rabbitmq.repo /etc/yum.repos.d/rabbitmq.repo

# install these dependencies from standard OS repositories
RUN dnf -y install \
        logrotate \
        socat \
    && dnf clean all && rm -rf /var/cache/dnf

# install RabbitMQ and zero dependency Erlang
RUN dnf -y install \
        erlang \
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
