#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017, 2018 Federico Gentile
# Simple plugin management system.


import logging
import logging.handlers
import os
from pike.manager import PikeManager


logger = logging.getLogger("mH." + __name__)

class Pluginmanager:
    """A very simple plugin manager."""

    def __init__(self, quickload=False):
        """Initialises the plugin manager."""
        self.p_mgr = None
        self.plugins = None
        self.plugins_loaded = False
        if quickload:
            self.load_plugins()
    
    def load_plugins(self):
        """Loads plugins"""
        if not self.plugins_loaded:
            logger.info("Loading plugins ...")
            # Preliminary check to only load classes that inherit from Pluginbase
            with PikeManager([os.path.dirname(os.path.realpath(__file__)) + '/plugins']) as self.p_mgr:
                classes = self.p_mgr.get_all_inherited_classes(Pluginbase)
            logger.debug("  >> %d class(es) inherited from Pluginbase detected: %s", len(classes), str(classes))

            # Second, more thorough checking
            self.plugins = []
            for pl_class in classes:
                if hasattr(pl_class, 'MHPLUGIN') and hasattr(pl_class, 'NAME') and pl_class.MHPLUGIN:
                    if pl_class.NAME is not None and pl_class.VERSION is not None and pl_class.AUTHOR is not None:
                        self.plugins.append(pl_class())
                        logger.info("  - Loaded: " + pl_class.NAME + " - version: " + str(pl_class.VERSION) + " by " + pl_class.AUTHOR)
                    else:
                        plugin_str = str(pl_class)
                        logger.warning("  >> Some mandatory attributes of plugin class %s are undefined. Please correct this and reload the application.", plugin_str)
            logger.info("%d plugin(s) found.", len(self.plugins))
            self.plugins_loaded = True

    def begin(self):
        for plugin in self.plugins:
            plugin.begin()
    
    def data(self, data):
        for plugin in self.plugins:
            plugin.data(data)
    
    def end(self):
        for plugin in self.plugins:
            plugin.end()

class Pluginbase:
    """Base class for mobiHue plugins."""

    MHPLUGIN = True
    NAME = None
    VERSION = None
    AUTHOR = None

    def begin(self):
        raise NotImplementedError
    
    def data(self, data):
        raise NotImplementedError
    
    def end(self):
        raise NotImplementedError