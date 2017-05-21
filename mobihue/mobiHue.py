#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# Main program

import logging
from mhcontroller import Controller
from mobifunctions import print_welcome


# Logging setup
logging_white_spaces = 13
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)-8s] %(name)13s ~ %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
logger = logging.getLogger(__name__)
requests_logger = logging.getLogger("requests.packages.urllib3.connectionpool")
requests_logger.name = "requests"


if __name__ == "__main__":
    """Main program runtime."""

    print_welcome()
    logger.info("Starting synchronisation module ...")
    controller = Controller()
    controller.run()
    logger.info("Exiting program ...")
