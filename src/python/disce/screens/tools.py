#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen management."""

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pyscript import document, window
from pyscript.ffi import create_proxy

type EventHandler = Callable[[], None] | Callable[[Any], None]

select_all_elements = document.querySelectorAll
select_element = document.querySelector


def create_element(
    tag: str,
    *children: Any,  # noqa: ANN401
    text: str | None = None,
    html: str | None = None,
    event_handlers: Mapping[str, EventHandler | Sequence[EventHandler]] | None = None,
    **attributes: str,
) -> Any:  # noqa: ANN401
    """Create a new HTML element with given attributes."""
    element = document.createElement(tag)
    for name, value in attributes.items():
        element.setAttribute(name.removesuffix("_").replace("_", "-"), value)
    if text is not None:
        element.innerText = text
    if html is not None:
        element.innerHTML = html
    if event_handlers:
        for event, handlers in event_handlers.items():
            for handler in handlers if isinstance(handlers, Sequence) else [handlers]:
                element.addEventListener(event, create_proxy(handler))
    for child in children:
        element.appendChild(child)
    return element


def append_child(
    parent: Any,  # noqa: ANN401
    tag: str,
    *children: Any,  # noqa: ANN401
    text: str | None = None,
    html: str | None = None,
    event_handlers: Mapping[str, EventHandler | Sequence[EventHandler]] | None = None,
    **attributes: str,
) -> Any:  # noqa: ANN401
    """Create a new HTML element with given attributes and append it to the parent."""
    element = create_element(tag, *children, text=text, html=html, event_handlers=event_handlers, **attributes)
    parent.appendChild(element)
    return element


def set_theme(theme: str | None = None) -> None:
    """Set the theme of the application."""
    if theme is None:
        theme = "dark" if window.matchMedia("(prefers-color-scheme: dark)").matches else "light"
    document.documentElement.setAttribute("data-bs-theme", theme)


def hide_all() -> None:
    """Hide all screens."""
    from disce.screens import decks as decks_screen  # noqa: PLC0415
    from disce.screens import edit_deck as edit_deck_screen  # noqa: PLC0415
    from disce.screens import load as load_screen  # noqa: PLC0415

    edit_deck_screen.hide()
    decks_screen.hide()
    load_screen.hide()


def download_file(filename: str, content: str) -> None:
    """Offer a file for download with the given content."""
    blob = window.Blob.new([content], {"type": "text/plain"})
    url = window.URL.createObjectURL(blob)
    a_element = create_element("a", href=url, download=filename)
    a_element.click()
    window.URL.revokeObjectURL(url)


def upload_file(accepted_types: str, handler: Callable[[str], None]) -> None:
    """Open a file dialog and handle the selected file with the given handler."""

    def handle_uploaded_file(event: Any) -> None:  # noqa: ANN401
        input_element = event.currentTarget
        for file in input_element.files:
            reader = window.FileReader.new()
            reader.addEventListener("load", create_proxy(process_imported_data))
            reader.readAsText(file)

    def process_imported_data(event: Any) -> None:  # noqa: ANN401
        handler(event.currentTarget.result)

    input_element = create_element(
        "input", event_handlers={"change": handle_uploaded_file}, type="file", accept=accepted_types
    )
    input_element.click()
