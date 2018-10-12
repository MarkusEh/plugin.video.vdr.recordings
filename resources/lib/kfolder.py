# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import string
import urllib
import xbmc
import xbmcplugin
import xbmcgui
import constants
import vdrrecordingfolder

class kFolder:

  def __init__(self, folder):
    self.path = folder
    self.fileRead = False

  def readKodiFile(self):
    if self.fileRead == True:
      return
    self.fileRead = True
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
          self.kodiLines[kodi_line[0]] = kodi_line[2:].strip()
 
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
    return self.kodiLines.get('C', default)

  def setContentType(self, contentType):
    self.readKodiFile()
    self.kodiLines['C'] = contentType
    self.writeKodiFile()

  def getEpisode(self, default):
    self.readKodiFile()
    return int(self.kodiLines.get('E', default))

  def getSeason(self, default):
    self.readKodiFile()
    return int(self.kodiLines.get('S', default))

  def setEpisode(self, Episode):
    self.readKodiFile()
    self.kodiLines['E'] = str(Episode)
    self.writeKodiFile()

  def setSeason(self, Season):
    self.readKodiFile()
    self.kodiLines['S'] = str(Season)
    self.writeKodiFile()

  def SetStrmFileName(self, strmFileName):
    self.readKodiFile()
    self.kodiLines['F'] = str(strmFileName).strip()
    self.writeKodiFile()

  def getStrmFileName(self):
    self.readKodiFile()
    return self.kodiLines.get('F')

  def parseFolder(self, addon_handle, base_url, rootFolder):
        onlySameTitle = True
        firstTitle = None
        recordingsList = []
        subfolderList = []
        for fileN in os.listdir(self.path):
          path = os.path.join(self.path, fileN)
          if os.path.isdir(path):
            subfolders = get_immediate_subdirectories(path)
            if len(subfolders) == 1:
              if os.path.splitext(subfolders[0])[1] == ".rec":
                path = os.path.join(path, subfolders[0])
            if os.path.splitext(path)[1] == ".rec":
              vdrRecordingFolder = vdrrecordingfolder.VdrRecordingFolder(path)
              if firstTitle == None:
                firstTitle = vdrRecordingFolder.title
              else:
                if vdrRecordingFolder.title != firstTitle:
                  onlySameTitle = False
              recordingsList.append(vdrRecordingFolder)
            else:
              if len(subfolders) > 0:
#               onlySameTitle = False
                subfolderList.append([path, fileN])
        if onlySameTitle and len(recordingsList) > 1:
#           xbmc.log("onlySameTitle: " + str(self.path), xbmc.LOGERROR)            
            contentType = self.getContentType(constants.TV_SHOWS)
#           xbmc.log("contentType: " + str(contentType), xbmc.LOGERROR)            
        else:
            contentType = self.getContentType(constants.MOVIES)

        libPath = self.getLibPath(contentType, rootFolder)
        if contentType == constants.TV_SHOWS:
            if onlySameTitle and firstTitle.strip() != os.path.split(self.path)[1].strip().replace('_', ' '):
# Name of folder differs from name of recordings
              libPath = os.path.join(libPath, firstTitle.strip()) 
            season = 1
            episode = 0
            for vdrRecordingFolder in sorted(recordingsList, key=lambda rec: rec.sortRecordingTimestamp):
                kf = kFolder(vdrRecordingFolder.path)
                season_n = kf.getSeason(season)
                if season_n == season:
                    episode = episode + 1
                else:
                    episode = 1
                    season = season_n
                episode = kf.getEpisode(episode)
                se = 'S' + string.zfill(str(season),2) + 'E' + string.zfill(str(episode),2)
                vdrRecordingFolder.title = vdrRecordingFolder.title.strip() + ' ' + se + '\n'
                if addon_handle == -10:
                    vdrRecordingFolder.addRecordingToLibrary(libPath, contentType)
                else:
# add context menu
                    commands = []
                    addContextMenuCommand(commands, "Set season", constants.SEASON, vdrRecordingFolder.path, str(season))
                    addContextMenuCommand(commands, "Set episode", constants.EPISODE, vdrRecordingFolder.path, str(episode))
                    addContextMenuCommand(commands, "Delete", constants.DELETE, vdrRecordingFolder.path)
                    vdrRecordingFolder.addDirectoryItem(addon_handle, commands)
        else:
            if addon_handle == -10:          
                for vdrRecordingFolder in recordingsList:
                    vdrRecordingFolder.addRecordingToLibrary(libPath, contentType)
            else:
              for vdrRecordingFolder in recordingsList:
                commands = []
                addContextMenuCommand(commands, "Delete", constants.DELETE, vdrRecordingFolder.path)
                vdrRecordingFolder.addDirectoryItem(addon_handle, commands)
        
        if addon_handle == -10:         
          for pathN in subfolderList:
            kFolder(pathN[0]).parseFolder(addon_handle, base_url, rootFolder)
        else:
          for pathN in subfolderList:
            url = build_url(base_url, {'mode': 'folder', 'currentFolder': pathN[0]})
            name = pathN[1].replace('_', ' ')
            li = xbmcgui.ListItem(name, iconImage = 'DefaultFolder.png')
# add context menu
            commands = []
            addContextMenuCommand(commands, "Set content: TV shows", constants.TV_SHOWS, pathN[0])
            addContextMenuCommand(commands, "Set content: Music videos", constants.MUSIC_VIDEOS, pathN[0])
            addContextMenuCommand(commands, "Set content: Movies", constants.MOVIES, pathN[0])
            addContextMenuCommand(commands, "Add all recordings to Library", constants.ADDALLTOLIBRARY, rootFolder)
            li.addContextMenuItems( commands )
           
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
        if addon_handle != -10: 
            if onlySameTitle:
              xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
            else:
              xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        
              xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
            xbmcplugin.endOfDirectory(addon_handle)

  def getLibPath(self, contentType, baseFolderVDR):
        relPath = self.path[len(baseFolderVDR)+1:]
        if relPath != '':
          while relPath[0] == '/' or relPath[0] == '\\':
             relPath = relPath[1:]
        if contentType == constants.TV_SHOWS:
            libPath = os.path.join(constants.LIBRARY_TV_SHOWS, relPath)
        elif contentType == constants.MUSIC_VIDEOS:
            libPath = os.path.join(constants.LIBRARY_MUSIC_VIDEOS, relPath)
        else:
            libPath = os.path.join(constants.LIBRARY_MOVIES, relPath)   
        return libPath                     


def addContextMenuCommand(commands, name, mode, url, arg3 = ''):
        script = "special://home/addons/plugin.video.vdr.recordings/resources/lib/contextMenu.py"
        if arg3 == '':
          runner = "XBMC.RunScript(" + str(script)+ ", " + str(mode) + ", " + str(url) + ")"
        else:
          runner = "XBMC.RunScript(" + str(script)+ ", " + str(mode) + ", " + str(url) + ", " + str(arg3) + ")"
#       xbmc.log("runner=" + str(runner), xbmc.LOGERROR)
        commands.append(( str(name), runner, ))

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def build_url(base_url, query):
        return base_url + '?' + urllib.urlencode(query)
