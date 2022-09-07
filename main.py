from poolstatus import *


stat = {
    "A": (2, .4), 
    "B": (3, .3)
}

ps = MultiTokenPoolStatus(stat)
print(ps)