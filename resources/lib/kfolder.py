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
import folder
import vdrrecordingfolder

class kFolder(folder.cFolder):

  def __init__(self, folder, filesFoldersProvided = False, dirs = [], files = []):
    super().__init__(folder, filesFoldersProvided, dirs, files)
    self.addon = xbmcaddon.Addon('plugin.video.vdr.recordings')
    self.rootFolder = None
    self.getRootFolder()
    self.contextMenuCommandYearText = self.addon.getLocalizedString(30105)
    self.contextMenuCommandRefreshText = self.addon.getLocalizedString(30102)

  def getRootFolder(self):
    if self.rootFolder == None:
      self.rootFolder = self.addon.getSetting("rootFolder")
      lastChar = self.rootFolder[-1] 
      if lastChar == '/' or lastChar == '\\':
        self.rootFolder = self.rootFolder[:-1]
    return self.rootFolder

  def selectFolder(self, ignoreSubfoldersOfThisFolder):
    ignoreThisFolder = self.path.startswith(ignoreSubfoldersOfThisFolder)
    FOLDER_UP = ".."
    THIS_FOLDER = self.addon.getLocalizedString(30300)
    CREATE_FOLDER = self.addon.getLocalizedString(30301)
    DELETE_FOLDER = self.addon.getLocalizedString(30302)
    self.subFolders = []
    if not ignoreThisFolder:
      if self.path != os.path.split(ignoreSubfoldersOfThisFolder)[0]:
        self.subFolders.append(THIS_FOLDER)
      self.subFolders.append(CREATE_FOLDER)
      if len(self.dirs) == 0 and len(self.files) == 0:
        self.subFolders.append(DELETE_FOLDER)
    if self.path != self.rootFolder:
      self.subFolders.append(FOLDER_UP)
    prefolders = len(self.subFolders)
    if not ignoreThisFolder:
      self.parseFolder(-20, {})
    if ignoreSubfoldersOfThisFolder in self.subFolders: self.subFolders.remove(ignoreSubfoldersOfThisFolder)
    dialog = xbmcgui.Dialog()
    d = dialog.select(self.path, self.subFolders)
    if d == None: return d
    if d == -1: return None
    if d >= prefolders:
      return kFolder(self.subFolders[d]).selectFolder(ignoreSubfoldersOfThisFolder)
    if self.subFolders[d] == FOLDER_UP:
      return kFolder(os.path.split(self.path)[0]).selectFolder(ignoreSubfoldersOfThisFolder)
    if self.subFolders[d] == THIS_FOLDER:
      return self.path
    if self.subFolders[d] == DELETE_FOLDER:
      if xbmcvfs.rmdir(self.path):
        return kFolder(os.path.split(self.path)[0]).selectFolder(ignoreSubfoldersOfThisFolder)
      else:
        xbmc.log("Error deleting directory " + str(self.path), xbmc.LOGERROR)            
        return self.selectFolder(ignoreSubfoldersOfThisFolder)

    if self.subFolders[d] == CREATE_FOLDER:
      d2 = dialog.input(self.addon.getLocalizedString(30303) )
      if d2 == "": return self.selectFolder(ignoreSubfoldersOfThisFolder)
      newpath = os.path.join(self.path, d2)
      xbmcvfs.mkdirs(newpath)
      if not xbmcvfs.exists(newpath + "/"):
        xbmc.log("Error creating directory " + str(newpath), xbmc.LOGERROR)            
        return self.selectFolder(ignoreSubfoldersOfThisFolder)
      return kFolder(newpath).selectFolder(ignoreSubfoldersOfThisFolder)

    xbmc.log("Error in selectFolder, d= " + str(d), xbmc.LOGERROR)            
    return None


  def parseFolder(self, addon_handle, current_files):
        if addon_handle >= 0: xbmc.log("parseFolder: Start, path: {}".format(str(self.path)), xbmc.LOGINFO)
        contentType = self.getContentType(constants.MOVIES)
        self.libPathMovies = self.getLibPath(constants.MOVIES)          
        onlySameTitle = True
        firstTitle = None
        totalItems = 0
        recordingsList = []
        recordingsListTV_shows = []
        subfolderList = []
        for rec_name in self.dirs:
          if rec_name.endswith(".move"): continue
          path = os.path.join(self.path, rec_name)
          rec_timestamps, files = xbmcvfs.listdir(path)
          if addon_handle != -20 and contentType == constants.MOVIES and len(rec_timestamps) == 1 and rec_timestamps[0].endswith(".rec"):
            totalItems = totalItems  + 1
            vdrRecordingFolder = vdrrecordingfolder.VdrRecordingFolder(os.path.join(path,rec_timestamps[0]))
            if vdrRecordingFolder.getContentType(contentType) == constants.TV_SHOWS:
              recordingsListTV_shows.append(vdrRecordingFolder)
            else:
              self.addMovie(vdrRecordingFolder, addon_handle, totalItems, current_files)
            if firstTitle == None:
              firstTitle = rec_name
            else:
              if rec_name != firstTitle:
                onlySameTitle = False
          else:
            subfolder = True
            for rec_timestamp in rec_timestamps:
              if rec_timestamp.endswith(".del") or rec_timestamp.endswith(".rec.move"):
                subfolder = False
              elif rec_timestamp.endswith(".rec"):
                subfolder = False
