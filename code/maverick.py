#!/usr/bin/env python3
# coding=utf-8

import argparse
import queue
import threading
import time

import jsonwriter
import pigpio
import protocol
import pinchangehandler

parser = argparse.ArgumentParser(description='Receives Wireless BBQ Thermometer Telegrams via RF-Receiver')
parser.add_argument('--pin', default=18, type=int, help='Sets the Pin number')

options = parser.parse_args()

json_queue = queue.Queue()


def worker():
    print('Main task running')
    while True:
        item_time, item = pinchangehandler.getqueue().get()
        type, chksum_is = protocol.chksum(item)
        temp1, temp2 = protocol.get_data(item)
        json_queue.put((item_time, chksum_is, type, temp1, temp2))
        pinchangehandler.getqueue().task_done()


def main():
    pi = pigpio.pi()
    pi.set_mode(options.pin, pigpio.INPUT)
    pi.set_noise_filter(options.pin, 4500, 400000)
    pi.callback(options.pin, pigpio.EITHER_EDGE, pinchangehandler.pinchange)

    worker1 = threading.Thread(target=worker)
    worker1.daemon = True
    worker1.start()

    json_writer_worker = threading.Thread(target=jsonwriter.json_writer(json_queue))
    json_writer_worker.daemon = True
    json_writer_worker.start()
    while 1:
        time.sleep(0.2)
    pi.stop()


main()
