# Shared utilities in server.py/client.py
import time

# Network utilities
MAX = 65535
PORT = 1060

# Time utilities
TICK_TIME = 31

def current_time():
    return(int(round(time.time() * 100)))

def time_it(function):
    lt = current_time()
    function
    t = current_time()
    return t - lt

# Color utilities
black    = (   0,   0,   0)
white    = ( 255, 255, 255)
green    = (   0, 255,   0)
red      = ( 255,   0,   0)
blue     = (  65, 105, 225)
yellow   = ( 255, 255,   0)
orchid   = ( 218, 112, 214)
