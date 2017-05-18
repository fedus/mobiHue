#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Auxiliary functions for mobiHue

import logging
import signal
from time import sleep
from settings import Settings
from schedule import Schedule
from huecontrols import Hue_Control


logger = logging.getLogger(__name__)

last_zone = None

def print_welcome():
    """Print welcome message on launch."""
    print("*** mobiHue.py (c) 2017 Federico Gentile")
    print("")
    logger.info("mobiHue starting ...")

def return_eta_alert_level(eta):
    """Returns the appropriate alert zone as defined in the configuration file for a given ETA."""
    if eta <= settings.alert["imminent"]["minutes"]:
        # Bus or train arrival imminent
        alert_type, alert_colour = "imminent", settings.alert["imminent"]["colour"]
    elif eta <= settings.alert["close"]["minutes"]:
        # Bus or train close
        alert_type, alert_colour = "close", settings.alert["close"]["colour"]
    elif eta <= settings.alert["intermediate"]["minutes"]:
        # Bus or train at intermediate distance
        alert_type, alert_colour = "intermediate", settings.alert["intermediate"]["colour"]
    elif eta > settings.alert["intermediate"]["minutes"]:
        # Bus or train at safe distance
        alert_type, alert_colour = "further", settings.alert["further"]["colour"]
    alert_level = {
            "level": alert_type,
            "colour": alert_colour,
        }
    return alert_level

def return_current_colour(colourContainer, isSchedule=True):
    """Similar to returnColour() but (1) always returns the appropriate colour for the next bus (2) converts it to XY format."""
    if isSchedule:
        colourRGB = name_to_rgb(returnColour(tdToMin(colourContainer[0]["eta"])))
        colourXY = converter.rgb_to_xy(colourRGB[0],colourRGB[1],colourRGB[2])
    elif not isSchedule:
        colourRGB = name_to_rgb(colourContainer)
        colourXY = converter.rgb_to_xy(colourRGB[0], colourRGB[1], colourRGB[2])
    return colourXY

def sigint_handler(signal, frame):
   """SIGINT signal handler."""
   global sigint_caught
   sigint_caught = True;

def sigint_handler_setup():
    """Sets up the SIGINT handler."""
    # Set SIGINT signal handler variable to standard state (i.e. SIGINT not caught yet)
    global sigint_caught
    sigint_caught = False;
    # Catch SIGINT
    signal.signal(signal.SIGINT, sigint_handler)

def sigint_is_caught():
    """Returns the sigint_caught variable. Makes it easy to read the vaiable's value across modules."""
    global sigint_caught
    return sigint_caught

def kill_check(hue_control):
    """Returns True or False depending on whether an event was triggered that should lead to the program's exit."""
    SENSOR_IGNORE_BUTTONS = (2000, 2001, 2002, 2003, 3000, 3001, 3002, 3003)
    if not sigint_caught:
        hue_control.sensor.poll()
        sensor_last_action = hue_control.sensor.last_action
        if sensor_last_action["actioned"]:
            if sensor_last_action["button"] not in SENSOR_IGNORE_BUTTONS:
                return True
            else:
                return False
        else:
            return False
    elif sigint_caught:
        return True

def reset_check(hue_control):
    """Checks if a reset to the Hue light's original state is warranted."""
    SENSOR_NO_RESET_BUTTONS = (2000, 2001, 2002, 2003, 3000, 3001, 3002, 3003, 4000,4001,4002,4003)
    sensor_last_action = hue_control.sensor.last_action
    if sensor_last_action["actioned"] and not hue_control.light.is_on and sensor_last_action["button"] not in SENSOR_NO_RESET_BUTTONS:
        return True
    else:
        return False

def setup_program():
    """Initialises the program."""

    # Print the welcome screen.
    print_welcome()

    # Set up the SIGINT handler.
    sigint_handler_setup()

    # Load the settings.
    settings = Settings()

    # Create schedule instance.
    schedule = Schedule(settings.transport, settings.stop, settings.mobiliteit_url, settings.zones)

    # Create hue control instance.
    hue_control = Hue_Control(**settings.hue)

    # Return instances.
    return settings, schedule, hue_control

def schedule_to_light(schedule, hue_control, settings):
    """Sets the Hue light colour according to the estimated time of arrival of the next bus."""
    global last_zone
    schedule.update()
    current_zone = schedule.next_departure.zone
    if current_zone != last_zone:
        hue_control.light.set_state(**settings.zones[current_zone]["hue_state"])
        last_zone = current_zone
        return True
    else:
        return False


def main():
    """Main program run-time."""
    settings, schedule, hue_control = setup_program()
    hue_control.light.on()
    loop_count = 0
    schedule_to_light(schedule, hue_control, settings)
    while not kill_check(hue_control):
        loop_count += 1
        hue_control.sensor.poll()
        if loop_count == settings.interval:
            schedule_to_light(schedule, hue_control, settings)
            print(str(schedule.next_departure))
            loop_count = 0
        sleep(1)
    if sigint_is_caught() or reset_check(hue_control):
        hue_control.light.reset()

