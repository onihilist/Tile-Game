
import math
from importlib import resources as impr
import pygame
from pygame.math import clamp
from random import randint
from typing import Self

from game import assets
from game.data.items import Items
from game.data.states import MouseStates, PlayerStates
from game.data.tiles import Tile, Tiles, TileTypes
from game.gui.screens.main_hud import MainHud
from game.utils.exceptions import ZeroOrLessSpawnPlayerAttempts
from game.utils.logger import logger
from game.world.camera import Camera
from game.world.map_manager import Map


class Player:
    """
    Class for creating a player.
    """

    TEXTURE: str = str(impr.files(assets) / "player.png")
    VELOCITY_STEP_START: float = 4.5
    VELOCITY_STEP_STOP: float = 5.0

    TIMERS_COUNT: int = 2
    MINING_TIMER: int = 0
    DAMAGE_TIMER: int = 1

    def __init__(self, x: int = 0, y: int = 0, speed: int = 50) -> None:
        super().__init__()
        self.asset: pygame.Surface | None = None
        self._x: int = x
        self._y: int = y
        self.screen_x: int = x
        self.screen_y: int = y
        self.width: int = 32
        self.height: int = 32
        self.velocity_x: float = 0.0
        self.velocity_y: float = 0.0
        self.speed: int = speed
        self.move: int = 0
        self.selected_tile_x: int = 0
        self.selected_tile_y: int = 0
        self.selected_tile_sx: int = 0
        self.selected_tile_sy: int = 0
        self.breaking_tile: tuple[int, int] | None = None
        self.breaking: bool = False
        self.hurt: bool = False
        self.prev_selected_tile: tuple[int, int] = (0, 0)
        self.score: int = 0
        self.health: int = 100
        self.edges = [False, False, False, False]
        self.timers: list[float] = [0.0] * Player.TIMERS_COUNT
        self.main_hud = None
        logger.debug(f'Created {__class__.__name__} with attributes {self.__dict__}')

    def init(self, game) -> None:
        """
        Define the player attributes that depend on the given game object.
        """
        self.main_hud = MainHud(game)
        self.main_hud.set_state(True)

    def events(self, game, e: pygame.event.Event | pygame.event.EventType) -> None:
        """
        Track the player events.
        """
        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == MouseStates.LMB:
                self.breaking = True
                self.timers[Player.MINING_TIMER] = pygame.time.get_ticks() / 1000.0
                game.world.get_map().tile_manager.draw(
                    self.selected_tile_x * game.world.get_map().tile_manager.SIZE,
                    self.selected_tile_y * game.world.get_map().tile_manager.SIZE,
                    game.world.get_map().get_tile(self.selected_tile_x, self.selected_tile_y),
                    game.world.get_map().get_dynatile_surface()
                )
        elif e.type == pygame.MOUSEBUTTONUP:
            if e.button == MouseStates.LMB:
                self.breaking = False
                self.timers[Player.MINING_TIMER] = pygame.time.get_ticks() / 1000.0
                game.world.get_map().tile_manager.draw(
                    self.selected_tile_x * game.world.get_map().tile_manager.SIZE,
                    self.selected_tile_y * game.world.get_map().tile_manager.SIZE,
                    game.world.get_map().get_tile(self.selected_tile_x, self.selected_tile_y),
                    game.world.get_map().get_dynatile_surface()
                )
            if e.button == MouseStates.RMB:
                pass
        if e.type == pygame.MOUSEWHEEL:
            self.main_hud.hotbar.unselect_slot(self.main_hud.hotbar.get_selected_slot())
            self.main_hud.hotbar.select_slot((self.main_hud.hotbar.get_selected_slot() - e.y) % len(self.main_hud.hotbar.get_slots()))
            self.main_hud.hotbar.init_slots()

    def draw(self, game) -> None:
        """
        Draw the player to the screen.
        """
        if not self.is_dead():
            self.screen_x = game.width / 2 - game.camera.x + self._x
            self.screen_y = game.height / 2 - game.camera.y + self._y
            if self.is_in_lava(game.world.get_map()):
                pygame.draw.rect(game.screen, (220, 200, 200), (self.screen_x, self.screen_y, self.width, self.height))
                return
            if not self.is_in_water(game.world.get_map()):
                pygame.draw.rect(game.screen, (255, 255, 255), (self.screen_x, self.screen_y, self.width, self.height))
                return
            pygame.draw.rect(game.screen, (200, 200, 220), (self.screen_x, self.screen_y, self.width, self.height))
        # screen.blit(self.asset, (self.screen_x, self.screen_y, self.width, self.height))

    def draw_selection_grid(self, game) -> None:
        """
        Draw the player tile selection grid to the screen.
        """
        if not game.paused and not self.is_dead() and self.main_hud.hotbar.get_selected_slot_item() == Items.SHOVEL:
            mx, my = pygame.mouse.get_pos()
            center_x, center_y = round(game.width // 2), round(game.height // 2)
            map_width, map_height = game.world.get_map().get_width_in_tiles(), game.world.get_map().get_height_in_tiles()
            camera_x, camera_y = int(game.camera.x), int(game.camera.y)

            wx, wy = (game.camera.x - (center_x - mx)) // 32, (game.camera.y - (center_y - my)) // 32

            x, y = game.world.get_map().tile_to_world_pos(wx + map_width // 2, wy + map_height // 2)
            self.selected_tile_sx, self.selected_tile_sy = x - camera_x + game.width // 2, y - camera_y + game.height // 2

            self.selected_tile_x = int(wx + map_width // 2)
            self.selected_tile_y = int(wy + map_height // 2)

            if (self.selected_tile_x >= game.world.get_map().get_width_in_tiles() or self.selected_tile_x < 0
                    or self.selected_tile_y >= game.world.get_map().get_height_in_tiles() or self.selected_tile_y < 0):
                return

            if self.has_selected_breakable(game.world.get_map()) and not self.is_selected_breakable_obstructed(game.world.get_map()):
                colour_anim: int = round(127.5 * math.sin(pygame.time.get_ticks() / 128) + 127.5)
                pygame.draw.rect(game.screen, (255, colour_anim, colour_anim), (
                                            self.selected_tile_sx,
                                            self.selected_tile_sy,
                                            game.world.get_map().tile_manager.SIZE,
                                            game.world.get_map().tile_manager.SIZE
                                        ), 2, 4)

    def update(self, game, map_obj: Map) -> None:
        """
        Update the player.
        """
        if self.is_dead():
            game.screens.gameover_screen.set_state(not game.paused)
            return
        d: float = game.clock.get_time() / 1000.0
        prev_x: int = self._x
        prev_y: int = self._y
        speed: int = round(
            self.speed // (int(not self.is_in_water(map_obj))
                           + 1.5 * self.is_in_water(map_obj)
                           + 1.5 * self.is_in_lava(map_obj))
        )
        tile_x, tile_y = map_obj.get_tile_pos(self._x, self._y)
        tile_wx, tile_wy = map_obj.tile_to_world_pos(tile_x, tile_y)
        tile_size = game.world.get_map().tile_manager.SIZE
        walls = self.get_walls(map_obj)
        keys = pygame.key.get_pressed()

        if not game.paused:
            self.move = self.move | (1 << PlayerStates.MOVE_LEFT) if keys[pygame.K_q] else self.move & ~(1 << PlayerStates.MOVE_LEFT)
            self.move = self.move | (1 << PlayerStates.MOVE_UP) if keys[pygame.K_z] else self.move & ~(1 << PlayerStates.MOVE_UP)
            self.move = self.move | (1 << PlayerStates.MOVE_RIGHT) if keys[pygame.K_d] else self.move & ~(1 << PlayerStates.MOVE_RIGHT)
            self.move = self.move | (1 << PlayerStates.MOVE_DOWN) if keys[pygame.K_s] else self.move & ~(1 << PlayerStates.MOVE_DOWN)
        else:
            self.move = 0

        if self.velocity_x != 0:
            self._x += speed * self.velocity_x * d
        if self.velocity_y != 0:
            self._y += speed * self.velocity_y * d

        if self.is_moving_left():
            self.velocity_x = clamp(self.velocity_x - Player.VELOCITY_STEP_START * d, -1, 1)
        if self.is_moving_right():
            self.velocity_x = clamp(self.velocity_x + Player.VELOCITY_STEP_START * d, -1, 1)
        if self.is_moving_up():
            self.velocity_y = clamp(self.velocity_y - Player.VELOCITY_STEP_START * d, -1, 1)
        if self.is_moving_down():
            self.velocity_y = clamp(self.velocity_y + Player.VELOCITY_STEP_START * d, -1, 1)

        if not self.is_moving_left() and not self.is_moving_right():
            if -0.0001 < self.velocity_x < 0.0001 and self.velocity_x != 0:
                self.velocity_x = 0
            if self.velocity_x > 0:
                self.velocity_x = clamp(self.velocity_x - Player.VELOCITY_STEP_STOP * d, 0, 1)
            elif self.velocity_x < 0:
                self.velocity_x = clamp(self.velocity_x + Player.VELOCITY_STEP_STOP * d, -1, 0)

        if not self.is_moving_up() and not self.is_moving_down():
            if -0.0001 < self.velocity_y < 0.0001 and self.velocity_y != 0:
                self.velocity_y = 0
            if self.velocity_y > 0:
                self.velocity_y = clamp(self.velocity_y - Player.VELOCITY_STEP_STOP * d, 0, 1)
            elif self.velocity_y < 0:
                self.velocity_y = clamp(self.velocity_y + Player.VELOCITY_STEP_STOP * d, -1, 0)

        # Player - map boundaries collision
        if self._x < map_obj.get_x() or self._x > map_obj.get_x() + map_obj.get_width_in_pixels() - self.width or \
                self._y < map_obj.get_y() or self._y > map_obj.get_y() + map_obj.get_height_in_pixels() - self.height:
            self._x = clamp(self._x, map_obj.get_x(), map_obj.get_x() + map_obj.get_width_in_pixels() - self.width)
            self._y = clamp(self._y, map_obj.get_y(), map_obj.get_y() + map_obj.get_height_in_pixels() - self.height)
            self.velocity_x = self.velocity_y = 0

        # Player - wall collision
        if walls[0] and self._x <= tile_wx:
            self._x = tile_wx
            self.velocity_x = 0 if self.velocity_x < 0 else self.velocity_x
        if walls[1] and self._x >= tile_wx:
            self._x = tile_wx
            self.velocity_x = 0 if self.velocity_x > 0 else self.velocity_x
        if walls[2] and self._y <= tile_wy:
            self._y = tile_wy
            self.velocity_y = 0 if self.velocity_y < 0 else self.velocity_y
        if walls[3] and self._y >= tile_wy:
            self._y = tile_wy
            self.velocity_y = 0 if self.velocity_y > 0 else self.velocity_y
        if walls[4] and self._x + 1 < tile_wx and self._y + 1 < tile_wy:
            if abs(tile_wx - self._x) >= abs(tile_wy - self._y):
                self._y = tile_wy - 1
                self.velocity_y = 0 if self.velocity_y < 0 else self.velocity_y
            elif abs(tile_wx - self._x) < abs(tile_wy - self._y):
                self._x = tile_wx - 1
                self.velocity_x = 0 if self.velocity_x < 0 else self.velocity_x
        if walls[5] and self._x - 1 > tile_wx and self._y + 1 < tile_wy:
            if abs(tile_wx - self._x) >= abs(tile_wy - self._y):
                self._y = tile_wy - 1
                self.velocity_y = 0 if self.velocity_y < 0 else self.velocity_y
            elif abs(tile_wx - self._x) < abs(tile_wy - self._y):
                self._x = tile_wx + 1
                self.velocity_x = 0 if self.velocity_x > 0 else self.velocity_x
        if walls[6] and self._x + 1 < tile_wx and self._y - 1 > tile_wy:
            if abs(tile_wx - self._x) >= abs(tile_wy - self._y):
                self._y = tile_wy + 1
                self.velocity_y = 0 if self.velocity_y > 0 else self.velocity_y
            elif abs(tile_wx - self._x) < abs(tile_wy - self._y):
                self._x = tile_wx - 1
                self.velocity_x = 0 if self.velocity_x < 0 else self.velocity_x
        if walls[7] and self._x - 1 > tile_wx and self._y - 1 > tile_wy:
            if abs(tile_wx - self._x) >= abs(tile_wy - self._y):
                self._y = tile_wy + 1
                self.velocity_y = 0 if self.velocity_y > 0 else self.velocity_y
            elif abs(tile_wx - self._x) < abs(tile_wy - self._y):
                self._x = tile_wx + 1
                self.velocity_x = 0 if self.velocity_x > 0 else self.velocity_x

        # Prevent wall-clipping when lagging
        if self.is_in_wall(map_obj):
            self._x, self._y = prev_x, prev_y

        if self.breaking and self.can_break_breakable(map_obj):
            self.break_tile(game)
        else:
            self.timers[Player.MINING_TIMER] = pygame.time.get_ticks() / 1000.0
            game.world.get_map().tile_manager.draw(
                self.prev_selected_tile[0] * tile_size,
                self.prev_selected_tile[1] * tile_size,
                game.world.get_map().get_tile(self.prev_selected_tile[0], self.prev_selected_tile[1]),
                game.world.get_map().get_dynatile_surface()
            )

        # Update player health
        if self.is_in_lethal_tile(map_obj):
            tile_x, tile_y = game.world.get_map().get_tile_pos(self._x, self._y)
            tile = game.world.get_map().get_tile(tile_x, tile_y)
            if pygame.time.get_ticks() / 1000.0 - self.timers[Player.DAMAGE_TIMER] >= tile.get_damage_delay():
                self.health -= tile.get_damage()
                self.timers[Player.DAMAGE_TIMER] = pygame.time.get_ticks() / 1000.0
                self.hurt = True
            else:
                self.hurt = False

        # Game over
        if self.is_dead():
            self.health = 0
            game.screens.map_screen.set_state(False)

        self.main_hud.health_bar.set_value(self.health)

        self.edges[PlayerStates.MOVE_LEFT] = (self.screen_x <= game.width // 2 - self.width // 2)
        self.edges[PlayerStates.MOVE_UP] = (self.screen_y <= game.height // 2 - self.height // 2)
        self.edges[PlayerStates.MOVE_DOWN] = (self.screen_y >= game.height // 2 + self.height // 2)
        self.edges[PlayerStates.MOVE_RIGHT] = (self.screen_x >= game.width // 2 + self.width // 2)

    def update_ui(self, game) -> None:
        """
        Update the player GUI.
        """
        self.main_hud.update_ui()

    def break_tile(self, game) -> None:
        """
        Break a map tile and update map surfaces.
        """
        delay: float
        tile: Tile
        tile_x: int
        tile_y: int

        tile_x, tile_y = self.selected_tile_x, self.selected_tile_y
        if not game.world.get_map().get_dynatile(tile_x, tile_y) and game.world.get_map().get_tile(tile_x, tile_y) in TileTypes.BREAKABLE:
            if self.breaking_tile != (self.selected_tile_x, self.selected_tile_y):
                self.breaking_tile = (self.selected_tile_x, self.selected_tile_y)
                self.timers[Player.MINING_TIMER] = pygame.time.get_ticks() / 1000.0

            if self.prev_selected_tile != (self.selected_tile_x, self.selected_tile_y):
                game.world.get_map().tile_manager.draw(
                    self.prev_selected_tile[0] * game.world.get_map().tile_manager.SIZE,
                    self.prev_selected_tile[1] * game.world.get_map().tile_manager.SIZE,
                    game.world.get_map().get_tile(self.prev_selected_tile[0], self.prev_selected_tile[1]),
                    game.world.get_map().get_dynatile_surface()
                )
                self.prev_selected_tile = (self.selected_tile_x, self.selected_tile_y)

            tile = game.world.get_map().get_tile(self.selected_tile_x, self.selected_tile_y)
            delay = tile.get_resistance() / self.main_hud.hotbar.get_selected_slot_item().get_strength()

            if pygame.time.get_ticks() / 1000.0 - self.timers[Player.MINING_TIMER] >= delay:
                game.world.get_map().set_dynatile(tile_x, tile_y, True)
                game.world.get_map().set_tile(tile_x, tile_y, Tiles.PLAINS)
                game.world.get_map().tile_manager.draw(
                    tile_x * game.world.get_map().tile_manager.SIZE,
                    tile_y * game.world.get_map().tile_manager.SIZE,
                    Tiles.PLAINS,
                    game.world.get_map().get_dynatile_surface()
                )
                logger.debug(f'Destroyed tile ({tile_x}, {tile_y}) of type {tile}')
            else:
                game.world.get_map().tile_manager.draw(
                    tile_x * game.world.get_map().tile_manager.SIZE,
                    tile_y * game.world.get_map().tile_manager.SIZE,
                    game.world.get_map().get_tile(tile_x, tile_y),
                    game.world.get_map().get_dynatile_surface()
                )
                game.world.get_map().tile_manager.draw(
                    tile_x * game.world.get_map().tile_manager.SIZE,
                    tile_y * game.world.get_map().tile_manager.SIZE,
                    Tiles.BREAK_TILES_ANIM[int((pygame.time.get_ticks() / 1000.0 - self.timers[Player.MINING_TIMER]) / delay * (len(Tiles.BREAK_TILES_ANIM) - 1))],
                    game.world.get_map().get_dynatile_surface()
                )

    def reset(self) -> None:
        """
        Reset the player's general attributes.
        """
        self._x = self._y = self.velocity_x = self.velocity_y = 0
        self.move = 0
        self.health = 100
        self.hurt = False

    def is_moving_left(self) -> bool:
        """
        Return True if the player is moving left.
        """
        return bool((self.move >> PlayerStates.MOVE_LEFT) & 1)

    def is_moving_up(self) -> bool:
        """
        Return True if the player is moving up.
        """
        return bool((self.move >> PlayerStates.MOVE_UP) & 1)

    def is_moving_right(self) -> bool:
        """
        Return True if the player is moving right.
        """
        return bool((self.move >> PlayerStates.MOVE_RIGHT) & 1)

    def is_moving_down(self) -> bool:
        """
        Return True if the player is moving down.
        """
        return bool((self.move >> PlayerStates.MOVE_DOWN) & 1)

    def is_near_left_edge(self) -> bool:
        """
        Return True if the player is at the left-center of the screen.
        """
        return self.edges[PlayerStates.MOVE_LEFT]

    def is_near_top_edge(self) -> bool:
        """
        Return True if the player is at the top-center of the screen.
        """
        return self.edges[PlayerStates.MOVE_UP]

    def is_near_right_edge(self) -> bool:
        """
        Return True if the player is to the right-center of the screen.
        """
        return self.edges[PlayerStates.MOVE_RIGHT]

    def is_near_bottom_edge(self) -> bool:
        """
        Return True if the player is to the bottom-center of the screen.
        """
        return self.edges[PlayerStates.MOVE_DOWN]

    def is_in_water(self, map_obj: Map) -> bool:
        """
        Returns True if the player is in water.
        """
        tile_x, tile_y = map_obj.get_tile_pos(self._x, self._y)
        return map_obj.get_tile(tile_x, tile_y) == Tiles.WATER

    def is_in_lava(self, map_obj: Map) -> bool:
        """
        Returns True if the player is in lava.
        """
        tile_x, tile_y = map_obj.get_tile_pos(self._x, self._y)
        return map_obj.get_tile(tile_x, tile_y) == Tiles.LAVA

    def is_in_lethal_tile(self, map_obj: Map) -> bool:
        """
        Returns True if the player is touching a lethal tile.
        """
        tile_x, tile_y = map_obj.get_tile_pos(self._x, self._y)
        return map_obj.get_tile(tile_x, tile_y) in TileTypes.LETHAL

    def is_in_wall(self, map_obj: Map) -> bool:
        """
        Returns True if the player is surrounded by tiles with collision.
        """
        tile_x, tile_y = map_obj.get_tile_pos(self._x, self._y)
        return map_obj.get_tile(tile_x, tile_y) in TileTypes.BREAKABLE

    def is_dead(self) -> bool:
        """
        Returns True if the player is dead.
        """
        return self.health <= 0

    def can_break_breakable(self, map_obj: Map) -> bool:
        """
        Returns True if the player is able to access and break a breakable tile.
        """
        return (pygame.mouse.get_pressed()[MouseStates.LMB - 1]
                and self.main_hud.hotbar.get_selected_slot_item() == Items.SHOVEL
                and self.has_selected_breakable(map_obj)
                and not self.is_selected_breakable_obstructed(map_obj))

    def has_selected_breakable(self, map_obj: Map) -> bool:
        """
        Returns True if the player has selected a breakable tile.
        """
        return map_obj.get_tile(self.selected_tile_x, self.selected_tile_y) in TileTypes.BREAKABLE

    def is_selected_breakable_obstructed(self, map_obj: Map) -> bool:
        """
        Returns True if the selected breakable tile is obstructed by other tiles with collision.
        """
        tile_x, tile_y = map_obj.get_tile_pos(self._x, self._y)
        x0, y0 = tile_x, tile_y
        x1, y1 = self.selected_tile_x, self.selected_tile_y
        print(self.selected_tile_x, self.selected_tile_y)

        # Bresenham (Thanks Wikipedia)
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy

        while True:  # Nul à chier mais flm de corriger
            if not (x0 == x1 and y0 == y1) and map_obj.get_tile(x0, y0) in TileTypes.BREAKABLE:
                return True
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * error
            if e2 >= dy:
                if x0 == x1:
                    break
                error += dy
                x0 += sx
            if e2 <= dx:
                if y0 == y1:
                    break
                error += dx
                y0 += sy

        try:
            if (map_obj.get_tile(self.selected_tile_x - 1, self.selected_tile_y) in TileTypes.BREAKABLE
                    and map_obj.get_tile(self.selected_tile_x + 1, self.selected_tile_y) in TileTypes.BREAKABLE
                    and map_obj.get_tile(self.selected_tile_x, self.selected_tile_y - 1) in TileTypes.BREAKABLE
                    and map_obj.get_tile(self.selected_tile_x, self.selected_tile_y + 1) in TileTypes.BREAKABLE):
                return True
            if tile_x > self.selected_tile_x and tile_y > self.selected_tile_y:
                return (map_obj.get_tile(self.selected_tile_x + 1, self.selected_tile_y) in TileTypes.BREAKABLE
                        and map_obj.get_tile(self.selected_tile_x, self.selected_tile_y + 1) in TileTypes.BREAKABLE)
            if tile_x < self.selected_tile_x and tile_y > self.selected_tile_y:
                return (map_obj.get_tile(self.selected_tile_x - 1, self.selected_tile_y) in TileTypes.BREAKABLE
                        and map_obj.get_tile(self.selected_tile_x, self.selected_tile_y + 1) in TileTypes.BREAKABLE)
            if tile_x > self.selected_tile_x and tile_y < self.selected_tile_y:
                return (map_obj.get_tile(self.selected_tile_x + 1, self.selected_tile_y) in TileTypes.BREAKABLE
                        and map_obj.get_tile(self.selected_tile_x, self.selected_tile_y - 1) in TileTypes.BREAKABLE)
            if tile_x < self.selected_tile_x and tile_y < self.selected_tile_y:
                return (map_obj.get_tile(self.selected_tile_x - 1, self.selected_tile_y) in TileTypes.BREAKABLE
                        and map_obj.get_tile(self.selected_tile_x, self.selected_tile_y - 1) in TileTypes.BREAKABLE)
        except IndexError:
            return True
        return False

    def set_x(self, x: int) -> Self:
        """
        Set the player's x position, then return the player itself.
        """
        self._x = x
        return self

    def get_x(self) -> int:
        """
        Return the player's x position.
        """
        return self._x

    def set_y(self, y: int) -> Self:
        """
        Set the player's y position, then return the player itself.
        """
        self._y = y
        return self

    def get_y(self) -> int:
        """
        Return the player's y position.
        """
        return self._y

    def get_absolute_x(self, map_obj: Map) -> int:
        """
        Return the player's x position as if the map's top-left corner were to be positioned at the origin (0, 0).
        This signifies that the returned value will always be positive.
        """
        return self._x + map_obj.get_width_in_pixels() // 2

    def get_absolute_y(self, map_obj: Map) -> int:
        """
        Return the player's y position as if the map's top-left corner were to be positioned at the origin (0, 0).
        This signifies that the returned value will always be positive.
        """
        return self._y + map_obj.get_height_in_pixels() // 2

    def get_coefficient_from_center_x(self, parent_width: int) -> float:
        """
        Return the coefficient indicating how far the player is away from the horizontal center of the screen.
        """
        return 1 + abs(self.screen_x - parent_width // 2) / (parent_width // 2)

    def get_coefficient_from_center_y(self, parent_height: int) -> float:
        """
        Return the coefficient indicating how far the player is away from the vertical center of the screen.
        """
        return 1 + abs(self.screen_y - parent_height // 2) / (parent_height // 2)

    def get_selected_tile_x(self) -> int:
        """
        Return the selected tile's x position.
        """
        return self.selected_tile_x

    def get_selected_tile_y(self) -> int:
        """
        Return the selected tile's y position.
        """
        return self.selected_tile_y

    def set_health(self, health: int) -> Self:
        """
        Set the player's health.
        """
        self.health = health
        return self

    def get_health(self) -> int:
        """
        Return the player's health.
        """
        return self.health

    def get_walls(self, map_obj: Map) -> list[bool]:
        """
        Return the tiles of type BREAKABLE surrounding the player.
        This is used for determining what tiles the player could potentially collide with.
        The order of the tiles are MOVE_LEFT, MOVE_RIGHT, MOVE_UP, MOVE_DOWN, UPPER MOVE_LEFT, UPPER MOVE_RIGHT, LOWER MOVE_LEFT, LOWER MOVE_RIGHT.
        """
        walls = [False] * 8
        tile_x, tile_y = map_obj.get_tile_pos(self._x, self._y)
        if tile_x > 0:
            walls[0] = map_obj.get_tile(tile_x - 1, tile_y) in TileTypes.BREAKABLE  # Left
        if tile_x < map_obj.get_width_in_tiles() - 1:
            walls[1] = map_obj.get_tile(tile_x + 1, tile_y) in TileTypes.BREAKABLE  # Right
        if tile_y > 0:
            walls[2] = map_obj.get_tile(tile_x, tile_y - 1) in TileTypes.BREAKABLE  # Up
        if tile_y < map_obj.get_height_in_tiles() - 1:
            walls[3] = map_obj.get_tile(tile_x, tile_y + 1) in TileTypes.BREAKABLE  # Down
        if tile_x > 0 and tile_y > 0:
            walls[4] = map_obj.get_tile(tile_x - 1, tile_y - 1) in TileTypes.BREAKABLE  # Upper left
        if tile_x < map_obj.get_width_in_tiles() - 1 and tile_y > 0:
            walls[5] = map_obj.get_tile(tile_x + 1, tile_y - 1) in TileTypes.BREAKABLE  # Upper right
        if tile_x > 0 and tile_y < map_obj.get_height_in_tiles() - 1:
            walls[6] = map_obj.get_tile(tile_x - 1, tile_y + 1) in TileTypes.BREAKABLE  # Lower left
        if tile_x < map_obj.get_width_in_tiles() - 1 and tile_y < map_obj.get_height_in_tiles() - 1:
            walls[7] = map_obj.get_tile(tile_x + 1, tile_y + 1) in TileTypes.BREAKABLE  # Lower right
        return walls

    def set_ideal_spawn_point(self, map_obj: Map, camera_obj: Camera, nb_attempts: int = 3) -> None:
        """
        Find the ideal starting position for the player when creating a new map.
        By default, three consecutive failed attempts will replace the tile at the last randomised tile position
        to plains and place the player there.
        Setting the number of attempts to anything less than 1 will raise an exception.
        """
        if nb_attempts < 1:
            raise ZeroOrLessSpawnPlayerAttempts

        tile_x: int = 0
        tile_y: int = 0
        bad_tiles = TileTypes.BREAKABLE + (Tiles.LAVA,)
        for i in range(nb_attempts):
            tile_x = randint(0, map_obj.get_width_in_tiles() - 1)
            tile_y = randint(0, map_obj.get_height_in_tiles() - 1)
            print(tile_x, tile_y, map_obj.get_tile(tile_x, tile_y))
            if map_obj.get_tile(tile_x, tile_y) not in bad_tiles:
                self._x, self._y = map_obj.tile_to_world_pos(tile_x, tile_y)
                camera_obj.x, camera_obj.y = self._x, self._y
                return
        map_obj.set_dynatile(tile_x, tile_y, True)
        map_obj.set_tile(tile_x, tile_y, Tiles.PLAINS)
        map_obj.tile_manager.draw(
            tile_x * map_obj.tile_manager.SIZE,
            tile_y * map_obj.tile_manager.SIZE,
            Tiles.PLAINS,
            map_obj.get_dynatile_surface()
        )
        self._x, self._y = map_obj.tile_to_world_pos(tile_x, tile_y)
        camera_obj.x, camera_obj.y = self._x, self._y

