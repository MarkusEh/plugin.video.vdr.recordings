# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import string
import urllib
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import xbmcvfs
import constants
import vdrrecordingfolder

class kFolder:

  def __init__(self, folder):
    self.path = folder
    self.fileRead = False
    self.rootFolder = None

  def readKodiFile(self):
    if self.fileRead == True:
      return
    self.fileRead = True
    self.kodiLines = {}
    kodiFileName = os.path.join(self.path, "kodi")
    if xbmcvfs.exists(kodiFileName):
      try:
#       f_kodi = open(kodiFileName, "r")
        f_kodi = xbmcvfs.File(kodiFileName, "r")
      except IOError:
        xbmc.log("Cannot open for read: " + str(kodiFileName), xbmc.LOGERROR)
        pass
      else:
# exists
        kodi_content = f_kodi.read()
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

  def setEpisode(self, Episode):
    self.readKodiFile()
    self.kodiLines['E'] = str(Episode)
    self.writeKodiFile()

  def getSeason(self, default):
    self.readKodiFile()
    return int(self.kodiLines.get('S', default))

  def setSeason(self, Season):
    self.readKodiFile()
    self.kodiLines['S'] = str(Season)
    self.writeKodiFile()

  def getYear(self):
    self.readKodiFile()
    return int(self.kodiLines.get('Y', -1))

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

  def getRootFolder(self):
    if self.rootFolder == None:
      addon = xbmcaddon.Addon('plugin.video.vdr.recordings')
      self.rootFolder = addon.getSetting("rootFolder")
      lastChar = self.rootFolder[-1] 
      if lastChar == '/' or lastChar == '\\':
        self.rootFolder = self.rootFolder[:-1]
    return self.rootFolder

  def selectFolder(self, rootFolder):
    FOLDER_UP = ".."
    THIS_FOLDER = "<select this folder>"
    CREATE_FOLDER = "<create folder>"
    DELETE_FOLDER = "<delete this folder>"
    self.subFolders = []
    self.subFolders.append(THIS_FOLDER)
#   if os.access(self.path, os.W_OK):
    self.subFolders.append(CREATE_FOLDER)
    dirs, files = xbmcvfs.listdir(self.path)
    if len(dirs) == 0 and len(files) == 0:
      self.subFolders.append(DELETE_FOLDER)
    if self.path != rootFolder:
      self.subFolders.append(FOLDER_UP)
    prefolders = len(self.subFolders)
    self.parseFolder(-20, rootFolder, rootFolder)
    dialog = xbmcgui.Dialog()
    d = dialog.select(self.path, self.subFolders)
    if d == None: return d
    if d == -1: return None
    if d >= prefolders:
      return kFolder(self.subFolders[d]).selectFolder(rootFolder)
    if self.subFolders[d] == FOLDER_UP:
      return kFolder(os.path.split(self.path)[0]).selectFolder(rootFolder)
    if self.subFolders[d] == THIS_FOLDER:
      return self.path
    if self.subFolders[d] == DELETE_FOLDER:
      try:
        xbmcvfs.rmdir(self.path)
      except:
        xbmc.log("Error deleting directory " + str(self.path), xbmc.LOGERROR)            
        return self.selectFolder(rootFolder)
      return kFolder(os.path.split(self.path)[0]).selectFolder(rootFolder)

    if self.subFolders[d] == CREATE_FOLDER:
      d2 = dialog.input("Enter name of new folder")
      if d2 == "": return self.selectFolder(rootFolder)
      newpath = os.path.join(self.path, d2)
      if not xbmcvfs.exists(newpath + "/"):
        try:
          xbmcvfs.makedirs(newpath)
        except:
          xbmc.log("Error creating directory " + str(newpath), xbmc.LOGERROR)            
          return self.selectFolder(rootFolder)
      return kFolder(newpath).selectFolder(rootFolder)

    xbmc.log("Error in selectFolder, d= " + str(d), xbmc.LOGERROR)            
    return None


  def parseFolder(self, addon_handle, base_url, rootFolder):
        onlySameTitle = True
        firstTitle = None
        recordingsList = []
        subfolderList = []
        rec_names, files = xbmcvfs.listdir(self.path)
        for rec_name in rec_names:
          if os.path.splitext(rec_name)[1] == ".move": continue
          path = os.path.join(self.path, rec_name)
          rec_timestamps, files = xbmcvfs.listdir(path)
          subfolder = False
          for rec_timestamp in rec_timestamps:
            if os.path.splitext(rec_timestamp)[1] != ".rec":
              subfolder = True
            else:
              vdrRecordingFolder = vdrrecordingfolder.VdrRecordingFolder(os.path.join(path,rec_timestamp))
              if firstTitle == None:
                firstTitle = vdrRecordingFolder.title
              else:
                if vdrRecordingFolder.title != firstTitle:
                  onlySameTitle = False
              recordingsList.append(vdrRecordingFolder)
          if subfolder:
             subfolderList.append([path, rec_name])

        if onlySameTitle and len(recordingsList) > 1:
#           xbmc.log("onlySameTitle: " + str(self.path), xbmc.LOGERROR)            
            contentType = self.getContentType(constants.TV_SHOWS)
