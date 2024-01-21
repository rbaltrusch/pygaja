# -*- coding: utf-8 -*-
"""Animation module"""

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Optional, Protocol

@dataclass
class Counter(Protocol):
    tick: int

@dataclass
class Animation:
    values: Iterable[Any]
    tick: int

    def __post_init__(self):
        self._iterator: Optional[Iterator[Any]] = None
        self.start_tick: Optional[int] = None
        self.current_tick: int = 0
        self.ongoing: bool = False
        self.current_value: Optional[Any] = None

    def stop(self):
        self.start()
        self.ongoing = False

    def start(self):
        self.start_tick = None
        self.current_tick = 0
        self.ongoing = True
        self._iterator = None
        self.current_value = None

    def update(self, counter: Counter):
        if not self.ongoing:
            return

        if self.start_tick is None:
            self.start_tick = counter.tick

        if self.current_tick % self.tick == 0:
            value = self._next()
            if value is not None:
                self.current_value = value

        if self.start_tick != counter.tick:
            self.current_tick += 1

    def _next(self) -> Optional[Any]:
        if self._iterator is None:
            self._iterator = iter(self.values)

        try:
            return next(self._iterator)
        except StopIteration:
            self.ongoing = False
            return None
