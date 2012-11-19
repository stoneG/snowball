# This is the server side
import json
import math
import pdb
import random
import socket
import sys
import threading
import weakref

from util import *

#-------------#
#  Constants  #
#-------------#

# Set listening IP
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(('google.com', 0))
    IP = sys.argv[1] if len(sys.argv) > 1 else s.getsockname()[0]
except socket.gaierror:
    IP = sys.argv[1] if len(sys.argv) > 1 else 'You are not connected to the internet'
s.close()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Model Constants
X_MAX = 1200
X_MID = X_MAX // 2
Y_MAX = 500
SNOW_X_MAX = X_MAX + 500
SNOW_X_MIN = -500
SNOW_Y_MAX = Y_MAX + 300
SNOW_Y_MIN = -300
GRAVITY_ON = True
WIND_ON = False
WIND_MAX = 7
X_WIND = [-2]*2 + [-1]*20 + [0]*300 + [1]*20 + [2]*2
Y_WIND = [-2, 1, 1, 0, 0, 0, 0, 1, 1, 2]
MIN_SNOWBALL_R = 3
MAX_SNOWBALL_SPEED = 20
IMMUNE_TIME = 2000
X_DAMPEN = 100
Y_DAMPEN = 100

# key:value -> (Client IP, Client Port):[[keys pressed], color]
clients = {}


#--------------------#
#  Helper Functions  #
#--------------------#

def sticky_sum(initial, shift):
    """Given an initial number and a shift to add to it, return the zero
    sticky sum."""
    if initial < 0:
        result = min(0, initial + shift)
        return result
    elif initial > 0:
        result = max(0, initial + shift)
        return result
    else: # initial == 0
        return 0

def dampen(initial, dampenAmount):
    """Given a initial number and a dampening amount, return the dampened
    result as an int."""
    initial_sign = math.copysign(1, initial)
    dampenAmount = math.copysign(dampenAmount, -initial_sign)
    result = sticky_sum(initial, dampenAmount)
    return(int(result))

def current_time():
    """Returns the current time in milliseconds."""
    return(int(round(time.time() * 1000)))

def partial_absorb(objOne, objTwo, collidingPixels):
    """objOne absorbs the area of objTwo, void return"""
    objTwo.r += int(-collidingPixels)
    area_loss = objTwo.area - math.pi * objTwo.r**2
    true_area_loss = objTwo.true_area * (area_loss / objTwo.area)
    objOne.area, objTwo.area = objOne.area + area_loss, objTwo.area - area_loss
    objOne.true_area = objOne.true_area + true_area_loss
    objTwo.true_area = objTwo.true_area - true_area_loss
    objOne.r = int(math.sqrt(objOne.area/math.pi))

def absorb(objOne, objTwo):
    """objOne absorbs the area of objTwo, void return"""
    objOne.area += objTwo.area
    objOne.true_area += objTwo.true_area
    objOne.r = int(math.sqrt(objOne.area/math.pi))

def collision(objOne, objTwo):
    """Given size and space parameters for each object, return boolean for
       whether collision occurs"""
    origin_distance = math.sqrt((objOne.x - objTwo.x)**2 + (objOne.y - objTwo.y)**2)
    collision_distance = objOne.r + objTwo.r
    colliding_pixels = max(0, collision_distance - origin_distance)
    if origin_distance <= max(objOne.r, objTwo.r):
        if objOne.area >= objTwo.area:
            absorb(objOne, objTwo)
            reset(objTwo)
        else:
            absorb(objTwo, objOne)
            reset(objOne)
    elif colliding_pixels:
        if objOne.area >= objTwo.area:
            partial_absorb(objOne, objTwo, colliding_pixels)
        else:
            partial_absorb(objTwo, objOne, colliding_pixels)

def reset(obj):
    """Return a tuple of x, y, r values to reset a snowflake."""
    x = random.randrange(SNOW_X_MIN, SNOW_X_MAX)
    y = random.randrange(SNOW_Y_MAX, SNOW_Y_MAX + 200)
    r = random.randrange(1, 8)
    area = math.pi * r**2
    obj.x, obj.y, obj.r, obj.area, obj.true_area = x, y, r, area, area

def serialize(snowstorm, allWhite=False):
    """Return a list of snow object attributes for sending as a JSON."""
    out = []
    if allWhite:
        for sf in snowstorm:
            x = sf.x
            y = sf.y
            r = sf.r
            out.append([x, y, r, []])
    else:
        for sb in snowstorm:
            x = sb.x
            y = sb.y
            r = sb.r
            c = sb.color
            out.append([x, y, r, c])
    return(out)

#-----------#
#  Classes  #
#-----------#

