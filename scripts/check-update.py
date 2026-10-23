#!/usr/bin/env python3
"""Update the RPM version from GitHub's latest stable release API."""
import argparse
import json
import os
from pathlib import Path
import re
import urllib.request

VERSION = re.compile(r"^(Version:\s*)(\d+\.\d+\.\d+)([ \t]*)$", re.MULTILINE)


def update_spec(spec, release):
    tag = release.get("tag_name", "")
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Expected a stable, published release")
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("Expected a stable vMAJOR.MINOR.PATCH tag")
    matches = list(VERSION.finditer(spec))
    if len(matches) != 1:
        raise ValueError("Expected exactly one numeric Version field")
    current = matches[0].group(2)
    version = tag[1:]
    if tuple(map(int, version.split('.'))) <= tuple(map(int, current.split('.'))):
        return spec, None
    updated = VERSION.sub(lambda m: m.group(1) + version + m.group(3), spec)
    updated, count = re.subn(r"^Release:.*$", "Release:        1%{?dist}", updated, flags=re.MULTILINE)
    if count != 1:
        raise ValueError("Expected exactly one Release field")
    return updated, version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=Path("seerr.spec"))
    parser.add_argument("--release-json", type=Path, help="Use an offline API response")
    args = parser.parse_args()
    if args.release_json:
        release = json.loads(args.release_json.read_text())
    else:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "seerr-rpm"}
        if os.environ.get("GH_TOKEN"):
            headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
        request = urllib.request.Request(
            "https://api.github.com/repos/seerr-team/seerr/releases/latest", headers=headers
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
    updated, version = update_spec(args.spec.read_text(), release)
    if version:
        args.spec.write_text(updated)
        print(f"Updated Seerr to {version}")
    else:
        print("Seerr is up to date")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"version={version or ''}\n")


if __name__ == "__main__":
    main()
