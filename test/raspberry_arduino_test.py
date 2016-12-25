#!/usr/bin/env python
#LED on pin 10 with 330 ohm resistor
from nanpy import (ArduinoApi, SerialManager)

connection = SerialManager()
a = ArduinoApi(connection=connection)

from time import sleep

a.pinMode(10, a.OUTPUT)
print"Starting"
while 1:
a.digitalWrite(10, a.HIGH)
print"ON"
sleep(0.5)
a.digitalWrite(10, a.LOW)
sleep(0.5)
print"OFF"