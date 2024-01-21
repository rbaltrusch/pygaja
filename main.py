# pylint: disable=missing-docstring
# pylint: disable=no-member
# pylint: disable=c-extension-no-member
# pylint: disable=import-error
# pylint: disable=global-statement
# pylint: disable=invalid-name
# pylint: disable=line-too-long

from __future__ import annotations

import sys
import json
import logging
import os
from pathlib import Path
import pickle
import random
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Union,
)

import pygame
from pygame import gfxdraw

from coordinate import Coordinate
from error import log_exception, no_error
from particle import DynamicColour

AUTHOR = "{}"
GAME_TITLE = "{}"
TITLE_FONT_SIZE = 70
SCREEN_SIZE = Coordinate(800, 600)
SAVE_FILEPATH = "game.sav"
CONFIG_FILEPATH = "config.json"
LOG_FILEPATH = "game.log"
MUSIC_FILEPATH = "music.wav" # TODO: replace with real path
ICON_FILEPATH = "icon.png" # TODO: replace with real path
FPS = 50
VOLUME_SCALING = 2
BACKGROUND_COLOUR = (0, 0, 0)
ASSETS_FOLDER = Path(__file__).parent

Font = pygame.font.Font
Surface = pygame.surface.Surface
Event = pygame.event.Event
Colour = Union[Tuple[int, int, int], Tuple[int, int, int, int], DynamicColour]
PathLike = Union[os.PathLike, str]


@dataclass
class Assets:
    font: Font
    gui_font: Font
    title_font: Font

    @classmethod
    def from_disk(cls) -> Assets:
        ... # TODO: add implementation

def init_font(filepath: PathLike, font_size: int) -> Optional[Font]:
    try:
        return pygame.font.Font(filepath, font_size)
    except Exception as exc:  # pylint: disable=broad-except
        log_exception("Could not init font", exc)
        logging.info("Falling back to default font...")

    try:
        return pygame.font.SysFont(name=pygame.font.get_default_font(), size=font_size)
    except Exception as exc:  # pylint: disable=broad-except
        log_exception("Could not init default font", exc)

@dataclass
class BaseEntity:

    position: Coordinate
    assets = Assets.from_disk()

class Entity(Protocol):
    def update(self, game: GameScene) -> None:
        ...

    def render(self, screen: Surface) -> None:
        ...

def default_game_over(game: GameScene) -> bool:
    return False # TODO: add implementation

@dataclass
class GameScene:
    window: Window
    game_over_strategy: Callable[[GameScene], bool]
    seed: Optional[int] = None

    def __post_init__(self):
        self.over: bool = False
        self.just_over: bool = False

    def update(self):
        self._update_over()

    def _update_over(self):
        over = self.game_over_strategy(self)
        self.just_over = over and not self.over
        self.over = over

    @property
    def tick(self) -> int:
        return self.window.tick

def init_game_scene(window: Window, seed: Optional[int] = None) -> GameScene:
    seed = seed or random.randint(0, 100_000_000)
    random.seed(seed)
    logging.info("Seed: %s", seed)
    return GameScene(window=window, game_over_strategy=default_game_over, seed=seed)

@dataclass
class TextRenderer:
    font: Optional[Font] = None
    colour: Colour = (255, 255, 255)

    def render(self, text: str) -> Surface:
        if not self.font:
            return pygame.Surface((1, 1))
        return self.font.render(text, True, tuple(self.colour))

@dataclass
class Window:
    screen: Surface
    clock: pygame.time.Clock
    scene: Optional[Scene] = None
    background_colour: Colour = (0, 0, 0)
    volume: float = 1
    running: bool = True
    muted: bool = False
    tick: int = 0

    def update(self):
        self._update_volume()
        if self.scene:
            self.scene.update()
        self.screen.fill(self.background_colour)
        if self.scene:
            self.scene.render(self.screen)
        pygame.display.flip()
        self.clock.tick(FPS)

    @no_error
    def _update_volume(self):
        SoundCollection.enabled = not self.muted
        volume = 0 if self.muted else self.volume
        pygame.mixer.music.set_volume(volume)

    def handle_event(self, event: Event) -> None:
        if self.scene:
            self.scene.handle_event(event)

    def toggle_mute(self):
        self.muted = not self.muted

@dataclass
class SaveData:

    @classmethod
    def from_game(cls, game: GameScene) -> SaveData:
        ... # TODO: add implementation

    @classmethod
    def load(cls, filepath: PathLike) -> SaveData:
        logging.info("Loading game save data...")
        try:
            with open(filepath, "rb") as file:
                dict_: Dict[str, Any] = pickle.load(file)
            return cls(**dict_)
        except Exception:  # pylint: disable=broad-except
            return cls()

    @no_error
    def save(self, filepath: PathLike) -> None:
        logging.info("Saving game save data...")
        with open(filepath, "wb") as file:
            pickle.dump(self.__dict__, file)

@dataclass
class Config:
    font_size: int = 25
    gui_font_size: int = 40
    full_screen: bool = False
    seed: Optional[int] = None
    muted: bool = False
    log_enabled: bool = True
    volume: float = 1

    @classmethod
    def load(cls, filepath: PathLike) -> Config:
        logging.info("Loading config data...")
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                dict_ = json.load(file)
            obj = cls()
            obj.__dict__.update(dict_)
            return obj
        except Exception as exc:  # pylint: disable=broad-except
            log_exception("Could not read config data", exc)
            return cls()

