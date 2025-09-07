#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Screen management."""

from typing import Any

from pyscript import document  # type: ignore[import-not-found]

select_element = document.querySelector


def create_element(tag: str, text: str | None = None, html: str | None = None, **attributes: str) -> Any:  # noqa: ANN401
    """Create a new HTML element with given attributes."""
    element = document.createElement(tag)
    for name, value in attributes.items():
        element.setAttribute(name.removesuffix("_").replace("_", "-"), value)
    if text is not None:
        element.innerText = text
    if html is not None:
        element.innerHTML = html
    return element


def append_child(
    parent: Any,  # noqa: ANN401
    tag: str,
    text: str | None = None,
    html: str | None = None,
    **attributes: str,
) -> Any:  # noqa: ANN401
    """Create a new HTML element with given attributes and append it to the parent."""
    element = create_element(tag, text=text, html=html, **attributes)
    parent.appendChild(element)
    return element


def hide_all() -> None:
    """Hide all screens."""
    from disce.screens import edit_decks as edit_decks_screen  # noqa: PLC0415
    from disce.screens import load as load_screen  # noqa: PLC0415
    from disce.screens import main as main_screen  # noqa: PLC0415

    edit_decks_screen.hide()
    main_screen.hide()
    load_screen.hide()
