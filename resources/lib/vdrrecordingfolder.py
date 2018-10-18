# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import string
import re
import xbmcgui
import xbmc
from array import array
import time
import datetime
from bookmarks import bookmarks
import xbmcplugin
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
            if (dcount == 4) and (int(yStr[i:i+4]) > 1860) and (int(yStr[i:i+4]) < 2100):
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
    self.resumeInitialized = False
    self.marksInitialized = False
    self.indexInitialized = False
    self.newResumeFormat = True
    self.initializeInfo()
    self.oBookmarks = bookmarks()
    self.contentType = None

  def initializeInfo(self):
    if self.infoInitialized == False:
        self.infoInitialized = True
        self.title = ''
        self.subtitle = ''
        self.description = ''
        self.framerate = 25
        self.streamInfo = []
# Recording date / time
        rt = os.path.split(self.path)[1]
#       xbmc.log("rectime_sort= " + rt, xbmc.LOGERROR)
        self.RecordingTime = datetime.datetime(year = int(rt[0:4]), month = int(rt[5:7]),
          day = int(rt[8:10]), hour = int(rt[11:13]), minute = int(rt[14:16]), second = 0)
#         xbmc.log("rectime= " + str(self.RecordingTime), xbmc.LOGERROR)
        self.sortRecordingTimestamp = str(self.RecordingTime)
        infoFileName = os.path.join(self.path, "info")
        if not os.path.isfile(infoFileName):
          infoFileName = os.path.join(self.path, "info.vdr")
        try:
          f_info = open(infoFileName, "r")
        except IOError:
# doesn't exist
          pass
        else:
# exists
          info = f_info.readlines()
          f_info.close()
          for info_line in info:
            if info_line[0] == 'T':
              self.title = info_line[2:]
            if info_line[0] == 'S':
              self.subtitle = info_line[2:]
            if info_line[0] == 'D':
              self.description = info_line[2:]
            if info_line[0] == 'F':                 
              self.framerate = int(info_line[2:])
            if info_line[0] == 'X':
              if info_line[2]  == '1':
                self.streamInfo.append(['video', {'codec': 'MPEG-2', 'width': 720, 'height': 576  }])
              if info_line[2]  == '5':
                self.streamInfo.append(['video', {'codec': 'h264', 'width': 1280, 'height': 720  }])
              if info_line[2]  == '2':
                if info_line[4:6]  == '05':
                  channels = 6
                else:
                  channels = 2
                self.streamInfo.append(['audio',
                 {'codec': 'mpeg-2', 'language': info_line[7:10], 'channels': channels }])
              if info_line[2]  == '4':
                self.streamInfo.append(['audio',
                  {'codec': 'AC3', 'language': info_line[7:10], 'channels': 5 }])
              if info_line[2]  == '6':
                self.streamInfo.append(['audio',
                  {'codec': 'HE-AAC', 'language': info_line[7:10], 'channels': 5 }])
              if info_line[2]  == '3':
                self.streamInfo.append(['subtitle', {'language': info_line[7:10] }])

        if self.title == '':
          self.title = os.path.split(os.path.split(self.path)[0])[1].replace('_', ' ')
        if self.description == '':
          try:
            f_summary = open(os.path.join(self.path, "summary.vdr"), "r")
          except IOError:
# doesn't exist
            pass
          else:
            self.description = f_summary.read()
            f_summary.close()
# exists

  def getListitem(self):
    self.initializeInfo()
    li = xbmcgui.ListItem(self.title + self.subtitle)
    if self.getResume() > 20:
      playCount = 1
    else:
      playCount = 0 
    li.setInfo(type='video', infoLabels={'plot': self.sortRecordingTimestamp + '\n' + self.description,
        'title':self.title + self.subtitle, 'sorttitle':self.sortRecordingTimestamp,
        'dateadded': self.sortRecordingTimestamp, 'playcount': playCount})
    li.setContentLookup(True)
    li.setProperty('IsPlayable', 'true')
    try:
      index_file_length = os.path.getsize(os.path.join(self.path, "index"))
    except OSError:
      index_file_length = os.path.getsize(os.path.join(self.path, "index.vdr"))
    self.duration = int(index_file_length / 8 / self.framerate)
    numVidStreams = 0
    for streamInfoLine in self.streamInfo:
      if(streamInfoLine[0] == "video"):
        numVidStreams = numVidStreams  + 1
        streamInfoLine[1]['duration'] = self.duration
        li.addStreamInfo(streamInfoLine[0], streamInfoLine[1])
    if numVidStreams == 0:
      li.addStreamInfo('video', {'duration': self.duration})
    for streamInfoLine in self.streamInfo:
      if(streamInfoLine[0] != "video"):
        li.addStreamInfo(streamInfoLine[0], streamInfoLine[1])

#    kf = kfolder.kFolder(self.path)
#    img = kf.getStrmFileName()
#    if img != None:
#       thumb = xbmc.getCacheThumbName(img)
#       xbmc.log("thumb= " + str(thumb), xbmc.LOGERROR)      
#       li.setArt({ 'thumb': thumb, 'poster': thumb })

