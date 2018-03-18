#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017, 2018 Federico Gentile
# Main program


import logging
import logging.handlers
from mhcontroller import Controller
from mobifunctions import print_welcome

# Logging setup
logger = logging.getLogger("mH")
logger.setLevel(logging.INFO)
logging_filehandler = logging.handlers.TimedRotatingFileHandler("/var/log/mobiHue/mobiHue.log", when='midnight', interval=1, backupCount=7, encoding=None, delay=True, utc=False, atTime=None)
logging_consolehandler = logging.StreamHandler()
logging_formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(name)15s ~ %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
logging_filehandler.setFormatter(logging_formatter)
logging_consolehandler.setFormatter(logging_formatter)
logger.addHandler(logging_consolehandler)


requests_logger = logging.getLogger("requests.packages.urllib3.connectionpool")
requests_logger.propagate = True
requests_logger.setLevel(logging.DEBUG)
requests_logger.name = "mH.requests"

backoff_logger = logging.getLogger("backoff")
backoff_logger.propagate = True
backoff_logger.setLevel(logging.DEBUG)
backoff_logger.name = "mH.backoff"
backoff_logger.setLevel(logging.INFO)



if __name__ == "__main__":
    """Main program runtime."""

    import sys

    if len(sys.argv) != 2:
        sys.exit("Syntax: %s standalone | start | stop | status" % sys.argv[0])

    cmd = sys.argv[1].lower()

    if cmd == "standalone":
        print_welcome()
        logger.info("Starting synchronisation module ...")
        controller = Controller()
        controller.run()
        logger.info("Exiting program ...")
    else:
        logger.addHandler(logging_filehandler)
        service = Controller.as_service(logger)
        if cmd == "start":
            service.start()
        elif cmd == "stop":
            service.stop()
        elif cmd == "status":
            if service.is_running():
                print("mobiHue service is running.")
            else:
                print("mobiHue service is not running.")
        else:
            sys.exit('Unknown command "%s".' % cmd)