class Event:
    """Superclass for any event that needs to be sent to the EventManager."""
    def __init__(self):
        self.name = "Event"

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
    pass


class TickEvent:
    def __init__(self, game_over=False):
        self.game_over = game_over


class QuitEvent:
    pass


class ResetEvent:
    pass


class Model:
    def __init__(self, eventManager):
        self.event_manager = eventManager
        self.event_manager.register_listener(self)

    def notify(self, event):
        if isinstance(event, TickEvent):

            if not snowballs:
                self.event_manager(ResetEvent())
                return

            # Choose wind
            wind.change_speed(random.choice(X_WIND), 0)

            # Snowstorm collision logic (only runs in the area of the screen+20px)
            quadtree = Quadtree(snowflakes+snowballs, bounds=(-20,X_MAX+20,Y_MAX+20,-20))
            for region in quadtree.regions():
                for i in range(len(region)-1):
                    sf = region.pop()
                    for other_sf in region:
                        collision(sf, other_sf)

            # Snowball logic and movement
            for (index, sb) in enumerate(snowballs):
                sb.calculate_speed()
                if sb.out_of_bounds(0, X_MAX, 0, Y_MAX):
                    del snowballs[index]
                    self.event_manager.post(TickEvent(game_over=True))
                    return
                # Currently not applying nature effects to snowballs
                # sb.nature_move(wind.xSpeed, gravity.ySpeed)
                for client in clients.values():
                    if client[1] == sb.color:
                        sb.control(client[0])
                        break

            # Snowflake movement and reset logic
            for sf in snowflakes:
                if sf.y < SNOW_Y_MIN or sf.x < SNOW_X_MIN or sf.x > SNOW_X_MAX:
                    reset(sf)
                sf.move(0, -1)
                sf.nature_move(wind.xSpeed, gravity.ySpeed)
            # TODO: Known bugs:
            # You lose screen


class PrintView:
    def __init__(self, eventManager):
        self.event_manager = eventManager
        self.event_manager.register_listener(self)

    def notify(self, event):

        if isinstance(event, ConnectEvent):
            pass

        if isinstance(event, TickEvent):
            snowstorm = serialize(snowflakes, True) + serialize(snowballs, False)
            snowstorm = ['START', snowstorm]
            snowstorm = json.dumps(snowstorm, separators=(',',':'))
            s.settimeout(10)
            for addr in clients:
                s.sendto(snowstorm, addr)

            if event.game_over:
                print 'Game Over'

        if isinstance(event, ResetEvent):
            print 'Reset Event'

class StateController:
    def __init__(self, eventManager):
        self.event_manager = eventManager
        self.event_manager.register_listener(self)
        self.master = None
        self.connect = True
        self.keep_going = True

    def run(self):

        s.bind((IP, PORT))
        print 'Listening at', s.getsockname()
        global clients
        global snowflakes
        global snowballs

        player_cols = [green, blue, red, yellow, orchid, white]

        while self.connect and self.keep_going:
            msg, addr = s.recvfrom(MAX)
            msg = json.loads(msg)
            if not self.master:
                if msg[0] == 'SPACE':
                    clients[addr] = [[], player_cols[0]]
                    msg = ['MASTER', 1]
                    msg = json.dumps(msg, separators=(',',':'))
                    s.sendto(msg, addr)
                    self.master = addr
                    print 'assigned master'
                    continue
            if addr == self.master:
                if msg[0] == 'START':
                    msg = ['START', len(clients.keys())]
                    msg = json.dumps(msg, separators=(',',':'))
                    for add in clients:
                        s.sendto(msg, add)
                    event = TickEvent()
                    self.notify(event)
                    print 'starting'
                    break
                else:
                    msg = ['MASTER', len(clients.keys())]
                    msg = json.dumps(msg, separators=(',',':'))
                    s.sendto(msg, addr)
                    print 'send to master'
                    continue
            if addr not in clients:
                clients[addr] = [[], player_cols[len(clients.keys())]]
            #msg = str(len(clients.keys()))
            msg = ['a', len(clients.keys())]
            msg = json.dumps(msg, separators=(',',':'))
            for add in clients:
                s.sendto(msg, add)

        players = len(clients.keys())

        # Snowballs
        balls = Snowstorm(players, 0, X_MAX, 0, Y_MAX)
        snowballs = balls.attributes('Snowballs', MIN_SNOWBALL_R, player_cols[:players])

        # Snowflakes
        flakes = Snowstorm(500, SNOW_X_MIN, SNOW_X_MAX, SNOW_Y_MIN, SNOW_Y_MAX)
        snowflakes = flakes.attributes('Snowflakes')

        while self.keep_going:
            # TickEvent starts events for the general game
            lt = current_time()
            event = TickEvent()
            self.event_manager.post(event)
            for client in clients.keys():
                clients[client] = [[], clients[client][1]]
            t = current_time()
            #print 'receiving keys starting %d' % (t - lt)
            while (TICK_TIME - t + lt) > 0:
                s.settimeout((TICK_TIME - t + lt)*0.001)
                try:
                    keys_pressed, addr = s.recvfrom(MAX)
                except socket.timeout:
                    break
                keys_pressed = json.loads(keys_pressed)
                for client in clients.keys():
                    if client == addr:
                        clients[client] = [keys_pressed, clients[client][1]]
                t = current_time()
            #abc = current_time()
            #print 'tick event over in %d' % (abc - lt)

        addr = json.dumps('Reset')
        for addr in clients:
            s.sendto(msg, addr)
        self.event_manager.post(ResetEvent())

    def notify(self, event):
        if isinstance(event, ResetEvent):
            self.master = None
            self.connect = True
            self.keep_going = True
        elif isinstance(event, QuitEvent):
            self.keep_going = False
        elif isinstance(event, TickEvent):
            self.connect = False


