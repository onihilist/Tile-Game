
from pygame import K_UP, K_DOWN, K_LEFT, K_RIGHT
from pygame import key
from pygame.math import clamp

from game.data.properties import CameraProperties
from game.utils.logger import logger


class Camera:
    """
    Class for creating a camera.
    The camera position is strictly relative to the center of the screen.
    """

    def __init__(self, speed: int = 50) -> None:
        self.x = 0
        self.y = 0
        self.speed = speed
        self.velocity_x = 0
        self.velocity_y = 0
        logger.debug(f'Created {__class__.__name__} with attributes {self.__dict__}')

    def update(self, game) -> None:
        """
        Update the camera.
        """
        d: float = game.clock.get_time() / 1000.0

        if self.velocity_x != 0:
            self.x += self.speed * game.client.player.get_coefficient_from_center_x(game.width) * self.velocity_x * d
        if self.velocity_y != 0:
            self.y += self.speed * game.client.player.get_coefficient_from_center_y(game.height) * self.velocity_y * d

        print(f'{self.velocity_x=} {self.velocity_y=}')

        if game.client.player.is_near_left_edge():
            self.velocity_x = clamp(self.velocity_x - d / CameraProperties.VELOCITY_START_DURATION, -1, 1)
        elif game.client.player.is_near_right_edge():
            self.velocity_x = clamp(self.velocity_x + d / CameraProperties.VELOCITY_START_DURATION, -1, 1)
        else:
            if -CameraProperties.VELOCITY_THRESHOLD / d < self.velocity_x < CameraProperties.VELOCITY_THRESHOLD / d and self.velocity_x != 0:
                self.velocity_x = 0
            elif self.velocity_x > 0:
                self.velocity_x = clamp(self.velocity_x - d / CameraProperties.VELOCITY_STOP_DURATION, 0, 1)
            elif self.velocity_x < 0:
                self.velocity_x = clamp(self.velocity_x + d / CameraProperties.VELOCITY_STOP_DURATION, -1, 0)

        if game.client.player.is_near_top_edge():
            self.velocity_y = clamp(self.velocity_y - d / CameraProperties.VELOCITY_START_DURATION, -1, 1)
        elif game.client.player.is_near_bottom_edge():
            self.velocity_y = clamp(self.velocity_y + d / CameraProperties.VELOCITY_START_DURATION, -1, 1)
        else:
            if -CameraProperties.VELOCITY_THRESHOLD / d < self.velocity_y < CameraProperties.VELOCITY_THRESHOLD / d and self.velocity_y != 0:
                self.velocity_y = 0
            elif self.velocity_y > 0:
                self.velocity_y = clamp(self.velocity_y - d / CameraProperties.VELOCITY_STOP_DURATION, 0, 1)
            elif self.velocity_y < 0:
                self.velocity_y = clamp(self.velocity_y + d / CameraProperties.VELOCITY_STOP_DURATION, -1, 0)

    def reset(self) -> None:
        """
        Reset the camera's general properties.
        """
        self.x = self.y = self.velocity_x = self.velocity_y = 0
