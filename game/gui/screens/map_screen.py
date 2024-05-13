
from pygame.draw import rect
from pygame.surface import Surface
from pygame.transform import smoothscale_by

from game.data.states import MapStates
from game.gui.screens.screen import Screen
from game.gui.label import Label
from game.utils.logger import logger



class MapScreen(Screen):
    """
    Class for creating the map screen.
    """

    def __init__(self, game) -> None:
        super().__init__()
        self.game = game
        self._got_map = False
        self.faded_surface = self.initialise_surface()
        self.title_label = Label('Map')
        self.scaled_map: Surface = Surface((0, 0))
        logger.debug(f'Created {__class__.__name__} with attributes {self.__dict__}')

    def initialise_surface(self) -> Surface:
        """
        Initialise the screen's surface.
        """
        surface = Surface((self.game.width, self.game.height))
        surface.fill((0, 0, 0))
        surface.set_alpha(96)
        return surface

    def initialise_map(self) -> None:
        """
        Initialise the screen's map component.
        """
        if self._got_map or self.game.world.get_map().get_state()[0] != MapStates.READY or not self.game.start_game:
            return
        print("GET NEW MAP")
        coefficient = min(self.game.width / self.game.world.get_map().get_width_in_pixels() * 0.5,
                          self.game.height / self.game.world.get_map().get_height_in_pixels() * 0.5)
        self.scaled_map = smoothscale_by(self.game.world.get_map().get_surface(), round(coefficient, 2))
        self._got_map = True

    def reset_map(self) -> None:
        """
        Reset the map attributes.
        """
        self._got_map = False

    def draw(self) -> None:
        """
        Draw the screen and its components.
        """
        if self._enabled:
            self.game.screen.blit(self.faded_surface, (0, 0))
            self.title_label.draw(self.game.screen)
            self.game.screen.blit(self.scaled_map, (self.game.width // 2 - self.scaled_map.get_width() // 2,
                                               self.game.height // 2 - self.scaled_map.get_height() // 2))
            rect(self.game.screen, (255, 255, 255), (self.game.width // 2 - self.scaled_map.get_width() // 2 - 2,
                                                     self.game.height // 2 - self.scaled_map.get_height() // 2 - 2,
                                                     self.scaled_map.get_width() + 4, self.scaled_map.get_height() + 4), 4, 4)

    def update_ui(self) -> None:
        """
        Update the screen UI.
        """
        if self._got_map:
            coefficient = min(self.game.width / self.game.world.get_map().get_width_in_pixels() * 0.5,
                              self.game.height / self.game.world.get_map().get_height_in_pixels() * 0.5)
            self.scaled_map = smoothscale_by(self.game.world.get_map().get_surface(), round(coefficient, 2))
        self.faded_surface = self.initialise_surface()
        self.title_label.update(self.game)
        self.title_label.center_with_offset(0, 0, self.game.width, self.game.height, 0, -self.scaled_map.get_height() // 2 - self.title_label.get_total_height() - 5)

    def set_state(self, state: bool) -> None:
        """
        Set the screen's visibility/interactivity.
        """
        super().set_state(state)
        self.title_label.set_state(state)