class ConnectionController:
    def __init__(self, eventManager):
        self.event_manager = eventManager
        self.event_manager.register_listener(self)

    def client_connect(self, client):
        event = ClientConnectEvent(client)
        self.event_manager.post(event)

    def notify(self):
        pass


class Quadtree:
    def __init__(self, snowObjects, maxLevels=5, bounds=None):
        # Subregions start empty
        self.nw = self.ne = self.se = self.sw = None

        maxLevels -= 1
        if maxLevels == 0:
            self.objects = [snowObjects]
            return

        if bounds:
            top, right, bottom, left = bounds
        else:
            top = min(snowObject.top() for snowObject in snowObjects)
            right = max(snowObject.right() for snowObject in snowObjects)
            bottom = max(snowObject.bottom() for snowObject in snowObjects)
            left = min(snowObject.left() for snowObject in snowObjects)
        center_x = (left + right) / 2
        center_y = (top + bottom) / 2

        self.objects = []
        nw_objects = []
        ne_objects = []
        se_objects = []
        sw_objects = []

        for obj in snowObjects:
            if obj.top() <= center_y and obj.left() <= center_x:
                nw_objects.append(obj)
            if obj.top() <= center_y and obj.right() >= center_x:
                ne_objects.append(obj)
            if obj.bottom() >= center_y and obj.right() >= center_x:
                se_objects.append(obj)
            if obj.bottom() >= center_y and obj.left() <= center_x:
                sw_objects.append(obj)

        if nw_objects:
            self.nw = Quadtree(nw_objects, maxLevels,
                               (top, center_x, center_y, left))

        if ne_objects:
            self.ne = Quadtree(ne_objects, maxLevels,
                               (top, right, center_y, center_x))

        if se_objects:
            self.se = Quadtree(se_objects, maxLevels,
                               (center_y, right, bottom, center_x))

        if sw_objects:
            self.sw = Quadtree(sw_objects, maxLevels,
                               (center_y, center_x, bottom, left))

    def regions(self):
        region = []

        if self.nw == self.ne == self.se == self.sw:
            region = self.objects

        if self.nw:
            region += self.nw.regions()
        if self.ne:
            region += self.ne.regions()
        if self.se:
            region += self.se.regions()
        if self.sw:
            region += self.sw.regions()

        return(region)


class Entity:
    def __init__(self, xPosition, yPosition, speed):
        self.x = xPosition
        self.y = yPosition
        self.speed = speed

