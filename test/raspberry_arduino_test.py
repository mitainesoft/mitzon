#!/usr/bin/env python
#LED on pin 10 with 330 ohm resistor
from nanpy import (ArduinoApi, SerialManager)

connection = SerialManager()
a = ArduinoApi(connection=connection)

from time import sleep

mypin=7

a.pinMode(mypin, a.OUTPUT)
print("Starting")

while 1:
    a.digitalWrite(mypin, a.HIGH)
    print ("ON")
    sleep(2)
    a.digitalWrite(mypin, a.LOW)
    print ("OFF")
    sleep(2)
