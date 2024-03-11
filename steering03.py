# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 14:40:33 2019

@author: XEG09907363

Klasse zur Erzeugung einer ganzen Serie von Bildern
"""

import xml.etree.ElementTree as ET
import logging
from picture10 import Picture
from rectangle_db_01 import RectangleDB


class Steering:
    """
    Klasse zur Erzeugung einer ganzen Serie von Bildern
    """

    def __init__(self, xml_filename, timestamp):
        """ Konstruktor """
        self.timestamp = timestamp
        self.seeds = []  # Liste der Impfpunkte

        # XML-File einlesen und parsen
        tree = ET.parse(xml_filename)
        root = tree.getroot()

        # Bild-Filenamen ermitteln
        for elem in root.iter('file'):
            self.filename = elem.text
            self.filename_org = elem.text

        # Datenbankpräfix ermitteln
        for elem in root.iter('db_prefix'):
            self.db_prefix = elem.text

        # Abweichung von, bis, schritt
        for elem in root.iter('deviation_von'):
            self.abw_s_von = float(elem.text)
        for elem in root.iter('deviation_bis'):
            self.abw_s_bis = float(elem.text)
        for elem in root.iter('deviation_ste'):
            self.abw_s_ste = float(elem.text)

            # Anzahl Farben auf die das Bild reduziert wird
        for elem in root.iter('number_of_colors'):
            self.num_colors = int(elem.text)

        # Rastergröße
        for elem in root.iter('raster_von'):
            self.step_size_von = int(elem.text)
        for elem in root.iter('raster_bis'):
            self.step_size_bis = int(elem.text)
        for elem in root.iter('raster_ste'):
            self.step_size_ste = int(elem.text)

        for elem in root.iter('recFactor'):  # Faktor für den Seedabstand
            self._rec_factor = float(elem.text)

        for elem in root.iter('minrec'):  # Mindestgröße eines gefundenen Rechtecks
            self._min_rec_sice = int(elem.text)

        for elem in root.iter('blurbox'):  # Rastergröße für ImageFilter.BoxBlur
            self._blurbox = int(elem.text)

        for seed in root.iter('seed'):  # Alle Impfpunkte einlesen
            for subsub in seed.iter('x'):
                seed_x = int(subsub.text)
            for subsub in seed.iter('y'):
                seed_y = int(subsub.text)

            seed_xy = (seed_x, seed_y)
            self.seeds.append(seed_xy)

    def print_config_data(self):
        """
        Ausgabe der XML-Werte
        """
        print("Deviation: von", self.abw_s_von,
              "bis", self.abw_s_bis,
              "Step", self.abw_s_ste)

        print("Raster: von", self.step_size_von,
              "bis", self.step_size_bis,
              "Step", self.step_size_ste)

    def iterate_deviation_raster(self):
        """
        Iteriert über deviation -> raster
        """

        dev_iter = 0  # Deviation Iteration = Version
        ras_iter = 0  # Raster Iteration = Version
        f_dev = self.abw_s_von  # Startwert Deviation

        while True:
            dev_iter = dev_iter + 1  # Versionsnummer hochzählen
            i_ras = self.step_size_von  # Startwert Raster

            while True:
                logging.info("Deviation:%f Raster:%i", f_dev, i_ras)

                # Instanz für das Bild erzeugen
                PICONE = Picture(self.filename, self.timestamp)

                # Für die richtigen Filenamen muss noch die "Version" übergeben werden
                ras_iter = ras_iter + 1  # Versionsnummer hochzählen
                version = str(dev_iter) + "." + str(ras_iter)
                logging.info("Version: %s", version)

                # Instanz für die Datenbank erzeugen und leere Tabellen anlegen
                db_name = self.db_prefix + "." + version + ".db"
                DBONE = RectangleDB(db_name)
                DBONE.drop_rec_db_tables()

                if DBONE.create_rec_db_tables() == False:
                    return  # Beim Fehler abhauen

                # Parameter für die Klasse übergeben
                PICONE.set_parameter(f_dev, i_ras, self._rec_factor,
                                     self._min_rec_sice, self._blurbox,
                                     self.seeds, version, self.num_colors)

                # Bild aufbereiten
                PICONE.preprocess_image()

                # #Bild rastern und komprimieren
                # PICONE.simplify_picture()

                # <<<<<<<<<<<<<<

                # Kunstwerk erzeugen
                ART_BILD, TEC_BILD, MER_BILD, VOR_BILD = PICONE.create_art(PICONE.get_filename("PreProcess"), DBONE)
                ART_BILD.save(PICONE.get_filename("Art"))  # Bild speichern
                TEC_BILD.save(PICONE.get_filename("Tec"))  # Bild speichern
                MER_BILD.save(PICONE.get_filename("Merge"))  # Bild speichern
                VOR_BILD.save(PICONE.get_filename("Vorlage"))  # Bild speichern

                # Mit Rechtecken auffüllen
                FIN_BILD, VOR_BILD = PICONE.fill_picture_with_rectangles(PICONE.get_filename("Art"),
                                                                         PICONE.get_filename("Merge"),
                                                                         PICONE.get_filename("Vorlage"))
                FIN_BILD.save(PICONE.get_filename("Final"))  # Bild speichern
                VOR_BILD.save(PICONE.get_filename("Vorlage"))  # Bild speichern

                # Datenbank Anzahl Einträge ausgeben und schließen
                logging.info("Anzahl DB-Einträge: %i", DBONE.count_all())
                DBONE.close()

                # Instanzen wieder freigeben
                del PICONE
                del DBONE

                # Nächsten Rasterwert ermitteln
                if i_ras < self.step_size_bis:
                    i_ras = i_ras + self.step_size_ste
                else:
                    ras_iter = 0
                    break

            # Nächsten Deviationwert ermitteln
            if f_dev < self.abw_s_bis:
                f_dev = f_dev + self.abw_s_ste
            else:
                break

            # Ende Schleife Abweichung

