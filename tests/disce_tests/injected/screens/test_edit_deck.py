#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import ANY, call, patch

import pytest
from disce.models.base import UUID
from disce.models.cards import Card, CardSide
from disce.models.configs import Configuration
from disce.models.deck_data import DeckData
from disce.models.deck_metadata import DeckMetadata
from disce.pyscript import Element, EventBinding
from disce.screens.decks import DecksScreen
from disce.screens.edit_deck import EditDeckScreen, SortingKey
from disce.storage.base import AbstractStorage

from disce_tests.injected.screens.tools import assert_event_bindings_registered
from disce_tests.injected.tools import assert_hidden, assert_visible


@pytest.fixture
def screen(storage: AbstractStorage) -> EditDeckScreen:
    screen = EditDeckScreen("deck1", storage)
    screen.show()
    return screen


class TestSortingKey:
    @staticmethod
    @pytest.mark.parametrize(
        ("sorting_key", "expected_selector"),
        [
            (SortingKey.ORIGINAL_ORDER, ".disce-sort-cards-by-original-order-link"),
            (SortingKey.FRONT_SIDE, ".disce-sort-cards-by-front-side-link"),
            (SortingKey.BACK_SIDE, ".disce-sort-cards-by-back-side-link"),
            (SortingKey.CORRECT_ANSWERS, ".disce-sort-cards-by-correct-answers-link"),
            (SortingKey.WRONG_ANSWERS, ".disce-sort-cards-by-wrong-answers-link"),
            (SortingKey.MISSING_ANSWERS, ".disce-sort-cards-by-missing-answers-link"),
        ],
    )
    def test_to_link(screen: DecksScreen, sorting_key: SortingKey, expected_selector: str) -> None:
        assert sorting_key.to_link(screen).isSameNode(screen.select_child(expected_selector))

    @staticmethod
    @pytest.mark.parametrize(
        ("sorting_key", "expected_order"),
        [
            (SortingKey.ORIGINAL_ORDER, [0, 1, 2]),
            (SortingKey.FRONT_SIDE, [2, 1, 0]),
            (SortingKey.BACK_SIDE, [0, 2, 1]),
            (SortingKey.CORRECT_ANSWERS, [2, 0, 1]),
            (SortingKey.WRONG_ANSWERS, [1, 0, 2]),
            (SortingKey.MISSING_ANSWERS, [0, 1, 2]),
        ],
    )
    def test_get_sorting_function(
        configuration: Configuration, sorting_key: SortingKey, expected_order: list[int]
    ) -> None:
        indexed_cards = [
            (
                0,
                Card(
                    uuid="card1",
                    front="Cherry",
                    back="A fruit",
                    front_answer_history=[True, False, True],
                    back_answer_history=[True],
                ),
            ),
            (
                1,
                Card(
                    uuid="card2",
                    front="Banana",
                    back="Another fruit",
                    front_answer_history=[False, False],
                    back_answer_history=[False, True],
                ),
            ),
            (
                2,
                Card(
                    uuid="card3",
                    front="Apple",
                    back="Also a fruit",
                    front_answer_history=[True, True, True],
                    back_answer_history=[True, True],
                ),
            ),
        ]
        sorted_cards = sorted(indexed_cards, key=sorting_key.get_sorting_function(configuration))
        assert sorted_cards == [indexed_cards[idx] for idx in expected_order]


