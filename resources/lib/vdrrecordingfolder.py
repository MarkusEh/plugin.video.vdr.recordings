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


class VdrRecordingFolder:
  """All about one Vdr Recording"""

  def __init__(self, vdrRecordingFolder):
    self.path = vdrRecordingFolder
    self.infoInitialized = False
    self.tsInitialized = False 
    self.resumeInitialized = False
    self.newResumeFormat = True
    self.initializeInfo()
    self.oBookmarks = bookmarks()

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
    self.marksToBookmarks(url, self.duration)
    li.addContextMenuItems( commands )    
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=False)

  def addDirectoryItem2(self):
    li = self.getListitem()
    url = self.getStackUrl()
    self.marksToBookmarks(url, self.duration)

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
#   xbmc.log("len(bm): " + str(len(bm)), xbmc.LOGERROR)
    if len(bm) == 0:
    # read marks, and add
      try:
        f_marks = open(os.path.join(self.path, "marks"), "r")
      except IOError:
  # doesn't exist
        xbmc.log("marks, path: " + str(self.path), xbmc.LOGINFO)        
        xbmc.log("marks don't exist", xbmc.LOGINFO)
      else:
  # exists
        marks_content = f_marks.readlines()
        f_marks.close()
        marks = []
        xbmc.log("marks: " + str(os.path.join(self.path, "marks")), xbmc.LOGINFO)        
        for marks_line in marks_content:
          if marks_line[1] == ':':
            m_time_sec = ((float(marks_line[0]) * 60) + float(marks_line[2:4]) ) * 60 + float(marks_line[5:10])
            xbmc.log("m_time_sec: " + str(m_time_sec), xbmc.LOGINFO)
            marks.append(m_time_sec)
        self.oBookmarks.insertBookmarks(fileId, marks, totalTimeInSeconds)

  def addRecordingToLibrary(self, libraryPath, contentType):
      if not os.path.exists(libraryPath):
            os.makedirs(libraryPath)
      sanTitle = re.sub(r'[/\\?%*:|"<>]', '_', self.title.strip())
      strmFileName = os.path.join(libraryPath, sanTitle + ".strm")
      nfoFileName = os.path.join(libraryPath, sanTitle + ".nfo")
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
      
      try:
        f_nfo = open(nfoFileName, "w")
      except IOError:
# cannot open for write
        xbmc.log("Cannot open for write: " + str(nfoFileName), xbmc.LOGERROR)        
        return
      else:
        if contentType == constants.TV_SHOWS:
          ot = '<episodedetails>'
          ct = '</episodedetails>'
        elif contentType == constants.MUSIC_VIDEOS:
          ot = '<musicvideo>'
          ct = '</musicvideo>'
        else:
          ot = '<movie>'
          ct = '</movie>'
        f_nfo.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
        f_nfo.write('<!-- created - by plugin.video.vdr.recordings -->')
        f_nfo.write(ot)
        f_nfo.write('<title>' + self.title.strip() + '</title>')
        f_nfo.write('<outline>' + self.subtitle.strip() + '</outline>')
        f_nfo.write('<plot>' + self.description.strip() + '</plot>')
        f_nfo.write(ct)
        f_nfo.close()

