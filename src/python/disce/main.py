#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Main module."""

from disce.screens import edit_decks as edit_decks_screen  # noqa: F401
from disce.screens import load as load_screen
from disce.screens import main as main_screen


def main() -> None:
    """Run the main application logic."""
    main_screen.show()
    load_screen.hide()
