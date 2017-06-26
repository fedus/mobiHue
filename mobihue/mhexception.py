#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Module containing a custom exception for the program.


import logging


logger = logging.getLogger("mH." + __name__)


class Mobihue_Exception(Exception):
    """Custom exception that is raised for purposes specific to the mobiHue program."""