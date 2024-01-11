# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import sys
import urllib
import urllib.parse
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
import folder
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

class VdrRecordingFolder(folder.cFolder):
  """All about one Vdr Recording"""

  def __init__(self, vdrRecordingFolder):
    super().__init__(vdrRecordingFolder)
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
#       xbmc.log("rectime_sort= " + rt, xbmc.LOGINFO)
        try:
          self.RecordingTime = datetime.datetime(year = int(rt[0:4]), month = int(rt[5:7]),
            day = int(rt[8:10]), hour = int(rt[11:13]), minute = int(rt[14:16]), second = 0)
#           xbmc.log("rectime= " + str(self.RecordingTime), xbmc.LOGINFO)
        except:
          xbmc.log("Error: Unknown format of rec folder name:" + rt, xbmc.LOGERROR)
          self.RecordingTime = datetime.datetime(year = 1960, month = 1,
            day = 1, hour = 0, minute = 0, second = 0)
        self.sortRecordingTimestamp = str(self.RecordingTime)
        if "info" in self.files:
          infoFileName = os.path.join(self.path, "info")
        elif "info.vdr" in self.files:
          infoFileName = os.path.join(self.path, "info.vdr")
        elif "info.txt" in self.files:
          infoFileName = os.path.join(self.path, "info.txt")
        else:
          infoFileName = ""
        info_str = ""
        if infoFileName != "":
          with xbmcvfs.File(infoFileName, "r") as f_info:
            try:
              info_str = f_info.read()
            except:
              xbmc.log("non-utf8 characters in file " + infoFileName, xbmc.LOGERROR)

        for info_line in info_str.splitlines():
            if info_line[0] == 'T':
              self.title = info_line[2:].strip()
            if info_line[0] == 'S':
              self.subtitle = info_line[2:].strip()
            if info_line[0] == 'D':
              self.description = info_line[2:].strip()
            if info_line[0] == 'F':
              this_line = info_line[2:].split(" ")
              self.framerate = float(this_line[0])

        if self.title == '':
          self.title = os.path.split(os.path.split(self.path)[0])[1].replace('_', ' ').strip()
          if self.title[:1] == "%": self.title = self.title[1:]
        if self.description == '' and "summary.vdr" in self.files:
          with xbmcvfs.File(os.path.join(self.path, "summary.vdr"), "r") as f_summary:
            try:
              self.description = f_summary.read().strip()
            except:
              xbmc.log("non-utf8 characters in file " + os.path.join(self.path, "summary.vdr"), xbmc.LOGERROR)

  def getListitem(self):
    self.initializeInfo()
# note: setting offscreen = True is a real performance booster here !!!
    li = xbmcgui.ListItem(self.title, offscreen = True)
    li.setInfo(type='video', infoLabels={
        'plot': "{}\n{}".format(self.sortRecordingTimestamp, self.description),
        'title': "{}\n{}".format(self.title, self.subtitle),
        'dateadded': self.sortRecordingTimestamp})
    li.setContentLookup(True)
    li.setProperty('IsPlayable', 'true')

    dict_art = {}
    if "poster.jpg" in self.files:
      poster_path = os.path.join(self.path, "poster.jpg")
      dict_art['poster'] = poster_path
      dict_art['thumb'] = poster_path
    if "fanart.jpg" in self.files:
      fanart_path = os.path.join(self.path, "fanart.jpg")
      dict_art['fanart'] = fanart_path

    li.setArt(dict_art)
    return li
# fanart: Hintergrund unter der Liste. Auch Bild im fanart Anzeigemodus
# clearlogo: Als Bild waehrend der Wiedergabe rechts oben, anstelle des Titels
# thumb (?): erscheint beim Anzeigen des Plots waehrend dem Abspielen links neben Plot
# thumb: last resort, wird z.B. auf Favoritenliste angezeigt

  def getTsFiles(self):
    if self.tsInitialized == False:
      self.tsInitialized = True
      self.ts_f = []
      for r_file in self.files:
        if r_file.endswith(".ts"):
          self.ts_f.append( os.path.join(self.path, r_file) )
        elif r_file.endswith(".vdr"):
          if len(os.path.split(r_file)[1]) == 7:
            self.ts_f.append( os.path.join(self.path, r_file) )
      self.ts_f.sort()
    return self.ts_f

  def getStackUrl(self):
    self.getTsFiles()
