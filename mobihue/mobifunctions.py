#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017, 2018 Federico Gentile
# Auxiliary functions for mobiHue

import logging


logger = logging.getLogger("mH." + __name__)


def print_welcome():
    """Print welcome message on launch."""
    print("*** mobiHue.py (c) 2017 Federico Gentile")
    print("")
    logger.info("mobiHue starting ...")

def backoff_handler(details):
    logger.warning("Backing off {wait:0.1f} seconds afters {tries} tries calling function {target} with args {args} and kwargs {kwargs}".format(**details))