#           xbmc.log("contentType: " + str(contentType), xbmc.LOGERROR)            
        else:
            contentType = self.getContentType(constants.MOVIES)

# Recordings
        if contentType == constants.TV_SHOWS:
            if onlySameTitle:
              TV_show_name = firstTitle
            else:
              TV_show_name = os.path.split(self.path)[1].strip()
            libPath = os.path.join(constants.LIBRARY_TV_SHOWS, TV_show_name)                
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
                vdrRecordingFolder.title = vdrRecordingFolder.title + ' ' + se
                if addon_handle == -10:
                    vdrRecordingFolder.addRecordingToLibrary(libPath)
                elif addon_handle >= 0:
# add context menu
                    commands = []
                    addContextMenuCommand(commands, "Set season", constants.SEASON, vdrRecordingFolder.path, str(season))
                    addContextMenuCommand(commands, "Set episode", constants.EPISODE, vdrRecordingFolder.path, str(episode))
                    addContextMenuCommand(commands, "Delete", constants.DELETE, vdrRecordingFolder.path)
                    addContextMenuCommand(commands, "Move", constants.MOVE, vdrRecordingFolder.path)
                    addContextMenuCommand(commands, "Refresh", constants.REFRESH, rootFolder, base_url)
                    vdrRecordingFolder.contentType = contentType
                    vdrRecordingFolder.addDirectoryItem(addon_handle, commands)
        elif contentType == constants.MUSIC_VIDEOS:
            if addon_handle == -10:          
                libPath = self.getLibPath(contentType, rootFolder)
                for vdrRecordingFolder in recordingsList:
                    vdrRecordingFolder.addRecordingToLibrary(libPath)
            elif addon_handle >= 0:
              for vdrRecordingFolder in recordingsList:
                commands = []
                addContextMenuCommand(commands, "Delete", constants.DELETE, vdrRecordingFolder.path)
                addContextMenuCommand(commands, "Move", constants.MOVE, vdrRecordingFolder.path)
                vdrRecordingFolder.contentType = contentType
                vdrRecordingFolder.addDirectoryItem(addon_handle, commands)
        else:
            libPath = self.getLibPath(contentType, rootFolder)          
            for vdrRecordingFolder in recordingsList:
                year = vdrRecordingFolder.getYear()
                if year > 0:
                   vdrRecordingFolder.title = vdrRecordingFolder.title + ' (' + str(year) + ')'
                if addon_handle == -10:
                    vdrRecordingFolder.addRecordingToLibrary(libPath)
                elif addon_handle >= 0:
                  commands = []
                  addContextMenuCommand(commands, "Set year", constants.YEAR, vdrRecordingFolder.path, str(year))
                  addContextMenuCommand(commands, "Delete", constants.DELETE, vdrRecordingFolder.path)
                  addContextMenuCommand(commands, "Move", constants.MOVE, vdrRecordingFolder.path)
                  addContextMenuCommand(commands, "Refresh", constants.REFRESH, rootFolder, base_url)
                  vdrRecordingFolder.contentType = contentType
                  vdrRecordingFolder.addDirectoryItem(addon_handle, commands)

        
# subfolders
        if addon_handle < 0: 
          if addon_handle == -20:
            for pathN in subfolderList:
                self.subFolders.append(pathN[0])
#               xbmc.log("subFolders= " + str(subFolders), xbmc.LOGERROR)
          else:   
            for pathN in subfolderList:
              kFolder(pathN[0]).parseFolder(addon_handle, base_url, rootFolder)
        else:
          for pathN in subfolderList:
            url = build_url(base_url, {'mode': 'folder', 'currentFolder': pathN[0]})
            name = pathN[1].replace('_', ' ')
            li = xbmcgui.ListItem(name)
            li.setArt({ 'icon' : 'DefaultFolder.png' })
# add context menu
            commands = []
            addContextMenuCommand(commands, "Set content: TV shows", constants.TV_SHOWS, pathN[0])
            addContextMenuCommand(commands, "Set content: Music videos", constants.MUSIC_VIDEOS, pathN[0])
            addContextMenuCommand(commands, "Set content: Movies", constants.MOVIES, pathN[0])
            addContextMenuCommand(commands, "Add all recordings to Library", constants.ADDALLTOLIBRARY, rootFolder)
            addContextMenuCommand(commands, "Move", constants.MOVE, pathN[0])
            addContextMenuCommand(commands, "Search", constants.SEARCH, rootFolder, base_url)
            addContextMenuCommand(commands, "Refresh", constants.REFRESH, rootFolder, base_url)
            li.addContextMenuItems( commands )
           
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
# finalize UI
        if addon_handle >= 0: 
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
          runner = "RunScript(" + str(script)+ ", " + str(mode) + ", \"" + str(url) + "\")"
        else:
          runner = "RunScript(" + str(script)+ ", " + str(mode) + ", \"" + str(url) + "\", \"" + str(arg3) + "\")"
#       xbmc.log("runner=" + str(runner), xbmc.LOGERROR)
        commands.append(( str(name), runner, ))

def get_immediate_subdirectories(a_dir):
    dirs, files = xbmcvfs.listdir(a_dir)
    return dirs

def build_url(base_url, query):
        return base_url + '?' + urllib.parse.urlencode(query)