#   url = "stack://file:/" + url1 + " , file:/" + url2
    if self.ts_f == []: return ""
    if len(self.ts_f) == 1: return "stack://{}".format(self.ts_f[0])
    return "stack://{}".format(" , ".join(self.ts_f))

  def addDirectoryItem(self, addon_handle, commands, totalItems):
    li = self.getListitem()
    url = self.getStackUrl()
    self.updateComskip()
    li.addContextMenuItems( commands )
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=False, totalItems = totalItems)
  def play(self):
    url = self.getStackUrl()
    li = xbmcgui.ListItem()
    li.setProperty('IsPlayable', 'true')
    li.setPath(url)
    xbmcplugin.setResolvedUrl(int(sys.argv[ 1 ]),True,li)
#    rt = li.getProperty('ResumeTime')
#    xbmc.log("play, resume position " + str(rt) + " url " + str(url), xbmc.LOGINFO)
# note: resume position is alway 0.0000
# see https://forum.kodi.tv/showthread.php?tid=358049
# if resume:
#    item.setProperty('totaltime', '1')
#else:
#    item.setProperty('StartPercent', '0')
#
#    xbmc.Player().play(url, li) : only works if there is no resume position

  def getMarks(self):
# read marks
    if self.marksInitialized: return
    self.marksInitialized = True
    self.marks = []
    if "marks" in self.files:
      marksFile = os.path.join(self.path, "marks")
    elif "marks.vdr" in self.files:
      marksFile = os.path.join(self.path, "marks.vdr")
    else:
      return
    with xbmcvfs.File(marksFile, "r") as f_marks:
        try:
          marks_content = f_marks.read()
        except:
          xbmc.log("non-utf8 characters in file " + marksFile, xbmc.LOGERROR)
          marks_content = ""
#       xbmc.log("marks_content: " + str(marks_content), xbmc.LOGINFO)
        for marks_line in marks_content.splitlines():
          if marks_line[1] == ':':
            m_time_sec = ((float(marks_line[0]) * 60) + float(marks_line[2:4]) ) * 60 + float(marks_line[5:10])
#           xbmc.log("m_time_sec: " + str(m_time_sec), xbmc.LOGINFO)
            self.marks.append(m_time_sec)

  def sanitizeMarks(self):
    self.marksS = []
    self.getMarks()   
    lastMarkComStart = 0
    lastMarkMovieCont = -1
#   xbmc.log("sanitizeMarks, path: " + str(self.path), xbmc.LOGINFO)        

    for mark in self.marks:
#     if mark < 5: continue
      if lastMarkMovieCont == -1:
        comLen = mark - lastMarkComStart
#       xbmc.log("sanitizeMarks, comLen: " + str(comLen), xbmc.LOGINFO)        
        if comLen > 15*60:
          if lastMarkComStart == 0:
            lastMarkComStart = mark
          else:
            break   # commercials are shorter than 15 minutes
        else:
          self.marksS.append([lastMarkComStart, mark])
          lastMarkMovieCont = mark
      else:
        movLen =  mark - lastMarkMovieCont
#       xbmc.log("sanitizeMarks, movLen: " + str(movLen), xbmc.LOGINFO)        
        if movLen < 5*60: continue
        lastMarkComStart = mark
        lastMarkMovieCont = -1

  def updateComskip(self):
    if "00001.edl" in self.files: return
    if "001.edl" in self.files: return
    self.getTsFiles()
    if self.ts_f == []: return
    self.getMarks()
    if len(self.marks) == 0:
      return
    xbmc.log("Creating commercials file, marks not empty " + self.path, xbmc.LOGINFO)
    self.sanitizeMarks()
    if self.marksS == []:
