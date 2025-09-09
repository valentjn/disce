#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for listing and editing decks."""

import logging
import re
from typing import Any

from pydantic import ValidationError
from pyscript import when, window

from disce import data
from disce.screens import edit_deck as edit_deck_screen
from disce.screens import tools as screen_tools
from disce.screens.tools import append_child, create_element, select_all_elements, select_element
from disce.tools import format_plural

_MINIMUM_NUMBER_OF_DECKS_TO_MERGE = 2

_logger = logging.getLogger(__name__)


def show() -> None:
    """Show the edit decks screen."""
    render_decks()
    screen_tools.hide_all()
    select_element("#disce-decks-screen").style.display = "block"


def hide() -> None:
    """Hide the edit decks screen."""
    select_element("#disce-decks-screen").style.display = "none"


def render_decks() -> None:
    """Render the list of decks."""
    decks_div = select_element("#disce-decks-screen .disce-decks")
    decks_div.innerHTML = ""
    configuration = data.Configuration.load_from_local_storage()
    for deck_metadata in sorted(configuration.deck_metadata, key=lambda deck_metadata: deck_metadata.name.casefold()):
        deck_div = create_element(
            "div", class_="disce-deck d-flex align-items-center mb-2", data_deck_uuid=deck_metadata.uuid
        )
        append_child(
            deck_div,
            "input",
            event_handlers={"change": update_bulk_buttons},
            id_=f"disce-selected-checkbox-{deck_metadata.uuid}",
            type="checkbox",
            class_="disce-selected-checkbox form-check-input me-2",
            data_deck_uuid=deck_metadata.uuid,
        )
        append_child(
            deck_div,
            "label",
            text=deck_metadata.name,
            for_=f"disce-selected-checkbox-{deck_metadata.uuid}",
            class_="disce-deck-name-label me-2",
        )
        append_child(
            deck_div,
            "button",
            create_element("i", class_="bi bi-lightbulb", title=f'Study the deck "{deck_metadata.name}"'),
            create_element("span", text=" Study", class_="disce-btn-text"),
            event_handlers={"click": study_deck},
            class_="disce-study-deck-btn btn btn-outline-success me-2",
            data_deck_uuid=deck_metadata.uuid,
        )
        append_child(
            deck_div,
            "button",
            create_element("i", class_="bi bi-pencil", title=f'Edit the deck "{deck_metadata.name}"'),
            create_element("span", text=" Edit", class_="disce-btn-text"),
            event_handlers={"click": edit_deck},
            class_="disce-edit-deck-btn btn btn-outline-primary me-2",
            data_deck_uuid=deck_metadata.uuid,
        )
        append_child(
            deck_div,
            "button",
            create_element("i", class_="bi bi-copy", title=f'Duplicate the deck "{deck_metadata.name}"'),
            create_element("span", text=" Duplicate", class_="disce-btn-text"),
            event_handlers={"click": duplicate_deck},
            class_="disce-duplicate-deck-btn btn btn-outline-primary me-2",
            data_deck_uuid=deck_metadata.uuid,
        )
        append_child(
            deck_div,
            "button",
            create_element("i", class_="bi bi-trash", title=f'Delete the deck "{deck_metadata.name}"'),
            create_element("span", text=" Delete", class_="disce-btn-text"),
            event_handlers={"click": delete_deck},
            class_="disce-delete-deck-btn btn btn-outline-danger",
            data_deck_uuid=deck_metadata.uuid,
        )
        decks_div.appendChild(deck_div)
    if not configuration.deck_metadata:
        decks_div.appendChild(create_element("p", text="No decks available. Please add a deck."))
    update_bulk_buttons()


@when("click", "#disce-decks-screen .disce-add-deck-btn")
def add_deck() -> None:
    """Add a new deck."""
    edit_deck_screen.show(deck_uuid=None)


