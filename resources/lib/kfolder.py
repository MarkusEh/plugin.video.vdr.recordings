# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import string
import urllib
import json
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
    self.scraperFileRead = False
    self.rootFolder = None
    self.source = ""
    self.addon = xbmcaddon.Addon('plugin.video.vdr.recordings')

  def readScrapperFiles(self):
    self.readKodiFile()
    self.readTvscrapperFile()

  def readTvscrapperFile(self):
    if self.scraperFileRead == True: return
    self.scraperFileRead = True
    self.tvscrapperData = {}
    j_filename = os.path.join(self.path, "tvscrapper.json")
    if not xbmcvfs.exists(j_filename): return
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
        xbmc.log("ERROR readTvscrapperFile, source == '', file = " + j_filename, xbmc.LOGERROR)
        return
# ignore tvscraper data if there is no name
      r = data[self.source].get('name')
      if r == None: return
      if r == "": return
      self.tvscrapperData = data[self.source]

  def readKodiFile(self):
    if self.fileRead == True:
      return
    self.fileRead = True
    self.kodiLines = {}
    kodiFileName = os.path.join(self.path, "kodi")
    if xbmcvfs.exists(kodiFileName):
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
    r = self.tvscrapperData.get('type')
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
    r = self.tvscrapperData.get('episode_number')
    if r == None: return default
    return r

  def getEpisodeName(self, default = ""):
    self.readScrapperFiles()
    r = self.tvscrapperData.get('episode_name')
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
    r = self.tvscrapperData.get('season_number')
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
    r = self.tvscrapperData.get('year')
    if r == None: return -1
    if type(r) != int: xbmc.log("kfolder, year not integer, year = " + str(r) + " path " + self.path, xbmc.LOGERROR)
    return r

  def getName(self, default):
    self.readScrapperFiles()
    r = self.tvscrapperData.get('name')
    if r == None: return default
    return r

  def getDbUrl(self):
    self.readScrapperFiles()
    r = self.tvscrapperData.get('movie_tv_id')
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

  def getRootFolder(self):
    if self.rootFolder == None:
      self.rootFolder = self.addon.getSetting("rootFolder")
      lastChar = self.rootFolder[-1] 
      if lastChar == '/' or lastChar == '\\':
        self.rootFolder = self.rootFolder[:-1]
    return self.rootFolder

  def selectFolder(self, rootFolder):
    FOLDER_UP = ".."
    THIS_FOLDER = xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30300)
    CREATE_FOLDER = xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30301)
    DELETE_FOLDER = xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30302)
    self.subFolders = []
    self.subFolders.append(THIS_FOLDER)
    self.subFolders.append(CREATE_FOLDER)
    dirs, files = xbmcvfs.listdir(self.path)
    if len(dirs) == 0 and len(files) == 0:
      self.subFolders.append(DELETE_FOLDER)
    if self.path != rootFolder:
      self.subFolders.append(FOLDER_UP)
    prefolders = len(self.subFolders)
    self.parseFolder(-20, rootFolder, rootFolder, {})
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


  def parseFolder(self, addon_handle, base_url, rootFolder, current_files):
        if addon_handle >= 0: xbmc.log("parseFolder: Start, path: " + str(self.path), xbmc.LOGINFO)
        onlySameTitle = True
        firstTitle = None
        recordingsList = []
        subfolderList = []
        rec_names, files = xbmcvfs.listdir(self.path)
        for rec_name in rec_names:
          if os.path.splitext(rec_name)[1] == ".move": continue
          path = os.path.join(self.path, rec_name)
          rec_timestamps, files = xbmcvfs.listdir(path)
          subfolder = True
          for rec_timestamp in rec_timestamps:
            if os.path.splitext(rec_timestamp)[1] == ".rec":
              subfolder = False
              vdrRecordingFolder = vdrrecordingfolder.VdrRecordingFolder(os.path.join(path,rec_timestamp))
              if firstTitle == None:
                firstTitle = vdrRecordingFolder.title
              else:
                if vdrRecordingFolder.title != firstTitle:
                  onlySameTitle = False
              recordingsList.append(vdrRecordingFolder)
          if subfolder:
             subfolderList.append([path, rec_name])

        totalItems = len(recordingsList) + len(subfolderList)
        if addon_handle >= 0:
          xbmc.log("parseFolder: finished analysing VDR structure, number of recordings: " + str(len(recordingsList)) + " number of folders: " + str(len(subfolderList)), xbmc.LOGINFO)
          xbmc.log("parseFolder: Start add recordings", xbmc.LOGINFO)
        if onlySameTitle and len(recordingsList) > 1:
