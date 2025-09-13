#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen for listing and editing decks."""

import logging
import re
from typing import override

from pydantic import ValidationError
from pyscript import document, window

import disce.screens.edit_deck as edit_deck_screen
from disce.data import UUID, Configuration, DeckData, DeckExport, DeckMetadata, ExportedDeck, UUIDModel, UUIDModelList
from disce.screens.base import AbstractScreen, EventBinding
from disce.screens.tools import Event, append_child, create_element, download_file, select_all_elements, upload_file
from disce.storage.base import AbstractStorage
from disce.tools import format_plural

_logger = logging.getLogger(__name__)


class DecksScreen(AbstractScreen):
    """Screen for listing and editing decks."""

    _MINIMUM_NUMBER_OF_DECKS_TO_MERGE = 2

    def __init__(self, storage: AbstractStorage) -> None:
        """Initialize the screen."""
        super().__init__("#disce-decks-screen")
        self._storage = storage

    @override
    def _get_static_event_listeners(self) -> list[EventBinding]:
        return [
            EventBinding(element=self.select_child(".disce-add-deck-btn"), event="click", listener=self.add_deck),
            EventBinding(
                element=self.select_child(".disce-import-decks-btn"), event="click", listener=self.import_decks
            ),
            EventBinding(
                element=self.select_child(".disce-select-all-btn"), event="click", listener=self.select_all_decks
            ),
            EventBinding(element=self.select_child(".disce-study-decks-btn"), event="click", listener=self.study_decks),
            EventBinding(element=self.select_child(".disce-merge-decks-btn"), event="click", listener=self.merge_decks),
            EventBinding(
                element=self.select_child(".disce-export-decks-btn"), event="click", listener=self.export_decks
            ),
            EventBinding(
                element=self.select_child(".disce-delete-decks-btn"), event="click", listener=self.delete_decks
            ),
            EventBinding(
                element=self.select_child(".disce-settings-btn"), event="click", listener=self.open_settings_modal
            ),
            EventBinding(
                element=self.select_child(".disce-save-settings-btn"), event="click", listener=self.save_settings
            ),
        ]

    @override
    def render(self) -> None:
        """Render the list of decks."""
        self.unregister_event_listeners(dynamic=True)
        decks_div = self.select_child(".disce-decks")
        decks_div.innerHTML = ""
        configuration = Configuration.load_from_storage(self._storage)
        for deck_metadata in sorted(
            configuration.deck_metadata, key=lambda deck_metadata: deck_metadata.name.casefold()
        ):
            deck_div = create_element(
                "div", class_="disce-deck d-flex align-items-center mb-2", data_deck_uuid=deck_metadata.uuid
            )
            selected_checkbox = append_child(
                deck_div,
                "input",
                id_=f"disce-selected-checkbox-{deck_metadata.uuid}",
                type="checkbox",
                class_="disce-selected-checkbox form-check-input me-2",
                data_deck_uuid=deck_metadata.uuid,
            )
            self.register_event_listener(
                EventBinding(element=selected_checkbox, event="change", listener=self.update_bulk_buttons), dynamic=True
            )
            append_child(
                deck_div,
                "label",
                text=deck_metadata.name,
                for_=f"disce-selected-checkbox-{deck_metadata.uuid}",
                class_="disce-deck-name-label me-2",
            )
            study_deck_button = append_child(
                deck_div,
                "button",
                create_element("i", class_="bi bi-lightbulb"),
                create_element("span", text=" Study", class_="disce-btn-text"),
                class_="disce-study-deck-btn btn btn-outline-success me-2",
                title=f'Study the deck "{deck_metadata.name}"',
                data_deck_uuid=deck_metadata.uuid,
            )
            self.register_event_listener(
                EventBinding(element=study_deck_button, event="click", listener=self.study_deck), dynamic=True
            )
            edit_deck_button = append_child(
                deck_div,
                "button",
                create_element("i", class_="bi bi-pencil"),
                create_element("span", text=" Edit", class_="disce-btn-text"),
                class_="disce-edit-deck-btn btn btn-outline-primary me-2",
                title=f'Edit the deck "{deck_metadata.name}"',
                data_deck_uuid=deck_metadata.uuid,
            )
            self.register_event_listener(
                EventBinding(element=edit_deck_button, event="click", listener=self.edit_deck), dynamic=True
            )
            duplicate_deck_button = append_child(
                deck_div,
                "button",
                create_element("i", class_="bi bi-copy"),
                create_element("span", text=" Duplicate", class_="disce-btn-text"),
                class_="disce-duplicate-deck-btn btn btn-outline-primary me-2",
                title=f'Duplicate the deck "{deck_metadata.name}"',
                data_deck_uuid=deck_metadata.uuid,
            )
            self.register_event_listener(
                EventBinding(element=duplicate_deck_button, event="click", listener=self.duplicate_deck), dynamic=True
            )
            delete_deck_button = append_child(
                deck_div,
                "button",
                create_element("i", class_="bi bi-trash"),
                create_element("span", text=" Delete", class_="disce-btn-text"),
                class_="disce-delete-deck-btn btn btn-outline-danger",
                title=f'Delete the deck "{deck_metadata.name}"',
                data_deck_uuid=deck_metadata.uuid,
            )
            self.register_event_listener(
                EventBinding(element=delete_deck_button, event="click", listener=self.delete_deck), dynamic=True
            )
            decks_div.appendChild(deck_div)
        if not configuration.deck_metadata:
            decks_div.appendChild(create_element("p", text="No decks available. Please add a deck."))
        self.update_bulk_buttons()

    def add_deck(self, _event: Event | None = None) -> None:
        """Add a new deck."""
        edit_deck_screen.EditDeckScreen(None, self._storage).show()
        self.hide()

    def import_decks(self, _event: Event | None = None) -> None:
        """Import decks from a JSON file."""

        def handle_imported_data(json: str) -> None:
            try:
                deck_export = DeckExport.model_validate_json(json)
            except ValidationError as exception:
                window.alert(f"failed to parse imported data: {exception}")
                return
            configuration = Configuration.load_from_storage(self._storage)
            overwriting_deck_uuids = {deck.metadata.uuid for deck in deck_export.decks} & {
                deck.uuid for deck in configuration.deck_metadata
            }
            if overwriting_deck_uuids and not window.confirm(
                f"The imported data contains {format_plural(len(overwriting_deck_uuids), 'deck')} (see below) that "
                f"will overwrite existing decks. Do you want to continue?\n\n"
                f"{format_plural(len(overwriting_deck_uuids), 'Name', omit_number=True)} of "
                f"{format_plural(len(overwriting_deck_uuids), 'deck', omit_number=True)} to be overwritten: "
                f"{', '.join(f'"{configuration.deck_metadata[uuid].name}"' for uuid in overwriting_deck_uuids)}"
            ):
                return
            for exported_deck in deck_export.decks:
                exported_deck.data.save_to_storage(self._storage)
                configuration.deck_metadata.set(exported_deck.metadata)
            configuration.save_to_storage(self._storage)
            self.render()

        upload_file(".json,application/json", handle_imported_data)

    def select_all_decks(self, _event: Event | None = None) -> None:
        """Select or deselect all decks."""
        deck_uuids = self.get_deck_uuids()
        selected_deck_uuids = self.get_selected_deck_uuids()
        select_all = len(selected_deck_uuids) < len(deck_uuids)
        for checkbox in select_all_elements("#disce-decks-screen .disce-selected-checkbox"):
            checkbox.checked = select_all
        self.update_bulk_buttons()

    def study_decks(self, _event: Event | None = None) -> None:
        """Study selected decks."""

    def merge_decks(self, _event: Event | None = None) -> None:
        """Merge selected decks."""
        selected_deck_uuids = self.get_selected_deck_uuids()
        if len(selected_deck_uuids) < DecksScreen._MINIMUM_NUMBER_OF_DECKS_TO_MERGE:
            window.alert(
                f"Please select at least {format_plural(DecksScreen._MINIMUM_NUMBER_OF_DECKS_TO_MERGE, 'deck')} to "
                "merge."
            )
            return
        merged_deck_name = window.prompt("Enter a name for the merged deck:", "Merged Deck")
        if not merged_deck_name:
            return
        configuration = Configuration.load_from_storage(self._storage)
        merged_deck_data = DeckData()
        merged_deck_metadata = DeckMetadata(uuid=merged_deck_data.uuid, name=merged_deck_name)
        for deck_uuid in selected_deck_uuids:
            merged_deck_data.merge(DeckData.load_from_storage(self._storage, deck_uuid))
        merged_deck_data.save_to_storage(self._storage)
        merged_deck_metadata.number_of_cards = len(merged_deck_data.cards)
        configuration.deck_metadata.set(merged_deck_metadata)
        configuration.save_to_storage(self._storage)
        self.render()

    def export_decks(self, _event: Event | None = None) -> None:
        """Export selected decks."""
        selected_deck_uuids = self.get_selected_deck_uuids()
        if not selected_deck_uuids:
            window.alert("Please select at least one deck to export.")
            return
        deck_data_to_export = [
            DeckData.load_from_storage(self._storage, deck_uuid) for deck_uuid in selected_deck_uuids
        ]
        configuration = Configuration.load_from_storage(self._storage)
        deck_metadata_to_export = [configuration.deck_metadata[deck_uuid] for deck_uuid in selected_deck_uuids]
        if len(deck_metadata_to_export) == 1:
            stem = re.sub(r"[^0-9A-Za-z]", "-", deck_metadata_to_export[0].name)
            stem = re.sub(r"-{2,}", "-", stem).strip("-")[:64].lower()
            if not stem:
                stem = "deck"
        else:
            stem = "decks"
        deck_export = DeckExport(
            decks=[
                ExportedDeck(data=deck_data, metadata=deck_metadata)
                for deck_data, deck_metadata in zip(deck_data_to_export, deck_metadata_to_export, strict=True)
            ]
        )
        download_file(f"{stem}.json", deck_export.model_dump_json(indent=4))
        self.render()

    def delete_decks(self, _event: Event | None = None) -> None:
        """Delete selected decks."""
        selected_deck_uuids = self.get_selected_deck_uuids()
        if not selected_deck_uuids:
            window.alert("Please select at least one deck to delete.")
            return
        if window.confirm(
            f"Are you sure you want to delete the selected {format_plural(len(selected_deck_uuids), 'deck')}?"
        ):
            configuration = Configuration.load_from_storage(self._storage)
            for deck_uuid in selected_deck_uuids:
                DeckData.delete_from_storage(self._storage, deck_uuid)
                del configuration.deck_metadata[deck_uuid]
            configuration.save_to_storage(self._storage)
            self.render()

    def update_bulk_buttons(self, _event: Event | None = None) -> None:
        """Update the bulk action buttons based on selection."""
        deck_uuids = self.get_deck_uuids()
        selected_deck_uuids = self.get_selected_deck_uuids()
        self.select_child(".disce-select-all-btn").setAttribute(
            "title", "Deselect all" if len(selected_deck_uuids) == len(deck_uuids) > 0 else "Select all"
        )
        self.select_child(".disce-select-all-btn .disce-btn-text").innerText = (
            " Deselect All" if len(selected_deck_uuids) == len(deck_uuids) > 0 else " Select All"
        )
        self.select_child(".disce-merge-decks-btn").disabled = (
            len(selected_deck_uuids) < DecksScreen._MINIMUM_NUMBER_OF_DECKS_TO_MERGE
        )
        self.select_child(".disce-export-decks-btn").disabled = len(selected_deck_uuids) == 0
        self.select_child(".disce-delete-decks-btn").disabled = len(selected_deck_uuids) == 0

    def study_deck(self, _event: Event | None = None) -> None:
        """Study a specific deck."""

    def edit_deck(self, event: Event) -> None:
        """Edit a specific deck."""
        edit_deck_screen.EditDeckScreen(event.currentTarget.getAttribute("data-deck-uuid"), self._storage).show()
        self.hide()

    def duplicate_deck(self, event: Event) -> None:
        """Duplicate a specific deck."""
        original_deck_uuid: UUID = event.currentTarget.getAttribute("data-deck-uuid")
        configuration = Configuration.load_from_storage(self._storage)
        original_deck_metadata = configuration.deck_metadata[original_deck_uuid]
        new_deck_name = window.prompt("Enter a name for the duplicated deck:", f"Copy of {original_deck_metadata.name}")
        if not new_deck_name:
            return
        original_deck_data = DeckData.load_from_storage(self._storage, original_deck_uuid)
        new_deck_data = original_deck_data.model_copy(
            update={
                "uuid": UUIDModel.generate_uuid(),
                "cards": UUIDModelList(
                    [card.model_copy(update={"uuid": UUIDModel.generate_uuid()}) for card in original_deck_data.cards]
                ),
            }
        )
        new_deck_data.save_to_storage(self._storage)
        new_deck_metadata = original_deck_metadata.model_copy(
            update={"uuid": new_deck_data.uuid, "name": new_deck_name}
        )
        configuration.deck_metadata.set(new_deck_metadata)
        configuration.save_to_storage(self._storage)
        self.render()

    def delete_deck(self, event: Event) -> None:
        """Delete a specific deck."""
        deck_uuid: UUID = event.currentTarget.getAttribute("data-deck-uuid")
        configuration = Configuration.load_from_storage(self._storage)
        deck_metadata = configuration.deck_metadata[deck_uuid]
        if window.confirm(f'Are you sure you want to delete the deck "{deck_metadata.name}"?'):
            DeckData.delete_from_storage(self._storage, deck_uuid)
            del configuration.deck_metadata[deck_uuid]
            configuration.save_to_storage(self._storage)
            self.render()

    def open_settings_modal(self, _event: Event | None = None) -> None:
        """Open the settings modal and populate fields from configuration."""
        configuration = Configuration.load_from_storage(self._storage)
        document.getElementById("disce-history-length-input").value = configuration.history_length
        document.getElementById("disce-typewriter-mode-input").checked = configuration.typewriter_mode
        window.bootstrap.Modal.new(self.select_child(".disce-settings-modal")).show()

    def save_settings(self, _event: Event | None = None) -> None:
        """Save settings from the modal dialog to configuration."""
        configuration = Configuration.load_from_storage(self._storage)
        configuration.history_length = int(document.getElementById("disce-history-length-input").value)
        configuration.typewriter_mode = document.getElementById("disce-typewriter-mode-input").checked
        configuration.save_to_storage(self._storage)

    def get_deck_uuids(self) -> list[UUID]:
        """Get the UUIDs of all decks."""
        return [
            deck_div.getAttribute("data-deck-uuid")
            for deck_div in select_all_elements("#disce-decks-screen .disce-deck")
        ]

    def get_selected_deck_uuids(self) -> list[UUID]:
        """Get the UUIDs of the selected decks."""
        return [
            checkbox.getAttribute("data-deck-uuid")
            for checkbox in select_all_elements("#disce-decks-screen .disce-selected-checkbox")
            if checkbox.checked
        ]
