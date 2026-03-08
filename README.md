# jellyseerr-rpm
Repo that contains the files to build a jellyseerr rpm. 

## [seerr](https://github.com/seerr-team/seerr/tree/develop)

## Build RPM

> [!IMPORTANT]
> This build has only been tested for Fedora 42 and 43

### EarthBuild

This project leans heavily on EarthBuild. Follow the [install instructions](https://www.earthbuild.dev/install.html) to get it setup

### Building

Using EarthBuild in artifact mode you can generate an RPM that will be written locally with:

`earthly -a '+build-rpm/*.rpm' --FEDORA_VERSION=43`

You can pass either `42` or `43` to `FEDORA_VERSION`

### Testing

If you want to generate the RPM and then see what it built you can run:

`earthly -i +test-rpm --FEDORA_VERSION=43`

This will build the rpm, unwrap it, then drop you in a shell to mess with it.

## TODO:
- Put RPM in a repo
- Put a task in the Version Checker to create a new tag outside of the build script. This should prevent a double run.
