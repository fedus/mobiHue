#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Control module to handle the Schedule and Hue_Control classes. Main app runtime.

import logging
from time import sleep
from settings import Settings
from schedule import Schedule
from huecontrols import Hue_Control
from signalhandler import Signal_Handler


logger = logging.getLogger(__name__)


class Controller():
    """"Main program runtime linking the data from the bus schedule to the Hue lights."""

    SENSOR_IGNORE_BUTTONS = (2000, 2001, 2002, 2003, 3000, 3001, 3002, 3003)
    SENSOR_NO_RESET_BUTTONS = (2000, 2001, 2002, 2003, 3000, 3001, 3002, 3003, 4000, 4001, 4002, 4003)

    def __init__(self):
        """Initialises the Controller class."""
        self.settings = Settings()
        self.schedule = Schedule(self.settings.transport, self.settings.stop, self.settings.mobiliteit_url, self.settings.zones)
        self.hue_control = Hue_Control(**self.settings.hue)
        self.signal_handler = Signal_Handler()
        self.last_zone = None
        self.current_zone = None
        self.sensor_last_action = None
        self.run_loop_count = 0

    def _schedule_to_light(self):
        """Sets the Hue light colour according to the estimated time of arrival of the next bus."""
        self.schedule.update()
        self.current_zone = self.schedule.next_departure.zone
        if self.current_zone != self.last_zone or self.settings.zones[self.current_zone]["hue_state"]["alert"] != "none":
            logger.debug("  >> Zone change detected, synching light to bus schedule.")
            self.hue_control.light.set_state(**self.settings.zones[self.current_zone]["hue_state"])
            self.last_zone = self.current_zone
            return True
        else:
            logger.debug("  >> No zone change detected. Light still in synch with bus schedule.")
            return False

    def _reset_check(self):
        """Checks if a reset to the Hue light's original state is warranted."""
        self.sensor_last_action = self.hue_control.sensor.last_action
        if self.sensor_last_action["actioned"] and self.hue_control.light.initial_state["on"] == True and self.sensor_last_action[
            "button"] not in self.SENSOR_NO_RESET_BUTTONS:
            logger.debug("  >> Reset check: Reset is warranted.")
            return True
        else:
            logger.debug("  >> Reset check: No reset needed.")
            return False

    def _kill_check(self):
        """Returns True or False depending on whether an event was triggered that should lead to the program's exit."""
        if not self.signal_handler.sigint_caught:
            self.hue_control.sensor.poll()
            self.sensor_last_action = self.hue_control.sensor.last_action
            if self.sensor_last_action["actioned"]:
                if self.sensor_last_action["button"] not in self.SENSOR_IGNORE_BUTTONS:
                    logger.debug("  >> Kill check positive: Sensor actioned with hot button.")
                    return True
                else:
                    logger.debug("  >> Kill check negative: Sensor actioned, but no hot button pressed.")
                    return False
            else:
                logger.debug("  >> Kill check negative: No sensor action, no SIGINT received.")
                return False
        elif self.signal_handler.sigint_caught:
            logger.debug("  >> Kill check positive: SIGINT received.")
            return True

    def run(self):
        """Main program runtime, synchronises the bus schedule and the Hue lights."""
        logger.info("Turning light on if needed.")
        self.hue_control.light.on()
        logger.info("Performing first synchronisation.")
        self._schedule_to_light()
        logger.info("Next bus: %s", str(self.schedule.next_departure))
        while not self._kill_check():
            self.run_loop_count += 1
            if self.run_loop_count == self.settings.interval:
                logger.info("Synching.")
                self._schedule_to_light()
                self.run_loop_count = 0
                logger.info("Next bus: %s", str(self.schedule.next_departure))
            sleep(1)
        logger.info("Synchronisation stopped. Resetting lights if needed.")
        if self.signal_handler.sigint_caught or self._reset_check():
            self.hue_control.light.reset()
