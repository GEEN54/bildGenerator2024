# -*- coding: utf-8 -*-
"""
Created on Mon Jan  7 17:15:59 2019

@author: Geert
"""

# Klasse polygon
#
# Aus einer Umriss-Line die idealerweise nur 2-Pixel breit ist wird
# zuerst ein Polygon erzeugt und dann ein maximales Rechteck einpepasst

import logging
import numpy as np


# import matplotlib.image as mpimg
# from PIL import Image, ImageDraw, ImageColor

class Polygons:
    """ Klasse zur Ermittlung des maximalen Rechtecks innerhalb eines Polygon """

    # Richtungen
    #                   x ->
    #               y   0 1 2
    #               |   7 x 3
    #               v   6 5 4

    #                 0           1       2        3       4       5       6        7
    YX_DIRECTION = ((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))

    # Welche Richtungen werden abgesucht (links,rechts, umkehren)
    #                        0          1          2          3
    DIRECTION_PATTERN = ([7, 1, 4], [0, 2, 5], [1, 3, 6], [2, 4, 7],
                         [3, 5, 0], [4, 6, 1], [5, 7, 2], [6, 0, 3])
    #                        4          5          6          7

    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4

    RAM_PIX = 3  # Anzahl Zufallspunkte die betrachtet werden im
    # Verhältnis zur Gesamtzahl der Pixel der Linie in %
    MAX_ROUNDS_REC = 800  # Maximale Anzahl von Runden zum Finden eines Rechtecks
    MAX_WHILE = 1000  # Maximale Anzahl an Runden bei einer beliebigen While-Schleife

    def __init__(self, xmax, ymax, mrs, abw):
        """ Konstruktor """
        # Abmessungen des zu erzeugenden Bildes. Achtung wird bei read_original_file überschrieben

        self._x_max_pic = xmax - 1  # Größe des Bildes X
        self._y_max_pic = ymax - 1  # Größe des Bildes Y
        self._preference = 1  # Vorzug der Richtungsauswahl. <1> oder <-1>
        self.polygon_found = []  # Punkte der gefundenen Linie

        # automatischer Abbruch wenn zehnmal hintereinander ein doppelter Eintrag gefunden wurde
        # das bedeuten das entweder followLine sich in einer Sackgasse befindet oder aber
        # schon alles gefunden wurde
        self._max_double_entry = 10

        # Zähler für doppelte Einträge; ist in Verbindung mit maxDoubleEntry zu sehen
        self._counter_double = 0

        self._max_steps = 1500  # Absolute Obergrenze an Punkte für ein Polygon klein 400

        self._min_rec_size = mrs  # Minimale Größe eines Rechtecks

        self._reference_rgb = [-1, -1, -1]  # Referenz-Farbe für Line

        self.possible_rec = []  # gefundene Rechtecke innerhalb des Polygon
        self.dot_list = []  # Alle Punkte die zu der geschlossenen Linie gehören

        self.bild_rechteck = []
        self.bild_polygon = []
        self.np_bild = []

        self.filename = ""

        self.abw = abw

    def is_deviation_okay(self, rgb1, rgb2, abweichung):
        # Abweichung zweier RGB-Werte prüfen, True wenn sie kleiner <Abweichung> ist
        a = ([rgb1[0], rgb2[0]])
        abwR = np.std(a)
        if abwR > abweichung: return False

        b = ([rgb1[1], rgb2[1]])
        abwG = np.std(b)
        if abwG > abweichung: return False

        c = ([rgb1[2], rgb2[2]])
        abwB = np.std(c)
        if abwB > abweichung: return False

        return True

    def get_random_pixel(self, amount_pixel):
        """ generiert n-Pixel die innerhalb des Polygon liegen """

        # hier muss auch noch das Probelm gelöst werden, dass die Zufallspunkte innerhalb
        # des Polygons, auf die maximale Ausdehnung des Polygons beschränkt wird.

        # Maximale Ausdehnung der Grenzline ermitteln um nicht auf andere Polygone zu treffen
        temp = tuple(map(sorted, zip(*self.dot_list)))
        min_x, max_x, min_y, max_y = temp[0][0], temp[0][-1], temp[1][0], temp[1][-1]
        logging.debug("Maximale Ausdehnung Polygon: %i,%i - %i,%i", min_x, min_y, max_x, max_y)

        np_polygon = np.array(self.bild_polygon)
        arr_random_pixel = []
        anzahl = 0
        i = 0

        while anzahl < amount_pixel:
            i = i + 1

            # Würfeln
            random_x = np.random.randint(min_x, max_x, size=1)
            random_y = np.random.randint(min_y, max_y, size=1)

            # prüfen ob Pixel innerhalb des Polygon
            if np.array_equal(np_polygon[random_y, random_x], [[0, 0, 0]]):
                # innerhalb
                if (random_x, random_y) not in arr_random_pixel:
                    arr_random_pixel.append((random_x[0], random_y[0]))
                    anzahl = anzahl + 1

            if i > self.MAX_WHILE:
                logging.error("Anzahl von Pixel innerhalb des Polygon zu klein %i", len(arr_random_pixel))
                break

        logging.debug("Random Pixels: %s", arr_random_pixel)

        return arr_random_pixel

    def is_line_within_polygon(self, s_xy, e_xy):
        """ ermittelt ob eine Kante innerhalb des Polygon liegt """
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

        # Line "Zeichen"
        while p_x <= endx:
            p_y = starty
            while p_y <= endy:
                dot_rgb = self.np_polygon[p_y, p_x]
                if self.is_deviation_okay(dot_rgb, self._reference_rgb, self.abw):
                    # Der Punkt liegt innerhalb des Polygons
                    p_y = p_y + 1
                else:
                    innerhalb = False
                    break
            p_x = p_x + 1

        return innerhalb

    def is_line_within_polygon_2(self, s_xy, e_xy):
        """ ermittelt ob eine Kante innerhalb des Polygon liegt """

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

        #        print("Startwerte)
        #        values = self.np_polygon[startx:endx+1,starty:endy+1,:]

        # Jetzt die Mittelwerte für R, G und B ermitteln
        r_values = self.np_polygon[starty:endy + 1, startx:endx + 1, [0]]  # R
        r_mean = np.mean(r_values)
        g_values = self.np_polygon[starty:endy + 1, startx:endx + 1, [1]]  # G
        g_mean = np.mean(g_values)
        b_values = self.np_polygon[starty:endy + 1, startx:endx + 1, [2]]  # B
        b_mean = np.mean(b_values)

        #       Mittelwerte zu einen RGB-Punkt zusammen fassen
        dot_mean = np.array([r_mean, g_mean, b_mean])

        #       Wenn die Abweichung innerhalb der Toleranz, dann TRUE zurückgeben
        if self.is_deviation_okay(dot_mean, self._reference_rgb, self.abw):
            return True

        return False

    @staticmethod
    def get_rec_area(a_xy, c_xy):
        """ Fläche des Rechtecks bestimmen """

        p_a = a_xy[0] - c_xy[0]
        p_b = a_xy[1] - c_xy[1]

        area = abs(p_a * p_b)

        return area

    def is_pixel_within_polygon(self, p_xy):
        """ prüft ob ein Pixel noch im Polygon """
        if self.is_deviation_okay(self.np_polygon[p_xy[1], p_xy[0]], self._reference_rgb, self.abw):
            innerhalb = True
        else:
            innerhalb = False

        return innerhalb

    def set_next_edge(self, p_xy, step_px, step_py):
        """ prüft ob die Grenzen des Bildes erreicht sind """

        logging.debug("set_next_edge:%s %i %i %i %i", p_xy, step_px, step_py, self._x_max_pic, self._y_max_pic)
        if p_xy[0] + step_px <= self._x_max_pic and p_xy[0] + step_px >= 0:
            p_xy = (p_xy[0] + step_px, p_xy[1])
        else:
            step_px = 0

        if p_xy[1] + step_py <= self._y_max_pic and p_xy[1] + step_py >= 0:
            p_xy = (p_xy[0], p_xy[1] + step_py)
        else:
            step_py = 0

        return p_xy, step_px, step_py

    def keep_biggest_rectangle(self):
        """ ermittelt das größte Recheck in der Liste und löscht alle anderen Einträge """
        amount = len(self.possible_rec)
        logging.debug("Anzahl Rechtecke in der aktuellen Runde: %i", amount)
        # Wenn nichts gefunden wurde muss auch nichts behalten werden
        if amount == 0:
            return (0, 0), (0, 0), 0

        i = 0
        rec_size = 0
        pos = 0

        # größten Wert ermitteln
        while i < amount:
            logging.debug("Runde, Size: %i %i", i, self.possible_rec[i][4])
            if self.possible_rec[i][4] >= rec_size:
                rec_size = self.possible_rec[i][4]
                a_xy = self.possible_rec[i][0]
                c_xy = self.possible_rec[i][2]
                pos = i

            i = i + 1

        # größtes Rechteck merken, Liste löschen und Größtes eintragen
        big_rec = self.possible_rec[pos]
        del self.possible_rec[:]
        self.possible_rec.append(big_rec)

        return a_xy, c_xy, rec_size

    def find_max_rectangle(self, p_xy):
        """ ermittelt alle Rechtecke ausgehend von einen gegebenen Punkt """

        # Richtungen und Seiten
        #               A    oben   B
        #                   x ->
        #               y   0 1 2
        #       links   |   7 x 3  rechts
        #               v   6 5 4
        #               D    unten  C

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

        # Die Ecken so lange ausdehnen bis es zu einem Problem im Rechteck kommt

        #       Ecke A nach links oben ziehen
        a_xy = p_xy
        step_a_x = -1
        step_a_y = -1

        #       Ecke B nach rechts oben ziehen
        b_xy = p_xy
        step_b_x = 1
        step_b_y = -1

        #       Ecke C nach rechts unten ziehen
        c_xy = p_xy
        step_c_x = 1
        step_c_y = 1

        #       Ecke D nach links unten ziehen
        d_xy = p_xy
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
            answer_ab = self.is_line_within_polygon_2(a_xy, b_xy)  # GEEN
            logging.debug("A ,B, Innerhalb ?: %s %s %s", a_xy, b_xy, answer_ab)

            # prüfe ob Kante BC innerhalb des Polygon
            answer_bc = self.is_line_within_polygon_2(b_xy, c_xy)
            logging.debug("B ,C, Innerhalb ?: %s %s %s", b_xy, c_xy, answer_bc)

            # prüfe ob Kante CD innerhalb des Polygon
            answer_cd = self.is_line_within_polygon_2(c_xy, d_xy)
            logging.debug("C ,D, Innerhalb ?: %s %s %s", c_xy, d_xy, answer_cd)

            # prüfe ob Kante DA innerhalb des Polygon
            answer_da = self.is_line_within_polygon_2(d_xy, a_xy)
            logging.debug("D ,A, Innerhalb ?: %s %s %s", d_xy, a_xy, answer_da)

            # wenn alle Kanten innerhalb des Polygon, dann dieses Rechteck speichern
            # und vorher die Fläche berechnen

            if (answer_ab and answer_bc and answer_cd and answer_da):
                rec_area = self.get_rec_area(a_xy, c_xy)
                self.possible_rec.append((a_xy, b_xy, c_xy, d_xy, rec_area))
                same_rec = 0  # Zähler für gleiche Rechtecke zurücksetzen

            elif not answer_ab:
                # die Kante AB ist außerhalb des Polygon
                logging.debug("Kante AB hat ein Problem")
                logging.debug("A,B,C,D: %s %s %s %s", a_xy, b_xy, c_xy, d_xy)

                # erst einmal prüfen ob die Ecke das Problem ist
                a_in_pol = self.is_pixel_within_polygon(a_xy)
                b_in_pol = self.is_pixel_within_polygon(b_xy)

                # alte Werte zurückschreiben
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
                logging.debug("Kante BC hat ein Problem")
                logging.debug("A,B,C,D: %s %s %s %s", a_xy, b_xy, c_xy, d_xy)

                # erst einmal prüfen ob die Ecke das Problem ist
                b_in_pol = self.is_pixel_within_polygon(b_xy)
                c_in_pol = self.is_pixel_within_polygon(c_xy)
                # alte Werte zurückschreiben
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
                logging.debug("Kante CD hat ein Problem")
                logging.debug("A,B,C,D: %s %s %s %s", a_xy, b_xy, c_xy, d_xy)

                # erst einmal prüfen ob die Ecke das Problem ist
                c_in_pol = self.is_pixel_within_polygon(c_xy)
                d_in_pol = self.is_pixel_within_polygon(d_xy)
                # alte Werte zurückschreiben
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
                logging.debug("Kante DA hat ein Problem")
                logging.debug("A,B,C,D: %s %s %s %s", a_xy, b_xy, c_xy, d_xy)
                # erst einmal prüfen ob die Ecke das Problem ist
                d_in_pol = self.is_pixel_within_polygon(d_xy)
                a_in_pol = self.is_pixel_within_polygon(a_xy)
                # alte Werte zurückschreiben
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
            #            if((last_a_xy == old_a_xy) and (last_c_xy == old_c_xy)):
            if ((a_xy == old_a_xy) and (c_xy == old_c_xy)):
                same_rec = same_rec + 1
                if same_rec == max_same_rec:
                    logging.debug("Rechteck unverändert in Runde:%i %s %s %s %s", i,
                                  a_xy, b_xy, c_xy, d_xy)
                    same_rec = 0
                    terminate = True

    def get_rectangle(self, np_bild_polygon, s_xy):
        """ findet das größte Rechteck """

        self.np_polygon = np_bild_polygon
        self._reference_rgb = self.np_polygon[s_xy[1], s_xy[0]]
        logging.debug("Referenz RGB:%s for %s", self._reference_rgb, s_xy)

        a_xy = (0, 0)
        c_xy = (0, 0)

        # sucht für einen Punkt ALLE möglichen Rechtecke
        self.find_max_rectangle(s_xy)
        # jetzt das größte Rechteck aus der Liste der gefundenen ermitteln
        a_xy, c_xy, rec_size = self.keep_biggest_rectangle()
        logging.debug("Rechteck: %s %s Größe:%i", a_xy, c_xy, rec_size)

        # Prüfen ob das Rechteck nicht zu klein ist
        if rec_size < self._min_rec_size:
            logging.debug("Rechteck zu klein: %s %s Größe:%i", a_xy, c_xy, rec_size)
            a_xy = (0, 0)
            c_xy = (0, 0)

        logging.debug("Rechteck: %s %s Größe:%i", a_xy, c_xy, rec_size)

        return a_xy, c_xy