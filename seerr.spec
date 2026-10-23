Name:           seerr
Version:        3.5.0
Release:        1%{?dist}
Summary:        Media request manager for Jellyfin, Plex, and Emby
License:        MIT
URL:            https://github.com/seerr-team/seerr
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        seerr.service
Source2:        seerr.conf

BuildRequires:  systemd-rpm-macros
BuildRequires:  nodejs22 >= 22.19.0
BuildRequires:  pnpm >= 10
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  tar
BuildRequires:  gzip
BuildRequires:  findutils
Requires:       nodejs22 >= 22.19.0
# The service account is created in %pre before owned directories are installed.
Provides:       user(seerr)
Provides:       group(seerr)
Requires(pre):  shadow-utils
%{?systemd_requires}

# The bundled dependencies contain architecture-specific native modules.
%global debug_package %{nil}
%global __requires_exclude_from ^%{_libdir}/%{name}/node_modules/.*$
%global __provides_exclude_from ^%{_libdir}/%{name}/node_modules/.*$
%global __brp_mangle_shebangs_exclude_from ^%{_libdir}/%{name}/node_modules/.*$

%description
Seerr manages media requests and integrates with Jellyfin, Plex, Emby,
Sonarr, and Radarr. This package bundles its production Node.js dependencies.

%prep
%autosetup

%build
export CI=true
export CYPRESS_INSTALL_BINARY=0
export NEXT_TELEMETRY_DISABLED=1
export COMMIT_TAG=v%{version}
pnpm install --frozen-lockfile
pnpm build
pnpm prune --prod --ignore-scripts
# bcrypt ships prebuilt binaries for other operating systems and architectures.
bcrypt_prebuilds=$(dirname "$(node -p "require.resolve('bcrypt/package.json')")")/prebuilds
find "$bcrypt_prebuilds" -mindepth 1 -maxdepth 1 -type d \
    ! -name "linux-$(node -p 'process.arch')" -exec rm -rf {} +
rm -rf .next/cache

%install
install -d %{buildroot}%{_libdir}/%{name}
# Keep the upstream runtime configuration alongside the compiled application.
cp -a package.json next.config.ts seerr-api.yml node_modules dist public .next \
    %{buildroot}%{_libdir}/%{name}/
printf '{"commitTag":"v%{version}"}\n' > %{buildroot}%{_libdir}/%{name}/committag.json
ln -s %{_localstatedir}/cache/%{name} %{buildroot}%{_libdir}/%{name}/.next/cache
install -Dpm0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
sed -i 's|@APP_DIR@|%{_libdir}/%{name}|g' %{buildroot}%{_unitdir}/%{name}.service
install -Dpm0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/%{name}/%{name}.conf
install -d -m0750 %{buildroot}%{_localstatedir}/lib/%{name}
install -d -m0750 %{buildroot}%{_localstatedir}/cache/%{name}

%check
test -s dist/index.js
test -s .next/BUILD_ID
node -e "require('bcrypt'); require('sqlite3'); require('sharp')"

%pre
getent group seerr >/dev/null || groupadd -r seerr
getent passwd seerr >/dev/null || \
    useradd -r -g seerr -d %{_localstatedir}/lib/seerr -s /sbin/nologin \
    -c 'Seerr service account' seerr

%post
%systemd_post seerr.service

%preun
%systemd_preun seerr.service

%postun
%systemd_postun_with_restart seerr.service

%files
%license LICENSE
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf
%{_libdir}/%{name}/
%{_unitdir}/%{name}.service
%attr(0750,seerr,seerr) %dir %{_localstatedir}/lib/%{name}
%attr(0750,seerr,seerr) %dir %{_localstatedir}/cache/%{name}

%changelog
* Fri Oct 23 2026 Seerr RPM maintainers <noreply@localhost> - 3.5.0-1
- Package Seerr with an unprivileged service and persistent state directories
