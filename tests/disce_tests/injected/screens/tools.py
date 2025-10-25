#!/usr/bin/env python
# Copyright (C) 2025 Julian Valentin
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


from disce.data import Card, DeckData, DeckMetadata, UUIDModelList


def create_decks(prefix: str) -> tuple[UUIDModelList[DeckData], UUIDModelList[DeckMetadata]]:
    prefix = prefix.rstrip("_")
    if prefix:
        prefix += "_"
    return UUIDModelList(
        [
            DeckData(
                uuid=f"{prefix}deck1",
                cards=UUIDModelList(
                    [
                        Card(uuid=f"{prefix}deck1_card1", front="deck1_card1_front", back="deck1_card1_back"),
                        Card(uuid=f"{prefix}deck1_card2", front="deck1_card2_front", back="deck1_card2_back"),
                    ]
                ),
            ),
            DeckData(
                uuid=f"{prefix}deck2",
                cards=UUIDModelList(
                    [Card(uuid=f"{prefix}deck2_card1", front="deck2_card1_front", back="deck2_card1_back")]
                ),
            ),
        ]
    ), UUIDModelList(
        [
            DeckMetadata(uuid=f"{prefix}deck1", name=f"{prefix}deck1_name", number_of_cards=2),
            DeckMetadata(uuid=f"{prefix}deck2", name=f"{prefix}deck2_name", number_of_cards=1),
        ]
    )
