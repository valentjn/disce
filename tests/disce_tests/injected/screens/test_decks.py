#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Sequence
from unittest.mock import call, patch

import pytest
from disce.data import DeckData, DeckExport, DeckMetadata, ExportedDeck
from disce.pyscript import EventBinding
from disce.screens.decks import DecksScreen
from disce.screens.edit_deck import EditDeckScreen
from disce.storage.local import LocalStorage

from disce_tests.injected.screens.tools import assert_decks, assert_event_bindings_registered, create_decks
from disce_tests.injected.tools import assert_hidden, assert_visible


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
        row = screen.select_child(".disce-decks").children[0]
        assert_event_bindings_registered(
            [
                *screen.get_static_event_bindings(),
                EventBinding(row.querySelector(".disce-selected-checkbox"), "change", screen.update_bulk_buttons),
                EventBinding(row.querySelector(".disce-study-deck-btn"), "click", screen.study_deck),
                EventBinding(row.querySelector(".disce-edit-deck-btn"), "click", screen.edit_deck),
                EventBinding(row.querySelector(".disce-duplicate-deck-btn"), "click", screen.duplicate_deck),
                EventBinding(row.querySelector(".disce-delete-deck-btn"), "click", screen.delete_deck),
            ]
        )

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

    @staticmethod
    def test_add_deck(screen: DecksScreen) -> None:
        screen.add_deck()
        assert_hidden(screen)
        assert_visible(EditDeckScreen(None, LocalStorage()))

    @staticmethod
    @pytest.fixture
    def deck_export() -> DeckExport:
        deck_data_list, deck_metadata_list = create_decks("exported")
        return DeckExport(
            decks=[
                ExportedDeck(data=deck_data, metadata=deck_metadata)
                for deck_data, deck_metadata in zip(deck_data_list, deck_metadata_list, strict=True)
            ]
        )

    @staticmethod
    def test_import_decks(
        deck_data_list: list[DeckData],
        deck_metadata_list: list[DeckMetadata],
        screen: DecksScreen,
        deck_export: DeckExport,
    ) -> None:
        screen.import_decks()
        with patch(
            "disce.screens.decks.upload_file", side_effect=lambda _, listener: listener(deck_export.model_dump_json())
        ):
            screen.import_decks()
        TestDecksScreen._assert_rendered_decks(
            screen, ["deck1_name", "deck2_name", "exported_deck1_name", "exported_deck2_name"]
        )
        assert_decks(
            deck_data_list + [deck.data for deck in deck_export.decks],
            deck_metadata_list + [deck.metadata for deck in deck_export.decks],
        )

    @staticmethod
    def test_import_decks_invalid_json(screen: DecksScreen) -> None:
        with (
            patch(
                "disce.screens.decks.upload_file",
                side_effect=lambda _, listener: listener("invalid_json"),
            ),
            patch("disce.screens.decks.alert") as alert_mock,
        ):
            screen.import_decks()
        assert alert_mock.call_count == 1
        assert (
            alert_mock.call_args_list[0]
            .args[0]
            .startswith("Failed to parse imported data: 1 validation error for DeckExport\n")
        )

    @staticmethod
    def test_import_decks_overwrite_approved(
        deck_data_list: list[DeckData],
        deck_metadata_list: list[DeckMetadata],
        screen: DecksScreen,
        deck_export: DeckExport,
    ) -> None:
        deck_export.decks[0].data.uuid = "deck1"
        deck_export.decks[0].metadata.uuid = "deck1"
        with (
            patch(
                "disce.screens.decks.upload_file",
                side_effect=lambda _, listener: listener(deck_export.model_dump_json()),
            ),
            patch("disce.screens.decks.confirm", return_value=True) as confirm_mock,
        ):
            screen.import_decks()
        assert confirm_mock.call_args_list == [
            call(
                "The imported data contains 1 deck (see below) that will overwrite existing decks. Do you want to "
                'continue?\n\nName of deck to be overwritten: "deck1_name"'
            )
        ]
        TestDecksScreen._assert_rendered_decks(screen, ["deck2_name", "exported_deck1_name", "exported_deck2_name"])
        assert_decks(
            deck_data_list[1:] + [deck.data for deck in deck_export.decks],
            deck_metadata_list[1:] + [deck.metadata for deck in deck_export.decks],
        )

    @staticmethod
    def test_import_decks_overwrite_declined(
        deck_data_list: list[DeckData],
        deck_metadata_list: list[DeckMetadata],
        screen: DecksScreen,
        deck_export: DeckExport,
    ) -> None:
        deck_export.decks[0].data.uuid = "deck1"
        deck_export.decks[0].metadata.uuid = "deck1"
        with (
            patch(
                "disce.screens.decks.upload_file",
                side_effect=lambda _, listener: listener(deck_export.model_dump_json()),
            ),
            patch("disce.screens.decks.confirm", return_value=False),
        ):
            screen.import_decks()
        TestDecksScreen._assert_rendered_decks(screen, ["deck1_name", "deck2_name"])
        assert_decks(deck_data_list, deck_metadata_list)