# create empty *.edl file, to avoid to check here again
      ts_file = self.ts_f[0]
      with xbmcvfs.File((os.path.splitext(ts_file)[0] + ".edl"), "w") as f_com:
        try:
          f_com.write('\n')
        except:
          xbmc.log("Error creating empty commercials file " + os.path.splitext(ts_file)[0] + ".edl", xbmc.LOGERROR)
      return
#   for mark in self.marksS:      
#       xbmc.log("updateComskip, mark: " + str(mark[0]) + " " + str(mark[1]), xbmc.LOGINFO)        

    if len(self.ts_f) >  1:
      self.initializeIndex()
      if len(self.ts_f) != len(self.ts_l):
        xbmc.log("ERROR updateComskip, len(self.ts_f) = " + str(len(self.ts_f)) + " len(self.ts_l) " + str(len(self.ts_l)) + " path = " + self.path, xbmc.LOGERROR)
        return

    lengthOfPreviousFiles = 0
    iIndex = 0
    for ts_file in self.ts_f:
      if len(self.ts_f) >  1: length = self.ts_l[iIndex] / self.framerate - lengthOfPreviousFiles
      else:                   length = 10*60
      if length > 2*60:
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
      else:
        with xbmcvfs.File((os.path.splitext(ts_file)[0] + ".edl"), "w") as f_com:
          try:
            f_com.write('\n')
          except:
            xbmc.log("Error creating commercials file " + os.path.splitext(ts_file)[0] + ".edl", xbmc.LOGERROR)
      if len(self.ts_f) >  1:
        lengthOfPreviousFiles = self.ts_l[iIndex] / self.framerate
        iIndex = iIndex +1
    xbmc.log("End creating commercials file " + self.path, xbmc.LOGINFO)

  def addRecordingToLibrary(self, libraryPath, filename, current_files, isMovie, nfoUrl):
      if len(self.getTsFiles() ) == 0: return
      self.updateComskip()
      xbmcvfs.mkdirs(libraryPath)
# can we use symlinks? (Otherwisae, edl / comskip does not work)
      use_symlinks = sys.platform.startswith('linux') and self.getTsFiles()[0].startswith('/')
      use_symlinks = use_symlinks and (isMovie or len(self.getTsFiles() ) == 1)
# extension of the new file / new symbolic link (.ts or .vdr or .strm)
      ext = os.path.splitext(self.getTsFiles()[0])[1]
      if not use_symlinks: ext = ".strm"
# basename of the new file / new symbolic link
      sanTitle = re.sub(r'[/\\?%*:|"<>]', '-', filename)
      base_name = os.path.join(libraryPath, sanTitle)
# create a unique basename, in case of duplicates
      i = 1
      strmFileName  = base_name + ext
      strmFileNameA = base_name + " part1" + ext
      while strmFileName in current_files or strmFileNameA in current_files:
        i = i + 1
        strmFileName  = base_name + str(i) + ext
        strmFileNameA = base_name + str(i) + " part1" + ext
      if i > 1: base_name = base_name + str(i)
# create nfo file
      if nfoUrl != "":
        if isMovie: nfoFileName = base_name + ".nfo"
        else: nfoFileName = os.path.join(libraryPath, "tvshow.nfo")
        xbmcvfs.delete(nfoFileName)
        current_files[nfoFileName] = True
        with xbmcvfs.File(nfoFileName, "w") as f_nfo:
          try:
            f_nfo.write(nfoUrl)
          except:
            xbmc.log("Cannot open for write: " + str(nfoFileName), xbmc.LOGERROR)        
      if use_symlinks:
