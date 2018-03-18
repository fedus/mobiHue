#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017, 2018 Federico Gentile
# Settings module

import yaml
import logging
import sys
import os
from rgb_xy import Converter, GamutC
from webcolors import name_to_rgb
from mhexception import Mobihue_Exception


logger = logging.getLogger("mH." + __name__)


class Settings:
    """A class that loads and holds the settings."""

    def __init__(self):
        """Initialise the program's settings."""
        try:
            self.directory = os.path.dirname(os.path.realpath(__file__))
            self.full_config_file_path = self.directory + "/config.yaml"
            self.stream = open(self.full_config_file_path, "r")
        except IOError:
            logger.error("Could not find configuration file under: %s", self.full_config_file_path)
            raise
        else:
            with self.stream:
                try:
                    self.config = yaml.safe_load(self.stream)
                    logger.info("Configuration file loaded successfully.")
                    self.converter = Converter(GamutC)
                    if self._use_scene_mode():
                        logger.debug("  >> Using scenes to set the Hue lights.")
                        self._scrape_hue_scenes()
                    else:
                        logger.debug("  >> Using states to set the Hue lights.")
                        self._build_hue_zone_state()
                except yaml.YAMLError as yaml_error:
                    logger.error("A YAML error was raised while reading the configuration file: " + str(yaml_error))
                    raise

    def __getattr__(self, name):
        """Helper function to access the config dictionary like a class attribute."""
        return self.config[name]

    def _colour_name_to_xy(self, colour_name):
        """Transforms a plain colour name to the XY format used by the Hue system."""
        self.colour_rgb = name_to_rgb(colour_name)
        self.colour_xy = self.converter.rgb_to_xy(self.colour_rgb[0], self.colour_rgb[1], self.colour_rgb[2])
        return self.colour_xy

    def _build_hue_zone_state(self):
        """Build a ready made Hue light state from the zone settings of the config file."""
        self.config["hue"]["states"] = {}
        for self.zone_key, self.zone_value in self.config["zones"].items():
            if self.zone_value["effect"] == "None":
                self.zone_alert, self.zone_effect = "none", "none"
            elif self.zone_value["effect"] == "blink":
                self.zone_alert, self.zone_effect = "lselect", "none"
            elif self.zone_value["effect"] == "colourloop":
                self.zone_alert, self.zone_effect = "none", "colorloop"
            else:
                logger.error("Invalid value found in effect settings: "+self.zone_value["effect"])
                sys.exit("Aborting ...")
            self.zone_xy_colour = self._colour_name_to_xy(self.zone_value["colour"])
            self.config["zones"][self.zone_key]["hue_state"] = {"xy": self.zone_xy_colour, "alert": self.zone_alert, "effect": self.zone_effect}
            self.config["hue"]["states"][self.zone_key] = self.config["zones"][self.zone_key]["hue_state"]
        return self.config

    def _scrape_hue_scenes(self):
        """Collects all Hue scene IDs entered in the zone section of the configuration file and appends it to the Hue section."""
        self.scene_list = {self.current_zone_key: self.current_zone_val["scene"] for self.current_zone_key, self.current_zone_val in self.config["zones"].items()}
        self.config["hue"]["scenes"] = self.scene_list
        return self.config

    def _use_scene_mode(self):
        """Returns true or false depending on whether or not the program should use the scenes indicated in the configuration file."""
        if any(self.current_zone_val["scene"] is None for self.current_zone_key, self.current_zone_val in self.config["zones"].items()):
            return False
        else:
            return True
