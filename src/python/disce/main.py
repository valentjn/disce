#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Main module."""

import logging

# import all screens to register event handlers
from disce.screens import *  # noqa: F403  # isort: skip

from disce import tools
from disce.screens import load as load_screen
from disce.screens import main as main_screen

_logger = logging.getLogger(__name__)


def main() -> None:
    """Run the main application logic."""
    tools.set_up_logging()
    _logger.info("application started")
    main_screen.show()
    load_screen.hide()
