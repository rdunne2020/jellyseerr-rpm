#!/bin/bash

# Get the most recent version
JELLYSEERR_CURRENT_VERSION=$(curl https://github.com/Fallenbagel/jellyseerr/releases 2>/dev/null | grep -Eo "Link--primary Link.*span>" | grep -m 1 -Eo "[0-9]+\.[0-9]+\.[0-9]+")
if [[ $? -gt 0 ]]; then
    echo "FATAL: Could not get version number from jellyseerr releases"
    exit 100
fi

# Now we need to clone down the jellyseerr-rpm repo and compare version number in the spec file

JELLYSEERR_RPM_VERSION=$(grep "Version:" jellyseerr.spec | awk '{print $2}')

#DEBUG
echo "RPM_VER: $JELLYSEERR_RPM_VERSION"
echo "SOFTWARE_VER: $JELLYSEERR_CURRENT_VERSION"

# The version's don't match, kick off the update
#****I HAVE ADDED A TEST BY SETTING THESE TO == and hard coding 1.8.0 to version num. REVERT TO COMMENTED OUT LINES
#if [[ ${JELLYSEERR_RPM_VERSION} != ${JELLYSEERR_CURRENT_VERSION} ]]; then
if [[ ${JELLYSEERR_RPM_VERSION} == ${JELLYSEERR_CURRENT_VERSION} ]]; then
    #sed -i 's/^\(Version:\s*\)[^\s]*$/\1${JELLYSEERR_CURRENT_VERSION}/' jellyseerr.spec
    sed -i 's/^\(Version:\s*\)[^\s]*$/\11.8.0/' jellyseerr.spec
    git add jellyseerr.spec
    git commit -m "Updated version number to ${JELLYSEERR_CURRENT_VERSION} to match codebase"
    git push origin main
    exit 0
else
    echo "INFO: jellyseerr-rpm is up to date!"
    exit 0
fi
