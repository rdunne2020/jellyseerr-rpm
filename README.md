# seerr-rpm

RPM packaging for [Seerr](https://github.com/seerr-team/seerr), a media request
manager for Jellyfin, Plex, and Emby. This is community packaging, independent of
upstream Seerr. Production Node.js dependencies are bundled in the binary RPM;
the package is architecture specific because several dependencies use native code.

## Build

The CI matrix builds Fedora 42 and 43 on x86_64. Builds need network access to fetch
the upstream source archive and the dependencies in its frozen pnpm lockfile.
Use a disposable Fedora environment with enough memory for a Next.js build.

With [EarthBuild](https://www.earthbuild.dev/):

```sh
earthly -a '+build-rpm/*.rpm' --FEDORA_VERSION=43
earthly +test-rpm --FEDORA_VERSION=43
```

Or inside a disposable Fedora 43 container, from this repository:

```sh
dnf install -y rpm-build rpmdevtools dnf5-plugins systemd
dnf builddep -y seerr.spec
bash scripts/build-rpm.sh
bash tests/smoke-rpm.sh artifacts/seerr-*.rpm
```

The script writes binary and source RPMs to `artifacts/`. Set `RPM_BUILD_DIR` to
change the default temporary build tree, `/tmp/seerr-rpmbuild`. The source RPM
includes the upstream source and packaging files; rebuilding still downloads npm
dependencies. This is not an offline or Fedora distribution repository build.

## Install and operate

Install the binary RPM matching your Fedora version, then start the service:

```sh
sudo dnf install ./seerr-3.5.0-1.fc43.x86_64.rpm
sudo systemctl enable --now seerr.service
```

Open `http://localhost:5055` to complete setup. The default listener is
`0.0.0.0:5055`; edit `/etc/seerr/seerr.conf` to change the host, port, or log level,
then run `sudo systemctl restart seerr`. Network access also depends on your
firewall configuration.

The package creates an unprivileged `seerr` account. Application files live under
`/usr/lib64/seerr` on x86_64, persistent data (including SQLite, settings, and logs)
under `/var/lib/seerr`, and disposable cache files under `/var/cache/seerr`.
Local environment configuration is preserved on upgrades. The service is not
started automatically during installation.

Before upgrading an older installation, stop its service and back up its data.
Earlier packages may have stored writable data within the application directory.
Copy the contents of that config directory into `/var/lib/seerr` and assign them
to `seerr:seerr` before starting the new service. Data migration is manual; this
package does not rename existing accounts, units, or data directories.

Useful diagnostics:

```sh
systemctl status seerr.service
journalctl -u seerr.service
rpm -V seerr
```

## Verification

Run the offline updater tests and shell validation:

```sh
python3 -m unittest discover -s tests -v
bash -n scripts/build-rpm.sh tests/smoke-rpm.sh
shellcheck scripts/build-rpm.sh tests/smoke-rpm.sh
```

`%check` verifies compiled output and loads the native bcrypt, SQLite, and sharp
modules. The container smoke test installs the actual RPM, verifies packaged
files, service syntax, ownership, API readiness, frontend response, and persistent
SQLite creation, configuration preservation on reinstall, and data retention on
removal. It starts the app as `seerr` without a systemd PID 1. On a Fedora
host, also use `systemctl enable --now seerr` and check `/api/v1/status` to verify
the systemd sandbox and host integration.

CI runs checks for pull requests, main pushes, and manual builds, uploading both
Fedora variants as artifacts. Only a pushed `vVERSION` tag publishes a GitHub
release, after all matrix builds and smoke tests pass. The tag must match the spec
version. Rebuilding the same tag replaces its release assets; increase `Release`
for packaging-only changes, and use a new upstream version tag for a new release.

The weekly updater uses GitHub's stable-release API and opens a pull request.
Enable GitHub Actions permission to create pull requests in repository settings.
The updater explicitly dispatches **Build Seerr RPMs** on new or updated pull
request branches so [default-token PR builds](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
can run without a manual workflow approval step.
The updater never pushes to main or publishes a release. Review runtime requirements,
reset `Release` to 1 for upstream version changes, and maintain the spec changelog.
