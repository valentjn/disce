#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen management."""

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pyodide.ffi.wrappers import add_event_listener
from pyscript import document, window

type Element = Any
type Event = Any
type EventListener = Callable[[], None] | Callable[[Event], None]

select_all_elements = document.querySelectorAll
select_element = document.querySelector


def create_element(
    tag: str,
    *children: Element,
    text: str | None = None,
    html: str | None = None,
    event_listeners: Mapping[str, EventListener | Sequence[EventListener]] | None = None,
    **attributes: str,
) -> Element:
    """Create a new HTML element with given attributes."""
    element = document.createElement(tag)
    for name, value in attributes.items():
        element.setAttribute(name.removesuffix("_").replace("_", "-"), value)
    if text is not None:
        element.innerText = text
    if html is not None:
        element.innerHTML = html
    if event_listeners:
        for event, listeners in event_listeners.items():
            for listener in listeners if isinstance(listeners, Sequence) else [listeners]:
                add_event_listener(element, event, listener)
    for child in children:
        element.appendChild(child)
    return element


def append_child(
    parent: Element,
    tag: str,
    *children: Element,
    text: str | None = None,
    html: str | None = None,
    event_listeners: Mapping[str, EventListener | Sequence[EventListener]] | None = None,
    **attributes: str,
) -> Element:
    """Create a new HTML element with given attributes and append it to the parent."""
    element = create_element(tag, *children, text=text, html=html, event_listeners=event_listeners, **attributes)
    parent.appendChild(element)
    return element


def hide_element(element: Element, *, hide: bool = True) -> None:
    """Hide the given element."""
    if hide:
        element.classList.add("d-none")
    else:
        show_element(element)


def show_element(element: Element, *, show: bool = True) -> None:
    """Show the given element."""
    if show:
        element.classList.remove("d-none")
    else:
        hide_element(element)


def set_theme(theme: str | None = None) -> None:
    """Set the theme of the application."""
    if theme is None:
        theme = "dark" if window.matchMedia("(prefers-color-scheme: dark)").matches else "light"
    document.documentElement.setAttribute("data-bs-theme", theme)


def download_file(filename: str, content: str) -> None:
    """Offer a file for download with the given content."""
    blob = window.Blob.new([content], {"type": "text/plain"})
    url = window.URL.createObjectURL(blob)
    a_element = create_element("a", href=url, download=filename)
    a_element.click()
    window.URL.revokeObjectURL(url)


def upload_file(accepted_types: str, listener: Callable[[str], None]) -> None:
    """Open a file dialog and handle the selected file with the given listener."""

    def handle_uploaded_file(event: Event) -> None:
        input_element = event.currentTarget
        for file in input_element.files:
            reader = window.FileReader.new()
            add_event_listener(reader, "load", process_imported_data)
            reader.readAsText(file)

    def process_imported_data(event: Event) -> None:
        listener(event.currentTarget.result)

    input_element = create_element(
        "input", event_listeners={"change": handle_uploaded_file}, type="file", accept=accepted_types
    )
    input_element.click()