#   li.addStreamInfo('video',
#     { 'codec': 'mpeg-2', 'aspect': 1.78, 'width': 1280, 'height': 720,
#          'duration': int(index_file_length / 200) })
# mpeg-2  , h264

# fanart: Hintergrund unter der Liste. Auch Bild im fanart Anzeigemodus
# clearlogo: Als Bild waehrend der Wiedergabe rechts oben, anstelle des Titels
# thumb (?): Zwingend, erscheint beim Anzeigen des Plots waehrend dem Abspielen links neben Plot
#   li.setArt({ 'thumb': 'DefaultFile.png' })
#   li.setArt({ 'thumb': image, 'poster': image})
#    li.setArt({ 'thumb': 'DefaultFile.png', 'poster': 'DefaultFile.png',
#       'banner' : 'DefaultFile.png', 'fanart': 'DefaultFile.png',
#       'clearart': 'DefaultFile.png', 'clearlogo': 'DefaultFile.png',
#       'landscape': 'DefaultFile.png', 'icon': 'DefaultFile.png' })
    return li

  def getTsFiles(self):
    if self.tsInitialized == False:
      self.tsInitialized = True
      self.ts_f = []
      for r_file in os.listdir(self.path):
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
    for r_file in self.ts_f:
      if isFirst:
        url = "stack://" + r_file
        isFirst = False
      else:
        url = url + " , " + r_file
    return url

  def getResume(self):
    self.initializeResume()
    return (self.resume)

  def initializeResume(self):
    if self.resumeInitialized:
      return
    self.resumeInitialized = True
    self.resume = 0
    self.newResumeFormat = True
    fileMode = "r"
    resumeFileName = os.path.join(self.path, "resume")
    if not os.path.isfile(resumeFileName):
      self.newResumeFormat = False
      resumeFileName = os.path.join(self.path, "resume.vdr")
      fileMode = "rb"
    try:
      f_resume = open(resumeFileName, fileMode)
    except IOError:
# doesn't exist
      self.resume = 0
    else:
# exists
      if self.newResumeFormat:
        resume_content = f_resume.readlines()
        f_resume.close()
        for resume_line in resume_content:
          if resume_line[0] == 'I':
            self.resume = int(resume_line[2:])
      else:
        resume_content = array('L')
        if resume_content.itemsize == 8:
          resume_content = array('I')
#       xbmc.log("resume_content.itemsize= " + str(resume_content.itemsize), xbmc.LOGERROR)
        resume_content.fromfile(f_resume, 1)
        f_resume.close()
        self.resume = int(resume_content[0])
    return
  def addDirectoryItem(self, addon_handle, commands = []):
    li = self.getListitem()
    url = self.getStackUrl()
#    if self.ts_f != [] and self.contentType != None:
#        nfoFileName = os.path.splitext(self.ts_f[-1])[0] + '.nfo'
#        self.writeNfoFile(nfoFileName)
    self.marksToBookmarks(url, self.duration)
    self.updateComskip()
    li.addContextMenuItems( commands )    
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=False)

  def getMarks(self):
# read marks
    if self.marksInitialized: return
    self.marksInitialized = True
    self.marks = []
    try:
        f_marks = open(os.path.join(self.path, "marks"), "r")
    except IOError:
# doesn't exist
        xbmc.log("marks don't exist, path: " + str(self.path), xbmc.LOGINFO)        
    else:
# exists
        marks_content = f_marks.readlines()
        f_marks.close()
#       xbmc.log("marks: " + str(os.path.join(self.path, "marks")), xbmc.LOGINFO)        
        for marks_line in marks_content:
          if marks_line[1] == ':':
            m_time_sec = ((float(marks_line[0]) * 60) + float(marks_line[2:4]) ) * 60 + float(marks_line[5:10])
#           xbmc.log("m_time_sec: " + str(m_time_sec), xbmc.LOGINFO)
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
        if comLen > 12*60:
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
    if os.path.exists(os.path.join(self.path, "00001.edl") ): return
    if os.path.exists(os.path.join(self.path, "001.edl") ): return
    self.sanitizeMarks()
    if self.marksS == []: return
#   for mark in self.marksS:      
#       xbmc.log("updateComskip, mark: " + str(mark[0]) + " " + str(mark[1]), xbmc.LOGERROR)        

    self.initializeIndex()
    self.getTsFiles()

    lengthOfPreviousFiles = 0
    iIndex = 0
    for ts_file in self.ts_f:

      try:
        f_com = open((os.path.splitext(ts_file)[0] + ".edl"), "w")
#       f_com_txt = open((os.path.splitext(ts_file)[0] + ".txt"), "w")
      except IOError as e:
        xbmc.log("Error creating commercials file" + str(e), xbmc.LOGERROR)
      else:
