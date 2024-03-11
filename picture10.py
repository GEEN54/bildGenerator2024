# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 10:46:16 2019

@author: Geert Engelhardt
"""

# Klasse picture
#
# Ein Bild wird in "gleichfarbige" Segmente (Quader) zerlegt

import logging
import matplotlib.image as mpimg
from PIL import Image, ImageDraw, ImageColor, ImageFilter
import numpy as np
from polygon09 import Polygons
import cv2 as cv
import pathlib


class Picture:
    """ Klasse zur Bearbeitung eines Bildes """

    MAX_WHILE = 10000  # Abbruchkriterium für alle While-Schleifen
    MAX_ROUNDS_REC = 400  # Maximale Anzahl von Runden zum Finden eines Rechtecks
    MAX_RECS_TO_FILL = 1000  # Anzahl Rechtecke die nachträglich eingezeichnet werden
    MAX_SEEDS = 1000  # Maximale Anzahl neuer Seeds

    def __init__(self, bild_filename, timestamp):
        """ Konstruktor """

        self._x_max_pic = 0  # Größe des Bildes X
        self._y_max_pic = 0  # Größe des Bildes Y
        self._abw_s = 0.1  # maximale Abweichung
        self._step_size = 0  # Rastergröße
        self.global_raster = []  # Speichert Mittelpunkte aller Raster als globale Variable
        # a_xy, c_xy, rgb, step_x, step_y, mitte_x, mitte_y
        self.seeds = []  # Liste der Impfpunkte
        self.step_size = 0  # Rastergröße
        self._rec_factor = 0.0  # Faktor für den Seedabstand
        self._min_rec_sice = 0  # Mindestgröße eines gefundenen Rechtecks
        self._filename_copy = "_kopie"  # Präfix für das File welches eigentlich bearbeitet wird
        self._timestamp = timestamp  # Marker für alles was gespeichert wird
        self._blurbox = 0  # Rastergröße für ImageFilter.BoxBlur
        self._standard_color = 'white'  # Standardfarbe für neue Bilder
        self._min_rec_size = 0  # Minimale Größe eines gefundnen Rechtecks

        self.bild_raster = Image.new('RGB', (1, 1), color=self._standard_color)
        self.np_bild = []

        self.filename = bild_filename
        self.filename_org = bild_filename

    def set_parameter(self, deviation, raster, faktor, rec_size, blur, seeds, version, num_colors):
        """
        Vorbelegen der Steuerparameter
        """
        self._abw_s = deviation  # Abweichung
        self._step_size = raster  # Rastergröße
        self._rec_factor = faktor  # Faktor für den Seedabstand
        self._min_rec_sice = rec_size  # Mindestgröße eines gefundenen Rechtecks
        self._blurbox = blur  # Rastergröße für ImageFilter.BoxBlur
        self.seeds = seeds  # Impfpunkte
        self.version = version  # Versionsnummer für die Files
        self.num_colors = num_colors  # Anzahl Farben die ein Bild haben darf

    def reduce_colors(self, img, n_colors):
        # Reshape the image to be a list of pixels
        pixels = img.reshape(-1, 3).astype(np.float32)

        # Perform K-means clustering to find the most dominant colors
        criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 100, 0.3)
        _, labels, centers = cv.kmeans(pixels, n_colors, None, criteria, 10, cv.KMEANS_RANDOM_CENTERS)

        # Convert the colors of the centers to integer (necessary for later operations)
        centers = np.uint8(centers)
        print('Centers: ', centers)
        # Map the labels to the centers
        segmented_image = centers[labels.flatten()]

        # Reshape back to the original image
        segmented_image = segmented_image.reshape(img.shape)

        return segmented_image

    def double_blur(self, img, counter):
        # Convert the image to RGB
        img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        # Apply median blur 2 fach
        dst1 = cv.medianBlur(img_rgb, counter)
        dst = cv.medianBlur(dst1, counter)
        return dst

    def preprocess_image(self):
        """
        Führt diverse "Vorarbeiten" mit Hilfe der Filter von image durch
        """
        # a) Bild als cvs Image einlesen
        im_tmp1 = cv.imread(self.filename)

        # b) Anzahl Farben reduzieren
        im_tmp1 = self.reduce_colors(im_tmp1, self.num_colors)  # Reduce to 5 colors

        # c) Double Blur
        im_tmp1 = self.double_blur(im_tmp1, 3)

        # d) Save Image
        prefix, ending = self.filename.split(".")
        self.filename = self.get_filename("PreProcess")
        cv.imwrite(self.filename, im_tmp1)

        # e) Bild als Image einlesen
        im_tmp = Image.open(self.filename)

        # # d) Bild mit einem neuen Namen abspeichern
        # im_tmp.save(self.filename)

        # Bild als numpy-Array einlesen
        self._read_original_file_as_np()

    def _read_original_file_as_np(self):
        """  Bild einlesen """
        self.np_bild = mpimg.imread(self.filename)
        # Dimensionen des Bildes ermitteln
        pic_org = np.array(self.np_bild)
        pic_dim = np.array(self.np_bild.shape)

        self._x_max_pic = pic_dim[1] - 1  # -1 da Array bei 0 anfängt
        self._y_max_pic = pic_dim[0] - 1

        #logging.info("%s: Bildgröße X: %i Y: %i Pixel", self.filename,
        #             self._x_max_pic + 1, self._y_max_pic + 1)

        dimension_pic = pic_org.shape[2]
        logging.debug("Dimension: %i", dimension_pic)

    def get_filename(self, argument):
        """ erzeugt verschiedene Filenamen """

        #print("Pfad:", pathlib.Path)
        logging.info("%s: Pfad ", pathlib.Path)




        prefix, ending = self.filename_org.split(".")

        if argument == "Raster":
            f_n = self._timestamp + '-02-Ras-' + prefix + '-' + self.version + "." + ending
        elif argument == "Merge":
            f_n = self._timestamp + '-03-Mer-' + prefix + '-' + self.version + "." + ending
        elif argument == "Compress":
            f_n = self._timestamp + '-04-Com-' + prefix + '-' + self.version + "." + ending
        elif argument == "Tec":
            f_n = self._timestamp + '-05-Tec-' + prefix + '-' + self.version + "." + ending
        elif argument == "Art":
            f_n = self._timestamp + '-06-Art-' + prefix + '-' + self.version + "." + ending
        elif argument == "Final":
            f_n = self._timestamp + '-07-Fin-' + prefix + '-' + self.version + "." + ending
        elif argument == "Vorlage":
            f_n = self._timestamp + '-08-Vor-' + prefix + '-' + self.version + "." + ending
        elif argument == "PreProcess":
            f_n = self._timestamp + '-01-PPr-' + prefix + '-' + self.version + "." + ending
        else:
            logging.error("Wrong Argument: %s", argument)
            f_n = ""

        return f_n

    @staticmethod
    def rgb_float_2_rgb_int(seed_xy):
        """ wandelt RGB-Float in RGB_Int um """

        if np.isnan(seed_xy[0]) or np.isnan(seed_xy[0]) or np.isnan(seed_xy[0]):
            rgb_r = 255
            rgb_g = 255
            rgb_b = 255
        else:
            rgb_r = int(round(seed_xy[0] * 255.0))
            rgb_g = int(round(seed_xy[1] * 255.0))
            rgb_b = int(round(seed_xy[2] * 255.0))

        int_rgb = (rgb_r, rgb_g, rgb_b)

        return int_rgb

    def create_rectangle_for_seed(self, np_bild_com, seed_xy):
        """ erzeugt ein maximales Rechteck innnerhalb einer Fläche von Pixeln,
        die ähnlich sind"""

        logging.debug("Impfpunkt %s ", seed_xy)

        # Dimensionen des Bildes ermitteln
        pic_dim = np.array(np_bild_com.shape)
        x_max_com = pic_dim[1]
        y_max_com = pic_dim[0]

        # Nur ein Rechteck ermitteln, wenn die Anzahl der Pixel der Grenzlinie groß genug ist.
        a_xy = (0, 0)
        c_xy = (0, 0)

        # Instanz erzeugen
        polygon1 = Polygons(x_max_com, y_max_com, self._min_rec_size, self._abw_s)

        # ====>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

        # maximales Rechteck suchen
        a_xy, c_xy = polygon1.get_rectangle(np_bild_com, seed_xy)

        # Instanz freigeben
        del polygon1

        return a_xy, c_xy

    def extend_tec_drawing(self, b_tec, a_xy, c_xy, dot_xy):
        """ Zeichnet in der "technischen Zeichung" die gefüllte Grenzlinie und
            das ermittelte Rechteck """
        logging.debug("a_xy:%s, c_xy:%s ", a_xy, c_xy)

        # sicherstellen, dass Integerwerte übergeben werden
        p_xy = [int(dot_xy[0]), int(dot_xy[1])]
        dot_xy = p_xy

        # Seed einzeichnen
        ImageDraw.Draw(b_tec).point(dot_xy, fill=ImageColor.getrgb("red"))

        # Rechteck einzeichnen
        if (a_xy != (0, 0)) or (c_xy != (0, 0)):
            ImageDraw.Draw(b_tec).rectangle([(a_xy), (c_xy)], outline="green")

        return b_tec

    def extend_mer_drawing(self, b_merge, a_xy, c_xy, org_rgb):
        """ Zeichnet das Rechteck in die ursprüngliche Zeichnung:
            a) Ein gefülltes Rechteck mit der Farbe des Seeds und
            b) Eine Abgrenzung um das Rechteck gezeichnet """

        if (a_xy != (0, 0)) or (c_xy != (0, 0)):
            ImageDraw.Draw(b_merge).rectangle([(a_xy), (c_xy)], fill=org_rgb)

        return b_merge

    def extend_art_drawing(self, b_art, a_xy, c_xy, org_rgb):
        """ Zeichnet das Kunstwerk; aktuell wird:
            a) Ein gefülltes Rechteck mit der Farbe des Seeds und
            b) Eine Abgrenzung um das Rechteck gezeichnet """

        if (a_xy != (0, 0)) or (c_xy != (0, 0)):
            ImageDraw.Draw(b_art).rectangle([(a_xy), (c_xy)],
                                            fill=org_rgb, outline=org_rgb)

        return b_art

    def extend_vor_drawing(self, b_vor, a_xy, c_xy, counter, db_handle, org_rgb):
        """ Zeichnet in der "Malvorlage" das ermittelte Rechteck wobei die
            Koordinaten des Rechteck noch umgerechnet werden müssen"""
        logging.debug("komprimiert a_xy:%s, c_xy:%s", a_xy, c_xy)

        a_xy = (int(a_xy[0] * self._step_size), int(a_xy[1] * self._step_size))
        c_xy = (int(c_xy[0] * self._step_size), int(c_xy[1] * self._step_size))

        logging.debug("Cxy:%s, x_max:%i", c_xy, self._x_max_pic)

        # Wenn x oder y zwischen x_max_pic - step_size und x_max_pic dann auf das Maximum setzen
        if (c_xy[0] >= self._x_max_pic - self._step_size):
            c_xy = (self._x_max_pic, c_xy[1])
        if (c_xy[1] >= self._y_max_pic - self._step_size):
            c_xy = (c_xy[0], self._y_max_pic)

        # Grenzen prüfen
        if a_xy[0] > self._x_max_pic:
            a_xy = (self._x_max_pic, a_xy[1])
        if a_xy[1] > self._y_max_pic:
            a_xy = (a_xy[0], self._y_max_pic)
        if c_xy[0] > self._x_max_pic:
            c_xy = (self._x_max_pic, c_xy[1])
        if c_xy[1] > self._y_max_pic:
            c_xy = (c_xy[0], self._y_max_pic)

        logging.debug("dekomprimiert a_xy:%s, c_xy:%s", a_xy, c_xy)

        # sicherstellen, dass Integerwerte übergeben werden
        if (a_xy != (0, 0)) or (c_xy != (0, 0)):
            # Rechteck einzeichnen
            ImageDraw.Draw(b_vor).rectangle([(a_xy), (c_xy)], outline="black")
            # Daten in die Datenbank schreiben
            db_handle.insert_entry_rec_db(counter, self._x_max_pic,
                                          self._y_max_pic, a_xy[0], a_xy[1], c_xy[0], c_xy[1],
                                          org_rgb[0], org_rgb[1], org_rgb[2])

        return b_vor

    def determine_child_seeds(self, b_art, a_xy, c_xy, x_max, y_max):
        """ Ermittelt für einen gegebenen seed, möglichst vier weitere
            seeds. Wichtig dabei ist, dass diese innerhalb des Bildes
            und nicht bereits durch ein Rechteck "belegt" sind  """

        # Vorgehen:
        # a) Abstand des neuen seed ermitteln. Dies könnte z.B.
        #    die doppelte Entfernung vom aktuellen seed zu dessen Rechteckgrenze sein
        # b) prüfen, ob der Punkt noch innerhalb des Bildes und nicht
        #    bereits belegt ist
        seeds = []
        pic = b_art.load()  # damit kann man auf die Pixel zugreifen
        empty_pixel_rgb = ImageColor.getrgb(self._standard_color)

        # Kantenlänge AB und BC ermitteln
        x_rec_length = abs(c_xy[0] - a_xy[0])
        y_rec_length = abs(c_xy[1] - a_xy[1])

        logging.debug(" ===> a_xy:%s c_xy:%s x-Kante:%i y-Kante:%i"
                      , a_xy, c_xy, x_rec_length, y_rec_length)

        # Prüfen, ob eine Länge > 0 ist
        if x_rec_length == 0 or y_rec_length == 0:
            return seeds

        # Für die neuen Seeds wird die Kantenlänge des Rechtecks verwendet
        x_mitte = int((a_xy[0] + c_xy[0]) / 2 * self._rec_factor)
        y_mitte = int(a_xy[1] - y_rec_length)
        seed_ab = (x_mitte, y_mitte)

        y_mitte = int((a_xy[1] + c_xy[1]) / 2 * self._rec_factor)
        x_mitte = int(c_xy[0] + x_rec_length)
        seed_bc = (x_mitte, y_mitte)

        x_mitte = int((a_xy[0] + c_xy[0]) / 2 * self._rec_factor)
        y_mitte = int(c_xy[1] + y_rec_length)
        seed_cd = (x_mitte, y_mitte)

        y_mitte = int((a_xy[1] + c_xy[1]) / 2 * self._rec_factor)
        x_mitte = int(a_xy[0] - x_rec_length)
        seed_da = (x_mitte, y_mitte)

        # prüfen ob die Punkte noch innerhalb des Bildes sind und
        # nicht Teil eines bereits bestehenden Rechtecks
        if not (seed_ab[0] < 0 or seed_ab[0] > x_max or
                seed_ab[1] < 0 or seed_ab[1] > y_max):
            if pic[int(seed_ab[0]), int(seed_ab[1])] == empty_pixel_rgb:
                seeds.append(seed_ab)
        if not (seed_bc[0] < 0 or seed_bc[0] > x_max or
                seed_bc[1] < 0 or seed_bc[1] > y_max):
            if pic[int(seed_bc[0]), int(seed_bc[1])] == empty_pixel_rgb:
                seeds.append(seed_bc)
        if not (seed_cd[0] < 0 or seed_cd[0] > x_max or
                seed_cd[1] < 0 or seed_cd[1] > y_max):
            if pic[int(seed_cd[0]), int(seed_cd[1])] == empty_pixel_rgb:
                seeds.append(seed_cd)
        if not (seed_da[0] < 0 or seed_da[0] > x_max or
                seed_da[1] < 0 or seed_da[1] > y_max):
            if pic[int(seed_da[0]), int(seed_da[1])] == empty_pixel_rgb:
                seeds.append(seed_da)

        return seeds

    def compress_seeds(self):
        """ Rechnet die x/y-Werte auf die reduzierten Werte um, damit auch
            auf den komprimierten Bild richtig gearbeitet wird.
        """
        com_seeds = []

        for i in range(0, len(self.seeds)):
            seed = (int(self.seeds[i][0] / self._step_size), int(self.seeds[i][1] / self._step_size))
            com_seeds.append(seed)

        return com_seeds

    def extend_frame(self, a, c, x_max_com, y_max_com):
        """ gefundenes Rechteck um einen Pixel ausdehnen, damit eine Überlappung entsteht.
            Andernfalls hat mein "doppelte" Grenzlinien """

        # Punkt A: x=x-1 und y=y-1
        ax = a[0]
        if a[0] > 0: ax = a[0] - 1
        ay = a[1]
        if a[1] > 0: ay = a[1] - 1
        a = (ax, ay)

        # Punkt C: x=x+1 und y=y+1, aber nur wenn nicht (0,0)
        if c != (0, 0):
            cx = c[0]
            if c[0] < x_max_com: cx = c[0] + 1
            cy = c[1]
            if c[1] < y_max_com: cy = c[1] + 1
            c = (cx, cy)

        return a, c

    def create_art(self, filename_bild, db_handle):
        """ Rechtecke für jedes "Samenkorn" erzeugen """

        # bearbeitetes Bild als numpy-array einlesen
        np_bild_com = mpimg.imread(filename_bild)

        # Dimensionen des Bildes ermitteln
        pic_dim = np.array(np_bild_com.shape)

        x_max_com = pic_dim[1] - 1  # -1 da Array bei 0 anfängt
        y_max_com = pic_dim[0] - 1

        logging.info("Bildgröße X: %i Y: %i Pixel", x_max_com + 1, y_max_com + 1)

        # Kunstbild erzeugen
        bild_com = Image.open(filename_bild).convert('RGB')
        bild_art = Image.new('RGB', (x_max_com + 1, y_max_com + 1), color=self._standard_color)
        bild_tec = Image.new('RGB', (x_max_com + 1, y_max_com + 1), color=self._standard_color)
        bild_vor = Image.new('RGB', (self._x_max_pic + 1, self._y_max_pic + 1), color=self._standard_color)

        # Für jedes Rechteck, welches ermittelt wurde, werden weitere
        # Rechtecke erzeugt werden. Im Prinzip werden 4 neue Seeds in allen
        # vier Richtungen des Rechtecks "erzeugt". Diese werden dann genauso
        # gehandhabt wie ein ursprünglicher Seed. Es ist dabei aufzupassen
        # dass kein neuer Seed in einem bereits bestehenden Rechteck liegt und
        # natürlich innerhalb des Bildes

        counter_while = 0

        # Achtung, da hier mit der komprimierten Variante des Bildes gearbeitet wird
        # Müssen die seeds auch entsprechend umgerechnet werden
        # com_seeds = self.compress_seeds()
        # print('TESTETSTETSTET')
        logging.info("Anzahl Seeds: %i", len(self.seeds))

        # while counter_while < self.MAX_WHILE and len(com_seeds) > 0:
        while counter_while < self.MAX_WHILE and len(self.seeds) > 0:
            # Suche ein maximales Rechteck um einem Seed herum
            # Rückgabe: Grenzline, Ecke A und C des Rechtecks, sowie einen Punkt der
            #           innerhalb der Grenzlinie liegt

            seed = self.seeds[0]  # den ersten seed aus der Liste nehmen
            # Prüfen ob der Punkt nicht im bereits bearbeiteten Bereich liegt
            org_rgb = self.rgb_float_2_rgb_int(np_bild_com[seed[1], seed[0]])
            logging.debug("Original RGB:%s Referenz RGB:%s", org_rgb, ImageColor.getrgb(self._standard_color))

            if not np.array_equal(org_rgb, ImageColor.getrgb(self._standard_color)):
                # Rechteck für Seed suchen
                a_xy, c_xy = self.create_rectangle_for_seed(np_bild_com, seed)

                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

                # gefundenes Rechteck um einen Pixel ausdehnen, damit eine Überlappung entsteht.
                a_xy, c_xy = self.extend_frame(a_xy, c_xy, x_max_com, y_max_com)
                logging.debug("Rechteck Nr.%i: a_xy:%s, c_xy:%s", counter_while, a_xy, c_xy)
                # Technische Ergebnisse in bild_tec einzeichnen
                bild_tec = self.extend_tec_drawing(bild_tec, a_xy, c_xy, seed)
                # In die Vorlage die Rahmen zeichnen (Bild hat Originalgröße!)
                bild_vor = self.extend_vor_drawing(bild_vor, a_xy, c_xy, counter_while, db_handle, org_rgb)
                # - Ergebnisse in bild_mer löschen
                bild_com = self.extend_mer_drawing(bild_com, a_xy, c_xy, ImageColor.getrgb(self._standard_color))
                # - bild_mer speichern
                bild_com.save(self.get_filename("Compress"))
                # - np_bild_merge schließen
                np_bild_com = []
                # - bild_merge erneut laden
                np_bild_com = mpimg.imread(self.get_filename("Compress"))
                # Ergebnisse in bild_art einzeichnen
                bild_art = self.extend_art_drawing(bild_art, a_xy, c_xy, org_rgb)

                # Jetzt für den aktuellen Seed nun Nachbar-Seeds erzeugen
                # ausgehend von den aktuellen Seed und dem bild_art, vier Punkte ermitteln,
                # bei denen noch nichts gezeichnet wurde.
                if counter_while < self.MAX_SEEDS:
                    new_seeds = self.determine_child_seeds(bild_art, a_xy, c_xy, x_max_com, y_max_com)
                    # com_seeds.extend(new_seeds)

            # logging.debug("Runde: %i - Anzahl Seeds: %s", counter_while, len(com_seeds))
            logging.debug("Runde: %i - Anzahl Seeds: %s", counter_while, len(new_seeds))

            # aktuellen Seed aus Array Seeds löschen, da bereits bearbeitet
            # com_seeds.remove(seed)
            self.seeds.remove(seed)
            # Zähler für maximale Schleifendurchläufe
            counter_while = counter_while + 1

        # Jetzt das Bild wieder dekomprimieren, damit man die originale Größe hat
        # bild_mer = self.decompress_picture_from_global_raster(bild_com)
        bild_mer = bild_com
        # bild_art = self.decompress_picture_from_global_raster(bild_art)

        return bild_art, bild_tec, bild_mer, bild_vor

    def get_random_pixel_with_color(self, bild_f, p_color):
        """ sucht einen zufälligen Pixel in der Farbe p_color im Bild bild_f """

        pic = bild_f.load()  # damit dann auf die Pixel zugreifen
        terminate = False
        i = 0

        while not terminate:
            # Würfeln
            random_x = int(np.random.randint(0, self._x_max_pic, size=1))
            random_y = int(np.random.randint(0, self._y_max_pic, size=1))

            if pic[random_x, random_y] == ImageColor.getrgb(p_color):
                p_xy = (random_x, random_y)
                terminate = True
            else:
                i = i + 1
                if i > self.MAX_WHILE:
                    p_xy = (0, 0)
                    terminate = True
                    logging.error("Keinen Zufallspixel gefunden")

        logging.debug("Zufalls-Pixel %s %s", p_xy, pic[random_x, random_y])

        return p_xy

    @staticmethod
    def get_rec_area(a_xy, c_xy):
        """ Fläche des Rechtecks bestimmen """

        p_a = a_xy[0] - c_xy[0]
        p_b = a_xy[1] - c_xy[1]

        area = abs(p_a * p_b)

        return area

    def set_next_edge(self, p_xy, step_px, step_py):
        """ prüft ob die Grenzen des Bildes erreicht sind """

        logging.debug("set_next_edge:%s %i %i %i %i", p_xy, step_px, step_py, self._x_max_pic, self._y_max_pic)

        # X-Wert
        if p_xy[0] + step_px <= self._x_max_pic and p_xy[0] + step_px >= 0:
            p_xy = (p_xy[0] + step_px, p_xy[1])
        else:
            step_px = 0

        # Y-Wert
        if p_xy[1] + step_py <= self._y_max_pic and p_xy[1] + step_py >= 0:
            p_xy = (p_xy[0], p_xy[1] + step_py)
        else:
            step_py = 0

        return p_xy, step_px, step_py

    def is_line_within_color_area_2(self, s_xy, e_xy, f_bild, p_color):
        """ ermittelt ob eine Kante (s,e) innerhalb der gleichen Farbe p_color im Bild f_bild liegt """

        np_pic = np.array(f_bild)

        # Startwerte festlegen
        startx = s_xy[0]
        starty = s_xy[1]
        endx = e_xy[0]
        endy = e_xy[1]

        # Werte umdrehen wenn die Richtung CD und DA, da die Abfrage immer
        # vom kleinern zu den größern Wert erfolgt
        if endx <= startx:
            startx = e_xy[0]
            endx = s_xy[0]

        if endy < starty:
            starty = e_xy[1]
            endy = s_xy[1]

        # Jetzt die Mittelwerte für R, G und B ermitteln
        r_values = np_pic[starty:endy + 1, startx:endx + 1, [0]]  # R
        r_mean = np.mean(r_values)
        g_values = np_pic[starty:endy + 1, startx:endx + 1, [1]]  # G
        g_mean = np.mean(g_values)
        b_values = np_pic[starty:endy + 1, startx:endx + 1, [2]]  # B
        b_mean = np.mean(b_values)

        #       Mittelwerte zu einen RGB-Punkt zusammen fassen
        dot_mean = (int(r_mean), int(g_mean), int(b_mean))

        #       Prüfen ob der Punkt innerhalb des Polygons
        if dot_mean == ImageColor.getrgb(p_color):
            return True

        return False

    def is_line_within_color_area(self, s_xy, e_xy, f_bild, p_color):
        """ ermittelt ob eine Kante (s,e) innerhalb der gleichen Farbe p_color im Bild f_bild liegt """
        pic = f_bild.load()

        #        np_pic = np.array(f_bild)
        #        print(ImageColor.getrgb(p_color))
        #        print(np_pic)

        innerhalb = True

        # Startwerte festlegen
        startx = s_xy[0]
        starty = s_xy[1]
        endx = e_xy[0]
        endy = e_xy[1]

        # Werte umdrehen wenn die Zeichenrichtung CD und DA, da immer mit +1 gezeichnet wird
        if endx <= startx:
            startx = e_xy[0]
            endx = s_xy[0]

        if endy < starty:
            starty = e_xy[1]
            endy = s_xy[1]

        p_x = startx

        # Line entlang "fahren". Pixel für Pixel
        while p_x <= endx:
            p_y = starty
            while p_y <= endy:
                if pic[p_x, p_y] == ImageColor.getrgb(p_color):
                    # Der Punkt liegt innerhalb des Polygons
                    p_y = p_y + 1
                else:
                    innerhalb = False
                    break
            p_x = p_x + 1

        return innerhalb

    def find_rectangles(self, f_bild, p_xy, p_color):
        """ ermittelt alle Rechtecke ausgehend von dem Punkt p_xy
            in Bild f_bild mit der Farbe p_color
        """
        # Kanten:
        # AB           x-Kante oben
        # BC           y-Kante rechts
        # CD           x-Kante unten
        # DA           y-Kante links

        # Ecken
        # a_xy
        # b_xy
        # c_xy
        # d_xy

        pic = f_bild.load()  # damit auf die einzelnen Pixel zugeriffen werden kann
        possible_rec = []  # gefundene Rechtecke innerhalb der Farbfläche

        # Die Ecken so lange ausdehnen bis es zu einem Problem im Rechteck kommt

        #       Ecke A nach links oben ziehen
        a_xy = (p_xy)
        step_a_x = -1
        step_a_y = -1

        #       Ecke B nach rechts oben ziehen
        b_xy = (p_xy)
        step_b_x = 1
        step_b_y = -1

        #       Ecke C nach rechts unten ziehen
        c_xy = (p_xy)
        step_c_x = 1
        step_c_y = 1

        #       Ecke D nach links unten ziehen
        d_xy = (p_xy)
        step_d_x = -1
        step_d_y = 1

        # Default alle Ecken innerhalb des Ploygons
        a_in_pol = True
        b_in_pol = True
        c_in_pol = True
        d_in_pol = True

        max_same_rec = 10  # Maximum gleicher Rechtecke => muss dann ein Fehler sein
        same_rec = 0
        i = 0

        terminate = False
        while not terminate:

            i = i + 1

            # die alten Ecken merken
            old_a_xy = a_xy
            old_b_xy = b_xy
            old_c_xy = c_xy
            old_d_xy = d_xy

            # die neuen Ecken berechnen
            a_xy, step_a_x, step_a_y = self.set_next_edge(a_xy, step_a_x, step_a_y)
            b_xy, step_b_x, step_b_y = self.set_next_edge(b_xy, step_b_x, step_b_y)
            c_xy, step_c_x, step_c_y = self.set_next_edge(c_xy, step_c_x, step_c_y)
            d_xy, step_d_x, step_d_y = self.set_next_edge(d_xy, step_d_x, step_d_y)

            # prüfe ob Kante AB innerhalb des Polygon
            answer_ab = self.is_line_within_color_area_2(a_xy, b_xy, f_bild, p_color)
            logging.debug("A ,B, Innerhalb: %s %s %s", a_xy, b_xy, answer_ab)

            # prüfe ob Kante BC innerhalb des Polygon
            answer_bc = self.is_line_within_color_area_2(b_xy, c_xy, f_bild, p_color)
            logging.debug("B ,C, Innerhalb: %s %s %s", b_xy, c_xy, answer_bc)

            # prüfe ob Kante CD innerhalb des Polygon
            answer_cd = self.is_line_within_color_area_2(c_xy, d_xy, f_bild, p_color)
            logging.debug("C ,D, Innerhalb: %s %s %s", c_xy, d_xy, answer_cd)

            # prüfe ob Kante DA innerhalb des Polygon
            answer_da = self.is_line_within_color_area_2(d_xy, a_xy, f_bild, p_color)
            logging.debug("D ,A, Innerhalb: %s %s %s", d_xy, a_xy, answer_da)

            # wenn alle Kanten innerhalb des Polygon, dann dieses Rechteck speichern
            # und vorher die Fläche berechnen

            if (answer_ab and answer_bc and answer_cd and answer_da):
                rec_area = self.get_rec_area(a_xy, c_xy)
                possible_rec.append((a_xy, b_xy, c_xy, d_xy, rec_area))
                same_rec = 0  # Zähler für gleiche Rechtecke zurücksetzen

            elif not answer_ab:
                # die Kante AB ist außerhalb der Farbfläche
                logging.debug("Kante AB hat ein Problem %s %s", a_xy, b_xy)

                # erst einmal prüfen ob die Ecke innerhalb des Polygons sind
                a_in_pol = False
                if pic[a_xy] == ImageColor.getrgb(self._standard_color):
                    a_in_pol = True
                b_in_pol = False
                if pic[b_xy] == ImageColor.getrgb(self._standard_color):
                    b_in_pol = True

                # Ecken auf alte Werte zurücksetzen
                a_xy = old_a_xy
                b_xy = old_b_xy
                c_xy = old_c_xy
                d_xy = old_d_xy
                # Es gibt nun vier Fälle
                if a_in_pol and b_in_pol:
                    # Die Ecken liegen im Polygon, dann hat die Gerade ein Problem
                    # Die Kante auf den alten Wert setzen und  y "stabilisieren"
                    logging.debug("Die Kante AB ist ausserhalb des Polygon")
                    step_a_y = 0
                    step_b_y = 0
                if a_in_pol and not b_in_pol:
                    # Die Ecke B macht ein Problem
                    # Die Ecke auf alten Wert setzen und den step_b_x auf 0
                    logging.debug("Die Ecke B ist außerhalb des Polygon")
                    if step_b_x == 0:
                        step_b_y = 0  # wenn x schon 0 dann sollte y= 0 gesetzt werden
                    step_b_x = 0
                if not a_in_pol and b_in_pol:
                    # Die Ecke A macht ein Problem
                    # Line zurücksetzen
                    # Die Ecke auf alten Wert setzen und den step_a_x auf 0
                    logging.debug("Die Ecke A ist außerhalb des Polygon")
                    if step_a_x == 0:
                        step_a_y = 0  # wenn x schon 0 dann sollte y= 0 gesetzt werden
                    step_a_x = 0
                if not a_in_pol and not b_in_pol:
                    # Beide Ecken liegen außerhalb des Polygon.
                    # Line zurücksetzen
                    # Beide Ecke "einrücken und step_a_x und step_b_x auf 0
                    logging.debug("Die Ecken A und B sind außerhalb des Polygon")
                    step_a_x = 0
                    step_b_x = 0

            elif not answer_bc:
                logging.debug("Kante BC hat ein Problem %s %s", b_xy, c_xy)

                # erst einmal prüfen ob die Ecken innerhalb des Polygons sind
                c_in_pol = False
                if pic[c_xy] == ImageColor.getrgb(self._standard_color):
                    c_in_pol = True
                b_in_pol = False
                if pic[b_xy] == ImageColor.getrgb(self._standard_color):
                    b_in_pol = True

                # Ecken auf alte Werte zurücksetzen
                a_xy = old_a_xy
                b_xy = old_b_xy
                c_xy = old_c_xy
                d_xy = old_d_xy
                # Es gibt nun vier Fälle
                if b_in_pol and c_in_pol:
                    # Die Ecken liegen im Polygon, dann hat die Gerade ein Problem
                    # Die Kante um eins nach links bewegen (x-1) und dann x "stabilisieren"
                    logging.debug("Die Kante BC ist ausserhalb des Polygon")
                    step_b_x = 0
                    step_c_x = 0
                if b_in_pol and not c_in_pol:
                    # Die Ecke C macht ein Problem
                    # Die Ecke um y-1 versetzen und den step_c_y auf 0
                    logging.debug("Die Ecke C ist außerhalb des Polygon")
                    if step_c_y == 0:
                        step_c_x = 0  # wenn y schon 0 dann sollte x= 0 gesetzt werden
                    step_c_y = 0
                if not b_in_pol and c_in_pol:
                    # Die Ecke B macht ein Problem
                    # Die Ecke um y+1 versetzen und den step_b_y auf 0
                    logging.debug("Die Ecke B ist außerhalb des Polygon")
                    if step_b_y == 0:
                        step_b_x = 0  # wenn y schon 0 dann sollte x= 0 gesetzt werden
                    step_b_y = 0
                if not b_in_pol and not c_in_pol:
                    # Beide Ecken liegen außerhalb des Polygon
                    # Beide Ecke "einrücken und step_b_y und step_c_y auf 0
                    logging.debug("Die Ecken B und C sind außerhalb des Polygon")
                    step_b_y = 0
                    step_c_y = 0

            elif not answer_cd:
                logging.debug("Kante CD hat ein Problem %s %s", c_xy, d_xy)

                # erst einmal prüfen ob die Ecken innerhalb des Polygons sind
                c_in_pol = False
                if pic[c_xy] == ImageColor.getrgb(self._standard_color):
                    c_in_pol = True
                d_in_pol = False
                if pic[d_xy] == ImageColor.getrgb(self._standard_color):
                    d_in_pol = True

                # Ecken auf alte Werte zurücksetzen
                a_xy = old_a_xy
                b_xy = old_b_xy
                c_xy = old_c_xy
                d_xy = old_d_xy
                # Es gibt nun vier Fälle
                if c_in_pol and d_in_pol:
                    # Die Ecken liegen im Polygon, dann hat die Gerade ein Problem
                    # Die Kante um eins nach oben bewegen (y-1) und dann y "stabilisieren"
                    logging.debug("Die Kante CD ist ausserhalb des Polygon")
                    step_c_y = 0
                    step_d_y = 0
                if c_in_pol and not d_in_pol:
                    # Die Ecke D macht ein Problem
                    # Die Ecke um x+1 versetzen und den step_d_x auf 0
                    logging.debug("Die Ecke D ist außerhalb des Polygon")
                    if step_d_x == 0:
                        step_d_y = 0  # wenn x schon 0 dann sollte y= 0 gesetzt werden
                    step_d_x = 0
                if not c_in_pol and d_in_pol:
                    # Die Ecke C macht ein Problem
                    # Die Ecke um x-1 versetzen und den step_c_x auf 0
                    logging.debug("Die Ecke C ist außerhalb des Polygon")
                    if step_c_x == 0:
                        step_c_y = 0  # wenn x schon 0 dann sollte y= 0 gesetzt werden
                    step_c_x = 0
                if not c_in_pol and not d_in_pol:
                    # Beide Ecken liegen außerhalb des Polygon
                    # Beide Ecke "einrücken und step_c_x und step_d_x auf 0
                    logging.debug("Die Ecken C und D sind außerhalb des Polygon")
                    step_c_x = 0
                    step_d_x = 0

            elif not answer_da:
                logging.debug("Kante DA hat ein Problem %s %s", d_xy, a_xy)

                # erst einmal prüfen ob die Ecken innerhalb des Polygons sind
                a_in_pol = False
                if pic[a_xy] == ImageColor.getrgb(self._standard_color):
                    a_in_pol = True
                d_in_pol = False
                if pic[d_xy] == ImageColor.getrgb(self._standard_color):
                    d_in_pol = True
                # Ecken auf alte Werte zurücksetzen
                a_xy = old_a_xy
                b_xy = old_b_xy
                c_xy = old_c_xy
                d_xy = old_d_xy
                # Es gibt nun vier Fälle
                if d_in_pol and a_in_pol:
                    # Die Ecken liegen im Polygon, dann hat die Gerade ein Problem
                    # Die Kante um eins nach rechts bewegen (x+1) und dann x "stabilisieren"
                    logging.debug("Die Kante DA ist ausserhalb des Polygon")
                    step_d_x = 0
                    step_a_x = 0
                if d_in_pol and not a_in_pol:
                    # Die Ecke A macht ein Problem
                    # Die Ecke um y+1 versetzen und den step_a_y auf 0
                    logging.debug("Die Ecke A ist außerhalb des Polygon")
                    if step_a_y == 0:
                        step_a_x = 0  # wenn y schon 0 dann sollte x= 0 gesetzt werden
                    step_a_y = 0
                if not d_in_pol and a_in_pol:
                    # Die Ecke D macht ein Problem
                    # Die Ecke um y-1 versetzen und den step_d_y auf 0
                    logging.debug("Die Ecke D ist außerhalb des Polygon")
                    if step_d_y == 0:
                        step_d_x = 0  # wenn y schon 0 dann sollte x= 0 gesetzt werden
                    step_d_y = 0
                if not d_in_pol and not a_in_pol:
                    # Beide Ecken liegen außerhalb des Polygon
                    # Beide Ecke "einrücken und step_d_y und step_a_y auf 0
                    logging.debug("Die Ecken D und A sind außerhalb des Polygon")
                    step_d_y = 0
                    step_a_y = 0

            else:
                # jetzt erst einmal abbrechen ... später mehr
                logging.error("Jetzt ist etwas schief gegangen: %i %s %s %s %s", i,
                              a_xy, b_xy, c_xy, d_xy)
                break

            # Abbruchbedingungen
            # a) maximale Rundenzahl erreicht
            # b) alle Steps sind auf Null
            # c) wenn sich das Recheckt nicht ändert

            # a) maximale Runden
            if i > self.MAX_ROUNDS_REC:
                logging.warning("Maximale Rundenzahl erreicht: %s %s %s %s %s", p_xy,
                                a_xy, b_xy, c_xy, d_xy)
                terminate = True

            # b) wenn alle step auf 0, dann geht nichts mehr
            if ((step_a_x == 0) and (step_a_y == 0) and
                    (step_b_x == 0) and (step_b_y == 0) and
                    (step_c_x == 0) and (step_c_y == 0) and
                    (step_d_x == 0) and (step_d_y == 0)):
                logging.debug("Alles auf Null")
                terminate = True

            # c) Rechteck unverändert
            if ((a_xy == old_a_xy) and (c_xy == old_c_xy)):
                same_rec = same_rec + 1
                if same_rec == max_same_rec:
                    logging.debug("Rechteck unverändert in Runde:%i %s %s %s %s", i,
                                  a_xy, b_xy, c_xy, d_xy)
                    same_rec = 0
                    terminate = True

        return possible_rec

    def keep_biggest_rectangle(self, a_recs):
        """ ermittelt das größte Recheck in der Liste """
        a_xy = (0, 0)
        c_xy = (0, 0)
        rec_size = 0

        amount = len(a_recs)
        logging.debug("Anzahl Rechtecke in der aktuellen Runde: %i", amount)
        # Wenn nichts gefunden wurde muss auch nichts behalten werden
        if amount != 0:
            i = 0
            rec_size = 0
            # größten Wert ermitteln
            while i < amount:
                logging.debug("Runde, Size: %i %i", i, a_recs[i][4])
                if a_recs[i][4] > rec_size:
                    rec_size = a_recs[i][4]
                    a_xy = a_recs[i][0]
                    c_xy = a_recs[i][2]
                i = i + 1

        return a_xy, c_xy, rec_size

    def find_rectangle_with_color(self, bild_f, p_xy, p_color):
        """ sucht ein maximales Rechteck in bild_f mit den Startpunkt p_xy und der Farbe p_color """

        a_xy = (0, 0)
        c_xy = (0, 0)
        list_of_recs = []

        list_of_recs = self.find_rectangles(bild_f, p_xy, p_color)
        logging.debug("Gefundene Rechtecke: %i", len(list_of_recs))
        a_xy, c_xy, rec_size = self.keep_biggest_rectangle(list_of_recs)
        logging.debug("Größtes Rechteck: %s %s %i", a_xy, c_xy, rec_size)

        return a_xy, c_xy

    def get_medium_rgb_of_picture(self, m_bild_name):
        """ ermittelt die mittlere Frage eines Rechtecks a_xy/c_xy aus
            dem Bild m_bild_name  """

        m_rgb = (0, 0, 0)
        myimg = mpimg.imread(m_bild_name)
        avg_color_per_row = np.average(myimg, axis=0)
        avg_color = np.average(avg_color_per_row, axis=0)
        # Werte in int umwandeln
        m_rgb = self.rgb_float_2_rgb_int(avg_color)

        return m_rgb

    def get_medium_rgb_of_rectangle(self, m_bild_name, xOff, yOff, xEdge, yEdge):
        """ Ermittle den Mittwelwert für RGB eines definierten Ausschnittes """

        tmpImage = mpimg.imread(m_bild_name)

        #   Als erstes die Zeilen (y) auswählen
        tmp1 = tmpImage[yOff:yEdge, :, :]
        #   Dann die Spalten (x) aus y auswählen
        tmp2 = tmp1[:, xOff:xEdge, :]
        #        print("Größe des gesamten Ausschnittes:", tmp2.shape,"\n")

        anzahl_zeilen = tmp2.shape[0]
        #        print("Anzahl Zeilen:", anzahl_zeilen)

        anzahl_werte_pro_spalte = tmp2.shape[1]
        #        print("Anzahl Werte pro Spalte:", anzahl_werte_pro_spalte)

        rgb_r = tmp2[0:anzahl_zeilen, 0:anzahl_werte_pro_spalte, 0]
        rgb_g = tmp2[0:anzahl_zeilen, 0:anzahl_werte_pro_spalte, 1]
        rgb_b = tmp2[0:anzahl_zeilen, 0:anzahl_werte_pro_spalte, 2]

        mittelWertR = rgb_r.mean()
        mittelWertG = rgb_g.mean()
        mittelWertB = rgb_b.mean()

        m_rgb = self.rgb_float_2_rgb_int((mittelWertR, mittelWertG, mittelWertB))

        return m_rgb

    def fill_picture_with_rectangles(self, f_bild_name, m_bild_name, v_bild_name):
        # f_bild_name = Bild mit den farbigen Rechtecken = Zielbild
        # m_bild_name = Bild aus dem der Mittelwert RGB für ein Rechteck ermittelt wird
        # v_bild_name = Bild mit den Rahmen. Ohne Farbe.

        # f_bild Original öffnen und kopieren
        bild_com = Image.open(f_bild_name).convert('RGB')
        bild_com.save(self.get_filename("Final"))
        bild_com.close()

        # Kopien öffnen und bearbeiten
        bild_fin = Image.open(self.get_filename("Final"))
        logging.info("Loaded: %s %s", bild_fin.filename, bild_fin.size)
        bild_vor = Image.open(v_bild_name)

        # Vorgehen:
        # a) Einen zufälligen Punkt im Bild finden der "standard_farbe" eines leeren Bildes entspricht
        # b) Ausgehend von diesen Punkt ein maximales Rechteck suchen
        # c) Für dieses Rechteck im Original_Bild den mittleren Farbwert holen (könnte auch poppiger sein)
        # d) Das ermittelte Rechteck mit dem mittleren Farbwert einzeichnen
        # e) Das Rechteck nur als Rahmen in die Vorlage einzeichen
        # f) Das Ganze nur x-mal wiederholen
        # g) Nun systematisch über das Bild laufen und alle verbleibenden Flächen (b-d) füllen

        for i in range(0, self.MAX_RECS_TO_FILL):
            # a) Zufalls-Pixel der Standardfarbe ermitteln
            p_xy = self.get_random_pixel_with_color(bild_fin, self._standard_color)
            if p_xy == (0, 0):
                break  # Nichts mehr gefunden ==> hier absprung nach f)

            # b) Ein maximales Rechteck ermitteln
            a_xy, c_xy = self.find_rectangle_with_color(bild_fin, p_xy, self._standard_color)
            #            ImageDraw.Draw(bild_fin).rectangle([(a_xy), (c_xy)],outline="yellow")

            # c) Für dieses Rechteck im Original_Bild den mittleren Farbwert holen
            m_rgb = self.get_medium_rgb_of_rectangle(m_bild_name, a_xy[0], a_xy[1], c_xy[0], c_xy[1])
            logging.debug("Runde %i Mittelwert %s für Ausschnitt %s %s", i, m_rgb, a_xy, c_xy)

            # d) Das ermittelte Rechteck mit dem mittleren Farbwert einzeichnen
            #    Gefundenes Rechteck um einen Pixel ausdehnen, damit eine Überlappung entsteht.
            a_xy, c_xy = self.extend_frame(a_xy, c_xy, self._x_max_pic, self._y_max_pic)
            #            ImageDraw.Draw(bild_fin).rectangle([(a_xy), (c_xy)], fill=m_rgb, outline=m_rgb)      #GEEN
            ImageDraw.Draw(bild_fin).rectangle([(a_xy), (c_xy)], fill=m_rgb, outline="yellow")  # GEEN

            # e) Das Rechteck nur als Rahmen in die Vorlage einzeichen
            ImageDraw.Draw(bild_vor).rectangle([(a_xy), (c_xy)], outline="red")  # GEEN = black

        #       f) Nun systematisch über das Bild laufen und alle verbleibenden Flächen (b-d) füllen
        pic_fin = bild_fin.load()
        print("Anzahl Raster II: ", len(self.global_raster))
        for i in range(1, len(self.global_raster)):
            # Mittelpunkt des Raster
            mitte_xy = (self.global_raster[i][5], self.global_raster[i][6])
            # Prüfen ob dieser noch nicht "gefüllt" ist
            #            logging.info("Runde %i Mittelpunkt %s %s",i, mitte_xy[0],mitte_xy[1])

            # Hier überprüfen ob die Obergrenze überschritten wird!
            if mitte_xy[0] > self._x_max_pic: mitte_xy = (int(self._x_max_pic), int(mitte_xy[1]))
            if mitte_xy[1] > self._y_max_pic: mitte_xy = (int(mitte_xy[0]), int(self._y_max_pic))

            # in Integer umwandeln
            #            image_color = int(ImageColor.getrgb(self._standard_color))
            #            print("1:", mitte_xy)
            #            print("2:", mitte_xy[0],mitte_xy[1])
            #            print("3:", pic_fin[int(mitte_xy[0]),int(mitte_xy[1])])
            #            print("4:", ImageColor.getrgb(self._standard_color) )
            if pic_fin[mitte_xy[0], mitte_xy[1]] == ImageColor.getrgb(self._standard_color):
                # b) Ein maximales Rechteck ermitteln
                a_xy, c_xy = self.find_rectangle_with_color(bild_fin, mitte_xy, self._standard_color)
                #                ImageDraw.Draw(bild_fin).rectangle([(a_xy), (c_xy)],outline="yellow")

                # c) Für dieses Rechteck im Original_Bild den mittleren Farbwert holen
                m_rgb = self.get_medium_rgb_of_rectangle(m_bild_name, a_xy[0], a_xy[1], c_xy[0], c_xy[1])
                logging.debug("Runde %i Mittelwert %s für Ausschnitt %s %s", i, m_rgb, a_xy, c_xy)

                # d) Das ermittelte Rechteck mit dem mittleren Farbwert einzeichnen
                #                ImageDraw.Draw(bild_fin).rectangle([(a_xy), (c_xy)], fill=m_rgb, outline="yellow")
                ImageDraw.Draw(bild_fin).rectangle([(a_xy), (c_xy)], fill=m_rgb, outline=m_rgb)
                # e) Das Rechteck nur als Rahmen in die Vorlage einzeichen
                #    Gefundenes Rechteck um einen Pixel ausdehnen, damit eine Überlappung entsteht.
                a_xy, c_xy = self.extend_frame(a_xy, c_xy, self._x_max_pic, self._y_max_pic)
                ImageDraw.Draw(bild_vor).rectangle([(a_xy), (c_xy)], outline="green")  # GEEN = black

        return bild_fin, bild_vor

