import logging
from MitzonBackend.Constants import *
from MitzonBackend.ConfigManager import *
from MitzonBackend.CommandQResponse import *
from MitzonBackend.ConfigManager import *
from MitzonBackend.CommandQResponse import *
from MitzonBackend.AlertManager import AlertManager
from time import sleep
import time
import datetime
import cherrypy
import os, sys, traceback
import aiohttp
import asyncio
import string
import re
from html import escape

log = logging.getLogger('Weather.WeatherManager')

class WeatherManager(metaclass=SingletonMeta):

    def __init__(self):
        #log.setLevel(logging.INFO)
        log.info("WeatherManager Starting")
        self.weather_manager_start_time=time.time()

        self.config_handler = ConfigManager()
        self.alarm_mgr_handler = AlertManager()
        self.cherryweb_server_last_run_time = time.time()

        self.meteo_url=self.config_handler.getConfigParam("WEATHER_MANAGER", "WEATHER_URL")
        self.meteo_url_json=self.config_handler.getConfigParam("WEATHER_MANAGER", "WEATHER_URL_JSON")
        self.use_json_resp=True

        self.isRainForecast=False



    def monitor(self):
        i=0
        lastlogprint = time.time()
        while (True):
            if i%10000==0 or time.time() > (lastlogprint+float(self.config_handler.getConfigParam("VALVE_MANAGER","VALVE_DISPLAY_ALL_STATUS_INTERVAL"))):
                log.info("** WeatherManager heart beat %d **" % (i))
                lastlogprint = time.time()

            if time.time() > (self.weather_manager_start_time+60):
                if cherrypy.engine.state == cherrypy.engine.states.STARTED:
                    if i%1000==0:
                        log.debug("Cherrypy Web Server Thread Running")
                    self.cherryweb_server_last_run_time = time.time()
                else:
                    log.error("Cherrypy Web Server Thread Dead")
                    if (time.time() > (self.cherryweb_server_last_run_time + 120) ):
                        log.error("Cherrypy Web server thread not running, force exit of valve processes for crontab restart !")
                        os._exit(-1)
                    elif (time.time() > (self.cherryweb_server_last_run_time + 30) ):
                        # 15sec to allow for cherry pi web server to start
                        log.error("Cherrypy Web server thread not running, sending alert SW001 !")
                        # status_text = self.alarm_mgr_handler.addAlert("SW001", "RASPBERRY_PI")
                        status_text = self.addAlert("SW001", "RASPBERRY_PI")
                        log.error(status_text)
            else:
                if i % 5 == 0:
                    log.debug("Cherrypy Web server thread monitoring off for 1 min after ValveManager thread startup")

            try:
                if self.use_json_resp==True:
                    asyncio.run(self.getJSONWeatherFromWTTR())
                else:
                    asyncio.run(self.getWeatherFromWTTR())
            except Exception:
                #self.addAlert("SW002", self.__class__.__name__ , "getWeatherFromWTTR Exeption")
                log.error("Get Weather Error!")
                traceback.print_exc()

            sleep(float(self.config_handler.getConfigParam("WEATHER_MANAGER","WEATHER_MANAGER_LOOP_TIMEOUT")))
            i=i+1
        pass

    async def getJSONWeatherFromWTTR(self):
        found_rain = False
        async with aiohttp.ClientSession() as session:
            meteo_url = self.meteo_url_json
            async with session.get(meteo_url) as resp:
                meteo_json = await resp.json()
                logstr1 = "Status:" + str(resp.status) + " Content-type:", resp.headers['content-type']
                log.debug(logstr1)
                logstr2=json.dumps(meteo_json)
                log.debug(logstr2)
                current_condition=meteo_json["current_condition"][0]["weatherDesc"][0]['value'].upper()
                localObsDateTime =meteo_json["current_condition"][0]["localObsDateTime"]
                if "RAIN" in current_condition:
                    found_rain = True
                logstr3= current_condition+ " on " + localObsDateTime
                log.info(logstr3)

        if found_rain == True:
            self.isRainForecast = True
        else:
            self.isRainForecast = False
        logstr = "is Rain Forecasted? " + str(self.isRainForecast)
        log.info(logstr)

    async def getWeatherFromWTTR(self):
        found_rain=False
        async with aiohttp.ClientSession() as session:
            meteo_url = self.meteo_url
            async with session.get(meteo_url) as resp:
                html = await resp.text()
                logstr1 = "Status:" + str(resp.status) + " Content-type:", resp.headers['content-type']
                log.debug(logstr1)
                lines = html.split('\n')
                log.info("*Weather*")
                for line in lines:
                    # linesub = line[16:]
                    # linesub2 = re.sub(f'[^{re.escape(string.printable)}]', '', linesub)
                    # linesub3 = linesub2.rstrip().lstrip().upper()
                    linetmp= line.upper()
                    if "RAIN" in linetmp:
                        found_rain = True
                    log.info(line)


        if found_rain == True:
            self.isRainForecast = True
        else:
            self.isRainForecast = False
        logstr = "is Rain Forecasted? " + str(self.isRainForecast)
        log.info(logstr)

    def isRainForecasted(self):
        return self.isRainForecast