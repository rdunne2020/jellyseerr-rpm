# seerr-rpm

RPM packaging for [Seerr](https://github.com/seerr-team/seerr), a media request
manager for Jellyfin, Plex, and Emby. This is community packaging, independent of
upstream Seerr. Production Node.js dependencies are bundled in the binary RPM;
the package is architecture specific because several dependencies use native code.

## Build

The CI matrix builds Fedora 44 and 45 on x86_64. Builds need network access to fetch
the upstream source archive and the dependencies in its frozen pnpm lockfile.
Use a disposable Fedora environment with enough memory for a Next.js build.

With [EarthBuild](https://www.earthbuild.dev/):

```sh
earthly -a '+build-rpm/*.rpm' --FEDORA_VERSION=44
earthly +test-rpm --FEDORA_VERSION=44
```

Or inside a disposable Fedora 44 container, from this repository:

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
sudo dnf install ./seerr-3.5.2-1.fc44.x86_64.rpm
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
bash -n scripts/*.sh tests/smoke-rpm.sh
shellcheck scripts/*.sh tests/smoke-rpm.sh
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

## Release signing

Tagged releases require these GitHub Actions repository secrets:

| Secret | Value |
| --- | --- |
| `RPM_SIGNING_PRIVATE_KEY` | ASCII-armored private signing key |
| `RPM_SIGNING_PASSPHRASE` | Passphrase protecting that key |
| `RPM_SIGNING_KEY_FINGERPRINT` | Full 40-character primary key fingerprint |

Generate a dedicated project key locally. Replace the example email with your
own; GPG prompts for a passphrase. Keep the passphrase in your password manager.
These commands use your local GPG keyring and GitHub CLI authentication:

```sh
gpg --quick-generate-key 'Seerr RPM signing <you@example.com>' rsa3072 sign 2y
gpg --list-secret-keys --keyid-format long --fingerprint
# Copy the full fingerprint of the new key, without spaces:
export RPM_SIGNING_KEY_FINGERPRINT=REPLACE_WITH_FULL_FINGERPRINT

# Run from this repository. Private key material goes directly to GitHub CLI.
set -o pipefail
gpg --armor --export-secret-keys "$RPM_SIGNING_KEY_FINGERPRINT" | gh secret set RPM_SIGNING_PRIVATE_KEY
# Interactive prompt: enter the same passphrase you used in GPG.
gh secret set RPM_SIGNING_PASSPHRASE
printf '%s' "$RPM_SIGNING_KEY_FINGERPRINT" | gh secret set RPM_SIGNING_KEY_FINGERPRINT

# Public material is safe to share:
gpg --armor --export "$RPM_SIGNING_KEY_FINGERPRINT" > /tmp/RPM-GPG-KEY-seerr
gpg --show-keys --fingerprint /tmp/RPM-GPG-KEY-seerr
```

Keep an encrypted offline backup of the private key and the revocation certificate
GPG creates. Never commit either to Git. The key expires in two years; renew it
before expiry with `gpg --quick-set-expire "$RPM_SIGNING_KEY_FINGERPRINT" 2y`,
then update the private-key secret and redistribute the updated public key.
If the key is compromised, revoke and replace it and notify package users.

Pull requests and ordinary builds never receive signing secrets. Their RPM
artifacts remain unsigned, and the disposable smoke test explicitly permits the
unsigned reinstall. After the build matrix passes, the tag-only release job signs
both binary and source RPMs in a separate Fedora container. It verifies signatures
and digests with a fresh RPM keyring containing only the project public key before
publishing. Missing or incorrect secrets fail the release; there is no unsigned
release fallback. Signing temporary files and the GPG agent are removed on exit.
The published key is `RPM-GPG-KEY-seerr` alongside the release RPMs.

Before installing a release, download its public key and binary RPM, compare the
key's full fingerprint with the maintainer's fingerprint from a separately trusted
channel, then import and verify it:

```sh
gpg --show-keys --fingerprint ./RPM-GPG-KEY-seerr
sudo rpm --import ./RPM-GPG-KEY-seerr
rpmkeys --define '_pkgverify_level all' --checksig ./seerr-3.5.2-1.fc45.x86_64.rpm
sudo dnf install ./seerr-3.5.2-1.fc45.x86_64.rpm
```

A signature proves that the package was signed by the holder of the corresponding
private key and has not changed since signing. Importing a public key establishes
your trust in that publisher; a matching fingerprint identifies the exact key.
This is OpenPGP signing, with no Fedora-issued key or X.509 certificate authority.
The CI runner can use the signing key because it holds both secrets, so protect
repository write access and review workflow changes before tagging a release.

Manual signing check in a disposable Fedora container: install `rpm-sign gnupg2`,
set the three environment variables above using a disposable test key, place a
throwaway RPM under `artifacts/`, and run
`bash scripts/sign-rpms.sh artifacts/*.rpm`. It must succeed with the correct
passphrase and fail with a wrong passphrase or fingerprint. Never use a production
private key for this check.
