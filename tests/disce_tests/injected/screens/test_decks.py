#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Sequence

import pytest
from disce.screens.decks import DecksScreen
from disce.storage.local import LocalStorage


class TestDecksScreen:
    @staticmethod
    @pytest.fixture
    def screen() -> DecksScreen:
        screen = DecksScreen(LocalStorage())
        screen.show()
        return screen

    @staticmethod
    def test_element(screen: DecksScreen) -> None:
        assert screen.element.id == "disce-decks-screen"

    @staticmethod
    def test_render(screen: DecksScreen) -> None:
        TestDecksScreen._assert_rendered_decks(screen, ["deck1_name", "deck2_name"])

    @staticmethod
    def _assert_rendered_decks(screen: DecksScreen, expected_deck_names: Sequence[str]) -> None:
        rows = screen.select_child(".disce-decks").children
        for row, expected_name in zip(rows, expected_deck_names, strict=True):
            assert row.querySelector(".disce-deck-name-label").innerText == expected_name

    @staticmethod
    def test_render_no_decks(screen: DecksScreen) -> None:
        LocalStorage().clear()
        screen.render()
        rows = screen.select_child(".disce-decks").children
        assert len(rows) == 1
        assert rows[0].innerText == "No decks available. Please add a deck."