@when("click", "#disce-decks-screen .disce-import-decks-btn")
def import_decks() -> None:
    """Import decks from a JSON file."""

    def handle_imported_data(json: str) -> None:
        try:
            deck_export = data.DeckExport.model_validate_json(json)
        except ValidationError as exception:
            window.alert(f"failed to parse imported data: {exception}")
            return
        configuration = data.Configuration.load_from_local_storage()
        overwriting_deck_uuids = {deck.metadata.uuid for deck in deck_export.decks} & {
            deck.uuid for deck in configuration.deck_metadata
        }
        if overwriting_deck_uuids and not window.confirm(
            f"The imported data contains {format_plural(len(overwriting_deck_uuids), 'deck')} (see below) that "
            f"will overwrite existing decks. Do you want to continue?\n\n"
            f"{format_plural(len(overwriting_deck_uuids), 'Name', omit_number=True)} of "
            f"{format_plural(len(overwriting_deck_uuids), 'deck', omit_number=True)} to be overwritten: "
            f"{', '.join(f'"{configuration.get_deck_metadata(uuid).name}"' for uuid in overwriting_deck_uuids)}"
        ):
            return
        for exported_deck in deck_export.decks:
            exported_deck.data.save_to_local_storage()
            configuration.set_deck_metadata(exported_deck.metadata)
        configuration.save_to_local_storage()
        render_decks()

    screen_tools.upload_file(".json,application/json", handle_imported_data)


@when("click", "#disce-decks-screen .disce-select-all-btn")
def select_all_decks() -> None:
    """Select or deselect all decks."""
    deck_uuids = get_deck_uuids()
    selected_deck_uuids = get_selected_deck_uuids()
    select_all = len(selected_deck_uuids) < len(deck_uuids)
    for checkbox in select_all_elements("#disce-decks-screen .disce-selected-checkbox"):
        checkbox.checked = select_all
    update_bulk_buttons()


@when("click", "#disce-decks-screen .disce-study-decks-btn")
def study_decks() -> None:
    """Study selected decks."""


@when("click", "#disce-decks-screen .disce-merge-decks-btn")
def merge_decks() -> None:
    """Merge selected decks."""
    selected_deck_uuids = get_selected_deck_uuids()
    if len(selected_deck_uuids) < _MINIMUM_NUMBER_OF_DECKS_TO_MERGE:
        window.alert(f"Please select at least {format_plural(_MINIMUM_NUMBER_OF_DECKS_TO_MERGE, 'deck')} to merge.")
        return
    merged_deck_name = window.prompt("Enter a name for the merged deck:", "Merged Deck")
    if not merged_deck_name:
        return
    configuration = data.Configuration.load_from_local_storage()
    merged_deck_data = data.DeckData()
    merged_deck_metadata = data.DeckMetadata(uuid=merged_deck_data.uuid, name=merged_deck_name)
    for deck_uuid in selected_deck_uuids:
        merged_deck_data.merge(data.DeckData.load_from_local_storage(deck_uuid))
    merged_deck_data.save_to_local_storage()
    merged_deck_metadata.number_of_cards = len(merged_deck_data.cards)
    configuration.set_deck_metadata(merged_deck_metadata)
    configuration.save_to_local_storage()
    render_decks()


@when("click", "#disce-decks-screen .disce-export-decks-btn")
def export_decks() -> None:
    """Export selected decks."""
    selected_deck_uuids = get_selected_deck_uuids()
    if not selected_deck_uuids:
        window.alert("Please select at least one deck to export.")
        return
    deck_data_to_export = [data.DeckData.load_from_local_storage(deck_uuid) for deck_uuid in selected_deck_uuids]
    configuration = data.Configuration.load_from_local_storage()
    deck_metadata_to_export = [configuration.get_deck_metadata(deck_uuid) for deck_uuid in selected_deck_uuids]
    if len(deck_metadata_to_export) == 1:
        stem = re.sub(r"[^0-9A-Za-z]", "-", deck_metadata_to_export[0].name)
        stem = re.sub(r"-{2,}", "-", stem).strip("-")[:64].lower()
        if not stem:
            stem = "deck"
    else:
        stem = "decks"
    deck_export = data.DeckExport(
        decks=[
            data.ExportedDeck(data=deck_data, metadata=deck_metadata)
            for deck_data, deck_metadata in zip(deck_data_to_export, deck_metadata_to_export, strict=True)
        ]
    )
    screen_tools.download_file(f"{stem}.json", deck_export.model_dump_json(indent=4))
    render_decks()