#           xbmc.log("onlySameTitle: " + str(self.path), xbmc.LOGINFO)
            contentType = self.getContentType(constants.TV_SHOWS)
        else:
            contentType = self.getContentType(constants.MOVIES)

# Recordings
        if contentType == constants.MUSIC_VIDEOS:
            if addon_handle == -10:          
                libPath = self.getLibPath(contentType, rootFolder)
                for vdrRecordingFolder in recordingsList:
                    vdrRecordingFolder.addRecordingToLibrary(libPath, vdrRecordingFolder.title, current_files, base_url, False, "")
            elif addon_handle >= 0:
              for vdrRecordingFolder in recordingsList:
                commands = []
                self.addContextMenuCommand(commands, 30100, constants.DELETE, vdrRecordingFolder.path)
                self.addContextMenuCommand(commands, 30101, constants.MOVE, vdrRecordingFolder.path)
                vdrRecordingFolder.addDirectoryItem(addon_handle, commands, totalItems)
        else:
            if onlySameTitle:
              TV_show_name = firstTitle
            else:
              TV_show_name = os.path.split(self.path)[1].strip()
            season = 1
            episode = 0
            for vdrRecordingFolder in sorted(recordingsList, key=lambda rec: rec.sortRecordingTimestamp):
              kf = kFolder(vdrRecordingFolder.path)
              year = kf.getYear()
              if year <= 0: year = vdrRecordingFolder.getYear()
              finalContentType = kf.getContentType(contentType)
              if finalContentType == constants.TV_SHOWS:
# TV shows
                final_TV_show_name = kf.getName(TV_show_name)
                if year > 0: final_TV_show_name = final_TV_show_name + ' (' + str(year) + ')'
                libPath = os.path.join(constants.LIBRARY_TV_SHOWS, final_TV_show_name)
                if contentType == constants.TV_SHOWS:
# automatically count episodes, but only if folder is explicitly marked as TV Shows or all recurdings have the same name
                  season_n = kf.getSeason(season)
                  if season_n == season:
                    episode = episode + 1
                  else:
                    episode = 1
                    season = season_n
                else:
# don't automatically count episodes, use season = 1 and episode = 1 if on other information is available
                  season = kf.getSeason(1)
                  episode = 1
                episode = kf.getEpisode(episode)

                se = 'S' + str(season).zfill(2) + 'E' + str(episode).zfill(2)
                vdrRecordingFolder.title = vdrRecordingFolder.title + ' ' + se
                if addon_handle == -10:
                    filename = kf.getEpisodeName(vdrRecordingFolder.subtitle)
                    if filename == "":
                      filename =  os.path.split(os.path.split(vdrRecordingFolder.path)[0])[1].replace('_', ' ').strip()
                      if filename[:1] == "%": filename = filename[1:]
                    vdrRecordingFolder.addRecordingToLibrary(libPath, filename + ' ' + se, current_files, base_url, False, kf.getDbUrl() )
                elif addon_handle >= 0:
