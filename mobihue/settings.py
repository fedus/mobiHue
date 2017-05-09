#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Settings module

import yaml, logging


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
                except yaml.YAMLError as yaml_error:
                    logger.critical("A YAML error was raised while reading the configuration file: " + str(yaml_error))
                    sys.exit("Aborting ...")

    def __getattr__(self, name):
        return self.config[name]