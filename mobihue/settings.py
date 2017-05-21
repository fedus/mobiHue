#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Settings module

import yaml, logging, sys
from rgb_xy import Converter, GamutC
from webcolors import name_to_rgb


logger = logging.getLogger(__name__)


class Settings():
    """A class that loads and holds the settings."""

    def __init__(self):
        """Initialise the program's settings."""
        try:
            self.stream = open("config.yaml", 'r')
        except IOError:
            logger.critical("Could not find configuration file!")
            sys.exit("Aborting ...")
        else:
            with self.stream:
                try:
                    self.config = yaml.safe_load(self.stream)
                    logger.info("Configuration file loaded successfully.")
                    self.converter = Converter(GamutC)
                    self._build_hue_zone_state(self.config)
                except yaml.YAMLError as yaml_error:
                    logger.error("A YAML error was raised while reading the configuration file: " + str(yaml_error))
                    sys.exit("Aborting ...")

    def __getattr__(self, name):
        """Helper function to access the config dictionary like a class attribute."""
        return self.config[name]
    
    def _colour_name_to_xy(self, colour_name):
        """Transforms a plain colour name to the XY format used by the Hue system."""
        self.colour_rgb = name_to_rgb(colour_name)
        self.colour_xy = self.converter.rgb_to_xy(self.colour_rgb[0], self.colour_rgb[1], self.colour_rgb[2])
        return self.colour_xy

    def _build_hue_zone_state(self,config):
        """Build a ready made Hue light state from the zone settings of the config file."""
        for zone in config["zones"]:
            if config["zones"][zone]["effect"] == "None":
                zone_alert, zone_effect = "none", "none"
            elif config["zones"][zone]["effect"] == "blink":
                zone_alert, zone_effect = "lselect", "none"
            elif config["zones"][zone]["effect"] == "colourloop":
                zone_alert, zone_effect = "none", "colorloop"
            else:
                logger.error("Invalid value found in effect settings. "+config["zones"][zone]["effect"])
                sys.exit("Aborting ...")
            zone_xy_colour = self._colour_name_to_xy(config["zones"][zone]["colour"])
            config["zones"][zone]["hue_state"] = {"xy": zone_xy_colour, "alert": zone_alert, "effect": zone_effect}
        return config
