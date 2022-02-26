# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import sys
import string
import re
import xbmcgui
import xbmc
import xbmcvfs
from array import array
import time
import datetime
import xbmcplugin
import json
import kfolder
import constants

def countDigits(dStr):
  for i, c in enumerate(dStr):
    if not c.isdigit():
      return i
  return len(dStr)

def getYear(yStr):
    i = 0
    while i < (len(yStr)-3):
        t = str(yStr[i])
        if t.isdigit():
            dcount = countDigits(yStr[i:])
            if (dcount == 4) and (int(yStr[i:i+4]) > 1860) and (int(yStr[i:i+4]) < 2025):
                return int(yStr[i:i+4])
            else:
                i += dcount
        else:
          i += 1
    return -1

class VdrRecordingFolder:
  """All about one Vdr Recording"""

  def __init__(self, vdrRecordingFolder):
    self.path = vdrRecordingFolder
    self.infoInitialized = False
    self.tsInitialized = False 
    self.marksInitialized = False
    self.indexInitialized = False
    self.initializeInfo()

  def initializeInfo(self):
    if self.infoInitialized == False:
        self.infoInitialized = True
        self.title = ''
        self.subtitle = ''
        self.description = ''
        self.framerate = 25
# Recording date / time
        rt = os.path.split(self.path)[1]
#       xbmc.log("rectime_sort= " + rt, xbmc.LOGERROR)
        try:
          self.RecordingTime = datetime.datetime(year = int(rt[0:4]), month = int(rt[5:7]),
            day = int(rt[8:10]), hour = int(rt[11:13]), minute = int(rt[14:16]), second = 0)
#           xbmc.log("rectime= " + str(self.RecordingTime), xbmc.LOGERROR)
        except:
          xbmc.log("Error: Unknown format of rec folder name:" + rt, xbmc.LOGERROR)
          self.RecordingTime = datetime.datetime(year = 1960, month = 1,
            day = 1, hour = 0, minute = 0, second = 0)
        self.sortRecordingTimestamp = str(self.RecordingTime)
        infoFileName = os.path.join(self.path, "info")
        if not xbmcvfs.exists(infoFileName):
          infoFileName = os.path.join(self.path, "info.vdr")
        if not xbmcvfs.exists(infoFileName):
          infoFileName = os.path.join(self.path, "info.txt")
        with xbmcvfs.File(infoFileName, "r") as f_info:
          try:
            info_str = f_info.read()
          except:
            xbmc.log("non-utf8 characters in file " + infoFileName, xbmc.LOGERROR)
            info_str = ""

        for info_line in info_str.splitlines():
            if info_line[0] == 'T':
              self.title = info_line[2:].strip()
            if info_line[0] == 'S':
              self.subtitle = info_line[2:].strip()
            if info_line[0] == 'D':
              self.description = info_line[2:].strip()
            if info_line[0] == 'F':                 
              self.framerate = float(info_line[2:])

        if self.title == '':
          self.title = os.path.split(os.path.split(self.path)[0])[1].replace('_', ' ').strip()
        if self.description == '':
          with xbmcvfs.File(os.path.join(self.path, "summary.vdr"), "r") as f_summary:
            try:
              self.description = f_summary.read().strip()
            except:
              xbmc.log("non-utf8 characters in file " + os.path.join(self.path, "summary.vdr"), xbmc.LOGERROR)

  def getListitem(self):
    self.initializeInfo()
    li = xbmcgui.ListItem(self.title)
    li.setInfo(type='video', infoLabels={'plot': self.sortRecordingTimestamp + '\n' + self.description,
        'title':self.title + '\n' + self.subtitle,
        'dateadded': self.sortRecordingTimestamp})
    li.setContentLookup(True)
    li.setProperty('IsPlayable', 'true')

    dict_art = {}
    poster_path = os.path.join(self.path, "poster.jpg")
    if xbmcvfs.exists(poster_path):
      dict_art['poster'] = poster_path
      dict_art['thumb'] = poster_path
    fanart_path = os.path.join(self.path, "fanart.jpg")
    if xbmcvfs.exists(fanart_path):
      dict_art['fanart'] = fanart_path

    li.setArt(dict_art)
# fanart: Hintergrund unter der Liste. Auch Bild im fanart Anzeigemodus
# clearlogo: Als Bild waehrend der Wiedergabe rechts oben, anstelle des Titels
# thumb (?): erscheint beim Anzeigen des Plots waehrend dem Abspielen links neben Plot
# thumb: last resort, wird z.B. auf Favoritenliste angezeigt
    return li

  def getTsFiles(self):
    if self.tsInitialized == False:
      self.tsInitialized = True
      self.ts_f = []
      dirs, files = xbmcvfs.listdir(self.path)
      for r_file in files:
        ext = os.path.splitext(r_file)[1]
        if ext == ".ts":
          self.ts_f.append( os.path.join(self.path, r_file) )
        if ext == ".vdr":
          if len(os.path.split(r_file)[1]) == 7:
            self.ts_f.append( os.path.join(self.path, r_file) )
      self.ts_f.sort()
    return self.ts_f

  def getStackUrl(self):
    self.getTsFiles()
