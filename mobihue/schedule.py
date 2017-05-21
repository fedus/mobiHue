#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mobiHue.py - announces real time bus arrivals using Philipps Hue lights
# (c) 2017 Federico Gentile
# HAFAS / Mobiliteit.lu schedule module

import logging
import requests
import operator
from datetime import datetime, timedelta
from time import sleep

logger = logging.getLogger(__name__)


class Bus():
    """Holds journey information for a single Bus at a time."""

    def __init__(self, line, direction, time, rtTime, eta, delay, zone):
        """Initialise the Bus class."""
        self.line = line
        self.direction = direction
        self.time = time
        self.rtTime = rtTime
        self.eta = eta
        self.delay = delay
        self.zone = zone

    def __str__(self):
        """Returns a human readable representation of the Bus class instance."""
        return "Bus instance [line: {}, direction: {}, time: {}, real time: {}, eta: {}, delay: {}, zone: {}]".format(self.line, self.direction, self.time, self.rtTime, self.eta, self.delay, self.zone)

    def __repr__(self):
        """Returns an object representation of the Bus class instance."""
        return "Bus({}, {}, {}, {}, {}, {}, {})".format(self.line, self.direction, self.time, self.rtTime, self.eta, self.delay, self.zone)


class Schedule():
    """Connects to the Mobiliteit.lu API and returns all relevant timetable data for the program"""

    def __init__(self, transport, stop_id, api_base_url, zones):
        """Initialise the Schedule class"""
        self.transport = transport
        self.stop_id = stop_id
        self.api_base_url = api_base_url
        self.api_final_url = self.api_base_url + self.stop_id
        self.zones = zones
        self.allowed_error_count = 3
        self.connection_timeout = None
        self.last_update = False
        self.next_departure = None
        self.last_departure = None
        self.all_departures = None
        self.total_departures = None

    def _mobi_api_request(self):
        """Executes a Mobiliteit.lu API HTTP request"""
        for self.error_count in range(self.allowed_error_count):
            try:
                self.api_request = requests.get(self.api_final_url, timeout=self.connection_timeout, headers={"host":"travelplanner.mobiliteit.lu"})
                self.api_request.raise_for_status()
            except (requests.ConnectionError, requests.HTTPError, requests.TooManyRedirects, requests.Timeout) as e:
                if self.error_count < self.allowed_error_count - 2:
                    logger.warning("The HTTP request to the Mobiliteit.lu API raised an exception. Waiting 2 seconds. Try " + str(
                        self.error_count + 2) + " of " + str(self.allowed_error_count) + " ...")
                    sleep(2)
                    continue
                else:
                    raise
            break
        return self.api_request

    def _mobi_api_json(self):
        """Executes the Mobiliteit.lu API request function and turns the result into a JSON object"""
        self.api_request = self._mobi_api_request()
        try:
            self.api_json = self.api_request.json()
        except ValueError:
            logger.critical("A JSON decoding error was encountered.")
            sys.exit("Aborting ...")
        else:
            return self.api_json

    def _string_to_datetime(self, journey, is_real_time):
        """"Converts strings of scheduled and realtime date-times to datetime objects"""
        self.hafas_datetime_pattern = "%Y-%m-%d %H:%M:%S"
        if is_real_time:
            return datetime.strptime(journey["rtDate"]+" "+journey["rtTime"], self.hafas_datetime_pattern)
        elif not is_real_time:
            return datetime.strptime(journey["date"]+" "+journey["time"], self.hafas_datetime_pattern)

    def _eta_to_zone(self, eta):
        """Returns the appropriate zone for a given estimated time of arrival."""
        self.eta_minutes = eta.seconds // 60
        if self.eta_minutes <= self.zones["imminent"]["minutes"]:
            # Bus or train arrival imminent
            self.zone_name = "imminent"
        elif self.eta_minutes <= self.zones["close"]["minutes"]:
            # Bus or train close
            self.zone_name = "close"
        elif self.eta_minutes <= self.zones["intermediate"]["minutes"]:
            # Bus or train at intermediate distance
            self.zone_name = "intermediate"
        elif self.eta_minutes > self.zones["intermediate"]["minutes"]:
            # Bus or train at safe distance
            self.zone_name = "further"
        return self.zone_name

    def _parseJourneyTimes(self, journey, time_anchor):
        """Calculates all relevant date-times for a given journey"""
        self.scheduled_time = self._string_to_datetime(journey, False)
        if "rtTime" in journey:
            self.rtTime = self._string_to_datetime(journey,True)
            self.eta = self.rtTime - time_anchor
            self.temp_delay = self.rtTime - self.scheduled_time
            if self.temp_delay.seconds > 0:
                self.delay = self.temp_delay
            elif self.temp_delay.seconds == 0:
                self.delay = False
        elif "rtTime" not in journey:
            self.rtTime = False
            self.delay = False
            self.eta = self.scheduled_time - time_anchor
        self.current_zone = self._eta_to_zone(self.eta)
        self.parsed_journey_times = {
            "time": self.scheduled_time,
            "rtTime": self.rtTime,
            "eta": self.eta,
            "delay": self.delay,
            "zone": self.current_zone,
        }
        return self.parsed_journey_times

    def update(self):
        """Parses the raw Mobiliteit.lu response and returns a final list of all relevant buses and all relevant times in accordance with the settings"""
        self.raw_schedule = self._mobi_api_json()
        self.parsed_schedule = []
        self.current_time = datetime.now().replace(second=0, microsecond=0)
        if "Departure" in self.raw_schedule:
            for self.journey in self.raw_schedule["Departure"]:
                if any(str(self.bus["number"]) == str(self.journey["Product"]["line"]) and self.bus["direction"] in self.journey["direction"] for self.bus in self.transport):
                    self.departure_times = self._parseJourneyTimes(self.journey, self.current_time)
                    self.new_bus = {
                        "line": self.journey["Product"]["line"],
                        "direction": self.journey["direction"],
                        "time": self.departure_times["time"],
                        "rtTime": self.departure_times["rtTime"],
                        "eta": self.departure_times["eta"],
                        "delay": self.departure_times["delay"],
                        "zone": self.departure_times["zone"],
                        }
                    self.parsed_schedule.append(Bus(**self.new_bus))
            self.parsed_schedule.sort(key=operator.attrgetter("eta"))
            self._assign_schedule_variables(self.parsed_schedule)
            self.last_update = self.current_time
            return True
        elif "Departure" not in self.raw_schedule:
            return False

    def _assign_schedule_variables(self, parsed_schedule):
        """Assigns schedule data to the right internal variables."""
        self.next_departure = parsed_schedule[0]
        self.last_departure = parsed_schedule[-1]
        self.all_departures = parsed_schedule
        self.total_departures = len(parsed_schedule)
        return True
