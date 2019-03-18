# mobiHue
Colours Philipps Hue bulbs according to the estimated time of arrival of the next bus at a given station using the mobiliteit.lu API.

Usage:
mobyHue.py standalone | start | stop | status

The "standalone" argument runs the program in the foreground and prints its log output to the console. "start", "stop" and "status" can be used to run this program as a daemon or service.

In principle, the program will attempt to log under /var/log/mobiHue.

TODO:
* Refactoring
* Commenting
* Setuptools
* Unit tests
* Documentation
