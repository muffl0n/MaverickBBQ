#!/usr/bin/env python3
# coding=utf-8

import time
import pigpio
import argparse
import queue
import threading
import math
import jsonwriter
import protocol

parser = argparse.ArgumentParser(description='Receives Wireless BBQ Thermometer Telegrams via RF-Receiver')
parser.add_argument('--debug', action='store_true', help='Generates additional debugging Output')
parser.add_argument('--pin', default=18, type=int, help='Sets the Pin number')
parser.add_argument('--nosync', action='store_true', help='Always register new IDs')
parser.add_argument('--verbose', action='store_true', help='Print more Information to stdout')

options = parser.parse_args()

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

# Queue für fertige Pakete
packet_queue = queue.Queue()

# Liste der Sender für die Synchronisierung
unit_list = {}

def pinchange(gpio, level, tick):
    # Interruptroutine
    # wertet das Funksignal aus
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
        if options.debug and preamblecount > 0:
            print(duration, ":", level, " ", sep="", end="", flush=False)

        # wait ist der Wartestatus
        if state == 'wait' and level == 1:
            # lange Ruhe = vermutlich Preamble
            if 4000 < duration < 5500:
                state = 'preamble'
                preamblecount = 1
                if options.debug:
                    print('\npreamble', flush=True)
        elif state == 'preamble':
            if (380 < duration < 650):
                if preamblecount > 6:
                    state = 'train'
                    traincount = 1
                    if options.debug:
                        print('train', flush=True)
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
                    if options.debug:
                        print('not enough long pulses', flush=True)
            elif (100 < duration < 350):
                state = 'preamble'
            elif 4000 < duration < 5500:
                preamblecount += 1
                if options.debug:
                    print('preamble', preamblecount, flush=True)
            else:
                state = 'wait'
                if options.debug:
                    print('wait', flush=True)
                preamblecount = 0
        elif state == 'train':
            traincount += 1
            if options.debug:
                print('train', traincount, flush=True)
            # L h   L l   L h   L l   L h   L l   L h   L l   S h   S l   L h   S l   S h   L l   S h   S l   L h
            # 2     3     4     5     6     7     8     9     10    11    12    13    14    15    16    17    18
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

                if options.debug:
                    print('long_high', round(long_high), "min", long_high_min, "max", long_high_max, flush=False)
                    print('short_high', round(short_high), "min", short_high_min, "max", short_high_max, flush=False)
                    print('long_low', round(long_low), "min", long_low_min, "max", long_low_max, flush=False)
                    print('short_low', round(short_low), "min", short_low_min, "max", short_low_max, flush=False)
                    print('data', flush=True)

        elif state == 'data':
            if level == 0:
                # level == 0 heisst, es wurde ein HIGH-Impuls ausgewertet
                if (short_low_min <= duration <= short_low_max):
                    # kurzer LOW = 0 wiederholt
                    if options.debug:
                        print("SL    ", end="", flush=False)
                    if bit == 0:
                        packet.append(0)
                elif (long_low_min <= duration <= long_low_max):
                    # langes LOW = 0
                    if options.debug:
                        print("LL    ", end="", flush=False)
                    packet.append(0)
                    bit = 0
                else:
                    # ungueltige Zeit
                    state = 'wait'
                    if options.debug:
                        print('wait ungueltig 0 bei ', len(packet), flush=True)
                    preamblecount = 0
            else:
                if (short_high_min <= duration <= short_high_max):
                    # kurzer HIGH = 1 wiederholt
                    if options.debug:
                        print("SH    ", end="", flush=False)
                    if bit == 1:
                        packet.append(1)
                elif (long_high_min <= duration <= long_high_max):
                    # langes HIGH = 1
                    if options.debug:
                        print("LH    ", end="", flush=False)
                    packet.append(1)
                    bit = 1
                else:
                    # ungueltige Zeit
                    state = 'wait'
                    if options.debug:
                        print('wait ungueltig 1 bei ', len(packet), flush=True)
                    preamblecount = 0
        if len(packet) == 104:
            # komplettes Paket empfangen
            if options.debug:
                print('wait - ready', flush=True)
            state = 'wait'
            preamblecount = 0
            packet_queue.put((time.time(), list(packet)))
            packet[:] = []


def worker():
    print('Main task running')
    # Hauptthread, wertet empfangene Pakete aus und verteilt an die anderen Queues
    global unit_list
    unit = '°C'
    while True:
        item_time, item = packet_queue.get()
        type, chksum_is = protocol.chksum(item)
        temp1, temp2 = protocol.get_data(item)
        state = protocol.get_state(item)
        json_queue.put((item_time, chksum_is, type, temp1, temp2))
        if options.verbose:
            print(time.strftime('%c:', time.localtime(item_time)), '-', chksum_is, '- Temperatur 1:', temp1, unit,
                  'Temperatur 2:', temp2, unit)
        if options.debug:
            print('raw:', item)
            print('hex', protocol.bitlist_to_hexlist(item))
        packet_queue.task_done()


pi = pigpio.pi()
oldtick = pi.get_current_tick()
pi.set_mode(options.pin, pigpio.INPUT)
pi.set_noise_filter(options.pin, 4500, 400000)
callback1 = pi.callback(options.pin, pigpio.EITHER_EDGE, pinchange)
start = time.time()

worker1 = threading.Thread(target=worker)
worker1.daemon = True
worker1.start()

json_queue = queue.Queue()
json_writer_worker = threading.Thread(target=jsonwriter.json_writer(json_queue))
json_writer_worker.daemon = True
json_writer_worker.start()

while (1):
    time.sleep(0.2)
pi.stop()
