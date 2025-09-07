#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for editing a single deck."""

import logging
from typing import Any

from pyscript import when, window

from disce import data
from disce.screens import edit_decks as edit_decks_screen
from disce.screens import tools as screen_tools
from disce.screens.tools import append_child, create_element, select_all_elements, select_element

_logger = logging.getLogger(__name__)


def show(*, deck_uuid: str | None) -> None:
    """Show the edit deck screen for a given deck (or new deck if ``None``)."""
    render_cards(deck_uuid)
    screen_tools.hide_all()
    select_element("#disce-edit-deck-screen").style.display = "block"


def hide() -> None:
    """Hide the edit deck screen."""
    select_element("#disce-edit-deck-screen").style.display = "none"


def render_cards(deck_uuid: str | None) -> None:
    """Render the edit deck screen."""
    saved_data = data.SavedData.load_from_local_storage()
    deck = saved_data.get_deck(deck_uuid) if deck_uuid is not None else data.Deck()
    select_element("#disce-edit-deck-screen .disce-deck-uuid-hidden").value = deck.uuid
    select_element("#disce-edit-deck-screen .disce-deck-name-textbox").value = deck.name
    cards_div = select_element("#disce-edit-deck-screen .disce-cards")
    cards_div.innerHTML = ""
    for card_index, card in enumerate([*deck.cards, create_empty_card()]):
        cards_div.appendChild(create_card_div(card_index, card))


def create_empty_card() -> data.Card:
    """Create a new empty card."""
    return data.Card(front="", back="", enabled=True, answer_history=[])


def create_card_div(card_index: int, card: data.Card) -> Any:  # noqa: ANN401
    """Create a div representing a card for editing."""
    card_div = create_element("div", class_="disce-card row mx-auto align-items-center mb-2")
    create_column(
        card_div,
        create_element(
            "input",
            type="checkbox",
            class_="disce-selected-checkbox form-check-input",
            data_card_index=str(card_index),
            title="Select this card for bulk actions",
        ),
        class_="form-check",
    )
    create_column(
        card_div,
        create_element(
            "input",
            event_handlers={"input": card_text_changed},
            type="text",
            class_="disce-front-textbox form-control",
            value=card.front,
            placeholder="Front",
            data_card_index=str(card_index),
        ),
    )
    create_column(
        card_div,
        create_element(
            "input",
            event_handlers={"input": card_text_changed},
            type="text",
            class_="disce-back-textbox form-control",
            value=card.back,
            placeholder="Back",
            data_card_index=str(card_index),
        ),
    )
    create_column(
        card_div,
        create_element(
            "input",
            id_=f"disce-enabled-checkbox-{card_index}",
            type="checkbox",
            class_="disce-enabled-checkbox form-check-input",
            checked="checked" if card.enabled else "",
            data_card_index=str(card_index),
        ),
        create_element("label", text="Enabled", for_=f"disce-enabled-checkbox-{card_index}"),
        class_="form-check",
    )
    create_column(
        card_div,
        create_element(
            "input",
            type="text",
            class_="disce-answer-history-textbox form-control",
            value="".join("Y" if x else "N" for x in card.answer_history),
            placeholder="Answer history (Y/N)",
            data_card_index=str(card_index),
        ),
    )
    return card_div


def create_column(parent: Any, *children: Any, class_: str = "") -> Any:  # noqa: ANN401
    """Create a column div and append the children to it."""
    column = append_child(parent, "div", class_=f"col-auto {class_}")
    for child in children:
        column.appendChild(child)
    return column


@when("input", "#disce-edit-deck-screen .disce-front-textbox, #disce-edit-deck-screen .disce-back-textbox")
def card_text_changed() -> None:
    """Make sure there's always an empty card at the end."""
    cards = select_all_elements("#disce-edit-deck-screen .disce-card")
    if not cards:
        msg = "no cards found in edit deck screen"
        raise RuntimeError(msg)
    last_card_front = cards[-1].querySelector(".disce-front-textbox").value
    last_card_back = cards[-1].querySelector(".disce-back-textbox").value
    if last_card_front or last_card_back:
        cards_div = select_element("#disce-edit-deck-screen .disce-cards")
        cards_div.appendChild(create_card_div(len(cards), create_empty_card()))


@when("click", "#disce-edit-deck-screen .disce-save-deck-btn")
def save_deck() -> None:
    """Save the current deck."""
    saved_data = data.SavedData.load_from_local_storage()
    saved_data.set_deck(get_deck())
    saved_data.save_to_local_storage()


@when("click", "#disce-edit-deck-screen .disce-back-to-decks-screen-btn")
def back_to_decks_screen() -> None:
    """Go back to the edit decks screen."""
    saved_data = data.SavedData.load_from_local_storage()
    deck = get_deck()
    if saved_data.deck_exists(deck.uuid):
        original_deck = saved_data.get_deck(deck.uuid)
        unsaved_changes = original_deck != deck
    else:
        unsaved_changes = len(deck.cards) > 0
    if unsaved_changes and not window.confirm("You have unsaved changes. Do you want to discard them?"):
        return
    edit_decks_screen.show()


def get_deck() -> data.Deck:
    """Get the current deck from the edit deck screen."""
    deck_uuid = select_element("#disce-edit-deck-screen .disce-deck-uuid-hidden").value
    deck_name = select_element("#disce-edit-deck-screen .disce-deck-name-textbox").value
    cards = []
    for card_div in select_all_elements("#disce-edit-deck-screen .disce-card"):
        front: str = card_div.querySelector(".disce-front-textbox").value
        back: str = card_div.querySelector(".disce-back-textbox").value
        if not front and not back:
            continue
        enabled = bool(card_div.querySelector(".disce-enabled-checkbox").checked)
        answer_history_str: str = card_div.querySelector(".disce-answer-history-textbox").value
        answer_history = [character.upper() == "Y" for character in answer_history_str]
        cards.append(data.Card(front=front, back=back, enabled=enabled, answer_history=answer_history))
    return data.Deck(uuid=deck_uuid, name=deck_name, cards=cards)
