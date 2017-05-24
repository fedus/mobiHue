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
        self.sigint_caught = False
        signal.signal(signal.SIGINT, self._sigint_handler)

    def _sigint_handler(self, signum, frame):
        """Gets called when a SIGINT is caught."""
        self.sigint_caught = True
        logger.debug("  >> SIGINT caught.")