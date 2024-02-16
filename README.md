# jellyseerr-rpm
Repo that contains the files to build a jellyseerr rpm. Only tested on fedora 38 so far

### [jellyseer](https://github.com/Fallenbagel/jellyseerr)

## Necessary packages to install
- rpmbuild
- rpmdevtools
- dnf builddep plugin
    - This is installed with special syntax: `dnf install 'dnf-command(builddep)'`

## Steps to create RPM
- Use rpmdevtools binary `rpmdev-setuptree` to create the necessary format
- Place your spec file in the *SPECS* folder in that created dir tree
- Use `rpmbuild` to create your rpm: `rpmbuild --define "_topdir /path/to/rpmbuild" -ba SPECS/jellyseer.spec`
- Once this finishes you will have an RPM you can place on a machine and install

## TODO:
- Put RPM in a repo
- Create RPM in CI/CD
