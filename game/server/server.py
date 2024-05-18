
from threading import Thread
from multiprocessing import Process, Value
import socket
from time import sleep

from game.data.properties import ServerProperties
from game.data.states import ServerStates
from game.network.protocol import Protocol
from game.network.packet import Hasher, Compressor
from game.server.player_handler import PlayerHandler
from game.server.tasks import Tasks
from game.server.world_handler import WorldHandler

# logger = logging.getLogger(__name__)


class Server:
    """
    Class for creating a new Server.
    """

    def __init__(self):
        self.state = Value('i', ServerStates.IDLE)
        self.player_count = 0
        self.sock: socket.socket | None = None
        self.timeout = 0
        self.world_handler: WorldHandler | None = None
        self.player_handler: PlayerHandler | None = None

    def client_handler(self, conn, addr):
        """
        Handle incoming server clients.
        """
        player_name: str = str()
        try:
            running = Tasks.recognition(conn, addr)
            Tasks.map_data(conn, addr, self.world_handler)
            data = conn.recv(Protocol.BUFFER_SIZE)
            if data and data == Hasher.enhash(Protocol.GAMEUPDATE_REQ):
                Tasks.send_game_state(conn, self.player_handler)
        except OSError:
            running = False
        print(f'Connection from: {addr}')
        self.player_count += 1
        while running:
            try:
                if self.state.value == ServerStates.IDLE:
                    running = False
                    continue
                data = conn.recv(Protocol.BUFFER_SIZE)
                # print(f'Message from {addr}: {data}')
                running = not Tasks.disconnection(data)
                name = Tasks.player_update(conn, self.player_handler, data)
                Tasks.send_game_state(conn, self.player_handler)
                player_name = name if name else player_name
                sleep(1.0 / ServerProperties.TICKS_PER_SECOND)
            except ConnectionResetError:
                running = False
            except BrokenPipeError:
                running = False
            except OSError:
                running = False
        print(f'Connection {addr} closing')
        self.player_handler.untrack_player(player_name)
        self.player_count -= 1
        conn.close()

    def update(self):
        pass

    def run(self, state):
        """
        Run the server and listen for connections.
        """
        self.world_handler = WorldHandler()
        self.player_handler = PlayerHandler()

        '''logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(threadName)s] [%(levelname)s] - %(message)s',
            handlers=[
                logging.FileHandler(path.join(get_game_property(LOG_DIR), strftime('%d-%m-%Y-%H-%M-%S.log'))),
                logging.StreamHandler(sys.stdout)
            ]
        )'''

        # Only IPv4 support for now
        # TODO: Add support for IPv6

        self.sock.listen()
        self.world_handler.create_world()

        state.value = ServerStates.RUNNING

        while state.value == ServerStates.RUNNING:
            conn, addr = self.sock.accept()
            thread = Thread(target=self.client_handler, args=(conn, addr))
            thread.start()

    def start(self):
        """
        Prepare the server.
        """

        self.state.value = ServerStates.STARTING
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        host = '0.0.0.0'
        port = 35000

        try:
            self.sock.bind((host, port))
        except OSError:
            self.state.value = ServerStates.FAIL
            print(f'Server failed to start.')
            return
        print(f'Starting server on {host}')
        server_thread = Process(target=self.run, args=(self.state,))
        server_thread.start()

    def stop(self):
        if self.state.value in (ServerStates.STARTING, ServerStates.RUNNING):
            self.sock.close()
            self.state.value = ServerStates.IDLE
            self.test()
            self.test()
            print(f'Server closed.')
            self.sock = None
            self.world_handler = None

    @staticmethod
    def test():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((socket.gethostbyname(socket.gethostname()), 35000))
            sock.send(Hasher.enhash('TEST'))
        except Exception:
            pass