#       n_frames_in_file = int(self.duration * self.framerate)
#       f_com_txt.write("FILE PROCESSING COMPLETE " + str(n_frames_in_file) + " FRAMES AT " + str(self.framerate) + "\n")
#       f_com_txt.write("FILE PROCESSING COMPLETE\n")
#       f_com_txt.write("------------------------\n")

        for mark in self.marksS:
            mark0 = mark[0] - lengthOfPreviousFiles
            mark1 = mark[1] - lengthOfPreviousFiles
            if mark1 <= 0.1: continue
            if mark0 < 0.1: mark0 = 0.1
            f_com.write(str(mark0).ljust(7)
               + "     "
               + str(mark1).ljust(7) + "     3" 
               + '\n')
#           f_com_txt.write(string.zfill(str(int(mark0* self.framerate)), 5)
#              + "   "
#              + string.zfill(str(int(mark1* self.framerate)), 5)
#              + '\n')
        f_com.close()
      lengthOfPreviousFiles = self.ts_l[iIndex] / self.framerate
      iIndex = iIndex +1

  def marksToBookmarks(self, url, totalTimeInSeconds):
    fileId = self.oBookmarks.getFileId(url)
    if fileId == -2:
# database format not supported      
      return
    if fileId == -1:
      self.oBookmarks.insertFile(url)
#     xbmc.log("file inserted: " + str(url), xbmc.LOGERROR)   
      fileId = self.oBookmarks.getFileId(url)
      if fileId == -1:      
        xbmc.log("Error, file Id still -1: " + str(url), xbmc.LOGERROR)   
        return
    bm = self.oBookmarks.getBookmarksFromFileId(fileId)
#   xbmc.log("bm: " + str(bm), xbmc.LOGERROR)
    if len(bm) == 0:
# read marks, and add
      self.getMarks()
      self.oBookmarks.insertBookmarks(fileId, self.marks, totalTimeInSeconds)

  def addRecordingToLibrary(self, libraryPath):
      if not os.path.exists(libraryPath):
            os.makedirs(libraryPath)
      sanTitle = re.sub(r'[/\\?%*:|"<>]', '-', self.title.strip())
      strmFileName = os.path.join(libraryPath, sanTitle + ".strm")
#     nfoFileName = os.path.join(libraryPath, sanTitle + ".nfo")
#     if os.path.isfile(strmFileName): return -1  # file exists
      try:
        f_strm = open(strmFileName, "w")
      except IOError:
# cannot open for write
        xbmc.log("Cannot open for write: " + str(strmFileName), xbmc.LOGERROR)        
        return -1
      else:
        f_strm.write(self.getStackUrl())
        f_strm.close()
#        kf = kfolder.kFolder(self.path)
#        kf.SetStrmFileName(strmFileName)
      

  def writeNfoFile(self, nfoFileName):
      try:
        f_nfo = open(nfoFileName, "w")
      except IOError:
# cannot open for write
        xbmc.log("Cannot open for write: " + str(nfoFileName), xbmc.LOGERROR)        
        return
      else:
        if self.contentType == constants.TV_SHOWS:
          ot = '<episodedetails>\n'
          ct = '</episodedetails>\n'
        elif self.contentType == constants.MUSIC_VIDEOS:
          ot = '<musicvideo>\n'
          ct = '</musicvideo>\n'
        else:
          ot = '<movie>\n'
          ct = '</movie>\n'
        f_nfo.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        f_nfo.write('<!-- created - by plugin.video.vdr.recordings -->\n')
        f_nfo.write(ot)
        f_nfo.write('<title>' + self.title.strip() + '</title>\n')
        f_nfo.write('<outline>' + self.subtitle.strip() + '</outline>\n')
        f_nfo.write('<plot>' + self.description.strip() + '</plot>\n')
        f_nfo.write(ct)
        f_nfo.close()

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
      if not os.path.isfile(indexFileName):
        newIndexFormat = False
        indexFileName = os.path.join(self.path, "index.vdr")
      try:
        f_index =  open(indexFileName, "rb")
      except IOError:
# doesn't exist
        xbmc.log("Cannot open index file " + str(indexFileName), xbmc.LOGERROR)
        pass
      else:
        if newIndexFormat:
          index = array( 'H', f_index.read() )
          numbersPerEntry = 4
          offsetRight = 1
        else:
          index = array( 'B', f_index.read() )
          numbersPerEntry = 8
          offsetRight = 3
        f_index.close
        index_len = len(index)
#       xbmc.log("index_len= " + str(index_len), xbmc.LOGERROR)
        number_of_entries = index_len / numbersPerEntry
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
          testPos =  number_of_entries * i/ numberOfTsFiles
          found = False
          while found == False:
            ts_file_at_test_pos = index[testPos * numbersPerEntry - offsetRight]
            if ts_file_at_test_pos > i:
              limit_high = testPos
              testPos = limit_low + (testPos - limit_low) / 2
            else:
              ts_file_at_test_pos_p1 = index[(testPos + 1)* numbersPerEntry - offsetRight]
              if ts_file_at_test_pos_p1 <= i:
                limit_low = testPos
                testPos = limit_high - (limit_high - testPos) / 2
              else:
                found = True
                self.ts_l.append(testPos)

        self.ts_l.append(number_of_entries)

