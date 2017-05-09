#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Hue system control module

import logging
from datetime import datetime
from time import time
from qhue import Bridge


logger = logging.getLogger(__name__)


class Light():
    """Class representing the Hue light to be controlled."""

    redundant_pairs = ("colormode", "reachable", "alert")

    def __init__(self, bridge, light_id):
        """Initialise the Light class."""
        self.hue_light = bridge.lights[light_id]
        self.initial_state = self._pop_redundant_state_vars(self.hue_light()["state"])
        self.state_has_changed = False

    def _pop_redundant_state_vars(self, light_state):
        """Removes certain variables from the Hue light state that interfere with this program's commands."""
        for pair in self.redundant_pairs:
            light_state.pop(pair, None)
        return light_state

    @property
    def is_on(self):
        """Returns True or False depending on whether the Hue light is on or off."""
        return self.hue_light()["state"]["on"]

    def set_state(self, **new_state):
        """Changes the state of the Hue light."""
        logger.info("Setting new light state.")
        logger.debug("  >> New state: " + str(new_state))
        self.hue_light.state(**new_state)
        self.state_has_changed = True
        return True

    def reset(self):
        """Resets the Hue light to its initial state."""
        logger.info("Resetting light.")
        if self.state_has_changed:
            if self.initial_state["on"]:
                logger.debug("  >> Light was on at program start, resetting relevant attributes.")
                self.set_state(**self.initial_state)
                return True
            elif not self.initial_state["on"]:
                logger.debug("  >> Light was off at program start, turning it off again.")
                self.set_state(on=False)
                return True
            else:
                logger.error("  >> Unexpected value encountered in initial_state variable.")
                return False
        elif not self.state_has_changed:
            logger.debug("  >> Light state had not been changed, no action necessary.")
            return True
        else:
            logger.error("  >> Unexpected value encountered in state_has_changed variable.")
            return False

    def on(self):
        """Turns the selected Hue light on."""
        if self.state_has_changed:
            self.current_on_state = self.is_on
        elif not self.state_has_changed:
            self.current_on_state = self.initial_state["on"]
        if not self.current_on_state:
            logger.info("Turning light on.")
            self.set_state(on=True)
            return True
        elif self.current_on_state:
            logger.info("Light already on.")
            return True
        else:
            return False


class Sensor():
    """Class representing the Hue sensor acting as a kill switch."""

    def __init__(self, bridge, sensor_id):
        """Initialise the Sensor class."""
        self.hue_sensor = bridge.sensors[sensor_id]
        self.reference_time = datetime.now().replace(microsecond=0)
        self.current_sensor_state = None

    def _datetime_from_utc_to_local(self, utc_datetime):
        self.current_time = time()
        self.offset = datetime.fromtimestamp(self.current_time) - datetime.utcfromtimestamp(self.current_time)
        self.local_time = utc_datetime + self.offset
        return self.local_time
    
    def poll(self):
        """Polls the Hue bridge for the current status of the sensor."""
        logger.info("Retrieving current sensor state.")
        self.current_sensor_state = self.hue_sensor()["state"]
        logger.debug("  >> Current sensor state: " + str(self.current_sensor_state))
        return True

    @property
    def last_action(self):
        """Returns a list with a datetime object of the last time the Hue sensor has been actioned and with what code"""
        logger.info("Last action of sensor has been requested.")
        if self.current_sensor_state:
            self.friendly_current_sensor_state = {
                    "time": self._datetime_from_utc_to_local(datetime.strptime(self.current_sensor_state["lastupdated"],
                        "%Y-%m-%dT%H:%M:%S")),
                    "action": self.current_sensor_state["buttonevent"],
                }
            return self.friendly_current_sensor_state
        elif self.current_sensor_state == None:
            logger.warning("Last action of sensor has been requested, but it seems that it has not been polled yet.")
            return False

    @property
    def actioned(self):
        """Returns a tuple of True and the corresponding action if sensor has been actioned since the instance start,
        or a simple False if not."""
        logger.info("Checking if sensor has been actioned since program start.")
        self.get_last_action = self.last_action
        if self.get_last_action["time"] >= self.reference_time:
            self.actioned_response = (True, self.get_last_action["action"])
            logger.debug("  >> Sensor has been actioned. Response: "+str(self.actioned_response))
            return self.actioned_response
        elif self.get_last_action["time"] < self.reference_time:
            logger.debug("  >> Sensor has not been actioned.")
            return False
        else:
            logger.error("  >> Unexpected value encountered in get_last_action variable.")
            return False


class Hue_Control():
    """Master class representing both the Hue light and sensor."""

    def __init__(self, ip, key, light_id, sensor_id):
        """Initialise the Hue_Control class."""
        self.bridge = Bridge(ip, key)
        self.light = Light(self.bridge, light_id)
        self.sensor = Sensor(self.bridge, sensor_id)