#   url = "stack://file:/" + url1 + " , file:/" + url2
    isFirst = True
    url = ""
    for r_file in self.ts_f:
      if isFirst:
        url = "stack://" + r_file
        isFirst = False
      else:
        url = url + " , " + r_file
    return url

  def addDirectoryItem(self, addon_handle, commands, totalItems):
    li = self.getListitem()
    url = self.getStackUrl()
    self.updateComskip()
    li.addContextMenuItems( commands )
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=False, totalItems = totalItems)

  def getMarks(self):
# read marks
    if self.marksInitialized: return
    self.marksInitialized = True
    self.marks = []
    marksFile = os.path.join(self.path, "marks")
    if not xbmcvfs.exists(marksFile):
      marksFile = os.path.join(self.path, "marks.vdr")
    with xbmcvfs.File(marksFile, "r") as f_marks:
        try:
          marks_content = f_marks.read()
        except:
          xbmc.log("non-utf8 characters in file " + marksFile, xbmc.LOGERROR)
          marks_content = ""
#       xbmc.log("marks_content: " + str(marks_content), xbmc.LOGERROR)
        for marks_line in marks_content.splitlines():
          if marks_line[1] == ':':
            m_time_sec = ((float(marks_line[0]) * 60) + float(marks_line[2:4]) ) * 60 + float(marks_line[5:10])
#           xbmc.log("m_time_sec: " + str(m_time_sec), xbmc.LOGERROR)
            self.marks.append(m_time_sec)

  def sanitizeMarks(self):
    self.marksS = []
    self.getMarks()   
    lastMarkComStart = 0
    lastMarkMovieCont = -1
#   xbmc.log("sanitizeMarks, path: " + str(self.path), xbmc.LOGERROR)        

    for mark in self.marks:
      if mark < 5: continue
      if lastMarkMovieCont == -1:
        comLen = mark - lastMarkComStart
#       xbmc.log("sanitizeMarks, comLen: " + str(comLen), xbmc.LOGERROR)        
        if comLen > 15*60:
          if lastMarkComStart == 0:
            lastMarkComStart = mark
          else:
            break   # commercials are shorter than 10 minutes
        else:
          self.marksS.append([lastMarkComStart, mark])
          lastMarkMovieCont = mark
      else:
        movLen =  mark - lastMarkMovieCont
#       xbmc.log("sanitizeMarks, movLen: " + str(movLen), xbmc.LOGERROR)        
        if movLen < 5*60: continue
        lastMarkComStart = mark
        lastMarkMovieCont = -1

  def updateComskip(self):
    if xbmcvfs.exists(os.path.join(self.path, "00001.edl") ): return
    if xbmcvfs.exists(os.path.join(self.path, "001.edl") ): return
#   xbmc.log("Start creating commercials file" + self.path, xbmc.LOGERROR)
    self.getMarks()
    self.sanitizeMarks()
    if self.marksS == []: return
