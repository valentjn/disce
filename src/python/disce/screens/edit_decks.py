#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for editing decks."""

import logging
from typing import Any

from pyscript import when, window

from disce import data, tools
from disce.screens import edit_deck as edit_deck_screen
from disce.screens import tools as screen_tools
from disce.screens.tools import append_child, create_element, select_all_elements, select_element

_MINIMUM_NUMBER_OF_DECKS_TO_MERGE = 2

_logger = logging.getLogger(__name__)


def show() -> None:
    """Show the edit decks screen."""
    render_decks()
    screen_tools.hide_all()
    select_element("#disce-edit-decks-screen").style.display = "block"


def hide() -> None:
    """Hide the edit decks screen."""
    select_element("#disce-edit-decks-screen").style.display = "none"


def render_decks() -> None:
    """Render the list of decks."""
    decks_div = select_element("#disce-edit-decks-screen .disce-decks")
    decks_div.innerHTML = ""
    saved_data = data.SavedData.load_from_local_storage()
    for deck_index, deck in enumerate(saved_data.decks):
        deck_div = create_element("div", class_="d-flex align-items-center mb-2")
        append_child(
            deck_div,
            "input",
            event_handlers={"change": toggle_bulk_buttons},
            id_=f"disce-selected-checkbox-{deck_index}",
            type="checkbox",
            class_="disce-selected-checkbox form-check-input me-2",
            data_deck_uuid=deck.uuid,
        )
        append_child(
            deck_div,
            "label",
            text=deck.name,
            for_=f"disce-selected-checkbox-{deck_index}",
            class_="disce-deck-name-label me-2",
        )
        append_child(
            deck_div,
            "button",
            text="Edit",
            event_handlers={"click": edit_deck},
            class_="disce-edit-deck-btn btn btn-outline-primary btn-sm me-2",
            data_deck_uuid=deck.uuid,
        )
        append_child(
            deck_div,
            "button",
            text="Duplicate",
            event_handlers={"click": duplicate_deck},
            class_="disce-duplicate-deck-btn btn btn-outline-primary btn-sm me-2",
            data_deck_uuid=deck.uuid,
        )
        append_child(
            deck_div,
            "button",
            text="Delete",
            event_handlers={"click": delete_deck},
            class_="disce-delete-deck-btn btn btn-outline-danger btn-sm",
            data_deck_uuid=deck.uuid,
        )
        decks_div.appendChild(deck_div)
    if not saved_data.decks:
        decks_div.appendChild(create_element("p", text="No decks available. Please add a deck."))
    toggle_bulk_buttons()


@when("click", "#disce-edit-decks-screen .disce-add-deck-btn")
def add_deck() -> None:
    """Add a new deck."""
    edit_deck_screen.show(deck_uuid=None)


@when("click", "#disce-edit-decks-screen .disce-merge-decks-btn")
def merge_decks() -> None:
    """Merge selected decks."""
    saved_data = data.SavedData.load_from_local_storage()
    selected_deck_uuids = get_selected_deck_uuids()
    if len(selected_deck_uuids) < _MINIMUM_NUMBER_OF_DECKS_TO_MERGE:
        window.alert(
            f"Please select at least {tools.format_number(_MINIMUM_NUMBER_OF_DECKS_TO_MERGE, 'deck')} to merge."
        )
        return
    merged_deck_name = window.prompt("Enter a name for the merged deck:", "Merged Deck")
    if not merged_deck_name:
        return
    merged_deck = data.Deck(name=merged_deck_name)
    for deck_uuid in selected_deck_uuids:
        merged_deck.merge(saved_data.get_deck(deck_uuid))
    saved_data.set_deck(merged_deck)
    saved_data.save_to_local_storage()
    render_decks()


@when("click", "#disce-edit-decks-screen .disce-delete-decks-btn")
def delete_decks() -> None:
    """Delete selected decks."""
    saved_data = data.SavedData.load_from_local_storage()
    selected_deck_uuids = get_selected_deck_uuids()
    if not selected_deck_uuids:
        window.alert("Please select at least one deck to delete.")
        return
    if window.confirm(
        f"Are you sure you want to delete the selected {tools.format_number(len(selected_deck_uuids), 'deck')}?"
    ):
        for deck_uuid in selected_deck_uuids:
            saved_data.delete_deck(deck_uuid)
        saved_data.save_to_local_storage()
        render_decks()


@when("change", "#disce-edit-decks-screen .disce-selected-checkbox")
def toggle_bulk_buttons() -> None:
    """Enable or disable the bulk action buttons based on selection."""
    selected_deck_uuids = get_selected_deck_uuids()
    select_element("#disce-edit-decks-screen .disce-merge-decks-btn").disabled = (
        len(selected_deck_uuids) < _MINIMUM_NUMBER_OF_DECKS_TO_MERGE
    )
    select_element("#disce-edit-decks-screen .disce-delete-decks-btn").disabled = len(selected_deck_uuids) == 0


@when("click", "#disce-edit-decks-screen .disce-edit-deck-btn")
def edit_deck(event: Any) -> None:  # noqa: ANN401
    """Edit a specific deck."""
    edit_deck_screen.show(deck_uuid=event.target.getAttribute("data-deck-uuid"))


@when("click", "#disce-edit-decks-screen .disce-duplicate-deck-btn")
def duplicate_deck(event: Any) -> None:  # noqa: ANN401
    """Duplicate a specific deck."""
    saved_data = data.SavedData.load_from_local_storage()
    original_deck = saved_data.get_deck(event.target.getAttribute("data-deck-uuid"))
    new_deck_name = window.prompt("Enter a name for the duplicated deck:", f"Copy of {original_deck.name}")
    if not new_deck_name:
        return
    new_deck = data.Deck(name=new_deck_name, cards=original_deck.cards.copy())
    saved_data.set_deck(new_deck)
    saved_data.save_to_local_storage()
    render_decks()


@when("click", "#disce-edit-decks-screen .disce-delete-deck-btn")
def delete_deck(event: Any) -> None:  # noqa: ANN401
    """Delete a specific deck."""
    saved_data = data.SavedData.load_from_local_storage()
    deck_uuid = event.target.getAttribute("data-deck-uuid")
    deck = saved_data.get_deck(deck_uuid)
    if window.confirm(f'Are you sure you want to delete the deck "{deck.name}"?'):
        saved_data.delete_deck(deck_uuid)
        saved_data.save_to_local_storage()
        render_decks()


def get_selected_deck_uuids() -> list[str]:
    """Get the UUIDs of the selected decks."""
    return [
        checkbox.getAttribute("data-deck-uuid")
        for checkbox in select_all_elements("#disce-edit-decks-screen .disce-selected-checkbox")
        if checkbox.checked
    ]
