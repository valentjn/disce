#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import ANY, call, patch

import pytest
from disce.data import UUID, Card, Configuration, DeckData, DeckMetadata
from disce.pyscript import Element, EventBinding
from disce.screens.decks import DecksScreen
from disce.screens.edit_deck import EditDeckScreen
from disce.storage.base import AbstractStorage

from disce_tests.injected.screens.tools import assert_event_bindings_registered
from disce_tests.injected.tools import assert_hidden, assert_visible


class TestEditDeckScreen:
    @staticmethod
    @pytest.fixture
    def screen(storage: AbstractStorage) -> EditDeckScreen:
        screen = EditDeckScreen("deck1", storage)
        screen.show()
        return screen

    @staticmethod
    @pytest.fixture
    def empty_card() -> Card:
        card = Card()
        card.uuid = ANY
        return card

    @staticmethod
    def test_element(screen: EditDeckScreen) -> None:
        assert screen.element.id == "disce-edit-deck-screen"

    @staticmethod
    def test_render(
        screen: EditDeckScreen, deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata], empty_card: Card
    ) -> None:
        assert screen.select_child(".disce-deck-name-textbox").value == deck_metadata_list[0].name
        cards_element = screen.select_child(".disce-cards")
        assert len(cards_element.children) == 3
        TestEditDeckScreen._assert_card_div(cards_element.children[0], deck_data_list[0].cards["deck1_card1"])
        TestEditDeckScreen._assert_card_div(cards_element.children[1], deck_data_list[0].cards["deck1_card2"])
        TestEditDeckScreen._assert_card_div(cards_element.children[2], empty_card)
        element = cards_element.children[0]
        assert_event_bindings_registered(
            [
                *screen.get_static_event_bindings(),
                EventBinding(element.querySelector(".disce-selected-checkbox"), "change", screen.update_bulk_buttons),
                EventBinding(element.querySelector(".disce-front-textbox"), "input", screen.card_text_changed),
                EventBinding(element.querySelector(".disce-back-textbox"), "input", screen.card_text_changed),
            ]
        )

    @staticmethod
    def test_create_card_div(screen: EditDeckScreen) -> None:
        card = Card(
            uuid="uuid",
            front="front",
            back="back",
            enabled=False,
            front_answer_history=[True],
            back_answer_history=[False],
        )
        card_div = screen.create_card_div(card)
        TestEditDeckScreen._assert_card_div(card_div, card)

    @staticmethod
    def _assert_card_div(card_div: Element, expected_card: Card) -> None:
        assert card_div.getAttribute("data-card-uuid") == expected_card.uuid
        TestEditDeckScreen._get_card_div_child(card_div, ".disce-selected-checkbox", expected_card.uuid)
        assert (
            TestEditDeckScreen._get_card_div_child(card_div, ".disce-front-textbox", expected_card.uuid).value
            == expected_card.front
        )
        assert (
            TestEditDeckScreen._get_card_div_child(card_div, ".disce-back-textbox", expected_card.uuid).value
            == expected_card.back
        )
        assert (
            TestEditDeckScreen._get_card_div_child(card_div, ".disce-enabled-checkbox", expected_card.uuid).checked
            == expected_card.enabled
        )
        assert TestEditDeckScreen._get_card_div_child(
            card_div, ".disce-front-answer-history-hidden", expected_card.uuid
        ).value == "".join("Y" if correct else "N" for correct in expected_card.front_answer_history)
        assert TestEditDeckScreen._get_card_div_child(
            card_div, ".disce-back-answer-history-hidden", expected_card.uuid
        ).value == "".join("Y" if correct else "N" for correct in expected_card.back_answer_history)

    @staticmethod
    def _get_card_div_child(card_div: Element, selector: str, expected_card_uuid: UUID) -> Element:
        element = card_div.querySelector(selector)
        assert element.getAttribute("data-card-uuid") == expected_card_uuid
        return element

    @staticmethod
    def test_card_text_changed(screen: EditDeckScreen) -> None:
        cards_div = screen.select_child(".disce-cards")
        cards_div.children[-1].querySelector(".disce-front-textbox").value = "front"
        screen.card_text_changed()
        assert len(cards_div.children) == 4
        cards_div.children[-1].querySelector(".disce-back-textbox").value = "back"
        screen.card_text_changed()
        assert len(cards_div.children) == 5

    @staticmethod
    def test_save_deck(
        storage: AbstractStorage,
        screen: EditDeckScreen,
        deck_data_list: list[DeckData],
        deck_metadata_list: list[DeckMetadata],
    ) -> None:
        screen.select_child(".disce-deck-name-textbox").value = "deck1_name_modified"
        cards_div = screen.select_child(".disce-cards")
        cards_div.children[0].querySelector(".disce-front-textbox").value = "deck1_card1_front_modified"
        cards_div.children[-1].querySelector(".disce-front-textbox").value = "new_card_front"
        cards_div.children[-1].querySelector(".disce-back-textbox").value = "new_card_back"
        screen.card_text_changed()
        with patch("disce.screens.edit_deck.show_toast") as show_toast_mock:
            screen.save_deck()
        assert show_toast_mock.call_args_list == [call(screen.select_child(".disce-deck-saved-toast"))]
        configuration = Configuration.load_from_storage(storage)
        assert len(configuration.deck_metadata) == 2
        assert configuration.deck_metadata["deck1"] == deck_metadata_list[0].model_copy(
            update={"name": "deck1_name_modified", "number_of_cards": 3}
        )
        deck_data = DeckData.load_from_storage(storage, "deck1")
        assert len(deck_data.cards) == 3
        assert deck_data.cards["deck1_card1"] == deck_data_list[0].cards["deck1_card1"].model_copy(
            update={"front": "deck1_card1_front_modified", "front_answer_history": [], "back_answer_history": []}
        )
        assert deck_data.cards["deck1_card2"] == deck_data_list[0].cards["deck1_card2"]
        new_card_uuid = next(
            uuid for card in deck_data.cards if (uuid := card.uuid) not in {"deck1_card1", "deck1_card2"}
        )
        assert deck_data.cards[new_card_uuid] == Card(
            uuid=new_card_uuid,
            front="new_card_front",
            back="new_card_back",
            enabled=True,
            front_answer_history=[],
            back_answer_history=[],
        )

    @staticmethod
    def test_select_all_decks(screen: EditDeckScreen) -> None:
        screen.select_child(".disce-selected-checkbox").checked = True
        screen.select_all_decks()
        for checkbox in screen.select_all_children(".disce-selected-checkbox"):
            assert checkbox.checked

    @staticmethod
    def test_select_all_decks_deselect(screen: EditDeckScreen) -> None:
        screen.select_all_decks()
        screen.select_all_decks()
        for checkbox in screen.select_all_children(".disce-selected-checkbox"):
            assert not checkbox.checked

    @staticmethod
    def test_delete_cards(screen: EditDeckScreen) -> None:
        cards_div = screen.select_child(".disce-cards")
        empty_card_uuid = cards_div.children[2].getAttribute("data-card-uuid")
        cards_div.children[0].querySelector(".disce-selected-checkbox").checked = True
        cards_div.children[2].querySelector(".disce-selected-checkbox").checked = True
        with patch("disce.screens.edit_deck.confirm", return_value=True) as confirm_mock:
            screen.delete_cards()
        assert confirm_mock.call_args_list == [call("Are you sure you want to delete the selected 1 card?")]
        new_card_uuids = TestEditDeckScreen._get_card_uuids(screen)
        assert len(new_card_uuids) == 2
        assert "deck1_card1" not in new_card_uuids
        assert "deck1_card2" in new_card_uuids
        assert empty_card_uuid not in new_card_uuids

    @staticmethod
    def test_delete_cards_canceled(screen: EditDeckScreen) -> None:
        screen.select_child(".disce-selected-checkbox").checked = True
        old_card_uuids = TestEditDeckScreen._get_card_uuids(screen)
        with patch("disce.screens.edit_deck.confirm", return_value=False) as confirm_mock:
            screen.delete_cards()
        assert confirm_mock.call_args_list == [call("Are you sure you want to delete the selected 1 card?")]
        assert TestEditDeckScreen._get_card_uuids(screen) == old_card_uuids

    @staticmethod
    def test_delete_cards_none_selected(screen: EditDeckScreen) -> None:
        old_card_uuids = TestEditDeckScreen._get_card_uuids(screen)
        with patch("disce.screens.edit_deck.confirm") as confirm_mock:
            screen.delete_cards()
        assert confirm_mock.call_args_list == []
        assert TestEditDeckScreen._get_card_uuids(screen) == old_card_uuids

    @staticmethod
    def _get_card_uuids(screen: EditDeckScreen) -> list[UUID]:
        cards_div = screen.select_child(".disce-cards")
        return [card_div.getAttribute("data-card-uuid") for card_div in cards_div.children]

    @staticmethod
    @pytest.mark.parametrize("number_of_selected_decks", [0, 1, 2])
    def test_update_bulk_buttons(screen: EditDeckScreen, number_of_selected_decks: int) -> None:
        for idx, checkbox in enumerate(screen.select_all_children(".disce-selected-checkbox")):
            checkbox.checked = idx < number_of_selected_decks
        screen.update_bulk_buttons()
        assert screen.select_child(".disce-select-all-btn").title == (
            "Deselect all" if number_of_selected_decks == 2 else "Select all"
        )
        assert screen.select_child(".disce-select-all-btn .disce-btn-text").innerText == (
            " Deselect All" if number_of_selected_decks == 2 else " Select All"
        )
        assert screen.select_child(".disce-delete-cards-btn").disabled == (number_of_selected_decks == 0)

    @staticmethod
    def test_back_to_decks_screen_no_changes(storage: AbstractStorage, screen: EditDeckScreen) -> None:
        with TestEditDeckScreen._assert_back_to_decks_screen_confirm(storage, screen, call_expected=False):
            screen.back_to_decks_screen()

    @staticmethod
    def test_back_to_decks_screen_changed_metadata(storage: AbstractStorage, screen: EditDeckScreen) -> None:
        screen.select_child(".disce-deck-name-textbox").value = "deck1_name_modified"
        with TestEditDeckScreen._assert_back_to_decks_screen_confirm(storage, screen):
            screen.back_to_decks_screen()

    @staticmethod
    def test_back_to_decks_screen_changed_cards(storage: AbstractStorage, screen: EditDeckScreen) -> None:
        cards_div = screen.select_child(".disce-cards")
        cards_div.children[-1].querySelector(".disce-front-textbox").value = "new_card_front"
        screen.card_text_changed()
        with TestEditDeckScreen._assert_back_to_decks_screen_confirm(storage, screen):
            screen.back_to_decks_screen()

    @staticmethod
    def test_back_to_decks_screen_new_deck_no_changes(storage: AbstractStorage) -> None:
        screen = EditDeckScreen(None, storage)
        screen.show()
        with TestEditDeckScreen._assert_back_to_decks_screen_confirm(storage, screen, call_expected=False):
            screen.back_to_decks_screen()

    @staticmethod
    def test_back_to_decks_screen_new_deck_changed_cards(storage: AbstractStorage) -> None:
        screen = EditDeckScreen(None, storage)
        screen.show()
        cards_div = screen.select_child(".disce-cards")
        cards_div.children[-1].querySelector(".disce-front-textbox").value = "new_card_front"
        screen.card_text_changed()
        with TestEditDeckScreen._assert_back_to_decks_screen_confirm(storage, screen):
            screen.back_to_decks_screen()

    @staticmethod
    def test_back_to_decks_screen_canceled(storage: AbstractStorage, screen: EditDeckScreen) -> None:
        screen.select_child(".disce-deck-name-textbox").value = "deck1_name_modified"
        with TestEditDeckScreen._assert_back_to_decks_screen_confirm(storage, screen, confirm=False):
            screen.back_to_decks_screen()

    @staticmethod
    @contextmanager
    def _assert_back_to_decks_screen_confirm(
        storage: AbstractStorage, screen: EditDeckScreen, *, confirm: bool = True, call_expected: bool = True
    ) -> Generator[None]:
        with patch("disce.screens.edit_deck.confirm", return_value=confirm) as confirm_mock:
            yield
        expected_calls = []
        if call_expected:
            expected_calls.append(call("You have unsaved changes. Do you want to discard them?"))
        else:
            assert confirm
        assert confirm_mock.call_args_list == expected_calls
        assert_hidden(screen, hidden=confirm)
        assert_visible(DecksScreen(storage), visible=confirm)

    @staticmethod
    def test_get_deck(
        screen: EditDeckScreen, deck_data_list: list[DeckData], deck_metadata_list: list[DeckMetadata]
    ) -> None:
        deck_data, deck_metadata = screen.get_deck()
        assert deck_data == deck_data_list[0]
        assert deck_metadata == deck_metadata_list[0]

    @staticmethod
    def test_get_card_uuids(screen: EditDeckScreen) -> None:
        assert screen.get_card_uuids() == ["deck1_card1", "deck1_card2"]

    @staticmethod
    def test_get_selected_card_uuids(screen: EditDeckScreen) -> None:
        screen.select_child(".disce-selected-checkbox").checked = True
        assert screen.get_selected_card_uuids() == ["deck1_card1"]