@when("click", "#disce-decks-screen .disce-delete-decks-btn")
def delete_decks() -> None:
    """Delete selected decks."""
    selected_deck_uuids = get_selected_deck_uuids()
    if not selected_deck_uuids:
        window.alert("Please select at least one deck to delete.")
        return
    if window.confirm(
        f"Are you sure you want to delete the selected {format_plural(len(selected_deck_uuids), 'deck')}?"
    ):
        configuration = data.Configuration.load_from_local_storage()
        for deck_uuid in selected_deck_uuids:
            data.DeckData.delete_from_local_storage(deck_uuid)
            configuration.delete_deck_metadata(deck_uuid)
        configuration.save_to_local_storage()
        render_decks()


@when("change", "#disce-decks-screen .disce-selected-checkbox")
def update_bulk_buttons() -> None:
    """Update the bulk action buttons based on selection."""
    deck_uuids = get_deck_uuids()
    selected_deck_uuids = get_selected_deck_uuids()
    select_element("#disce-decks-screen .disce-select-all-btn .disce-btn-text").innerText = (
        " Deselect All" if len(selected_deck_uuids) == len(deck_uuids) and deck_uuids else " Select All"
    )
    select_element("#disce-decks-screen .disce-merge-decks-btn").disabled = (
        len(selected_deck_uuids) < _MINIMUM_NUMBER_OF_DECKS_TO_MERGE
    )
    select_element("#disce-decks-screen .disce-export-decks-btn").disabled = len(selected_deck_uuids) == 0
    select_element("#disce-decks-screen .disce-delete-decks-btn").disabled = len(selected_deck_uuids) == 0


@when("click", "#disce-decks-screen .disce-study-deck-btn")
def study_deck(event: Any) -> None:  # noqa: ANN401
    """Study a specific deck."""


@when("click", "#disce-decks-screen .disce-edit-deck-btn")
def edit_deck(event: Any) -> None:  # noqa: ANN401
    """Edit a specific deck."""
    edit_deck_screen.show(deck_uuid=event.currentTarget.getAttribute("data-deck-uuid"))


@when("click", "#disce-decks-screen .disce-duplicate-deck-btn")
def duplicate_deck(event: Any) -> None:  # noqa: ANN401
    """Duplicate a specific deck."""
    original_deck_uuid: str = event.currentTarget.getAttribute("data-deck-uuid")
    configuration = data.Configuration.load_from_local_storage()
    original_deck_metadata = configuration.get_deck_metadata(original_deck_uuid)
    new_deck_name = window.prompt("Enter a name for the duplicated deck:", f"Copy of {original_deck_metadata.name}")
    if not new_deck_name:
        return
    original_deck_data = data.DeckData.load_from_local_storage(original_deck_uuid)
    new_deck_data = original_deck_data.model_copy(
        update={
            "uuid": data.generate_uuid(),
            "cards": [card.model_copy(update={"uuid": data.generate_uuid()}) for card in original_deck_data.cards],
        }
    )
    new_deck_data.save_to_local_storage()
    new_deck_metadata = original_deck_metadata.model_copy(update={"uuid": new_deck_data.uuid, "name": new_deck_name})
    configuration.set_deck_metadata(new_deck_metadata)
    configuration.save_to_local_storage()
    render_decks()


@when("click", "#disce-decks-screen .disce-delete-deck-btn")
def delete_deck(event: Any) -> None:  # noqa: ANN401
    """Delete a specific deck."""
    deck_uuid: str = event.currentTarget.getAttribute("data-deck-uuid")
    configuration = data.Configuration.load_from_local_storage()
    deck_metadata = configuration.get_deck_metadata(deck_uuid)
    if window.confirm(f'Are you sure you want to delete the deck "{deck_metadata.name}"?'):
        data.DeckData.delete_from_local_storage(deck_uuid)
        configuration.delete_deck_metadata(deck_uuid)
        configuration.save_to_local_storage()
        render_decks()


def get_deck_uuids() -> list[str]:
    """Get the UUIDs of all decks."""
    return [
        deck_div.getAttribute("data-deck-uuid") for deck_div in select_all_elements("#disce-decks-screen .disce-deck")
    ]


def get_selected_deck_uuids() -> list[str]:
    """Get the UUIDs of the selected decks."""
    return [
        checkbox.getAttribute("data-deck-uuid")
        for checkbox in select_all_elements("#disce-decks-screen .disce-selected-checkbox")
        if checkbox.checked
    ]
