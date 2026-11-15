#!/usr/bin/env bash
# Run in a disposable Fedora container with rpm-sign and gnupg2 installed.
set -euo pipefail
set +x
: "${RPM_SIGNING_PRIVATE_KEY:?Set the armored private key}"
: "${RPM_SIGNING_PASSPHRASE:?Set the key passphrase}"
: "${RPM_SIGNING_KEY_FINGERPRINT:?Set the full primary key fingerprint}"
[[ "$RPM_SIGNING_KEY_FINGERPRINT" =~ ^[A-Fa-f0-9]{40}$ ]] || {
    echo 'Expected a full 40-character OpenPGP v4 fingerprint' >&2
    exit 1
}
[[ $# -gt 0 ]] || { echo 'Pass RPM paths to sign' >&2; exit 1; }
umask 077
sign_dir=$(mktemp -d /tmp/seerr-sign.XXXXXXXX)
export GNUPGHOME="$sign_dir/gnupg"
mkdir "$GNUPGHOME" "$sign_dir/rpmdb"
cleanup() {
    gpgconf --kill gpg-agent || true
    rm -rf -- "$sign_dir"
}
trap cleanup EXIT
printf '%s\n' "$RPM_SIGNING_PRIVATE_KEY" | gpg --batch --import
printf '%s' "$RPM_SIGNING_PASSPHRASE" > "$sign_dir/passphrase"
unset RPM_SIGNING_PRIVATE_KEY RPM_SIGNING_PASSPHRASE
rpmsign --addsign \
    --define '_openpgp_sign gpg' \
    --define "_openpgp_sign_id $RPM_SIGNING_KEY_FINGERPRINT" \
    --define "_gpg_sign_cmd_extra_args --batch --pinentry-mode loopback --passphrase-file $sign_dir/passphrase" \
    "$@"
gpg --batch --armor --export "$RPM_SIGNING_KEY_FINGERPRINT" > artifacts/RPM-GPG-KEY-seerr
# Use a fresh RPM keyring containing only the exported project public key.
rpm --dbpath "$sign_dir/rpmdb" --import artifacts/RPM-GPG-KEY-seerr
rpmkeys --dbpath "$sign_dir/rpmdb" --define '_pkgverify_level all' --checksig "$@"
