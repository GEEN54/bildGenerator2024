# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 13:00:02 2019

@author: XEG09907363

Klasse zur Verwaltung der Rechteckdatenbank
"""

import os, sqlite3
from sqlite3 import Error
import logging


class RectangleDB:
    """
    Klasse zur Erzeugung einer ganzen Serie von Bildern
    """

    def __init__(self, db_name):
        """ Konstruktor """

        self.db_path = os.path.join(os.path.dirname(__file__), db_name)
        self.db_name = db_name
        self.db_table1 = "Rechtecke"  # Name der ersten Tabelle

        # Mit der Datenbank verbinden
        try:
            self.con = sqlite3.connect(self.db_path)
        except Error:
            logging.error("Probleme beim Öffnen der DB: %s %s", self.db_path, Error)

    def drop_rec_db_tables(self):
        """ Löscht alle Datenbanktabellen """

        sql = "DROP table if exists " + self.db_table1
        cursorObj = self.con.cursor()
        cursorObj.execute(sql)
        self.con.commit()

        logging.info("Datenbanktabelle %s dropped", self.db_table1)

    def create_rec_db_tables(self):
        """ Legt alle Datenbanktabellen an """

        # Mit der Datenbank verbinden
        self.con = sqlite3.connect(self.db_path)
        cursorObj = self.con.cursor()

        # Tabelle 1 anlegen
        sql = "CREATE TABLE " + self.db_table1 + "(id integer PRIMARY KEY, " \
                                                 "xmax integer, ymax integer, " \
                                                 "x1 integer, y1 integer, x2 integer, y2 integer, " \
                                                 "R integer, G integer, B integer)"

        try:
            cursorObj.execute(sql)
            self.con.commit()
        except:
            logging.error("Probleme beim Anlegen der Tabellen: %s %s", self.db_table1, Error)
            return False

        return True

    def insert_entry_rec_db(self, id, xmax, ymax, x1, y1, x2, y2, R, G, B):
        """ insert """

        cursorObj = self.con.cursor()

        try:
            entities = (id, int(xmax), int(ymax), int(x1), int(y1), int(x2), int(y2), int(R), int(G), int(B))
            cursorObj.execute("INSERT INTO " + self.db_table1 + " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", entities)
            self.con.commit()
        except:
            logging.error("Probleme beim Insert: %i %s", id, Error)

    def close(self):
        """ Datenbankverbindung schließen """
        self.con.close()

    def count_all(self):
        cursorObj = self.con.cursor()
        cursorObj.execute("SELECT count(*) FROM " + self.db_table1)
        result = cursorObj.fetchone()
        return result[0]
