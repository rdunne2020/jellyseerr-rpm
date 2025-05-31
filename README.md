# jellyseerr-rpm
Repo that contains the files to build a jellyseerr rpm. Only tested on fedora 38 and 41 so far

### [jellyseerr](https://github.com/Fallenbagel/jellyseerr)


## Steps to create RPM manually
### Necessary packages to install
    - rpmbuild
    - rpmdevtools
    - createrepo
    - rpm-devel
    - rpmlint
    - make
    - coreutils
    - gcc
    - dnf builddep plugin
        - This is installed with special syntax: `dnf install 'dnf-command(builddep)'`

- Use rpmdevtools binary `rpmdev-setuptree` to create the necessary format, this will default to ${HOME} on your machine
- Place your spec file in the *SPECS* folder in that created dir tree
- Use `rpmbuild` to create your rpm: `rpmbuild --define "_topdir /path/to/rpmbuild" -ba SPECS/jellyseer.spec`
- Once this finishes you will have an RPM you can place on a machine and install

## TODO:
- Put RPM in a repo
- Put a task in the Version Checker to create a new tag outside of the build script. This should prevent a double run.
