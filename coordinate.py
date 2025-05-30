# -*- coding: utf-8 -*-
"""Coordinates module"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinate:
    """Coordinate point class"""

    x: float = 0  # pylint: disable=invalid-name
    y: float = 0  # pylint: disable=invalid-name

    def __iter__(self):
        yield self.x
        yield self.y

    def __str__(self):
        return f"Pos({self.x}, {self.y})"

    def __hash__(self):
        return hash(tuple(self))

    def __add__(self, coord: Coordinate) -> Coordinate:
        return Coordinate(self.x + coord.x, self.y + coord.y)

    def __sub__(self, coord: Coordinate) -> Coordinate:
        return Coordinate(self.x - coord.x, self.y - coord.y)

    def compute_distance(self, coordinate: Coordinate) -> float:
        """Returns the distance from this point to the specified point"""
        return math.dist(tuple(self), tuple(coordinate))
