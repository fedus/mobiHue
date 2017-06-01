#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Module used to handle signals.

import signal
import logging


logger = logging.getLogger("mH." + __name__)


class Signal_Handler():
    """This class handles signals and exposes a catch to other modules."""

    def __init__(self):
        """Initialise the Signal_Handler class."""
        self._sigint_caught = False
        self._sigint_response = None
        signal.signal(signal.SIGINT, self._sigint_handler)

    def _sigint_handler(self, signum, frame):
        """Gets called when a SIGINT is caught."""
        self._sigint_caught = True
        logger.debug("  >> SIGINT caught.")

    @property
    def sigint_caught(self):
        """Returns whether or not a SIGINT has been received and resets the Signal handler."""
        self._sigint_response = self._sigint_caught
        self._sigint_caught = False
        return self._sigint_response