# create the symlinks
        stack_number = ""
        i = 1
        for tsFile in self.getTsFiles():
          if len(self.getTsFiles() ) > 1: stack_number = " part" + str(i)
          i = i + 1
          strmFileName = base_name + stack_number + ext
          edlFileName  = base_name + stack_number + ".edl"
          xbmcvfs.delete(strmFileName)
          xbmcvfs.delete( edlFileName)
          try:
            os.symlink(tsFile, strmFileName)
            os.symlink(os.path.splitext(tsFile)[0] + ".edl", edlFileName)
          except:
            xbmc.log("Cannot create symlink: " + str(strmFileName), xbmc.LOGERROR)        
            return -1
          try:
            os.utime(strmFileName, times=(datetime.datetime.now().timestamp(), self.RecordingTime.timestamp() ))
          except:
            xbmc.log("Cannot update time of symlink: " + str(strmFileName), xbmc.LOGERROR)        
          current_files[strmFileName] = True
      else:
# symlinks are not supported, use strm file
        strmFileName = base_name + ".strm"
        xbmcvfs.delete(strmFileName)
        with xbmcvfs.File(strmFileName, "w") as f_strm:
          try:
            plu = constants.BASE_URL + '?' + urllib.parse.urlencode({'mode': 'play', 'recordingFolder': self.path})
            f_strm.write(plu)
## use the plugin to play files with multiple *.ts files. Putting all these ts files in an strm file is broken for too many ts files
#           f_strm.write(self.getStackUrl())
          except:
            xbmc.log("Cannot open for write: " + str(strmFileName), xbmc.LOGERROR)        
            return -1
        try:
          os.utime(strmFileName, times=(datetime.datetime.now().timestamp(), self.RecordingTime.timestamp() ))
        except:
          xbmc.log("Cannot update time of strm file: " + str(strmFileName), xbmc.LOGERROR)        
        current_files[strmFileName] = True

  def getYearR(self):
    year = self.getYear()
    if year > 0: return year
    self.initializeInfo()
    year = getYear(self.subtitle[1:])
    if year > 0: return year
    yp = self.description.find("Jahr")
    if yp >= 0:
      year = getYear(self.description[yp+4:yp+15])
      if year > 0: return year
    yp = self.description.find("Year")
    if yp >= 0:
      year = getYear(self.description[yp+4:yp+15])
      if year > 0: return year
    year = getYear(self.description[1:])
    return year

  def initializeIndex(self):
    if self.indexInitialized == False:
      self.indexInitialized = True
      if "index" in self.files:
        newIndexFormat = True
        indexFileName = os.path.join(self.path, "index")
      elif "index.vdr" in self.files:
        newIndexFormat = False
        indexFileName = os.path.join(self.path, "index.vdr")
      else:
        xbmc.log("No index or index.vdr file is in " + str(self.path), xbmc.LOGERROR)
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
#       xbmc.log("index file size= " + str(index_len), xbmc.LOGINFO)
        index = array( 'B', f_index.readBytes() )
        f_index.close
        numbersPerEntry = 8
        if newIndexFormat:
          offsetRight = 2
        else:
          offsetRight = 3
#       index_len = len(index)
#       xbmc.log("index_len= " + str(index_len), xbmc.LOGINFO)
        number_of_entries = index_len / numbersPerEntry
#       xbmc.log("number_of_entries= " + str(number_of_entries), xbmc.LOGINFO)
        self.frameNumbers = number_of_entries
        len_sec = number_of_entries / self.framerate
        self.len_sec = len_sec
        numberOfTsFiles = index[index_len - offsetRight]
#       xbmc.log("numberOfTsFiles= " + str(numberOfTsFiles), xbmc.LOGINFO)
# find length (sec) for each ts file
        self.ts_l = []
        for i in range(1, numberOfTsFiles):
          limit_low = 1
          limit_high = number_of_entries
          testPos =  int(number_of_entries * i/ numberOfTsFiles)
          found = False
          while found == False:
#           xbmc.log("testPos= " + str(testPos), xbmc.LOGINFO)
#           xbmc.log("numbersPerEntry= " + str(numbersPerEntry), xbmc.LOGINFO)
#           xbmc.log("offsetRight= " + str(offsetRight), xbmc.LOGINFO)
            
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

