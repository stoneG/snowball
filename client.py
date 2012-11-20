# This is the client side
import json
import math
import pdb
import pygame
import pygame.gfxdraw
import socket
import sys
import weakref

from util import *
#import server

# socket family is AF_INET, the Internet family of protocols
# SOCK_DGRAM refers to using UDP (and sending 'datagrams' aka packets)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

SERVER = sys.argv[1]

# Server will delegate game_master identity to first client to connect.
# If True, this client will initialize the start of the game

X_MAX = 1200
Y_MAX = 500
SCREEN_SIZE = [X_MAX, Y_MAX]


class Game:
    def __init__(self):
        self.master = False
        self.players = 0
        self.timeouts = 0
        self.timer = 4.0
        self.reset = False
        self.snowstorm = []
        self.playing = True
        self.winner = white


class EventManager:
    """Coordinates communication between Model, View, and Controller."""
    def __init__(self):
        self.listeners = weakref.WeakKeyDictionary()

    # Listeners are objects that are awaiting input on which event they should
    # process (ie TickEvent or QuitEvent)
    def register_listener(self, listener):
        self.listeners[listener] = 1

    def unregister_listener(self, listener):
        if listener in self.listeners.keys():
            del self.listeners[listener]

    def post(self, event):
        """Post a new event broadcasted to listeners"""
        for listener in self.listeners.keys():
            # NOTE: if listener was unregistered then it will be gone already
            listener.notify(event)


class ConnectEvent:
    def __init__(self):
        pass


class StartEvent:
    def __init__(self):
        pass


class TickEvent:
    def __init__(self, game_over=False):
        self.game_over = game_over


class ResetEvent:
    def __init__(self, reset=False):
        game.master = False
        game.players = 0
        game.timeouts = 0
        self.reset = reset


class QuitEvent:
    def __init__(self):
        game.playing = False


class StateController:
    def __init__(self, eventManager):
        self.event_manager = eventManager
        self.event_manager.register_listener(self)
        self.connect = True
        self.start = True
        self.keep_going = True

    def run(self):

        while self.connect and self.start and self.keep_going:
            posting_time = time_it(self.event_manager.post(ConnectEvent()))
            time_remaining = TICK_TIME - posting_time # milliseconds
            if time_remaining > 0:
                s.settimeout((time_remaining)*0.001) # seconds
                try:
                    msg, _ = s.recvfrom(MAX)
                except socket.timeout:
                    continue
            instruction, players = json.loads(msg)
            if instruction == 'MASTER':
                game.master = True
            game.players = int(players)
            event = StartEvent()
            self.notify(event)

        while self.start and self.keep_going:
            posting_time = time_it(self.event_manager.post(StartEvent()))
            time_remaining = TICK_TIME - posting_time # milliseconds
            if time_remaining > 0:
                s.settimeout((time_remaining)*0.001) # seconds
                try:
                    msg, _ = s.recvfrom(MAX)
                except socket.timeout:
                    continue
            instruction, players = json.loads(msg)
            if instruction == 'START':
                self.notify(TickEvent())
            else:
                game.players = int(players)

        while self.keep_going:
            if game.reset:
                event = ResetEvent()
            else:
                event = TickEvent()
            posting_time = time_it(self.event_manager.post(event))
            if game.reset:
                game.timer -= 0.03
                time.sleep((30-posting_time)*0.001)
            if game.timer < 1.1:
                event = ResetEvent(reset=True)
                self.event_manager.post(event)

        self.keep_going = True
        game.reset = False
        game.timer = 4.0

    def notify(self, event):
        if isinstance(event, QuitEvent):
            self.keep_going = False
        if isinstance(event, TickEvent):
            self.start = False
        if isinstance(event, ResetEvent):
            self.connect, self.start = True, True
            if event.reset:
                self.keep_going = False
        if isinstance(event, StartEvent):
            self.connect = False


class ConnectionController:
# NOTE currently not used
    def __init__(self):
        self.event_manager = eventManager
        self.event_manager.register_listener(self)
        self.state = 'asdf'

    def notify(self, event):
        if isinstance(event, TickEvent):
            self.connect = False

    def receive(time_remaining):
        if time_remaining > 0:
            s.settimeout((time_remaining)*0.001) # seconds
            try:
                msg, _ = s.recvfrom(MAX)
                game.instructions, data = json.loads(msg)
            except socket.timeout:
                return False
        if instruction == 'START' and self.connect:
                self.notify(TickEvent())
                return True
        elif instruction == 'MASTER' and self.connect:
            game.master = True
        game.players = int(data)
        return True

    def send():
        pass


