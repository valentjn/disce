#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for loading."""

from disce.screens.tools import select_element


def hide() -> None:
    """Hide the loading screen."""
    select_element("#loading-screen").style.display = "none"
