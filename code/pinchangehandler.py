import math
import time
import queue

# Liste der Sender für die Synchronisierung
unit_list = {}
# Globals für die Pinchange-Routine
oldtick = 0
oldlevel = None
state = 'wait'
packet = []
bit = 0
preamblecount = 0
traincount = 0
long_high = 0
long_low = 0
short_high = 0
short_low = 0
long_high_min = 0
long_low_min = 0
short_high_min = 0
short_low_min = 0
long_high_max = 0
long_low_max = 0
short_high_max = 0
short_low_max = 0
packet_queue = queue.Queue()

def getqueue():
    global packet_queue
    return packet_queue


def pinchange(gpio, level, tick):
    global oldtick
    global oldlevel
    global state
    global packet
    global bit
    global packet_queue
    global preamblecount
    global traincount
    global long_high
    global long_low
    global short_high
    global short_low
    global long_high_min
    global long_low_min
    global short_high_min
    global short_low_min
    global long_high_max
    global long_low_max
    global short_high_max
    global short_low_max

    if oldlevel is None:
        oldlevel = level
    elif oldlevel == level:
        print('\nLost_Tick!')
    oldlevel = level
    duration = tick - oldtick
    oldtick = tick
    if duration >= 70:
        # wait ist der Wartestatus
        if state == 'wait' and level == 1:
            # lange Ruhe = vermutlich Preamble
            if 4000 < duration < 5500:
                state = 'preamble'
                preamblecount = 1
        elif state == 'preamble':
            if 380 < duration < 650:
                if preamblecount > 6:
                    state = 'train'
                    traincount = 1
                    bit = 1
                    packet[:] = []
                    packet.append(1)
                    packet.append(0)
                    packet.append(1)
                    packet.append(0)
                    packet.append(1)
                    packet.append(0)
                    packet.append(1)
                    packet.append(0)

                    packet.append(1)
                    packet.append(0)
                    packet.append(0)
                    packet.append(1)
                    packet.append(1)
                    packet.append(0)
                    packet.append(0)
                    packet.append(1)

                    long_high = 0
                    long_low = duration
                    short_high = 0
                    short_low = 0
                    long_high_min = 0
                    long_low_min = duration
                    short_high_min = 0
                    short_low_min = 0
                    long_high_max = 0
                    long_low_max = duration
                    short_high_max = 0
                    short_low_max = 0
                else:
                    state = 'wait'
                    preamblecount = 0
            elif (100 < duration < 350):
                state = 'preamble'
            elif 4000 < duration < 5500:
                preamblecount += 1
            else:
                state = 'wait'
                preamblecount = 0
        elif state == 'train':
            traincount += 1
            if traincount in (2, 4, 6, 8, 12, 18):
                # Long high
                long_high += duration
                if long_high_min > duration:
                    long_high_min = duration
                if long_high_max < duration:
                    long_high_min = duration
            elif traincount in (3, 5, 7, 9, 15):
                long_low += duration
                if long_low_min > duration:
                    long_low_min = duration
                if long_low_max < duration:
                    long_low_min = duration
            elif traincount in (10, 14, 16):
                short_high += duration
                if short_high_min > duration:
                    short_high_min = duration
                if short_high_max < duration:
                    short_high_min = duration
            elif traincount in (11, 13, 17):
                short_low += duration
                if short_low_min > duration:
                    short_low_min = duration
                if short_low_max < duration:
                    short_low_min = duration

            if traincount == 18:
                long_high /= 6
                long_low /= 6
                short_high /= 3
                short_low /= 3
                state = 'data'

                if long_high_min > long_high * 0.75:
                    long_high_min = long_high * 0.75
                if long_low_min > long_low * 0.75:
                    long_low_min = long_low * 0.75
                if short_high_min > short_high * 0.2:
                    short_high_min = short_high * 0.2
                if short_low_min > short_low * 0.2:
                    short_low_min = short_low * 0.2

                if long_high_max < long_high * 1.4:
                    long_high_max = long_high * 1.4
                if long_low_max < long_low * 1.4:
                    long_low_max = long_low * 1.4
                if short_high_max < short_high * 1.25:
                    short_high_max = short_high * 1.25
                if short_low_max < short_low * 1.25:
                    short_low_max = short_low * 1.25

                long_high_max = math.floor(long_high_max)
                long_low_max = math.floor(long_low_max)
                short_high_max = math.floor(short_high_max)
                short_low_max = math.floor(short_low_max)

                long_high_min = math.ceil(long_high_min)
                long_low_min = math.ceil(long_low_min)
                short_high_min = math.ceil(short_high_min)
                short_low_min = math.ceil(short_low_min)

        elif state == 'data':
            if level == 0:
                # level == 0 heisst, es wurde ein HIGH-Impuls ausgewertet
                if short_low_min <= duration <= short_low_max:
                    if bit == 0:
                        packet.append(0)
                elif long_low_min <= duration <= long_low_max:
                    # langes LOW = 0
                    packet.append(0)
                    bit = 0
                else:
                    # ungueltige Zeit
                    state = 'wait'
                    preamblecount = 0
            else:
                if (short_high_min <= duration <= short_high_max):
                    # kurzer HIGH = 1 wiederholt
                    if bit == 1:
                        packet.append(1)
                elif (long_high_min <= duration <= long_high_max):
                    # langes HIGH = 1
                    packet.append(1)
                    bit = 1
                else:
                    # ungueltige Zeit
                    state = 'wait'
                    preamblecount = 0
        if len(packet) == 104:
            # komplettes Paket empfangen
            state = 'wait'
            preamblecount = 0
            packet_queue.put((time.time(), list(packet)))
            packet[:] = []
