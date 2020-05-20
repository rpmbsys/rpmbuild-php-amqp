ARG centos=7.8.2003
ARG image=php-7.1

FROM aursu/pearbuild:${centos}-${image}

ARG os_id=centos
ARG os_version_id=7

ENV OS_ID $os_id
ENV OS_VERSION_ID $os_version_id

COPY system/etc/yum.repos.d/erlang-solutions.repo /etc/yum.repos.d/erlang-solutions.repo
RUN curl -sSf "https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/config_file.repo?os=${OS_ID}&dist=${OS_VERSION_ID}&source=script" -o /etc/yum.repos.d/rabbitmq_rabbitmq-server.repo

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
