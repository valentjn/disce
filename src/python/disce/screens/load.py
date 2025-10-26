#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Loading screen."""

from typing import override

from disce.pyscript import EventBinding
from disce.screens.base import AbstractScreen


class LoadScreen(AbstractScreen):
    """Loading screen."""

    def __init__(self) -> None:
        """Initialize the screen."""
        super().__init__("#disce-load-screen")

    @override
    def _get_static_event_bindings(self) -> list[EventBinding]:
        return []

    @override
    def render(self) -> None:
        pass