# add context menu
                    commands = []
                    self.addContextMenuCommand(commands, 30103, constants.SEASON, vdrRecordingFolder.path, str(season))
                    self.addContextMenuCommand(commands, 30104, constants.EPISODE, vdrRecordingFolder.path, str(episode))
                    self.addContextMenuCommand(commands, 30100, constants.DELETE, vdrRecordingFolder.path)
                    self.addContextMenuCommand(commands, 30101, constants.MOVE, vdrRecordingFolder.path)
                    self.addContextMenuCommand(commands, 30102, constants.REFRESH, rootFolder, base_url)
                    vdrRecordingFolder.addDirectoryItem(addon_handle, commands, totalItems)
              else:
# Movies
                libPath = self.getLibPath(finalContentType, rootFolder)          
                if addon_handle == -10:
                    filename =  kf.getName(vdrRecordingFolder.title)
                    if year > 0:
                       filename = filename + ' (' + str(year) + ')'
                    vdrRecordingFolder.addRecordingToLibrary(libPath, filename, current_files, base_url, True, kf.getDbUrl() )
                elif addon_handle >= 0:
                  if year > 0:
                     vdrRecordingFolder.title = vdrRecordingFolder.title + ' (' + str(year) + ')'
                  commands = []
                  self.addContextMenuCommand(commands, 30105, constants.YEAR, vdrRecordingFolder.path, str(year))
                  self.addContextMenuCommand(commands, 30100, constants.DELETE, vdrRecordingFolder.path)
                  self.addContextMenuCommand(commands, 30101, constants.MOVE, vdrRecordingFolder.path)
                  self.addContextMenuCommand(commands, 30102, constants.REFRESH, rootFolder, base_url)
                  vdrRecordingFolder.addDirectoryItem(addon_handle, commands, totalItems)

        
# subfolders
        if addon_handle < 0: 
          if addon_handle == -20:
            for pathN in subfolderList:
                self.subFolders.append(pathN[0])
#               xbmc.log("subFolders= " + str(subFolders), xbmc.LOGINFO)
          else:   
            for pathN in subfolderList:
              kFolder(pathN[0]).parseFolder(addon_handle, base_url, rootFolder, current_files)
        else:
          xbmc.log("parseFolder: Start add folders", xbmc.LOGINFO)
          for pathN in subfolderList:
            url = build_url(base_url, {'mode': 'folder', 'currentFolder': pathN[0]})
            name = pathN[1].replace('_', ' ')
            li = xbmcgui.ListItem(name)
            li.setArt({ 'icon' : 'DefaultFolder.png' })
# add context menu
            commands = []
            self.addContextMenuCommand(commands, 30106, constants.TV_SHOWS, pathN[0])
            self.addContextMenuCommand(commands, 30107, constants.MUSIC_VIDEOS, pathN[0])
            self.addContextMenuCommand(commands, 30108, constants.MOVIES, pathN[0])
            self.addContextMenuCommand(commands, 30109, constants.ADDALLTOLIBRARY, rootFolder, base_url)
            self.addContextMenuCommand(commands, 30101, constants.MOVE, pathN[0])
            self.addContextMenuCommand(commands, 30110, constants.SEARCH, rootFolder, base_url)
            self.addContextMenuCommand(commands, 30102, constants.REFRESH, rootFolder, base_url)
            li.addContextMenuItems( commands )
           
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True, totalItems = totalItems)
# finalize UI
        if addon_handle >= 0: 
            xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
            xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
            xbmcplugin.endOfDirectory(addon_handle)
            xbmc.log("parseFolder: End", xbmc.LOGINFO)

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


  def addContextMenuCommand(self, commands, name, mode, url, arg3 = ''):
        if arg3 == '':
          runner = "RunScript(plugin.video.vdr.recordings, " + str(mode) + ", \"" + str(url) + "\")"
        else:
          runner = "RunScript(plugin.video.vdr.recordings, " + str(mode) + ", \"" + str(url) + "\", \"" + str(arg3) + "\")"
#       xbmc.log("runner=" + str(runner), xbmc.LOGINFO)
        name_text = self.addon.getLocalizedString(name)
        commands.append(( name_text, runner, ))

def build_url(base_url, query):
        return base_url + '?' + urllib.parse.urlencode(query)
