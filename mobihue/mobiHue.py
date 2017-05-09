#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Main program

import logging
from settings import Settings
from schedule import Schedule
from huecontrols import Hue_Control
from mobifunctions import print_welcome
from time import sleep


# Logging setup
logging_white_spaces = 13
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)-8s] %(name)13s ~ %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
logger = logging.getLogger(__name__)
requests_logger = logging.getLogger("requests.packages.urllib3.connectionpool")
requests_logger.name = "requests"


if __name__ == "__main__":

    print_welcome()
    settings = Settings()

    schedule = Schedule(settings.transport, settings.stop, settings.mobiliteit_url)

    schedule.update()
    hue_control = Hue_Control(**settings.hue)
    print(schedule.last_update)
    print(schedule.next_departure.line, schedule.next_departure.direction)

    for Bus in schedule.all_departures:
        print(Bus.eta)

    hue_control.light.on()

    hue_control.light.set_state(alert="select")

    sleep(3)
    hue_control.light.reset()
    hue_control.sensor.poll()
    hue_control.sensor.last_action