#               vdrRecordingFolder = vdrrecordingfolder.VdrRecordingFolder(os.path.join(path,rec_timestamp))
#               recordingsList.append(vdrRecordingFolder)
                recordingsList.append(os.path.join(rec_name, rec_timestamp))
                if firstTitle == None:
                  firstTitle = rec_name
                else:
                  if rec_name != firstTitle:
                    onlySameTitle = False
            if subfolder:
               subfolderList.append([path, rec_name])

        totalItems = len(recordingsList) + len(subfolderList)
        if addon_handle >= 0:
          xbmc.log("parseFolder: finished analysing VDR structure, number of recordings: " + str(len(recordingsList)) + " number of folders: " + str(len(subfolderList)), xbmc.LOGINFO)
          xbmc.log("parseFolder: Start add recordings", xbmc.LOGINFO)
        if onlySameTitle and len(recordingsList) > 3:
#           xbmc.log("onlySameTitle: " + str(self.path), xbmc.LOGINFO)
            contentType = self.getContentType(constants.TV_SHOWS)
        else:
            contentType = self.getContentType(constants.MOVIES)

# Recordings
        if contentType == constants.MUSIC_VIDEOS:
          if addon_handle == -10:          
            libPath = self.getLibPath(contentType)
            for rec in recordingsList:
              vdrRecordingFolder = vdrrecordingfolder.VdrRecordingFolder(os.path.join(self.path,rec))
              vdrRecordingFolder.addRecordingToLibrary(libPath, vdrRecordingFolder.title, current_files, False, "")
          elif addon_handle >= 0:
            for rec in recordingsList:
              vdrRecordingFolder = vdrrecordingfolder.VdrRecordingFolder(os.path.join(self.path,rec))
              commands = []
              self.addContextMenuCommand(commands, 30100, constants.DELETE, vdrRecordingFolder.path)
              self.addContextMenuCommand(commands, 30101, constants.MOVE, vdrRecordingFolder.path)
              vdrRecordingFolder.addDirectoryItem(addon_handle, commands, totalItems)
        else:
# movie or TV show
          for rec in recordingsList:
            vdrRecordingFolder = vdrrecordingfolder.VdrRecordingFolder(os.path.join(self.path,rec))
            finalContentType = vdrRecordingFolder.getContentType(contentType)
            if finalContentType == constants.TV_SHOWS:
              recordingsListTV_shows.append(vdrRecordingFolder)
            else:
              self.addMovie(vdrRecordingFolder, addon_handle, totalItems, current_files)
# TV shows
          if onlySameTitle:
            TV_show_name = firstTitle
          else:
            TV_show_name = os.path.basename(self.path)
          season = 1
          episode = 0
          for vdrRecordingFolder in sorted(recordingsListTV_shows, key=lambda rec: rec.sortRecordingTimestamp):
              year = vdrRecordingFolder.getYearR()
              final_TV_show_name = vdrRecordingFolder.getName(TV_show_name)
              if year > 0: final_TV_show_name = "{} ({})".format(final_TV_show_name, str(year) )
              if contentType == constants.TV_SHOWS:
# automatically count episodes, but only if folder is explicitly marked as TV Shows or all recordings have the same name
                season_n = vdrRecordingFolder.getSeason(season)
                if season_n == season:
                  episode = episode + 1
                else:
                  episode = 1
                  season = season_n
              else:
# don't automatically count episodes, use season = 1 and episode = 1 if on other information is available
                season = vdrRecordingFolder.getSeason(1)
                episode = 1
              episode = vdrRecordingFolder.getEpisode(episode)

              se = "S{}E{}".format(str(season).zfill(2), str(episode).zfill(2) )
              vdrRecordingFolder.title = "{} {}".format(vdrRecordingFolder.title, se)
              if addon_handle == -10:
                filename = vdrRecordingFolder.getEpisodeName(vdrRecordingFolder.subtitle)
                if filename == "":
                  filename =  os.path.split(os.path.split(vdrRecordingFolder.path)[0])[1].replace('_', ' ').strip()
                  if filename[:1] == "%": filename = filename[1:]
                libPath = os.path.join(constants.LIBRARY_TV_SHOWS, final_TV_show_name)
                vdrRecordingFolder.addRecordingToLibrary(libPath, "{} {}".format(filename, se), current_files, False, vdrRecordingFolder.getDbUrl() )
              elif addon_handle >= 0:
