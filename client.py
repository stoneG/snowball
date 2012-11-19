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
game_master = False
players = 0

X_MAX = 1200
Y_MAX = 500
SCREEN_SIZE = [X_MAX, Y_MAX]


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


class QuitEvent:
    def __init__(self):
        pass


class StateController:
    def __init__(self, eventManager):
        self.event_manager = eventManager
        self.event_manager.register_listener(self)
        self.connect = True
        self.start = True
        self.keep_going = True

    def run(self):

        global players
        global game_master
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
                game_master = True
            players = int(players)
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
                players = int(players)

        while self.keep_going:
            self.event_manager.post(TickEvent())

    def notify(self, event):
        if isinstance(event, QuitEvent):
            self.keep_going = False
        if isinstance(event, TickEvent):
            self.start = False
        if isinstance(event, StartEvent):
            self.connect = False


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

            if pressed[pygame.K_s] and game_master:
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

            if game_master:
                self.draw_text("hit 's' to start game", self.msg, blue, y=400)
                self.draw_text('snowballs formed: %d' % players, self.msg, blue, y=350)
            else:
                self.draw_text('snowballs formed: %d' % players, self.msg, blue, y=350)

        if isinstance(event, TickEvent):

            s.settimeout((TICK_TIME)*0.001)
            try:
                snowstorm, address = s.recvfrom(MAX)
                _, snowstorm = json.loads(snowstorm)
            except socket.timeout:
                #print 'Server not responding'
                return

            if len(snowstorm):
                for snow in snowstorm:
                    x, y, r, c = snow
                    if not c:
                        c = white
                    pygame.gfxdraw.aacircle(self.window, x, y, r, c)
                    pygame.gfxdraw.filled_circle(self.window, x, y, r, c)

            if event.game_over:
                self.draw_text('You Lose', self.title, red)

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

def main():
    event_manager = EventManager()
    keyboard = KeyboardController(event_manager)
    state = StateController(event_manager)
    view = View(event_manager)

    state.run()

if __name__ == '__main__':
    main()
