#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from collections.abc import Generator
from contextlib import contextmanager

from disce.screens.tools import Element, Event, append_child, create_element, hide_element, show_element
from pyscript import document, window


class TestCreateElement:
    @staticmethod
    def test_tag() -> None:
        element = create_element("div")
        assert element.tagName == "DIV"

    @staticmethod
    def test_children() -> None:
        child1 = create_element("span")
        child2 = create_element("p")
        parent = create_element("div", child1, child2)
        assert parent.childNodes.length == 2
        assert parent.childNodes[0].isSameNode(child1)
        assert parent.childNodes[1].isSameNode(child2)

    @staticmethod
    def test_text() -> None:
        element = create_element("div", text="test")
        assert element.innerText == "test"

    @staticmethod
    def test_html() -> None:
        element = create_element("div", html="<span>inner</span>")
        assert element.innerHTML == "<span>inner</span>"

    @staticmethod
    def test_event_listeners() -> None:
        triggered = {"click": False, "mouseover": False}

        def on_click(event: Event) -> None:
            triggered["click"] = True

        def on_mouseover(event: Event) -> None:
            triggered["mouseover"] = True

        element = create_element(
            "div",
            event_listeners={
                "click": on_click,
                "mouseover": on_mouseover,
            },
        )
        element.dispatchEvent(window.Event.new("click"))
        assert triggered["click"]
        element.dispatchEvent(window.Event.new("mouseover"))
        assert triggered["mouseover"]

    @staticmethod
    def test_attributes() -> None:
        element = create_element("div", id_="test_id", data_value="test_value")
        assert element.getAttribute("id") == "test_id"
        assert element.getAttribute("data-value") == "test_value"


def test_append_child() -> None:
    parent = create_element("div")
    child = append_child(parent, "span", text="child")
    assert parent.childNodes.length == 1
    assert parent.childNodes[0].isSameNode(child)
    assert child.tagName == "SPAN"
    assert child.innerText == "child"


def test_hide_element() -> None:
    with _insert_element_into_body(create_element("div")) as element:
        style = window.getComputedStyle(element)
        hide_element(element)
        assert style.display == "none"
        hide_element(element, hide=False)
        assert style.display != "none"


def test_show_element() -> None:
    with _insert_element_into_body(create_element("div")) as element:
        style = window.getComputedStyle(element)
        show_element(element)
        assert style.display != "none"
        show_element(element, show=False)
        assert style.display == "none"


@contextmanager
def _insert_element_into_body(element: Element) -> Generator[Element]:
    document.body.appendChild(element)
    try:
        yield element
    finally:
        document.body.removeChild(element)
