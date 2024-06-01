
import pygame

from game.data.data_manager import get_game_property, KEY_DELAY, KEY_INTERVAL
from game.data.keys import Keys
from game.data.states import MouseStates, ServerStates, ConnectionStates
from game.gui.screens.crash_screen import CrashScreen
from game.gui.screens.credits_screen import CreditsScreen
from game.gui.screens.gameover_screen import GameoverScreen
from game.gui.screens.loading_screen import LoadingScreen
from game.gui.screens.mainmenu_screen import MainMenuScreen
from game.gui.screens.map_screen import MapScreen
from game.gui.screens.options_screen import OptionsScreen
from game.gui.screens.pause_screen import PauseScreen
from game.gui.screens.servercreate_screen import ServerCreateScreen
from game.gui.screens.serverjoin_screen import ServerJoinScreen
from game.gui.screens.serverconnect_screen import ServerConnectScreen
from game.gui.screens.servermenu_screen import ServerMenuScreen
from game.utils.logger import logger


class Screens:
    """
    Class for creating a collection of screens.
    """

    def __init__(self, window) -> None:
        self.window = window
        self.game = None
        self.screen = self.window.screen
        self.crash_screen = CrashScreen(window)
        self.main_menu_screen = MainMenuScreen(window)
        self.server_menu_screen = ServerMenuScreen(window)
        self.server_join_screen = ServerJoinScreen(window)
        self.server_create_screen = ServerCreateScreen(window)
        self.server_connect_screen = ServerConnectScreen(window)
        self.loading_screen = LoadingScreen(window)
        self.pause_screen = PauseScreen(window)
        self.options_screen = OptionsScreen(window)
        self.credits_screen = CreditsScreen(window)
        self.gameover_screen = GameoverScreen(window)
        self.map_screen = MapScreen(window)
        logger.debug(f'Created {__class__.__name__} with attributes {self.__dict__}')

    def link_game(self, game_obj) -> None:
        """
        Link the global game instance.
        TODO: Remove this, it isn't good practice. And it's dirty.
        """
        self.game = game_obj
        self.options_screen.game = self.game
        self.map_screen.game = self.game

    def events(self, e: pygame.event.Event) -> None:
        """
        Track the events of the different screens.
        """
        keys = pygame.key.get_pressed()

        self.map_screen.initialise_map()

        if self.server_join_screen.get_state():
            self.server_join_screen.events(e)
        if self.server_create_screen.get_state():
            self.server_create_screen.events(e)
        self.loading_screen.events(e)
        self.options_screen.events(e)
        self.credits_screen.events(e)

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE and self.game.start_game and not self.loading_screen.get_state() and not self.gameover_screen.get_state():
                if self.options_screen.get_state():
                    self.options_screen.set_state(not self.options_screen.get_state())
                else:
                    self.pause_screen.set_state(not self.pause_screen.get_state())
                self.window.paused = self.pause_screen.get_state()
                self.map_screen.set_state(False)

        if self.game.start_game and not self.loading_screen.get_state() and not self.game.player.is_dead() and not self.game.paused:
            self.map_screen.set_state(keys[Keys.SHOW_MAP])

        if e.type == pygame.MOUSEBUTTONUP:
            if e.button == MouseStates.LMB:
                if self.options_screen.back_button.is_hovering_over():
                    self.options_screen.set_state(False)
                    if self.game.start_game:
                        self.pause_screen.set_state(True)
                    else:
                        self.main_menu_screen.set_state(True)

                elif self.credits_screen.back_button.is_hovering_over():
                    self.credits_screen.set_state(False)
                    self.main_menu_screen.set_state(True)

                elif self.main_menu_screen.play_button.is_hovering_over() and self.main_menu_screen.get_state():
                    self.main_menu_screen.set_state(False)
                    self.server_menu_screen.set_state(True)
                elif self.main_menu_screen.options_button.is_hovering_over() and self.main_menu_screen.get_state():
                    self.options_screen.set_state(True)
                    self.main_menu_screen.set_state(False)
                elif self.main_menu_screen.credits_button.is_hovering_over() and self.main_menu_screen.get_state():
                    self.credits_screen.set_state(True)
                    self.main_menu_screen.set_state(False)
                elif self.main_menu_screen.quit_button.is_hovering_over() and self.main_menu_screen.get_state():
                    self.window.stop()

                elif self.server_menu_screen.join_button.is_hovering_over() and self.server_menu_screen.get_state():
                    self.server_menu_screen.set_state(False)
                    self.server_join_screen.set_state(True)
                    pygame.key.set_repeat(int(get_game_property(KEY_DELAY)), int(get_game_property(KEY_INTERVAL)))
                    self.server_join_screen.join_button.set_state(
                        self.server_join_screen.ign_input.get_text().strip()
                        and self.server_join_screen.ip_input.get_text().strip()
                        and self.server_join_screen.port_input.get_text().strip()
                    )
                    self.server_join_screen.ign_input.set_text(self.game.player.get_player_name())
                    self.server_join_screen.update_ui()
                elif self.server_menu_screen.create_button.is_hovering_over() and self.server_menu_screen.get_state():
                    self.server_menu_screen.set_state(False)
                    self.server_create_screen.set_state(True)
                    pygame.key.set_repeat(int(get_game_property(KEY_DELAY)), int(get_game_property(KEY_INTERVAL)))
                    self.server_create_screen.create_button.set_state(
                        bool(self.server_create_screen.ign_input.get_text().strip())
                    )
                    self.server_create_screen.ign_input.set_text(self.game.player.get_player_name())
                    self.server_create_screen.update_ui()

                elif self.server_menu_screen.back_button.is_hovering_over() and self.server_menu_screen.get_state():
                    self.server_menu_screen.set_state(False)
                    self.main_menu_screen.set_state(True)

                elif self.server_join_screen.join_button.is_hovering_over() and self.server_join_screen.get_state():
                    self.server_join_screen.set_state(False)
                    self.server_connect_screen.set_state(True)
                    self.server_connect_screen.back_button.set_state(False)
                    self.game.connection_handler.start_connection = True
                    self.game.player.set_player_name(self.server_join_screen.ign_input.get_text().strip())
                elif self.server_join_screen.back_button.is_hovering_over() and self.server_join_screen.get_state():
                    self.server_join_screen.set_state(False)
                    self.server_menu_screen.set_state(True)
                    pygame.key.set_repeat()
                    self.game.player.set_player_name(self.server_join_screen.ign_input.get_text().strip())

                elif self.server_create_screen.create_button.is_hovering_over() and self.server_create_screen.get_state():
                    self.server_create_screen.set_state(False)
                    self.server_connect_screen.set_state(True)
                    self.server_connect_screen.back_button.set_state(False)
                    self.game.server.start()
                    if self.game.server.state.value != ServerStates.FAIL:
                        self.game.connection_handler.host = 'localhost'
                        self.game.connection_handler.port = 35000
                        self.game.connection_handler.start_connection = True
                        self.game.player.set_player_name(self.server_create_screen.ign_input.get_text().strip())
                    else:
                        self.game.server.stop()
                        self.server_connect_screen.back_button.set_state(True)
                        self.server_connect_screen.update_info_label(ConnectionStates.SERVFAIL)
                elif self.server_create_screen.back_button.is_hovering_over() and self.server_create_screen.get_state():
                    self.server_create_screen.set_state(False)
                    self.server_menu_screen.set_state(True)
                    pygame.key.set_repeat()
                    self.game.player.set_player_name(self.server_create_screen.ign_input.get_text().strip())

                elif self.server_connect_screen.back_button.is_hovering_over() and self.server_connect_screen.back_button.get_state():
                    self.server_connect_screen.set_state(False)
                    self.server_connect_screen.reset_info_label()
                    if self.server_connect_screen.default_screen:
                        self.server_join_screen.set_state(True)
                    else:
                        self.server_menu_screen.set_state(True)

                elif self.pause_screen.resume_button.is_hovering_over():
                    self.pause_screen.set_state(False)
                    self.window.paused = False
                elif self.pause_screen.options_button.is_hovering_over():
                    self.pause_screen.set_state(False)
                    self.options_screen.set_state(True)
                elif self.pause_screen.disconnect_button.is_hovering_over():
                    self.game.start_game = False
                    self.window.paused = False
                    self.game.connection_handler.stop_connection = True
                    self.game.server.stop()
                    self.pause_screen.set_state(False)
                    self.main_menu_screen.set_state(True)
                    self.map_screen.reset_map()

                elif self.gameover_screen.respawn_button.is_hovering_over():
                    self.gameover_screen.set_state(False)
                    self.game.player.reset(self.game.world.get_map(), self.game.camera)
                elif self.gameover_screen.disconnect_button.is_hovering_over():
                    self.game.start_game = False
                    self.window.paused = False
                    self.game.connection_handler.stop_connection = True
                    self.gameover_screen.set_state(False)
                    self.main_menu_screen.set_state(True)

    def update(self) -> None:
        """
        Update the screens.
        """
        self.crash_screen.draw()
        self.main_menu_screen.draw()
        self.server_menu_screen.draw()
        self.server_join_screen.draw()
        self.server_create_screen.draw()
        self.server_connect_screen.draw()
        self.loading_screen.draw()
        self.pause_screen.draw()
        self.options_screen.draw()
        self.credits_screen.draw()
        self.gameover_screen.draw()
        self.map_screen.draw()

    def update_ui(self) -> None:
        """
        Update the screen UIs.
        """
        self.crash_screen.update_ui()
        self.main_menu_screen.update_ui()
        self.server_menu_screen.update_ui()
        self.server_join_screen.update_ui()
        self.server_create_screen.update_ui()
        self.server_connect_screen.update_ui()
        self.loading_screen.update_ui()
        self.pause_screen.update_ui()
        self.options_screen.update_ui()
        self.credits_screen.update_ui()
        self.gameover_screen.update_ui()
        self.map_screen.update_ui()

