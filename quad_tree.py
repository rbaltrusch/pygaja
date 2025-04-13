from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Protocol

import pygame

from coordinate import Coordinate as Point


class Positioned(Protocol):
    position: Point


@dataclass
class Rect:
    """Rectangle class for 2D space"""

    position: Point
    size: Point

    def __iter__(self):
        yield from self.position
        yield from self.position + self.size

    def contains(self, point: Point) -> bool:
        bottom = self.position + self.size
        return (
            self.position.x <= point.x < bottom.x
            and self.position.y <= point.y < bottom.y
        )

    def intersects(self, rect: Rect) -> bool:
        return self.contains(rect.position) or rect.contains(self.position)


class QuadTree:
    def __init__(self, boundary: Rect, max_points: int = 4):
        self.boundary = boundary
        self.max_points = max_points
        self.entities: list[Positioned] = []
        self.sub_quads: list[QuadTree] = []

    def find(self, boundary: Rect) -> Iterable[Positioned]:
        if not self.boundary.intersects(boundary):
            return

        for point in self.entities:
            if boundary.contains(point.position):
                yield point

        for quad in self.sub_quads:
            yield from quad.find(boundary)

    def insert(self, entity: Positioned) -> bool:
        if not self.boundary.contains(entity.position):
            return False

        if len(self.entities) < self.max_points:
            self.entities.append(entity)
            return True

        if not self.sub_quads:
            self._subdivide()

        for quad in self.sub_quads:
            if quad.insert(entity):
                return True

        return False

    def remove(self, entity: Positioned) -> Positioned | None:
        if entity in self.entities:
            self.entities.remove(entity)
            return entity

        for quad in self.sub_quads:
            removed = quad.remove(entity)
            if removed:
                return removed

        return None

    def move(self, entity: Positioned) -> bool:  # TODO: optimize
        if not self.boundary.contains(entity.position):
            removed = self.remove(entity)
            if removed:
                return self.insert(entity)
        return True

    def _subdivide(self) -> None:
        half_width = self.boundary.size.x / 2
        half_height = self.boundary.size.y / 2
        x, y = self.boundary.position.x, self.boundary.position.y

        self.sub_quads.append(
            QuadTree(Rect(Point(x, y), Point(half_width, half_height)))
        )
        self.sub_quads.append(
            QuadTree(Rect(Point(x + half_width, y), Point(half_width, half_height)))
        )
        self.sub_quads.append(
            QuadTree(Rect(Point(x, y + half_height), Point(half_width, half_height)))
        )
        self.sub_quads.append(
            QuadTree(
                Rect(
                    Point(x + half_width, y + half_height),
                    Point(half_width, half_height),
                )
            )
        )


if __name__ == "__main__":
    import random

    def get_selected_entities(entities: list[Rect], selection: Rect | None):
        for entity in entities:
            selected = selection is not None and selection.intersects(entity)
            if selected:
                yield entity

    def main():
        count = 0
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        clock = pygame.time.Clock()
        running = True
        entities: list[Rect] = []
        selection: Optional[Rect] = None
        quad_tree = QuadTree(boundary=Rect(Point(), Point(800, 600)), max_points=10)
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    selection = Rect(
                        position=Point(*pygame.mouse.get_pos()), size=Point()
                    )
                if event.type == pygame.MOUSEBUTTONUP:
                    selection = None
                if event.type == pygame.MOUSEMOTION and selection is not None:
                    selection = Rect(
                        selection.position,
                        Point(*pygame.mouse.get_pos()) - selection.position,
                    )

            max_entities = 500
            if len(entities) > max_entities:
                entity = entities.pop(random.randint(0, max_entities))
                quad_tree.remove(entity)
            while len(entities) < max_entities:
                entity = Rect(
                    position=Point(random.randint(0, 800), random.randint(0, 600)),
                    size=Point(random.randint(5, 25), random.randint(5, 25)),
                )
                entities.append(entity)
                quad_tree.insert(entity)

            selection = Rect(position=Point(200, 150), size=Point(400, 300))

            screen.fill((0, 0, 0))
            if selection is not None:
                pygame.draw.rect(
                    screen,
                    (220, 220, 220, 0),
                    pygame.rect.Rect(*selection.position, *selection.size),
                )

            selected = True
            selected_entities = list(get_selected_entities(entities, selection))
            # selected_entities = list(quad_tree.find(selection))
            print(len(selected_entities))
            for entity in selected_entities:
                colour = (200, 255, 200) if selected else (255, 200, 200)
                pygame.draw.rect(
                    screen,
                    colour,
                    pygame.rect.Rect(*entity.position, *entity.size),
                )

            pygame.display.flip()
            # clock.tick(60)

            count += 1
            if count > 1000:
                running = False

    main()
