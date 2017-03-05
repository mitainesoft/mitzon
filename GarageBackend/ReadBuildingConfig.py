""" Read Building definifion from file"""
import logging
from GarageBackend.Constants import *



#log = logging.getLogger('')

NBR_GARAGE=2
GARAGE_BOARD_PIN = [7, 6, 5, 4]

''' 2 sensor on top config '''
GARAGE_SENSORS_PIN = [[8,9],
                     [10,11],
                     [8, 9], # invalid !
                     [10, 11] # invalid !
                      ]

'''4 sensor on side config '''
# GARAGE_SENSORS_PIN = [[8,9,10,11],
#                      [2,3,12,13]]

GARAGE_NAME = ["GARAGE_0", "GARAGE_1", "GARAGE_2", "GARAGE_3"]