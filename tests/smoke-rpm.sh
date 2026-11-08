#!/usr/bin/env bash
# Run as root in a disposable Fedora container. No systemd PID 1 is required.
set -euo pipefail

rpms=()
for candidate in "$@"; do
    [[ "$candidate" == *.src.rpm ]] || rpms+=("$candidate")
done
[[ ${#rpms[@]} -eq 1 ]] || { echo 'Expected one binary RPM' >&2; exit 1; }
rpm_path=$(realpath "${rpms[0]}")
dnf install -y curl util-linux "$rpm_path"
app_dir=$(rpm --eval '%{_libdir}')/seerr
rpm -V seerr
systemd-analyze verify /usr/lib/systemd/system/seerr.service
[[ $(id -u seerr) -ne 0 ]]
[[ $(stat -c '%U:%G:%a' /var/lib/seerr) == seerr:seerr:750 ]]
[[ $(stat -c '%U:%G:%a' /var/cache/seerr) == seerr:seerr:750 ]]
[[ -L "$app_dir/.next/cache" ]]

cleanup() {
    kill "$server_pid" 2>/dev/null || true
    wait "$server_pid" 2>/dev/null || true
    cat /tmp/seerr-smoke.log
}
cd "$app_dir"
runuser -u seerr -- env NODE_ENV=production CONFIG_DIRECTORY=/var/lib/seerr \
    HOST=127.0.0.1 PORT=5055 LOG_LEVEL=info \
    /usr/bin/node dist/index.js >/tmp/seerr-smoke.log 2>&1 &
server_pid=$!
trap cleanup EXIT
ready=false
for _attempt in {1..90}; do
    kill -0 "$server_pid" || { echo 'Seerr exited before readiness' >&2; exit 1; }
    if curl --fail --silent --max-time 5 http://127.0.0.1:5055/api/v1/status/appdata >/tmp/seerr-status.json; then
        ready=true
        break
    fi
    sleep 2
done
[[ "$ready" == true ]] || { echo 'Seerr did not become ready' >&2; exit 1; }
node -e "const s=require('/tmp/seerr-status.json'); if (s.appDataPath !== '/var/lib/seerr' || !s.appDataPermissions) process.exit(1)"
curl --fail --silent --location --max-time 30 http://127.0.0.1:5055/ >/tmp/seerr-home.html
grep -qi '<html' /tmp/seerr-home.html
# The service must have persisted its SQLite database outside the application tree.
find /var/lib/seerr -name '*.sqlite*' -type f | grep -q .
runuser -u seerr -- test ! -w "$app_dir/dist/index.js"
echo 'Seerr RPM smoke test passed'

# A reinstall must preserve administrator configuration and existing data.
kill "$server_pid"
wait "$server_pid" || true
trap - EXIT
printf '\n# smoke-test local setting\n' >> /etc/seerr/seerr.conf
rpm -U --replacepkgs "$rpm_path"
grep -q 'smoke-test local setting' /etc/seerr/seerr.conf
find /var/lib/seerr -name '*.sqlite*' -type f | grep -q .
rpm -e seerr
find /var/lib/seerr -name '*.sqlite*' -type f | grep -q .
test -f /etc/seerr/seerr.conf.rpmsave
echo 'Seerr RPM reinstall and removal tests passed'
