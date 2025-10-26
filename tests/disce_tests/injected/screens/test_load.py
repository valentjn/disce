#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from disce.screens.load import LoadScreen


class TestLoadScreen:
    @staticmethod
    @pytest.fixture
    def screen() -> LoadScreen:
        return LoadScreen()

    @staticmethod
    def test_element(screen: LoadScreen) -> None:
        assert screen.element.id == "disce-load-screen"

    @staticmethod
    def test_get_static_event_listeners(screen: LoadScreen) -> None:
        assert screen.get_static_event_bindings() == []

    @staticmethod
    def test_render(screen: LoadScreen) -> None:
        screen.render()
