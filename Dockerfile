ARG centos=7.8.2003
ARG image=php-7.1

FROM aursu/pearbuild:${centos}-${image}

COPY system/etc/yum.repos.d/erlang-solutions.repo /etc/yum.repos.d/erlang-solutions.repo

RUN rpm --import https://packages.erlang-solutions.com/rpm/erlang_solutions.asc \
    && curl -s https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.rpm.sh -o script.rpm.sh \
    && chmod +x script.rpm.sh  \
    && bash script.rpm.sh

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
