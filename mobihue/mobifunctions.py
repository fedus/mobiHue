#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Auxiliary functions for mobiHue

import logging
from rgb_xy import Converter, GamutC
from webcolors import name_to_rgb


logger = logging.getLogger(__name__)


def print_welcome():
    """Print welcome message on launch."""
    print("mobiHue.py (c) 2017 Federico Gentile")
    print("")
    logger.info("mobiHue starting ...")

def return_eta_alert_level(eta):
    """Returns the appropriate alert zone as defined in the configuration file for a given ETA"""
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

def colour_name_to_xy(colour_name):
    """Transforms a plain colour name to the XY format used by the Hue system."""
    colour_rgb = name_to_rgb(colour_name)
    colour_xy = Converter.rgb_to_xy(colour_rgb)
    return colour_xy

def return_current_colour(colourContainer, isSchedule=True):
    """Similar to returnColour() but (1) always returns the appropriate colour for the next bus (2) converts it to XY format"""
    if isSchedule:
        colourRGB = name_to_rgb(returnColour(tdToMin(colourContainer[0]["eta"])))
        colourXY = converter.rgb_to_xy(colourRGB[0],colourRGB[1],colourRGB[2])
    elif not isSchedule:
        colourRGB = name_to_rgb(colourContainer)
        colourXY = converter.rgb_to_xy(colourRGB[0], colourRGB[1], colourRGB[2])
    return colourXY