class TestEditDeckScreen:
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
        configuration: Configuration,
        screen: EditDeckScreen,
        deck_data_list: list[DeckData],
        deck_metadata_list: list[DeckMetadata],
        empty_card: Card,
    ) -> None:
        assert screen.select_child(".disce-deck-name-textbox").value == deck_metadata_list[0].name
        cards_element = screen.select_child(".disce-cards")
        assert len(cards_element.children) == 3
        TestEditDeckScreen._assert_card_div(
            configuration, cards_element.children[0], deck_data_list[0].cards["deck1_card1"], 0
        )
        TestEditDeckScreen._assert_card_div(
            configuration, cards_element.children[1], deck_data_list[0].cards["deck1_card2"], 1
        )
        TestEditDeckScreen._assert_card_div(configuration, cards_element.children[2], empty_card, 2)
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
    def test_create_card_div(configuration: Configuration, screen: EditDeckScreen) -> None:
        card = Card(
            uuid="uuid",
            front="front",
            back="back",
            enabled=False,
            front_answer_history=[True],
            back_answer_history=[False],
        )
        card_div = screen.create_card_div(card, 42)
        TestEditDeckScreen._assert_card_div(configuration, card_div, card, 42)

    @staticmethod
    def _assert_card_div(
        configuration: Configuration, card_div: Element, expected_card: Card, expected_index: int
    ) -> None:
        assert card_div.getAttribute("data-card-uuid") == expected_card.uuid
        assert card_div.getAttribute("data-card-index") == str(expected_index)
        TestEditDeckScreen._get_card_div_child(card_div, ".disce-selected-checkbox", expected_card.uuid)
        front_textbox = TestEditDeckScreen._get_card_div_child(card_div, ".disce-front-textbox", expected_card.uuid)
        assert front_textbox.value == expected_card.front
        answer_counts = expected_card.get_answer_counts(CardSide.FRONT, history_length=configuration.history_length)
        assert front_textbox.title == f"{answer_counts} in last {configuration.history_length} reviews"
        assert front_textbox.style.background == answer_counts.gradient
        back_textbox = TestEditDeckScreen._get_card_div_child(card_div, ".disce-back-textbox", expected_card.uuid)
        assert back_textbox.value == expected_card.back
        answer_counts = expected_card.get_answer_counts(CardSide.BACK, history_length=configuration.history_length)
        assert back_textbox.title == f"{answer_counts} in last {configuration.history_length} reviews"
        assert back_textbox.style.background == answer_counts.gradient
        assert (
            TestEditDeckScreen._get_card_div_child(card_div, ".disce-enabled-checkbox", expected_card.uuid).checked
            == expected_card.enabled
        )

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
            update={
                "name": "deck1_name_modified",
                "number_of_cards": 3,
                "answer_counts": {
                    history_length: answer_counts.model_copy(
                        update={"missing": answer_counts.missing + history_length * len(CardSide)}
                    )
                    for history_length, answer_counts in deck_metadata_list[0].answer_counts.items()
                },
            }
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
    @pytest.mark.parametrize(
        ("sorting_key", "expected_order"),
        [
            (SortingKey.ORIGINAL_ORDER, [0, 1]),
            (SortingKey.FRONT_SIDE, [0, 1]),
            (SortingKey.BACK_SIDE, [0, 1]),
            (SortingKey.CORRECT_ANSWERS, [1, 0]),
            (SortingKey.WRONG_ANSWERS, [0, 1]),
            (SortingKey.MISSING_ANSWERS, [0, 1]),
            (None, [1, 0]),
        ],
    )
    def test_sort_cards(  # noqa: PLR0913
        configuration: Configuration,
        screen: EditDeckScreen,
        deck_data_list: list[DeckData],
        empty_card: Card,
        sorting_key: SortingKey | None,
        expected_order: list[int],
    ) -> None:
        screen.sort_cards(
            SimpleNamespace(
                currentTarget=sorting_key.to_link(screen)
                if sorting_key
                else screen.select_child(".disce-sort-cards-reverse-link")
            )
        )
        cards_element = screen.select_child(".disce-cards")
        assert len(cards_element.children) == 3
        card_uuids = ["deck1_card1", "deck1_card2"]
        for card_idx, card_div in zip(expected_order, cards_element.children, strict=False):
            TestEditDeckScreen._assert_card_div(
                configuration, card_div, deck_data_list[0].cards[card_uuids[card_idx]], card_idx
            )
        TestEditDeckScreen._assert_card_div(configuration, cards_element.children[2], empty_card, 2)

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
    def test_load_deck_data(screen: EditDeckScreen, deck_data_list: list[DeckData]) -> None:
        assert screen.load_deck_data() == deck_data_list[0]

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
