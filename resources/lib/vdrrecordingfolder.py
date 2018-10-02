# Copyright: GNU GPLv3

import os
import string
import xbmcgui
import xbmc
from array import array
import time
import datetime


class VdrRecordingFolder:
  """All about one Vdr Recording"""

  def __init__(self, vdrRecordingFolder):
    self.path = vdrRecordingFolder
    self.infoInitialized = False
    self.tsInitialized = False 
    self.resumeInitialized = False
    self.newResumeFormat = True
    self.initializeInfo()

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
        if rt[18] == "-":
          rec_seconds = int(rt[17])
        else:
          rec_seconds = int(rt[17:19])
        if (rec_seconds < 0) or (rec_seconds > 59):
          rec_seconds = 0
        self.RecordingTime = datetime.datetime(year = int(rt[0:4]), month = int(rt[5:7]),
          day = int(rt[8:10]), hour = int(rt[11:13]), minute = int(rt[14:16]), second = rec_seconds)
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
    duration = int(index_file_length / 8 / self.framerate)
    numVidStreams = 0
    for streamInfoLine in self.streamInfo:
      if(streamInfoLine[0] == "video"):
        numVidStreams = numVidStreams  + 1
        streamInfoLine[1]['duration'] = duration
        li.addStreamInfo(streamInfoLine[0], streamInfoLine[1])
    if numVidStreams == 0:
      li.addStreamInfo('video', {'duration': duration})
    for streamInfoLine in self.streamInfo:
      if(streamInfoLine[0] <> "video"):
        li.addStreamInfo(streamInfoLine[0], streamInfoLine[1])

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