# add context menu
                commands = []
                self.addContextMenuCommand(commands, 30103, constants.SEASON, vdrRecordingFolder.path, str(season))
                self.addContextMenuCommand(commands, 30104, constants.EPISODE, vdrRecordingFolder.path, str(episode))
                self.addContextMenuCommand(commands, 30100, constants.DELETE, vdrRecordingFolder.path)
                self.addContextMenuCommand(commands, 30101, constants.MOVE, vdrRecordingFolder.path)
                self.addContextMenuCommandRefresh(commands)
                vdrRecordingFolder.addDirectoryItem(addon_handle, commands, totalItems)

# subfolders
        if addon_handle < 0: 
          if addon_handle == -20:
            for pathN in subfolderList:
                self.subFolders.append(pathN[0])
#               xbmc.log("subFolders= " + str(subFolders), xbmc.LOGINFO)
          else:   
            for pathN in subfolderList:
              kFolder(pathN[0]).parseFolder(addon_handle, current_files)
        else:
          xbmc.log("parseFolder: Start add folders", xbmc.LOGINFO)
          for pathN in subfolderList:
            url = build_url({'mode': 'folder', 'currentFolder': pathN[0]})
            name = pathN[1].replace('_', ' ')
            li = xbmcgui.ListItem(name, offscreen = True)
            li.setArt({ 'icon' : 'DefaultFolder.png' })
# add context menu for folders
            commands = []
            self.addContextMenuCommand(commands, 30106, constants.TV_SHOWS, pathN[0])
            self.addContextMenuCommand(commands, 30107, constants.MUSIC_VIDEOS, pathN[0])
            self.addContextMenuCommand(commands, 30108, constants.MOVIES, pathN[0])
            self.addContextMenuCommand(commands, 30109, constants.ADDALLTOLIBRARY)
            self.addContextMenuCommand(commands, 30111, constants.MOVE, pathN[0])
            self.addContextMenuCommand(commands, 30110, constants.SEARCH)
            self.addContextMenuCommandRefresh(commands)
            li.addContextMenuItems( commands )
           
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True, totalItems = totalItems)
# finalize UI
        if addon_handle >= 0: 
            xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
            xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
            xbmcplugin.endOfDirectory(addon_handle)
            xbmc.log("parseFolder: End", xbmc.LOGINFO)


  def addMovie(self, vdrRecordingFolder, addon_handle, totalItems, current_files):
    year = vdrRecordingFolder.getYearR()
    if addon_handle == -10:
      filename =  vdrRecordingFolder.getName(vdrRecordingFolder.title)
      if year > 0:
         filename = "{} ({})".format(filename, str(year) )
      vdrRecordingFolder.addRecordingToLibrary(self.libPathMovies, filename, current_files, True, vdrRecordingFolder.getDbUrl() )
    elif addon_handle >= 0:
      if year > 0:
         vdrRecordingFolder.title = "{} ({})".format(vdrRecordingFolder.title, str(year) )
      commands = []
      self.addContextMenuCommandYear(commands, vdrRecordingFolder.path, year)
      self.addContextMenuCommand(commands, 30100, constants.DELETE, vdrRecordingFolder.path)
      self.addContextMenuCommand(commands, 30101, constants.MOVE, vdrRecordingFolder.path)
      self.addContextMenuCommandRefresh(commands)
      vdrRecordingFolder.addDirectoryItem(addon_handle, commands, totalItems)

  def getLibPath(self, contentType):
    relPath = self.path[len(self.rootFolder)+1:]
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

  def addContextMenuCommandYear(self, commands, url, year):
    runner = "RunScript(plugin.video.vdr.recordings, Year, \"{}\", \"{}\")".format(str(url), str(year) )
    commands.append((self.contextMenuCommandYearText, runner, ))

  def addContextMenuCommandRefresh(self, commands):
    commands.append((self.contextMenuCommandRefreshText, "RunScript(plugin.video.vdr.recordings, Refresh)", ))

  def addContextMenuCommand(self, commands, name, mode, url = '', arg3 = ''):
        if url == '':
          runner = "RunScript(plugin.video.vdr.recordings, {})".format(str(mode))
        elif arg3 == '':
          runner = "RunScript(plugin.video.vdr.recordings, {}, \"{}\")".format(str(mode), str(url))
        else:
          runner = "RunScript(plugin.video.vdr.recordings, {}, \"{}\", \"{}\")".format(str(mode), str(url), str(arg3))
#       xbmc.log("runner=" + str(runner), xbmc.LOGINFO)
        name_text = self.addon.getLocalizedString(name)
        commands.append(( name_text, runner, ))

def build_url(query):
  return "{}?{}".format(constants.BASE_URL, urllib.parse.urlencode(query))
