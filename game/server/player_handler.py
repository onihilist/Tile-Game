
from game.entity.player import Player
from game.utils.logger import logger


class PlayerHandler:
    """
    Class for creating the player handler.
    """

    def __init__(self) -> None:
        self._players: list[dict] = list()

    def track_player(self, player: dict) -> str:
        """
        Track the specified player by adding them to the players list.
        """
        self._players.append(player)
        print(f'Welcome, {player["name"]}!')
        return player['name']

    def update_player(self, player: dict) -> None:
        """
        Update the player attributes with the received player object, if possible.
        """
        logger.debug(f'Updating player \'{player["name"]}\'')
        index = next((i for i, p in enumerate(self._players) if p['name'] == player['name']), None)
        if index is None:
            self.track_player(player)
            return
        self._players[index]['previous_x'] = self._players[index]['x']
        self._players[index]['previous_y'] = self._players[index]['y']
        self._players[index]['x'] = player['x']
        self._players[index]['y'] = player['y']

    def untrack_player(self, player_name: str) -> None:
        """
        Untrack the player by removing them from the players list, if possible.
        """
        logger.debug(f'Untracking player \'{player_name}\'')
        index = next((i for i, p in enumerate(self._players) if p['name'] == player_name), None)
        if index is None:
            logger.debug(f'Player \'{player_name}\' could not be untracked, as they were not found in the player list.')
            return
        self._players.pop(index)

    def get_players(self) -> list[dict]:
        """
        Return the players list.
        """
        return self._players