#   for mark in self.marksS:      
#       xbmc.log("updateComskip, mark: " + str(mark[0]) + " " + str(mark[1]), xbmc.LOGERROR)        

    self.initializeIndex()
    if self.ts_l == []: return
    self.getTsFiles()

    if len(self.ts_f) != len(self.ts_l):
      xbmc.log("ERROR updateComskip, len(self.ts_f) = " + str(len(self.ts_f)) + " len(self.ts_l) " + str(len(self.ts_l)) + " path = " + self.path, xbmc.LOGERROR)
      return


    lengthOfPreviousFiles = 0
    iIndex = 0
    for ts_file in self.ts_f:
      with xbmcvfs.File((os.path.splitext(ts_file)[0] + ".edl"), "w") as f_com:
        for mark in self.marksS:
            mark0 = mark[0] - lengthOfPreviousFiles
            mark1 = mark[1] - lengthOfPreviousFiles
            if mark1 <= 0.1: continue
            if mark0 < 0.1: mark0 = 0.1
            try:
              f_com.write(str(mark0).ljust(7)
                 + "     "
                 + str(mark1).ljust(7) + "     3" 
                 + '\n')
            except:
              xbmc.log("Error creating commercials file " + os.path.splitext(ts_file)[0] + ".edl", xbmc.LOGERROR)
      lengthOfPreviousFiles = self.ts_l[iIndex] / self.framerate
      iIndex = iIndex +1

  def addRecordingToLibrary(self, libraryPath, filename, current_files):
      if len(self.getTsFiles() ) == 0: return
      self.updateComskip()
      if not xbmcvfs.exists(libraryPath): xbmcvfs.mkdirs(libraryPath)
      sanTitle = re.sub(r'[/\\?%*:|"<>]', '-', filename)
      base_name = os.path.join(libraryPath, sanTitle)
      i = 1
      if sys.platform.startswith('linux') and len(self.getTsFiles() ) == 1 and self.getTsFiles()[0].startswith('/'):
        basename, ext = os.path.splitext(self.getTsFiles()[0])
        strmFileName = base_name + ext
        edlFileName  = base_name + ".edl"
        while strmFileName in current_files:
          i = i + 1
          strmFileName = base_name + str(i) + ext
          edlFileName  = base_name + str(i) + ".edl"
        xbmcvfs.delete(strmFileName)
        xbmcvfs.delete( edlFileName)
        os.symlink(self.getTsFiles()[0], strmFileName)
        os.symlink(basename + ".edl", edlFileName)
      else:
        strmFileName = base_name + ".strm"
        while strmFileName in current_files:
          i = i + 1
          strmFileName = base_name + str(i) + ".strm"
        xbmcvfs.delete(strmFileName)
        with xbmcvfs.File(strmFileName, "w") as f_strm:
          try:
            f_strm.write(self.getStackUrl())
          except:
            xbmc.log("Cannot open for write: " + str(strmFileName), xbmc.LOGERROR)        
            return -1
      current_files[strmFileName] = True


  def getYear(self):
    year = kfolder.kFolder(self.path).getYear()
    if year <= 0: 
      year = getYear(self.subtitle[1:])
    if year <= 0: 
      yp = self.description.find("Jahr")
      if yp >= 0:
        year = getYear(self.description[yp+4:yp+15])
    if year <= 0: 
      yp = self.description.find("Year")
      if yp >= 0:
        year = getYear(self.description[yp+4:yp+15])
    if year <= 0: 
      year = getYear(self.description[1:])
    return year

  def initializeIndex(self):
    if self.indexInitialized == False:
      self.indexInitialized = True
      newIndexFormat = True
      indexFileName = os.path.join(self.path, "index")
      if not xbmcvfs.exists(indexFileName):
        newIndexFormat = False
        indexFileName = os.path.join(self.path, "index.vdr")
      if not xbmcvfs.exists(indexFileName):
        xbmc.log("Cannot open index file " + str(indexFileName), xbmc.LOGERROR)
        self.ts_l = []
        return
      try:
        f_index =  xbmcvfs.File(indexFileName, "rb")
      except:
# doesn't exist
        xbmc.log("Cannot open index file " + str(indexFileName), xbmc.LOGERROR)
        self.ts_l = []
      else:
        index_len = f_index.size()
#       xbmc.log("index file size= " + str(index_len), xbmc.LOGERROR)
        index = array( 'B', f_index.readBytes() )
        f_index.close
        numbersPerEntry = 8
        if newIndexFormat:
          offsetRight = 2
        else:
          offsetRight = 3
#       index_len = len(index)
#       xbmc.log("index_len= " + str(index_len), xbmc.LOGERROR)
        number_of_entries = index_len / numbersPerEntry
#       xbmc.log("number_of_entries= " + str(number_of_entries), xbmc.LOGERROR)
        self.frameNumbers = number_of_entries
        len_sec = number_of_entries / self.framerate
        self.len_sec = len_sec
        numberOfTsFiles = index[index_len - offsetRight]
#       xbmc.log("numberOfTsFiles= " + str(numberOfTsFiles), xbmc.LOGERROR)
# find length (sec) for each ts file
        self.ts_l = []
        for i in range(1, numberOfTsFiles):
          limit_low = 1
          limit_high = number_of_entries
          testPos =  int(number_of_entries * i/ numberOfTsFiles)
          found = False
          while found == False:
#           xbmc.log("testPos= " + str(testPos), xbmc.LOGERROR)
#           xbmc.log("numbersPerEntry= " + str(numbersPerEntry), xbmc.LOGERROR)
#           xbmc.log("offsetRight= " + str(offsetRight), xbmc.LOGERROR)
            
            ts_file_at_test_pos = index[testPos * numbersPerEntry - offsetRight]
            if ts_file_at_test_pos > i:
              limit_high = testPos
              testPos = int(limit_low + (testPos - limit_low) / 2)
            else:
              ts_file_at_test_pos_p1 = index[(testPos + 1)* numbersPerEntry - offsetRight]
              if ts_file_at_test_pos_p1 <= i:
                limit_low = testPos
                testPos = int(limit_high - (limit_high - testPos) / 2)
              else:
                found = True
                self.ts_l.append(testPos)

        self.ts_l.append(number_of_entries)

