#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for editing decks."""

from typing import Any

from pyscript import when  # type: ignore[import-not-found]

from disce import data
from disce.screens import tools as screen_tools
from disce.screens.tools import append_child, create_element, select_element


@when("click", "#edit-decks-btn")  # type: ignore[misc]
def show() -> None:
    """Show the edit decks screen."""
    render_decks()
    screen_tools.hide_all()
    select_element("#edit-decks-screen").style.display = "block"


def hide() -> None:
    """Hide the edit decks screen."""
    select_element("#edit-decks-screen").style.display = "none"


def render_decks() -> None:
    """Render the list of decks."""
    decks_div = select_element("#decks")
    decks_div.innerHTML = ""
    saved_data = data.SavedData.load_from_local_storage()
    for deck_index, deck in enumerate(saved_data.decks):
        deck_div = create_element("div", className="deck-item d-flex align-items-center mb-2")
        append_child(
            deck_div, "input", type="checkbox", className="form-check-input me-2", data_deck_index=str(deck_index)
        )
        append_child(deck_div, "span", className="me-3", innerText=deck.name)
        append_child(
            deck_div,
            "button",
            className="edit-deck-btn btn btn-outline-primary btn-sm me-2",
            innerText="Edit",
            data_deck_index=str(deck_index),
        )
        append_child(
            deck_div,
            "button",
            className="duplicate-deck-btn btn btn-outline-secondary btn-sm me-2",
            innerText="Duplicate",
            data_deck_index=str(deck_index),
        )
        append_child(
            deck_div,
            "button",
            className="delete-deck-btn btn btn-outline-danger btn-sm",
            innerText="Delete",
            data_deck_index=str(deck_index),
        )
        decks_div.appendChild(deck_div)
    if not saved_data.decks:
        decks_div.appendChild(create_element("p", text="No decks available. Please add a deck."))


@when("click", "#add-deck-btn")  # type: ignore[misc]
def add_deck() -> None:
    """Add a new deck."""
    from disce.screens import edit_deck as edit_deck_screen  # noqa: PLC0415

    edit_deck_screen.show(deck_index=None)


@when("click", ".edit-deck-btn")  # type: ignore[misc]
def edit_deck(event: Any) -> None:  # noqa: ANN401
    """Edit a specific deck."""
    from disce.screens import edit_deck as edit_deck_screen  # noqa: PLC0415

    deck_index = int(event.target.getAttribute("data-deck-index"))
    edit_deck_screen.show(deck_index=deck_index)
