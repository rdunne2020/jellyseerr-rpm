Name:       seerr
Version:    2.7.3
Release:    %autorelease
Summary:    Fork of overseerr for jellyfin support

License:    MIT
URL:        https://github.com/seerr-team/seerr
Source:     https://github.com/seerr-team/seerr/archive/refs/tags/v%{version}.tar.gz

# Use this to make sure the necessary macros are available like _unitdir
BuildRequires: systemd
BuildRequires: systemd-rpm-macros
BuildRequires: tar
BuildRequires: gzip

Requires(post):    systemd
Requires(post):    pnpm
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
Seerr is a free and open source software application for managing requests for your media library. It is a a fork of Overseerr built to bring support for Jellyfin & Emby media servers!


%prep
%autosetup


%build
# Install pnpm locally, need to allow legacy deps
npm i --global pnpm@9.15.9
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
ExecStart=pnpm start

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
mv pnpm-lock.yaml %{buildroot}%{_datadir}/%{name}/
mv *.js %{buildroot}%{_datadir}/%{name}/
mv *.ts %{buildroot}%{_datadir}/%{name}/
mv seerr-api.yml %{buildroot}%{_datadir}/%{name}/
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

