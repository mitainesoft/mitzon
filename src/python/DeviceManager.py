from time import sleep

from nanpy import ArduinoApi, SerialManager

mypin = 6
connection = SerialManager()
usbConnectHandler = ArduinoApi(connection=connection)
usbConnectHandler.pinMode(mypin, usbConnectHandler.OUTPUT)


class DeviceManager():
    def __init__(self):
        print("init deviceManager")

    def testConnection(self):
        print("Arduino Pin=", mypin)
        for n in range(0, 1):
            usbConnectHandler.digitalWrite(mypin, usbConnectHandler.HIGH)
            print("ON")
            sleep(2)
            usbConnectHandler.digitalWrite(mypin, usbConnectHandler.LOW)
            print("OFF")
            sleep(2)
            n += 1