class Snowflake(Entity):
    def __init__(self, xPosition, yPosition, radius, speed, color):
        Entity.__init__(self, xPosition, yPosition, speed)
        self.r = radius
        self.color = color
        self.area = math.pi * self.r**2
        self.true_area = self.area # Area if never compressed

    def __str__(self):
        return('(%d, %d)' % (self.x, self.y))

    #def position(self):
    #    return([self.xPosition, self.yPosition])

    def top(self):
        return(self.y - self.r)

    def bottom(self):
        return(self.y + self.r)

    def left(self):
        return(self.x - self.r)

    def right(self):
        return(self.x + self.r)

    def calculate_speed(self):
        limit = min(MAX_SNOWBALL_SPEED, int(self.true_area // (2 * self.area)))
        self.speed = max(1, limit)

    def move(self, x, y):
        """Move x and y position of Snowflake."""
        self.x += x
        self.y += y

    def nature_move(self, xSpeed, ySpeed):
        """Movement to Snowflake caused by wind."""
        if WIND_ON:
            self.x += dampen(xSpeed, self.true_area / X_DAMPEN)
        if GRAVITY_ON:
            self.y += dampen(ySpeed, self.true_area / Y_DAMPEN)

    def distance_from(self, position):
        """Distance from Snowflake to another [x, y] position"""
        distance = math.sqrt((self.x - position[0])**2
                             + (self.y - position[1])**2)
        return(distance)

    def recolor(self, newColor):
        # TODO: Make super colors later maybe
        # maybe the snow will be RGB and add to each RGB value!
        self.color = newColor

    def change_speed(self, amount):
        if (self.speed + amount) > 0:
            self.speed += amount
        else:
            self.speed = 1

    def draw(self, screen, antialias=False):
        """Draw snowflake on screen."""
        if antialias:
            pygame.gfxdraw.aacircle(screen, self.x, self.y, self.r, self.color)
        pygame.draw.circle(screen, self.color, [self.x, self.y], self.r)


class Snowball(Snowflake):
    def __init__(self, xPosition, yPosition, radius, speed, color):
        Snowflake.__init__(self, xPosition, yPosition, radius, speed, color)

    def control(self, keysPressed):
        """Given a list of keysPressed, alter Snowflake's attributes."""

        if 'SPACE' in keysPressed:
            self.compress(self.area/100)
            limit = min(MAX_SNOWBALL_SPEED, int(self.true_area // (2 * self.area)))
            self.speed = max(1, limit)

        if 'UP' in keysPressed:
            self.move(0, -self.speed)

        if 'DOWN' in keysPressed:
            self.move(0, self.speed)

        if 'LEFT' in keysPressed:
            self.move(-self.speed, 0)

        if 'RIGHT' in keysPressed:
            self.move(self.speed, 0)

    def compress(self, amount):
        """Given an amount to compress Snowflake, return compressed area."""
        minimum_area = MIN_SNOWBALL_R**2 * math.pi
        result = max(minimum_area, self.area - amount)
        resulting_radius = math.sqrt(result/math.pi)
        self.r = int(resulting_radius)
        self.area = int(result)

    def out_of_bounds(self, xMin, xMax, yMin, yMax):
        if self.x < xMin or self.x > xMax or self.y < yMin or self.y > yMax:
            return(True)

    def resize(self, amount):
        """Given amount to change radius, return radius sticky at 1."""
        if (self.r + amount) > 1:
            self.r + amount
        else:
            self.r == 1 # Cannot resize to nothing


class Snowstorm:
    def __init__(self, numberOfSnowflakes, xMin, xMax, yMin, yMax):
        self.intensity = numberOfSnowflakes
        self.xMin, self.xMax = xMin, xMax
        self.yMin, self.yMax = yMin, yMax

    def attributes(self, typeOfSnow, playerRadius=None,
                   playerColors=None):
        """Return list of snowflakes with given attributes."""

        attrs = []
        if typeOfSnow == 'Snowflakes':
            for i in range(self.intensity):
                x = random.randrange(self.xMin, self.xMax)
                y = random.randrange(self.yMin, self.yMax)
                r = random.randrange(1, 10)
                attrs.append(Snowflake(x, y, r, 1, white))
            return(attrs)

        if typeOfSnow == 'Snowballs':
            for i in range(self.intensity):
                x = (self.xMax * (i + 1)) / (self.intensity + 1)
                y = (self.yMax * (i + 1)) / (self.intensity + 1)
                r = playerRadius
                attrs.append(Snowball(x, y, r, 1, playerColors[i]))
            return(attrs)


class NatureEffect:
    def __init__(self, xSpeed, ySpeed):
        self.xSpeed, self.ySpeed = xSpeed, ySpeed

    def change_speed(self, xChange, yChange):
        self.xSpeed += xChange
        self.ySpeed += yChange
        if self.xSpeed >= WIND_MAX:
            self.xSpeed = WIND_MAX
        if self.xSpeed <= -WIND_MAX:
            self.xSpeed = -WIND_MAX
        if self.ySpeed >= WIND_MAX:
            self.ySpeed = WIND_MAX
        if self.ySpeed <= -WIND_MAX:
            self.ySpeed = -WIND_MAX

    def x_change(self, transition):
        "Uniformly draw the wind speed change in the x axis"
        i = random.randrange(len(transition))
        return(transition[i])

    def y_change(self, transition):
        "Uniformly draw the wind speed change in the y axis"
        i = random.randrange(len(transition))
        return(transition[i])

    def effect_on(self, obj):
        return(dampen(wind.speed, obj.r // 2))

# Wind
wind = NatureEffect(0,0)
gravity = NatureEffect(0,-3)

snowflakes = ''
snowballs = ''

#-----------------#
#  Main function  #
#-----------------#

def main():
    event_manager = EventManager()
    model = Model(event_manager)
    view = PrintView(event_manager)
    state = StateController(event_manager) 
    state.run()

if __name__ == '__main__':
    main()
