#!/usr/bin/env python3
# coding=utf-8

import time
import pigpio
import argparse
import queue
import threading
import jsonwriter
import protocol
import pinchangehandler

parser = argparse.ArgumentParser(description='Receives Wireless BBQ Thermometer Telegrams via RF-Receiver')
parser.add_argument('--debug', action='store_true', help='Generates additional debugging Output')
parser.add_argument('--pin', default=18, type=int, help='Sets the Pin number')
parser.add_argument('--nosync', action='store_true', help='Always register new IDs')
parser.add_argument('--verbose', action='store_true', help='Print more Information to stdout')

options = parser.parse_args()


def worker():
    print('Main task running')
    # Hauptthread, wertet empfangene Pakete aus und verteilt an die anderen Queues
    global unit_list
    unit = '°C'
    while True:
        item_time, item = pinchangehandler.getqueue().get()
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
        pinchangehandler.getqueue().task_done()


pi = pigpio.pi()
oldtick = pi.get_current_tick()
pi.set_mode(options.pin, pigpio.INPUT)
pi.set_noise_filter(options.pin, 4500, 400000)
callback1 = pi.callback(options.pin, pigpio.EITHER_EDGE, pinchangehandler.pinchange)
start = time.time()

worker1 = threading.Thread(target=worker)
worker1.daemon = True
worker1.start()

json_queue = queue.Queue()
json_writer_worker = threading.Thread(target=jsonwriter.json_writer(json_queue))
json_writer_worker.daemon = True
json_writer_worker.start()

while 1:
    time.sleep(0.2)
pi.stop()
