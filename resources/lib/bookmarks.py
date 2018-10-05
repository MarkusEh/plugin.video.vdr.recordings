# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import sqlite3
import xbmc
import os

class bookmarks:
    def __init__(self):
        dbFileMyVideos = xbmc.translatePath("special://database/MyVideos107.db")
        if os.path.isfile(dbFileMyVideos):
            self.dbKnown = True
        # Connect to database
            self.conn = sqlite3.connect(dbFileMyVideos)
            self.conn.text_factory = str
            self.cur = self.conn.cursor()
        else:
            self.dbKnown = False

    def getFileId(self, fileName):
        if self.dbKnown == False:
            return -2
        self.cur.execute('SELECT (idFile) FROM files WHERE strFilename=?', ([fileName]))
        resu = self.cur.fetchone()
        if resu == None:
            return -1  
        if len(resu) == 1:
            return resu[0]
        else:
            return -1

    def getBookmarksFromFileId(self, fileId):
        if self.dbKnown == False:
            return -2
        # type 1: Resume pos
        # type 0: Bookmark
#       self.cur.execute('SELECT idBookmark, timeInSeconds, type FROM bookmark WHERE idFile=?', ([fileId]))
        self.cur.execute('SELECT * FROM bookmark WHERE idFile=? AND type=0', ([fileId]))
        resu = self.cur.fetchall()
        return resu
    def insertBookmarks(self, fileId, bookmarksInSeconds, totalTimeInSeconds):
        if self.dbKnown == False:
            return -2
        for bTime in bookmarksInSeconds:
          self.cur.execute("INSERT INTO bookmark (idFile, timeInSeconds, totalTimeInSeconds, type) VALUES (?, ?, ?, ?)",
           (fileId, float(bTime), float(totalTimeInSeconds), 0))
        self.conn.commit()
    def deleteBookmarks(self):
        if self.dbKnown == False:
            return -2
        self.cur.execute("DELETE FROM bookmark WHERE type=0")
        self.conn.commit()

    def insertFile(self, fileName):
        if self.dbKnown == False:
            return -2
        self.cur.execute("INSERT INTO files (idPath, strFilename) VALUES (?, ?)", (1, fileName))
        self.conn.commit()



