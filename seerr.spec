Name:       seerr
Version:    3.3.0
Release:    %autorelease
Summary:    Free and open source software application for managing requests for your media library

License:    MIT
URL:        https://github.com/seerr-team/seerr
Source:     https://github.com/seerr-team/seerr/archive/refs/tags/v%{version}.tar.gz

# Use this to make sure the necessary macros are available like _unitdir
BuildRequires: systemd
BuildRequires: systemd-rpm-macros
BuildRequires: tar
BuildRequires: gzip
BuildRequires: pnpm
BuildRequires: nodejs22

Requires:          nodejs22
Requires:          pnpm
Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd

# Turn off debugging
%global debug_package %{nil}
# Turn off scanning node_modules for dependencies
%global __requires_exclude_from ^.*node_modules/.*$

# Tells RPM not to fail the build if it finds binaries in noarch packages
%global _binaries_in_noarch_packages_terminate_build 0

# Tells the shebang mangler script to skip files in node_modules
%global __brp_mangle_shebangs_exclude_from node_modules

%description
Seerr is a free and open source software application for managing requests for your media library. It integrates with the media server of your choice: Jellyfin, Plex, and Emby. In addition, it integrates with your existing services, such as Sonarr, Radarr.

%prep
%autosetup


%build
# Install pnpm locally, need to allow legacy deps
PATH=%{_builddir}/%{name}-%{version}/node_modules/.bin/:${PATH}

# Install packages
CYPRESS_INSTALL_BINARY=0 pnpm install --frozen-lockfile

# Compile everything
pnpm build

# Prune unneeded deps
pnpm prune --prod --ignore-scripts

# Clean out un-needed files
rm -rf ./src ./server ./.next/cache

# Create env file
echo PORT=5055 > ./seerr.conf
echo HOST=0.0.0.0 >> ./seerr.conf

# Create systemd file
cat <<EOT >> %{name}.service
[Unit]
Description=Seerr Service
Wants=network-online.target
After=network-online.target

[Service]
EnvironmentFile=%{_sysconfdir}/%{name}/seerr.conf
Environment=NODE_ENV=production
Type=exec
Restart=on-failure
WorkingDirectory=%{_datadir}/%{name}
ExecStart=/usr/bin/pnpm start

[Install]
WantedBy=multi-user.target
EOT

%install
rm -rf %{buildroot}

mkdir -m 755 -p %{buildroot}%{_datadir}/%{name}
mkdir -m 755 -p %{buildroot}%{_sysconfdir}/%{name}

# Install the config file where the systemd unit expects it
install -p -D -m 0644 seerr.conf %{buildroot}%{_sysconfdir}/%{name}/

# Install systemd unit file
install -p -D -m 0644 %{name}.service %{buildroot}%{_unitdir}/%{name}.service

mv package.json %{buildroot}%{_datadir}/%{name}/
mv pnpm-lock.yaml %{buildroot}%{_datadir}/%{name}/
mv *.js %{buildroot}%{_datadir}/%{name}/
mv *.ts %{buildroot}%{_datadir}/%{name}/
mv seerr-api.yml %{buildroot}%{_datadir}/%{name}/
mv node_modules %{buildroot}%{_datadir}/%{name}/
mv dist/ %{buildroot}%{_datadir}/%{name}/
mv public/ %{buildroot}%{_datadir}/%{name}/
mv .next/ %{buildroot}%{_datadir}/%{name}/

%post
%systemd_post seerr.service

%preun
%systemd_preun seerr.service


%postun
%systemd_postun_with_restart seerr.service

# TODO Get perms right
%files
%config(noreplace) %{_sysconfdir}/%{name}
%{_datadir}/%{name}
%{_unitdir}/%{name}.service


%changelog
%autochangelog
