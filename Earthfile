VERSION 0.8

rpm-builder:
    ARG FEDORA_VERSION=43
    FROM fedora:${FEDORA_VERSION}
    RUN dnf install -y rpm-build rpmdevtools dnf5-plugins
    WORKDIR /seerr
    COPY seerr.spec ./
    RUN dnf builddep -y seerr.spec

build-rpm:
    FROM +rpm-builder
    COPY packaging ./packaging
    COPY scripts ./scripts
    RUN bash scripts/build-rpm.sh
    SAVE ARTIFACT artifacts/*.rpm

test-rpm:
    FROM +rpm-builder
    COPY +build-rpm/*.rpm ./artifacts/
    COPY tests ./tests
    RUN bash tests/smoke-rpm.sh artifacts/seerr-*.rpm
