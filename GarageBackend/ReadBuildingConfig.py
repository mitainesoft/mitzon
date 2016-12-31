""" Read Building definifion from file"""
import logging
from GarageBackend.Constants import *



log = logging.getLogger(__name__)

NBR_GARAGE=2
GARAGE_BOARD_PIN = [7, 6, 5, 4]

''' 2 sensor on top config '''
GARAGE_SENSORS_PIN = [[8,9],
                     [10,11]]

'''4 sensor on side config '''
# GARAGE_SENSORS_PIN = [[8,9,10,11],
#                      [2,3,12,13]]

GARAGE_NAME = ["GARAGE_VERT", "GARAGE_ROUGE"]