@no_error
def set_taskbar_icon():
    # pylint: disable=import-outside-toplevel
    import ctypes
    if sys.platform.startswith("win32"):
        myappid = f"{AUTHOR}.games.{GAME_TITLE}.0.1.0"  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

@no_error
def load_icon(filepath: PathLike) -> None:
    icon = pygame.image.load(filepath)
    pygame.display.set_icon(icon)
    set_taskbar_icon()

@no_error
def load_music(filepath: PathLike, volume: float):
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.load(filepath)
    try:
        pygame.mixer.music.play(loops=-1, fade_ms=10)
    except Exception: # pylint: disable=broad-except
        pygame.mixer.music.play(loops=-1)  # fade_ms not recognized in pygame < 2

@no_error
def disable_mouse():
    pygame.mouse.set_cursor(
            (8, 8), (0, 0), (0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)
        )  # make cursor invisible

@dataclass
class Sound:
    filepath: PathLike
    volume: float = 1

    def __post_init__(self):
        self.sound: Optional[pygame.mixer.Sound] = self._load_sound()

    @no_error # type: ignore
    def _load_sound(self) -> Optional[pygame.mixer.Sound]:
        sound = pygame.mixer.Sound(self.filepath)
        sound.set_volume(self.volume)
        return sound

    def play(self):
        if not self.sound:
            return
        self.sound.play()

    @property
    def playable(self) -> bool:
        return self.sound is not None

def pick_random_sound(sounds: List[Sound]) -> Optional[Sound]:
    playable_sounds = [x for x in sounds if x.playable]
    return random.choice(playable_sounds) if playable_sounds else None

@dataclass
class SoundCollection:

    sounds: List[Sound]
    sound_pick_strategy: Callable[[List[Sound]], Optional[Sound]] = pick_random_sound

    enabled = True

    def play(self):
        if not self.enabled:
            return

        sound = self.sound_pick_strategy(self.sounds)
        if sound:
            sound.play()


@dataclass
class Player(BaseEntity):
    pass

def chance(factor: float) -> bool:
    return random.random() < factor


def saturate(num: float, min_: float = 0, max_: float = 1):
    return max(min_, min(num, max_))

def init_logging(filepath: PathLike, enabled: bool = True) -> None:
    handler = logging.FileHandler(filepath) if enabled else logging.NullHandler()
    logging.basicConfig(
        handlers=[handler], level=logging.INFO, format="%(asctime)s %(message)s"
    )

def draw_circle(
    surface: Surface,
    position: Coordinate,
    size: int,
    colour: Colour,
):
    gfxdraw.aacircle(surface, int(position.x), int(position.y), size, tuple(colour))
    gfxdraw.filled_circle(surface, int(position.x), int(position.y), size, tuple(colour))

class Scene(Protocol):
    def update(self) -> None:
        ...

    def render(self, screen: Surface) -> None:
        ...

    def handle_event(self, event: Event) -> None:
        ...

@dataclass
class MenuScene:
    def __post_init__(self):
        self.renderer = TextRenderer(font=init_font("", 16))  # TODO: remove test implementation

    def update(self) -> None:
        ...

    def render(self, screen: Surface) -> None:
        text = self.renderer.render("Hello World")  # TODO: remove test implementation
        screen.blit(text, (0,0))

    def handle_event(self, event: Event) -> None:
        ...

def init_menu_scene(window: Window) -> Scene:
    load_music(filepath=MUSIC_FILEPATH, volume=window.volume)
    return MenuScene() # TODO: add implementation # type: ignore

def init_window() -> Window:
    pygame.init()
    pygame.display.set_caption(GAME_TITLE)
    load_icon(filepath=ICON_FILEPATH)
    disable_mouse()
    config = Config.load(filepath=CONFIG_FILEPATH)
    init_logging(filepath=LOG_FILEPATH, enabled=config.log_enabled)

    flags = pygame.FULLSCREEN if config.full_screen else 0
    screen = pygame.display.set_mode(tuple(SCREEN_SIZE), flags=flags)
    clock = pygame.time.Clock()
    window = Window(screen, clock, muted=config.muted, volume=config.volume, background_colour=BACKGROUND_COLOUR)
    window.scene = init_menu_scene(window)
    return window

def main_loop(window: Window):
    for event in pygame.event.get():
        window.handle_event(event)
        if event.type == pygame.QUIT:
            window.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                window.running = False
            elif event.key == pygame.K_m:
                window.toggle_mute()
            elif event.key == pygame.K_f:
                pygame.display.toggle_fullscreen()
    window.update()

def wasm_main():
    # pylint: disable=import-outside-toplevel
    import asyncio
    window = init_window()
    async def runner():
        while window.running:
            main_loop(window)
            await asyncio.sleep(0)
    asyncio.run(runner())


def main():
    window = init_window()
    while window.running:
        main_loop(window)

    pygame.display.quit()

if __name__ == "__main__":
    # run normal main function when running as python script
    # run wasm async main function when calling with pygbag for web build
    (main if __file__ == sys.argv[0] else wasm_main)()
