#!/usr/bin/env python
#LED on pin 10 with 330 ohm resistor
from nanpy import (ArduinoApi, SerialManager)
from time import sleep

connection = SerialManager()
a = ArduinoApi(connection=connection)

mypin=7

a.pinMode(mypin, a.OUTPUT)
print("Rapberry Arduino connection Starting")

while 1:
    a.digitalWrite(mypin, a.HIGH)
    print ("ON")
    sleep(2)
    a.digitalWrite(mypin, a.LOW)
    print ("OFF")
    sleep(2)
