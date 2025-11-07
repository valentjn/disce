#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Sequence
from types import SimpleNamespace
from unittest.mock import ANY, call, patch

import pytest
from disce.data import Configuration, DeckData, DeckExport, DeckMetadata, ExportedDeck
from disce.pyscript import EventBinding
from disce.screens.decks import DecksScreen
from disce.screens.edit_deck import EditDeckScreen
from disce.screens.study import StudyScreen
from disce.storage.base import AbstractStorage

from disce_tests.injected.screens.tools import assert_decks, assert_event_bindings_registered, create_decks
from disce_tests.injected.tools import assert_hidden, assert_visible


class TestDecksScreen:
    @staticmethod
    @pytest.fixture
    def screen(storage: AbstractStorage) -> DecksScreen:
        screen = DecksScreen(storage)
        screen.show()
        return screen

    @staticmethod
    def test_element(screen: DecksScreen) -> None:
        assert screen.element.id == "disce-decks-screen"

    @staticmethod
    def test_render(screen: DecksScreen) -> None:
        TestDecksScreen._assert_rendered_decks(screen, ["deck1_name", "deck2_name"])
        element = screen.select_child(".disce-decks").children[0]
        assert_event_bindings_registered(
            [
                *screen.get_static_event_bindings(),
                EventBinding(element.querySelector(".disce-selected-checkbox"), "change", screen.update_bulk_buttons),
                EventBinding(element.querySelector(".disce-study-deck-btn"), "click", screen.study_deck),
                EventBinding(element.querySelector(".disce-edit-deck-btn"), "click", screen.edit_deck),
                EventBinding(element.querySelector(".disce-duplicate-deck-btn"), "click", screen.duplicate_deck),
                EventBinding(element.querySelector(".disce-delete-deck-btn"), "click", screen.delete_deck),
            ]
        )

    @staticmethod
    def _assert_rendered_decks(screen: DecksScreen, expected_deck_names: Sequence[str]) -> None:
        rows = screen.select_child(".disce-decks").children
        for row, expected_name in zip(rows, expected_deck_names, strict=True):
            assert row.querySelector(".disce-deck-name-label").innerText == expected_name

    @staticmethod
    def test_render_no_decks(storage: AbstractStorage, screen: DecksScreen) -> None:
        storage.clear()
        screen.render()
        rows = screen.select_child(".disce-decks").children
        assert len(rows) == 1
        assert rows[0].innerText == "No decks available. Please add a deck."

    @staticmethod
    def test_add_deck(storage: AbstractStorage, screen: DecksScreen) -> None:
        screen.add_deck()
        assert_hidden(screen)
        assert_visible(EditDeckScreen(None, storage))

    @staticmethod
    @pytest.fixture
    def deck_export() -> DeckExport:
        deck_data_list, deck_metadata_list = create_decks("exported")
        return DeckExport(
            decks=[
                ExportedDeck.from_deck(deck_data, deck_metadata)
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
            deck_data_list + [deck.to_deck_data() for deck in deck_export.decks],
            deck_metadata_list + [deck.to_deck_metadata() for deck in deck_export.decks],
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
        deck_export.decks[0].uuid = "deck1"
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
            deck_data_list[1:] + [deck.to_deck_data() for deck in deck_export.decks],
            deck_metadata_list[1:] + [deck.to_deck_metadata() for deck in deck_export.decks],
        )

    @staticmethod
    def test_import_decks_overwrite_declined(
        deck_data_list: list[DeckData],
        deck_metadata_list: list[DeckMetadata],
        screen: DecksScreen,
        deck_export: DeckExport,
    ) -> None:
        deck_export.decks[0].uuid = "deck1"
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

    @staticmethod
    def test_select_all_decks(screen: DecksScreen) -> None:
        screen.select_child(".disce-selected-checkbox").checked = True
        screen.select_all_decks()
        for checkbox in screen.select_all_children(".disce-selected-checkbox"):
            assert checkbox.checked

    @staticmethod
    def test_select_all_decks_deselect(screen: DecksScreen) -> None:
        screen.select_all_decks()
        screen.select_all_decks()
        for checkbox in screen.select_all_children(".disce-selected-checkbox"):
            assert not checkbox.checked

    @staticmethod
    def test_study_decks(storage: AbstractStorage, screen: DecksScreen) -> None:
        screen.select_child(".disce-selected-checkbox").checked = True
        screen.study_decks()
        assert_hidden(screen)
        assert_visible(StudyScreen(["deck1"], storage))

    @staticmethod
    def test_merge_decks(storage: AbstractStorage, screen: DecksScreen) -> None:
        screen.select_all_decks()
        with patch("disce.screens.decks.prompt", return_value="merged_deck_name") as prompt_mock:
            screen.merge_decks()
        assert prompt_mock.call_args_list == [call("Enter a name for the merged deck:", "Merge Decks")]
        TestDecksScreen._assert_rendered_decks(screen, ["deck1_name", "deck2_name", "merged_deck_name"])
        TestDecksScreen._assert_texts_of_deck(
            storage,
            "merged_deck_name",
            {"deck1_card1_front", "deck1_card2_front", "deck2_card1_front"},
            {"deck1_card1_back", "deck1_card2_back", "deck2_card1_back"},
        )

    @staticmethod
    def _assert_texts_of_deck(
        storage: AbstractStorage, deck_name: str, expected_front_texts: set[str], expected_back_texts: set[str]
    ) -> None:
        configuration = Configuration.load_from_storage(storage)
        deck_metadata = next(
            deck_metadata for deck_metadata in configuration.deck_metadata if deck_metadata.name == deck_name
        )
        deck_data = DeckData.load_from_storage(storage, deck_metadata.uuid)
        assert {card.front for card in deck_data.cards} == expected_front_texts
        assert {card.back for card in deck_data.cards} == expected_back_texts

    @staticmethod
    def test_merge_decks_canceled(
        deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata], screen: DecksScreen
    ) -> None:
        screen.select_all_decks()
        with patch("disce.screens.decks.prompt", return_value=None):
            screen.merge_decks()
        TestDecksScreen._assert_rendered_decks(screen, ["deck1_name", "deck2_name"])
        assert_decks(deck_data_list, deck_metadata_list)

    @staticmethod
    def test_merge_decks_none_selected(screen: DecksScreen) -> None:
        with patch("disce.screens.decks.alert") as alert_mock:
            screen.merge_decks()
        assert alert_mock.call_args_list == [call("Please select at least 2 decks to merge.")]

    @staticmethod
    def test_export_decks(
        deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata], screen: DecksScreen
    ) -> None:
        screen.select_all_decks()
        with patch("disce.screens.decks.download_file") as download_file_mock:
            screen.export_decks()
        download_file_mock.assert_called_once()
        filename, type_, content = download_file_mock.call_args_list[0].args
        assert filename == "decks.json"
        assert type_ == "application/json"
        deck_export = DeckExport.model_validate_json(content)
        assert [deck.to_deck_data() for deck in deck_export.decks] == deck_data_list
        assert [deck.to_deck_metadata() for deck in deck_export.decks] == deck_metadata_list

    @staticmethod
    def test_export_deck_single_deck(screen: DecksScreen) -> None:
        screen.select_child(".disce-selected-checkbox").checked = True
        with patch("disce.screens.decks.download_file") as download_file_mock:
            screen.export_decks()
        assert download_file_mock.call_args_list == [call("deck1-name.json", "application/json", ANY)]

    @staticmethod
    def test_export_deck_single_deck_invalid_name(storage: AbstractStorage, screen: DecksScreen) -> None:
        configuration = Configuration.load_from_storage_or_create(storage)
        configuration.deck_metadata["deck1"].name = "???"
        configuration.save_to_storage(storage)
        screen.select_child(".disce-selected-checkbox").checked = True
        with patch("disce.screens.decks.download_file") as download_file_mock:
            screen.export_decks()
        assert download_file_mock.call_args_list == [call("deck.json", "application/json", ANY)]

    @staticmethod
    def test_export_decks_none_selected(screen: DecksScreen) -> None:
        with patch("disce.screens.decks.alert") as alert_mock:
            screen.export_decks()
        assert alert_mock.call_args_list == [call("Please select at least one deck to export.")]

    @staticmethod
    def test_delete_decks(
        deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata], screen: DecksScreen
    ) -> None:
        screen.select_child(".disce-selected-checkbox").checked = True
        with patch("disce.screens.decks.confirm", return_value=True) as confirm_mock:
            screen.delete_decks()
        assert confirm_mock.call_args_list == [call("Are you sure you want to delete the selected 1 deck?")]
        TestDecksScreen._assert_rendered_decks(screen, ["deck2_name"])
        assert_decks(deck_data_list[1:], deck_metadata_list[1:])

    @staticmethod
    def test_delete_decks_canceled(
        deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata], screen: DecksScreen
    ) -> None:
        screen.select_child(".disce-selected-checkbox").checked = True
        with patch("disce.screens.decks.confirm", return_value=False):
            screen.delete_decks()
        TestDecksScreen._assert_rendered_decks(screen, ["deck1_name", "deck2_name"])
        assert_decks(deck_data_list, deck_metadata_list)

    @staticmethod
    def test_delete_decks_none_selected(screen: DecksScreen) -> None:
        with patch("disce.screens.decks.alert") as alert_mock:
            screen.delete_decks()
        assert alert_mock.call_args_list == [call("Please select at least one deck to delete.")]

    @staticmethod
    @pytest.mark.parametrize("number_of_selected_decks", [0, 1, 2])
    def test_update_bulk_buttons(screen: DecksScreen, number_of_selected_decks: int) -> None:
        for idx, checkbox in enumerate(screen.select_all_children(".disce-selected-checkbox")):
            checkbox.checked = idx < number_of_selected_decks
        screen.update_bulk_buttons()
        assert screen.select_child(".disce-select-all-btn").title == (
            "Deselect all" if number_of_selected_decks == 2 else "Select all"
        )
        assert screen.select_child(".disce-select-all-btn .disce-btn-text").innerText == (
            " Deselect All" if number_of_selected_decks == 2 else " Select All"
        )
        assert screen.select_child(".disce-study-decks-btn").disabled == (number_of_selected_decks == 0)
        assert screen.select_child(".disce-merge-decks-btn").disabled == (number_of_selected_decks < 2)
        assert screen.select_child(".disce-export-decks-btn").disabled == (number_of_selected_decks == 0)
        assert screen.select_child(".disce-delete-decks-btn").disabled == (number_of_selected_decks == 0)

    @staticmethod
    def test_study_deck(storage: AbstractStorage, screen: DecksScreen) -> None:
        screen.study_deck(SimpleNamespace(currentTarget=screen.select_child(".disce-study-deck-btn")))
        assert_hidden(screen)
        assert_visible(StudyScreen(["deck1"], storage))

    @staticmethod
    def test_edit_deck(storage: AbstractStorage, screen: DecksScreen) -> None:
        screen.edit_deck(SimpleNamespace(currentTarget=screen.select_child(".disce-edit-deck-btn")))
        assert_hidden(screen)
        assert_visible(EditDeckScreen("deck1", storage))

    @staticmethod
    def test_duplicate_deck(storage: AbstractStorage, screen: DecksScreen) -> None:
        with patch("disce.screens.decks.prompt", return_value="deck1_copy_name") as prompt_mock:
            screen.duplicate_deck(SimpleNamespace(currentTarget=screen.select_child(".disce-duplicate-deck-btn")))
        assert prompt_mock.call_args_list == [call("Enter a name for the duplicated deck:", "Copy of deck1_name")]
        TestDecksScreen._assert_rendered_decks(screen, ["deck1_copy_name", "deck1_name", "deck2_name"])
        TestDecksScreen._assert_texts_of_deck(
            storage,
            "deck1_copy_name",
            {"deck1_card1_front", "deck1_card2_front"},
            {"deck1_card1_back", "deck1_card2_back"},
        )

    @staticmethod
    def test_duplicate_deck_canceled(
        deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata], screen: DecksScreen
    ) -> None:
        with patch("disce.screens.decks.prompt", return_value=None):
            screen.duplicate_deck(SimpleNamespace(currentTarget=screen.select_child(".disce-duplicate-deck-btn")))
        TestDecksScreen._assert_rendered_decks(screen, ["deck1_name", "deck2_name"])
        assert_decks(deck_data_list, deck_metadata_list)

    @staticmethod
    def test_delete_deck(
        deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata], screen: DecksScreen
    ) -> None:
        with patch("disce.screens.decks.confirm", return_value=True) as confirm_mock:
            screen.delete_deck(SimpleNamespace(currentTarget=screen.select_child(".disce-delete-deck-btn")))
        assert confirm_mock.call_args_list == [call('Are you sure you want to delete the deck "deck1_name"?')]
        TestDecksScreen._assert_rendered_decks(screen, ["deck2_name"])
        assert_decks(deck_data_list[1:], deck_metadata_list[1:])

    @staticmethod
    def test_delete_deck_canceled(
        deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata], screen: DecksScreen
    ) -> None:
        with patch("disce.screens.decks.confirm", return_value=False):
            screen.delete_deck(SimpleNamespace(currentTarget=screen.select_child(".disce-delete-deck-btn")))
        TestDecksScreen._assert_rendered_decks(screen, ["deck1_name", "deck2_name"])
        assert_decks(deck_data_list, deck_metadata_list)

    @staticmethod
    def test_open_settings_modal(storage: AbstractStorage, screen: DecksScreen) -> None:
        with patch("disce.screens.decks.show_modal") as show_modal_mock:
            screen.open_settings_modal()
        assert show_modal_mock.call_args_list == [call(screen.select_child(".disce-settings-modal"))]
        configuration = Configuration.load_from_storage_or_create(storage)
        assert screen.select_child(".disce-history-length-input").value == str(configuration.history_length)
        assert screen.select_child(".disce-typewriter-mode-checkbox").checked == configuration.typewriter_mode

    @staticmethod
    def test_save_settings(storage: AbstractStorage, screen: DecksScreen) -> None:
        screen.select_child(".disce-history-length-input").value = "5"
        screen.select_child(".disce-typewriter-mode-checkbox").checked = True
        screen.save_settings()
        configuration = Configuration.load_from_storage(storage)
        assert configuration.history_length == 5
        assert configuration.typewriter_mode

    @staticmethod
    def test_get_deck_uuids(screen: DecksScreen) -> None:
        assert screen.get_deck_uuids() == ["deck1", "deck2"]

    @staticmethod
    def test_get_selected_deck_uuids(screen: DecksScreen) -> None:
        screen.select_child(".disce-selected-checkbox").checked = True
        assert screen.get_selected_deck_uuids() == ["deck1"]
