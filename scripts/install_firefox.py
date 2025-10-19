#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Install Firefox if not already installed.

Requires APT and root privileges.
"""

import argparse
import logging
import urllib.request
from pathlib import Path
from shutil import which
from subprocess import run
from textwrap import dedent

_logger = logging.getLogger(__name__)


def main() -> None:
    """Make sure pyscript.toml is up to date."""
    parse_arguments()
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    install_firefox()


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def install_firefox() -> None:
    """Install Firefox if not already installed."""
    if which("firefox") is not None:
        _logger.info("Firefox is already installed.")
        return
    with urllib.request.urlopen("https://packages.mozilla.org/apt/repo-signing-key.gpg") as response:
        keyring = response.read()
    keyring_path = Path("/etc/apt/keyrings/packages.mozilla.org.asc")
    keyring_path.parent.mkdir(parents=True, exist_ok=True)
    keyring_path.write_bytes(keyring)
    Path("/etc/apt/sources.list.d/mozilla.sources").write_text(
        dedent("""\
            Types: deb
            URIs: https://packages.mozilla.org/apt
            Suites: mozilla
            Components: main
            Signed-By: /etc/apt/keyrings/packages.mozilla.org.asc
        """),
    )
    Path("/etc/apt/preferences.d/mozilla").write_text(
        dedent("""\
            Package: *
            Pin: origin packages.mozilla.org
            Pin-Priority: 1000
        """),
    )
    run(["apt-get", "update"], check=True)
    run(["apt-get", "install", "--no-install-recommends", "--yes", "firefox"], check=True)


if __name__ == "__main__":
    main()
