#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Hue system control module

import logging
from datetime import datetime, timedelta
from time import time
from qhue import Bridge


logger = logging.getLogger("mH." + __name__)


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
        self.is_on_result = self.hue_light()["state"]["on"]
        logger.debug("  >> On / off state of light requested. Result: %s", self.is_on_result)
        return self.is_on_result

    def set_state(self, **new_state):
        """Changes the state of the Hue light."""
        logger.debug("  >> Setting new light state: %s", str(new_state))
        self.hue_light.state(**new_state)
        self.state_has_changed = True
        return True

    def reset(self):
        """Resets the Hue light to its initial state."""
        if self.state_has_changed:
            if self.initial_state["on"]:
                logger.debug("  >> Light reset requested: Light was on at program start, restoring relevant attributes.")
                self.set_state(**self.initial_state)
                return True
            elif not self.initial_state["on"]:
                logger.debug("  >> Light reset requested: Light was off at program start, turning it off again.")
                self.set_state(on=False)
                return True
            else:
                logger.error("  >> Light reset requested: Unexpected value encountered in initial_state variable.")
                return False
        elif not self.state_has_changed:
            logger.debug("  >> Light reset requested: Light state had not been changed, no action necessary.")
            return True
        else:
            logger.error("  >> Light reset requested: Unexpected value encountered in state_has_changed variable.")
            return False

    def on(self):
        """Turns the selected Hue light on."""
        if self.state_has_changed:
            self.current_on_state = self.is_on
        elif not self.state_has_changed:
            self.current_on_state = self.initial_state["on"]
        if not self.current_on_state:
            logger.debug("  >> Light turned on.")
            self.set_state(on=True)
            return True
        elif self.current_on_state:
            logger.debug("  >> Light already on.")
            return True
        else:
            return False


class Sensor():
    """Class representing the Hue sensor acting as a kill switch."""

    def __init__(self, bridge, sensor_id):
        """Initialise the Sensor class."""
        self.hue_sensor = bridge.sensors[sensor_id]
        self.reference_time = datetime.now().replace(microsecond=0) + timedelta(seconds=1)
        self.current_sensor_state = None
        self.has_been_polled = False

    def _datetime_from_utc_to_local(self, utc_datetime):
        """Converts UTC time to the local timezone."""
        self.current_time = time()
        self.offset = datetime.fromtimestamp(self.current_time) - datetime.utcfromtimestamp(self.current_time)
        self.local_time = utc_datetime + self.offset
        return self.local_time

    def reset_reference_time(self):
        """Resets the reference time used to check for a relevant button press."""
        self.reference_time = datetime.now().replace(microsecond=0) + timedelta(seconds=1)
        return True

    def poll(self):
        """Polls the Hue bridge for the current status of the sensor."""
        self.current_sensor_state = self.hue_sensor()["state"]
        logger.debug("  >> Polling sensor. Current sensor state : %s", str(self.current_sensor_state))
        self.has_been_polled = True
        return True

    @property
    def last_action(self):
        """Returns a list with a datetime object of the last time the Hue sensor has been actioned and with what code"""
        if self.has_been_polled:
            self.friendly_sensor_time = self._datetime_from_utc_to_local(datetime.strptime(self.current_sensor_state["lastupdated"], "%Y-%m-%dT%H:%M:%S"))
            if self.friendly_sensor_time >= self.reference_time:
                self.actioned_response = True
            elif self.friendly_sensor_time < self.reference_time:
                self.actioned_response = False
            self.friendly_current_sensor_state = {
                    "time": self.friendly_sensor_time,
                    "button": self.current_sensor_state["buttonevent"],
                    "actioned": self.actioned_response,
                }
            logger.debug("  >> Last action of sensor has been requested: Returning parsed sensor data from cache. Data: %s", str(self.friendly_current_sensor_state))
            return self.friendly_current_sensor_state
        elif not self.has_been_polled:
            logger.warning("  >> Last action of sensor has been requested: Could not return data as it seems that the sensor has not been polled yet.")
            return False


class On_Switch():
    """Class representing a generic Hue sensor (type: CLIPGenericStatus) used to trigger the program's on switch."""

    def __init__(self, bridge, on_switch_id):
        """Initialise the On_Switch class."""
        self.on_switch = bridge.sensors[on_switch_id]

    def poll(self):
        """Polls the sensor acting as an on switch, exposes the result and resets it."""
        self.current_on_switch_status = self.on_switch()["state"]["status"]
        if self.current_on_switch_status == 1:
            self.on_switch.state(status=0)
            return True
        elif self.current_on_switch_status != 1:
            return False


class Hue_Control():
    """Master class representing both the Hue light and sensor."""

    def __init__(self, ip, key, light_id, sensor_id, on_switch_id):
        """Initialise the Hue_Control class."""
        self.bridge = Bridge(ip, key)
        self.light = Light(self.bridge, light_id)
        self.sensor = Sensor(self.bridge, sensor_id)
        self.on_switch = On_Switch(self.bridge, on_switch_id)
