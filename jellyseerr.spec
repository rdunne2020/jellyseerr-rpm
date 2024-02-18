Name:       jellyseerr
Version:    1.8.0
Release:    %autorelease
Summary:    Fork of overseerr for jellyfin support

License:    MIT
URL:        https://github.com/Fallenbagel/jellyseerr
Source:     https://github.com/Fallenbagel/jellyseerr/archive/refs/tags/v1.7.0.tar.gz

# Use this to make sure the necessary macros are available like _unitdir
BuildRequires: systemd
BuildRequires: systemd-rpm-macros
BuildRequires: tar
BuildRequires: gzip
BuildRequires: nodejs

Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd

# Turn off debugging
%global debug_package %{nil}
# Turn off scanning node_modules for dependencies
%global __requires_exclude_from ^.*node_modules/.*$

%description
Jellyseerr is a free and open source software application for managing requests for your media library. It is a a fork of Overseerr built to bring support for Jellyfin & Emby media servers!


%prep
%autosetup


%build
# Install yarn locally, need to allow legacy deps
npm i -S --legacy-peer-deps  yarn
PATH=%{_builddir}/%{name}-%{version}/node_modules/.bin/:${PATH}

# Install packages
CYPRESS_INSTALL_BINARY=0 yarn install --frozen-lockfile --network-timeout 1000000

# Compile everything
yarn run build

# Turn node_modules into just prod deps
yarn install --production --ignore-scripts --prefer-offline

# Clean out un-needed files
rm -rf ./src ./server ./.next/cache

# Create env file
echo PORT=5055 > ./jellyseerr.conf
echo HOST=127.0.0.1 >> ./jellyseerr.conf

# Create systemd file
cat <<EOT >> %{name}.service
[Unit]
Description=Jellyseerr Service
Wants=network-online.target
After=network-online.target

[Service]
EnvironmentFile=%{_sysconfdir}/%{name}/jellyseerr.conf
Environment=NODE_ENV=production
Type=exec
Restart=on-failure
WorkingDirectory=%{_datadir}/%{name}
ExecStart=/usr/bin/node dist/index.js

[Install]
WantedBy=multi-user.target
EOT

%install
rm -rf %{buildroot}

mkdir -m 755 -p %{buildroot}%{_datadir}/%{name}
mkdir -m 755 -p %{buildroot}%{_sysconfdir}/%{name}

# Install the config file where the systemd unit expects it
install -p -D -m 0644 jellyseerr.conf %{buildroot}%{_sysconfdir}/%{name}/

# Install systemd unit file
install -p -D -m 0644 %{name}.service %{buildroot}%{_unitdir}/%{name}.service

mv package.json %{buildroot}%{_datadir}/%{name}/
mv package-lock.json %{buildroot}%{_datadir}/%{name}/
mv *.js %{buildroot}%{_datadir}/%{name}/
mv *.ts %{buildroot}%{_datadir}/%{name}/
mv overseerr-api.yml %{buildroot}%{_datadir}/%{name}/
mv node_modules %{buildroot}%{_datadir}/%{name}/
mv dist/ %{buildroot}%{_datadir}/%{name}/
mv public/ %{buildroot}%{_datadir}/%{name}/
mv .next/ %{buildroot}%{_datadir}/%{name}/

%post
%systemd_post jellyseerr.service

%preun
%systemd_preun jellyseerr.service


%postun
%systemd_postun_with_restart jellyseerr.service

# TODO Get perms right
%files
%config(noreplace) %{_sysconfdir}/%{name}
%{_datadir}/%{name}
%{_unitdir}/%{name}.service


%changelog
%autochangelog

