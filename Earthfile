VERSION 0.8

rpm-builder:
    ARG FEDORA_VERSION=43
    FROM fedora:${FEDORA_VERSION}
    RUN dnf install -y createrepo \
                       'dnf-command(builddep)' \
                       git \
                       rpmdevtools \
                       gcc \
                       rpm-build \
                       rpm-devel \
                       rpmlint \
                       make \
                       coreutils \
                       nodejs22 \
                       pnpm
configure-build:
    FROM +rpm-builder
    WORKDIR /seerr
    COPY ./seerr.spec ./
    # Setup the build structure defaults to ${HOME}/rpmbuild
    RUN rpmdev-setuptree && \
        dnf builddep -y seerr.spec && \
        spectool -g -R seerr.spec

build-rpm:
    FROM +configure-build
    RUN rpmbuild -ba seerr.spec
    SAVE ARTIFACT /root/rpmbuild/RPMS/x86_64/*.rpm

test-rpm:
    FROM +rpm-builder
    WORKDIR /opt/rpm
    COPY +build-rpm/*.rpm ./
    RUN rpm2cpio *.rpm | cpio -idmv
    # RUN rpm -ivh /opt/rpm/*.rpm
    RUN false
