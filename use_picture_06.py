    # -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 10:52:24 2019

@author: Geert Engelhardt
"""

from datetime import datetime as DateTime
import logging
from steering03 import Steering

# Für das Logging alles vorbereiten
# Log-Level •DEBUG •INFO •WARNING •ERROR •CRITICAL
# Format-Attribute: https://docs.python.org/3/library/logging.html#logrecord-attributes
#logging.basicConfig(format='%(levelname)s:%(funcName)s:%(message)s', level=logging.INFO)
logging.basicConfig(format='%(module)s:%(funcName)s:%(message)s', level=logging.INFO)
#logging.basicConfig(format='%(module)s:%(funcName)s:%(message)s',level=logging.DEBUG)
# logging.basicConfig(filename='picture.log', filemode='w',
                            # format='%(module)s:%(funcName)s:%(message)s',level=logging.DEBUG)

#=============================================================================
#   Hauptprogramm
#=============================================================================
# Filenamen
# XML_FILENAME_ORIGINAL = 'kurve-gross.xml'
# XML_FILENAME_ORIGINAL = 'kurve-wild-klein-serie.xml'
# XML_FILENAME_ORIGINAL = 'pilz-klein-serie.xml'
XML_FILENAME_ORIGINAL = 'Schmetterling-klein-serie.xml'

TIME_STAMP = format(DateTime.now(), '%H%M%S')

# Objekt erzeugen und Konfiguration aus XML-File lesen
STEER01 = Steering(XML_FILENAME_ORIGINAL, TIME_STAMP)
STEER01.print_config_data()

#Über Abweichung-> Raster iterieren
STEER01.iterate_deviation_raster()


print("\n Ende der Fahnenstange")