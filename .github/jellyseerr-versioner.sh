#!/bin/bash

# Get the most recent version
SEERR_CURRENT_VERSION=$(curl https://github.com/seerr-team/seerr/releases 2>/dev/null | grep -Eo "Link--primary Link.*span>" | grep -m 1 -Eo "[0-9]+\.[0-9]+\.[0-9]+")
if [[ $? -gt 0 ]]; then
    echo "FATAL: Could not get version number from seerr releases"
    exit 100
fi

SEERR_RPM_VERSION=$(grep "Version:" seerr.spec | awk '{print $2}')

# The version's don't match, kick off the update
if [[ ${SEERR_RPM_VERSION} != ${SEERR_CURRENT_VERSION} ]]; then
    sed -i "s/^\(Version:\s*\)[^\s]*$/\1${SEERR_CURRENT_VERSION}/" seerr.spec
    git add jellyseerr.spec
    git commit -m "chore: update version number to ${SEERR_CURRENT_VERSION} to match upstream"
    git push origin main
    exit 0
else
    echo "INFO: seerr-rpm is up to date!"
    exit 0
fi
