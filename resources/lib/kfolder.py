# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import xbmc
import constants

class kFolder:

  def __init__(self, folder):
    self.path = folder

  def readKodiFile(self):
    self.kodiLines = {}
    kodiFileName = os.path.join(self.path, "kodi")
    if os.path.isfile(kodiFileName):
      try:
        f_kodi = open(kodiFileName, "r")
      except:
        pass
      else:
# exists
        kodi_content = f_kodi.readlines()
        f_kodi.close()
        for kodi_line in kodi_content:
          self.kodiLines[kodi_line[0]] = kodi_line[2:]
 
  def writeKodiFile(self):
    kodiFileName = os.path.join(self.path, "kodi")
    try:
        f_kodi = open(kodiFileName, "w")
    except:
# cannot open for write
        xbmc.log("Cannot open for write: " + str(kodiFileName), xbmc.LOGERROR)        
        return -1
    else:
# can open file for write
        for kodiLine in self.kodiLines:
          f_kodi.write(kodiLine + " " + self.kodiLines[kodiLine] + "\n")
        f_kodi.close()
  
  def getContentType(self, default = constants.MOVIES):
# default, if we can't figure out anything else
    self.readKodiFile()
    self.contentType = self.kodiLines.get('C', default)
    return self.contentType

  def setContentType(self, contentType):
    self.contentType = contentType
    self.readKodiFile()
    self.kodiLines['C'] = contentType
    self.writeKodiFile()
  