class KeyboardController:
    def __init__(self, eventManager):
        self.event_manager = eventManager
        self.event_manager.register_listener(self)

    def notify(self, event):

        if isinstance(event, QuitEvent):
            return

        for game_event in pygame.event.get():
            if game_event.type == pygame.QUIT:
                self.event_manager.post(QuitEvent())
                return

        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_ESCAPE]:
            self.event_manager.post(QuitEvent())
            return

        if isinstance(event, ConnectEvent):

            if pressed[pygame.K_SPACE]:
                connect = json.dumps(['SPACE'], separators=(',',':'))
                s.sendto(connect, (SERVER, PORT))

        if isinstance(event, StartEvent):

            if pressed[pygame.K_s] and game.master:
                start = json.dumps(['START'], separators=(',',':'))
                s.sendto(start, (SERVER, PORT))

        if isinstance(event, TickEvent):

            keys_pressed = []

            if not event.game_over:
                # Keyboard Game Controls
                if pressed[pygame.K_UP]:
                    keys_pressed += ['UP']

                if pressed[pygame.K_DOWN]:
                    keys_pressed += ['DOWN']

                if pressed[pygame.K_LEFT]:
                    keys_pressed += ['LEFT']

                if pressed[pygame.K_RIGHT]:
                    keys_pressed += ['RIGHT']

                if pressed[pygame.K_SPACE]:
                    keys_pressed += ['SPACE']

                if keys_pressed:
                    keys_pressed = json.dumps(keys_pressed, separators=(',',':'))
                    s.sendto(keys_pressed, (SERVER, PORT))


class View:
    def __init__(self, eventManager):
        self.event_manager = eventManager
        self.event_manager.register_listener(self)

        self.window = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("snowball, the game")

        self.title = pygame.font.Font(None, 100)
        self.msg = pygame.font.Font(None, 40)

    def notify(self, event):

        self.window.fill(black)

        if isinstance(event, ConnectEvent):

            self.draw_text('~*~snowball~*~', self.title, white, y=200)
            self.draw_text('hit SPACE to connect to server', self.msg, blue, y=400)

        elif isinstance(event, StartEvent):

            self.draw_text('~*~snowball~*~', self.title, white, y=200)

            if game.master:
                self.draw_text("hit 's' to start game", self.msg, blue, y=400)
                self.draw_text('snowballs formed: %d' % game.players, self.msg, blue, y=350)
            else:
                self.draw_text('snowballs formed: %d' % game.players, self.msg, blue, y=350)

        if isinstance(event, TickEvent):

            if game.timeouts > 161:
                self.event_manager.post(ResetEvent())
                return

            s.settimeout((TICK_TIME)*0.001)
            try:
                snowstorm, address = s.recvfrom(MAX)
            except socket.timeout:
                game.timeouts += 1
                return
            instructions, snowstorm = json.loads(snowstorm)
            game.timeouts = 0

            if instructions[0] == 'RESET':
                print 'posting reset'
                game.reset = True
                game.winner = instructions[1]
                self.event_manager.post(ResetEvent())
                return
            elif len(snowstorm):
                game.snowstorm = snowstorm

            if len(game.snowstorm):
                for snow in game.snowstorm:
                    x, y, r, c = snow
                    if not c:
                        c = white
                    pygame.gfxdraw.aacircle(self.window, x, y, r, c)
                    pygame.gfxdraw.filled_circle(self.window, x, y, r, c)

            if event.game_over:
                self.draw_text('You Lose', self.title, red)

        if isinstance(event, ResetEvent):
            for snow in game.snowstorm:
                x, y, r, c = snow
                if not c:
                    c = white
                pygame.gfxdraw.aacircle(self.window, x, y, r, c)
                pygame.gfxdraw.filled_circle(self.window, x, y, r, c)

            self.draw_text('WINNER!', self.title, game.winner)
            self.draw_text('reset in %d' % game.timer, self.msg, blue, y=400)

        pygame.display.flip()

        if isinstance(event, QuitEvent):
            pass

    def draw_text(self, text, textType, color, x=X_MAX/2, y=Y_MAX/2):
        """Given text to draw, draw text on self.window."""
        text = textType.render(text, True, color)
        text_rectangle = text.get_rect()
        text_rectangle.centerx, text_rectangle.centery = x, y
        self.window.blit(text, text_rectangle)


pygame.init()

game = Game()

def main():
    event_manager = EventManager()
    keyboard = KeyboardController(event_manager)
    state = StateController(event_manager)
    view = View(event_manager)

    while game.playing:
        state.run()

if __name__ == '__main__':
    main()
