# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import string
import json
import xbmc
import xbmcvfs
import constants

class cFolder:

  def __init__(self, folder, filesFoldersProvided = False, dirs = [], files = []):
    self.path = folder
    self.fileRead = False
    self.scraperFileRead = False
    if filesFoldersProvided:
      self.dirs = dirs
      self.files = files
    else:
      self.dirs, self.files = xbmcvfs.listdir(self.path)

  def readScrapperFiles(self):
    self.readKodiFile()
    self.readTvscraperFile()

  def readTvscraperFile(self):
    if self.scraperFileRead == True: return
    self.scraperFileRead = True
    self.tvscraperData = {}
    if not "tvscraper.json" in self.files: return
    j_filename = os.path.join(self.path, "tvscraper.json")
    with xbmcvfs.File(j_filename, "r") as j_file:
      try:
        j_string = j_file.read()
      except:
        xbmc.log("non-utf8 characters in file " + j_filename, xbmc.LOGERROR)
        return
      try:
        data = json.loads(j_string)
      except:
        xbmc.log("ERROR parsing json file " + j_filename, xbmc.LOGERROR)
        return
      keys0 = list(data.keys() )
      self.source = ''
      if 'thetvdb' in keys0: self.source = 'thetvdb'
      if 'themoviedb' in keys0: self.source = 'themoviedb'
      if self.source == '' :
        xbmc.log("ERROR readTvscraperFile, source == '', file = " + j_filename, xbmc.LOGERROR)
        return
# ignore tvscraper data if there is no name
      r = data[self.source].get('name')
      if r == None: return
      if r == "": return
      self.tvscraperData = data[self.source]

  def readKodiFile(self):
    if self.fileRead == True:
      return
    self.fileRead = True
    self.kodiLines = {}
    if not "kodi" in self.files: return
    kodiFileName = os.path.join(self.path, "kodi")
    try:
      f_kodi = xbmcvfs.File(kodiFileName, "rb")
    except IOError:
      xbmc.log("Cannot open for read: " + str(kodiFileName), xbmc.LOGERROR)
      pass
    else:
# exists
      try:
        kodi_content = f_kodi.read()
      except:
        xbmc.log("non-utf8 characters in file " + kodiFileName, xbmc.LOGERROR)
        kodi_content = ""

      f_kodi.close()
      for kodi_line in kodi_content.splitlines():
        try:
          self.kodiLines[kodi_line[0]] = kodi_line[2:].strip()
        except:
          pass
 
  def writeKodiFile(self):
    kodiFileName = os.path.join(self.path, "kodi")
    try:
        f_kodi = xbmcvfs.File(kodiFileName, "w")
    except IOError:
# cannot open for write
        xbmc.log("Cannot open for write: " + str(kodiFileName), xbmc.LOGERROR)        
        return -1
    else:
# can open file for write
        for kodiLine in self.kodiLines:
          f_kodi.write(kodiLine + " " + self.kodiLines[kodiLine] + "\n")
        f_kodi.close()
  
  def getContentType(self, default = constants.MOVIES):
    self.readScrapperFiles()
    r = self.kodiLines.get('C')
    if r != None: return r
    r = self.tvscraperData.get('type')
    if r == 'movie': return constants.MOVIES
    if r == 'tv show': return constants.TV_SHOWS

    return default

  def setContentType(self, contentType):
    self.readKodiFile()
    self.kodiLines['C'] = contentType
    self.writeKodiFile()

  def getEpisode(self, default):
    self.readScrapperFiles()
    r = self.kodiLines.get('E')
    if r != None: return int(r)
    r = self.tvscraperData.get('episode_number')
    if r == None: return default
    return r

  def getEpisodeName(self, default = ""):
    self.readScrapperFiles()
    r = self.tvscraperData.get('episode_name')
    if r == None: return default
    return r

  def setEpisode(self, Episode):
    self.readKodiFile()
    self.kodiLines['E'] = str(Episode)
    self.writeKodiFile()

  def getSeason(self, default):
    self.readScrapperFiles()
    r = self.kodiLines.get('S')
    if r != None: return int(r)
    r = self.tvscraperData.get('season_number')
    if r == None: return default
    return r

  def setSeason(self, Season):
    self.readKodiFile()
    self.kodiLines['S'] = str(Season)
    self.writeKodiFile()

  def getYear(self):
    self.readScrapperFiles()
    r = self.kodiLines.get('Y')
    if r != None:
      if not r.isdigit(): xbmc.log("kfolder, file kodi, year not integer, year = " + str(r) + " path " + self.path, xbmc.LOGERROR)
    if r != None: return int(r)
    r = self.tvscraperData.get('year')
    if r == None: return -1
    if type(r) != int: xbmc.log("kfolder, year not integer, year = " + str(r) + " path " + self.path, xbmc.LOGERROR)
    return r

  def getName(self, default):
    self.readScrapperFiles()
    r = self.tvscraperData.get('name')
    if r == None: return default
    return r

  def getDbUrl(self):
    self.readScrapperFiles()
    r = self.tvscraperData.get('movie_tv_id')
    if r == None: return ""
    if self.source == 'themoviedb': return "https://www.themoviedb.org/movie/" + str(r)
    if self.source == 'thetvdb': return "https://www.thetvdb.com/index.php?tab=series&id=" + str(r)
    return ""


  def setYear(self, Year):
    self.readKodiFile()
    self.kodiLines['Y'] = str(Year)
    self.writeKodiFile()

  def SetStrmFileName(self, strmFileName):
    self.readKodiFile()
    self.kodiLines['F'] = str(strmFileName).strip()
    self.writeKodiFile()

  def getStrmFileName(self):
    self.readKodiFile()
    return self.kodiLines.get('F')

