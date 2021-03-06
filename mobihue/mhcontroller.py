#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017, 2018 Federico Gentile
# Control module to handle the Schedule and Hue_Control classes. Main app runtime.

import logging
import logging.handlers
from time import sleep, time
from service import find_syslog, Service
from settings import Settings
from schedule import Schedule
from huecontrols import Hue_Control
from signalhandler import Signal_Handler
from mhplugin import Pluginmanager


logger = logging.getLogger("mH." + __name__)


class Controller(Service):
    """"Main program runtime linking the data from the bus schedule to the Hue lights."""

    SENSOR_IGNORE_BUTTONS = (2000, 2001, 2002, 2003, 3000, 3001, 3002, 3003)
    SENSOR_NO_RESET_BUTTONS = (2000, 2001, 2002, 2003, 3000, 3001, 3002, 3003, 4000, 4001, 4002, 4003)

    def __init__(self, as_service=False, with_logger=None):
        """Initialises the Controller class."""
        if as_service:
            super(Controller, self).__init__("mobiHue", pid_dir="/tmp")
            self.is_service = True
            self.initialised = False
            if with_logger is not None:
                self.original_logger = with_logger
                self.logger = logging.getLogger("mH." + __name__)
            global logger
            logger = self.logger
        elif not as_service:
            self.is_service = False
            self._deferred_init()

    @classmethod
    def as_service(cls, with_logger=None):
        """Initialises the Controller class to be used as a service."""
        return cls(True, with_logger)

    def _deferred_init(self):
        """Deferred initialisation of the class, used in case the class is used as a service."""
        self.settings = Settings()
        self.schedule = Schedule(self.settings.transport, self.settings.stop, self.settings.mobiliteit_url, self.settings.zones)
        self._cyclable_init()
        self.plugin_mgr = Pluginmanager(True)
        self.initialised = True

    def _cyclable_init(self):
        if not self.is_service:
            self.signal_handler = Signal_Handler()
        self.hue_control = Hue_Control(**self.settings.hue)
        self.last_zone = None
        self.current_zone = None
        self.sensor_last_action = None
        self.run_loop_count = 0
        self.sigterm_caught = False
        self.sigint_caught = False

    def _schedule_to_light(self):
        """Sets the Hue light colour according to the estimated time of arrival of the next bus."""
        self.schedule.update()
        if self.schedule.next_departure is None:
            self.current_zone = "warning"
            logger.debug("  >> No next departure found. Warning zone enabled.")
        else:
            self.current_zone = self.schedule.next_departure.zone
        if self.current_zone != self.last_zone or (self.hue_control.light_mode == "states" and self.settings.zones[self.current_zone]["hue_state"]["alert"] != "none"):
            logger.debug("  >> Zone change detected, synching light to schedule.")
            self.hue_control.slave.set_zone(self.current_zone)
            self.last_zone = self.current_zone
            return True
        else:
            logger.debug("  >> No zone change detected. Light still in sync with schedule.")
            return False

    def _reset_check(self):
        """Checks if a reset to the Hue light's original state is warranted."""
        self.sensor_last_action = self.hue_control.sensor.last_action
        if self.sensor_last_action["actioned"] and self.hue_control.slave.initial_on == True and self.sensor_last_action[
            "button"] not in self.SENSOR_NO_RESET_BUTTONS:
            logger.debug("  >> Reset check: Reset is warranted.")
            return True
        else:
            logger.debug("  >> Reset check: No reset needed.")
            return False

    def _kill_check(self):
        """Returns True or False depending on whether an event was triggered that should lead to the program's exit."""
        self._sigint_check()
        self._sigterm_check()
        if not self.sigint_caught and not self.sigterm_caught and self.settings.use_kill_switch:
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
                logger.debug("  >> Kill check negative: No sensor action, no SIGINT, no SIGTERM received.")
                return False
        elif self.sigint_caught:
            logger.debug("  >> Kill check positive: SIGINT received.")
            return True
        elif self.sigterm_caught:
            logger.debug("  >> Kill check positive: SIGTERM received by service.")
            return True

    def _sigint_check(self):
        """Checks if SIGINT was received in case the Controller was initialised in standalone mode."""
        if not self.is_service:
            self.sigint_caught = self.signal_handler.sigint_caught
            return self.sigint_caught
        elif self.is_service:
            self.sigint_caught = False
            return False

    def _sigterm_check(self):
        """Checks if SIGTERM was received in case the Controller was initialised as a service."""
        if self.is_service:
            self.sigterm_caught = self.got_sigterm()
            return self.sigterm_caught
        elif not self.is_service:
            self.sigterm_caught = False
            return False

    def _run_with_on_switch(self):
        """Provides a runtime-wrapper to operate the program with an on-switch."""
        self.on_switch_running = True
        while not self.sigint_caught and not self.sigterm_caught:
            if self.hue_control.on_switch.poll():
                logger.info("On-switch actioned. Starting runtime.")
                self._cyclable_init()
                self._run_core()
                if not self.sigint_caught and not self.sigterm_caught:
                    logger.info("Watching on-switch ...")
            else:
                logger.debug("  >> On-switch not actioned. Polling again in 1 second.")
                self._sigterm_check()
                self._sigint_check()
            sleep(1)
        logger.info("Stopping on-switch polling routine as SIGINT or SIGTERM has been received.")

    def _run_core(self):
        """Provides the core runtime for the synchronisation of the lights to the schedule."""
        logger.info("Turning light on if needed.")
        self.hue_control.slave.on()
        self.plugin_mgr.begin()
        while not self._kill_check():
            if self.run_loop_count == 0:
                logger.info("Synching light to schedule.")
                self._schedule_to_light()
                logger.info("Next bus: %s", str(self.schedule.next_departure))
                self.plugin_mgr.data(self.schedule.all_departures)
            elif self.run_loop_count == self.settings.interval:
                self.run_loop_count = -1
            self.run_loop_count += 1
            sleep(1)
        logger.info("Synchronisation stopped. Resetting light if needed.")
        self.plugin_mgr.end()
        if self.sigint_caught or self.sigterm_caught or self._reset_check():
            self.hue_control.slave.reset()

    def run(self):
        """Main program runtime."""
        if not self.initialised:
            logger.info("Launched as a service, running deferred initialisation.")
            self._deferred_init()
        if self.settings.use_on_switch:
            logger.info("Watching on-switch ...")
            self._run_with_on_switch()
        elif not self.settings.use_on_switch:
            logger.info("Not using on-switch.")
            self._run_core()
        if self.is_service:
            logger.info("Service halted.")

