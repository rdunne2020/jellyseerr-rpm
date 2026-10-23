#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
build_dir=${RPM_BUILD_DIR:-/tmp/seerr-rpmbuild}
mkdir -p "$build_dir"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
cp "$repo_dir/seerr.spec" "$build_dir/SPECS/"
cp "$repo_dir/packaging/"* "$build_dir/SOURCES/"
spectool -g -C "$build_dir/SOURCES" "$repo_dir/seerr.spec"
rpmbuild --define "_topdir $build_dir" -ba "$build_dir/SPECS/seerr.spec"
mkdir -p "$repo_dir/artifacts"
find "$build_dir/RPMS" "$build_dir/SRPMS" -type f -name '*.rpm' \
    -exec cp -t "$repo_dir/artifacts" {} +
