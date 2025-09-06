#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for editing a single deck."""

from typing import Any

from pyscript import when  # type: ignore[import-not-found]

from disce import data
from disce.screens import tools as screen_tools
from disce.screens.tools import append_child, create_element, select_element


def show(*, deck_index: int | None) -> None:
    """Show the edit deck screen for a given deck index (or new deck if ``None``)."""
    render_cards(deck_index)
    screen_tools.hide_all()
    select_element("#edit-deck-screen").style.display = "block"


def hide() -> None:
    """Hide the edit deck screen."""
    select_element("#edit-deck-screen").style.display = "none"


def render_cards(deck_index: int | None) -> None:
    """Render the edit deck screen."""
    saved_data = data.SavedData.load_from_local_storage()
    deck = saved_data.decks[deck_index] if deck_index is not None else data.Deck(name="New Deck", cards=[])
    select_element("#deck-name-input").value = deck.name
    cards_div = select_element("#cards")
    cards_div.innerHTML = ""
    empty_card = data.Card(front="", back="", enabled=True, answer_history=[])
    for card_index, card in enumerate([*deck.cards, empty_card]):
        cards_div.appendChild(create_card_div(card_index, card))


def create_card_div(card_index: int, card: data.Card) -> Any:  # noqa: ANN401
    """Create a div representing a card for editing."""
    card_div = create_element("div", className="card-row d-flex align-items-center mb-2")
    append_child(
        card_div,
        "input",
        type="checkbox",
        className="card-selected-checkbox form-check-input me-2",
        data_card_index=str(card_index),
    )
    front_textbox = append_child(
        card_div,
        "input",
        type="text",
        className="card-front-textbox form-control me-2",
        value=card.front,
        placeholder="Front",
        data_card_index=str(card_index),
    )
    # front_textbox.addEventListener("change", card_text_changed)
    when(front_textbox, "change", card_text_changed)  # type: ignore[misc]
    back_textbox = append_child(
        card_div,
        "input",
        type="text",
        className="card-back-textbox form-control me-2",
        value=card.back,
        placeholder="Back",
        data_card_index=str(card_index),
    )
    # back_textbox.addEventListener("change", card_text_changed)
    append_child(
        card_div,
        "input",
        type="checkbox",
        className="card-enabled-checkbox form-check-input me-2",
        checked="checked" if card.enabled else "",
        data_card_index=str(card_index),
    )
    append_child(
        card_div,
        "input",
        type="text",
        className="card-answer-history-textbox form-control me-2",
        value="".join(["Y" if x else "N" for x in card.answer_history]),
        placeholder="Answer history (Y/N)",
        data_card_index=str(card_index),
    )
    return card_div


def card_text_changed() -> None:
    """Make sure there's always an empty card at the end."""
    cards_div = select_element("#cards")
    card_rows = cards_div.querySelectorAll(".card-row")
    if not card_rows:
        return
    last_card_row = card_rows.item(card_rows.length - 1)
    front_input = last_card_row.querySelector(".card-front-textbox")
    back_input = last_card_row.querySelector(".card-back-textbox")
    if front_input.value.strip() != "" or back_input.value.strip() != "":
        # Add a new empty card row
        empty_card = data.Card(front="", back="", enabled=True, answer_history=[])
        cards_div.appendChild(create_card_div(len(card_rows), empty_card))
