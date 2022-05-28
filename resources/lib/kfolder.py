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
    self.rootFolder = None
    self.addon = xbmcaddon.Addon('plugin.video.vdr.recordings')
    self.contextMenuCommandYearText = self.addon.getLocalizedString(30105)

  def getRootFolder(self):
    if self.rootFolder == None:
      self.rootFolder = self.addon.getSetting("rootFolder")
      lastChar = self.rootFolder[-1] 
      if lastChar == '/' or lastChar == '\\':
        self.rootFolder = self.rootFolder[:-1]
    return self.rootFolder

  def selectFolder(self, rootFolder, ignoreSubfoldersOfThisFolder):
    ignoreThisFolder = self.path.startswith(ignoreSubfoldersOfThisFolder)
    FOLDER_UP = ".."
    THIS_FOLDER = xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30300)
    CREATE_FOLDER = xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30301)
    DELETE_FOLDER = xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30302)
    self.subFolders = []
    if not ignoreThisFolder:
      if self.path != os.path.split(ignoreSubfoldersOfThisFolder)[0]:
        self.subFolders.append(THIS_FOLDER)
      self.subFolders.append(CREATE_FOLDER)
      if len(self.dirs) == 0 and len(self.files) == 0:
        self.subFolders.append(DELETE_FOLDER)
    if self.path != rootFolder:
      self.subFolders.append(FOLDER_UP)
    prefolders = len(self.subFolders)
    if not ignoreThisFolder:
      self.parseFolder(-20, rootFolder, rootFolder, {})
    dialog = xbmcgui.Dialog()
    d = dialog.select(self.path, self.subFolders)
    if d == None: return d
    if d == -1: return None
    if d >= prefolders:
      return kFolder(self.subFolders[d]).selectFolder(rootFolder, ignoreSubfoldersOfThisFolder)
    if self.subFolders[d] == FOLDER_UP:
      return kFolder(os.path.split(self.path)[0]).selectFolder(rootFolder, ignoreSubfoldersOfThisFolder)
    if self.subFolders[d] == THIS_FOLDER:
      return self.path
    if self.subFolders[d] == DELETE_FOLDER:
      if xbmcvfs.rmdir(self.path):
        return kFolder(os.path.split(self.path)[0]).selectFolder(rootFolder, ignoreSubfoldersOfThisFolder)
      else:
        xbmc.log("Error deleting directory " + str(self.path), xbmc.LOGERROR)            
        return self.selectFolder(rootFolder, ignoreSubfoldersOfThisFolder)

    if self.subFolders[d] == CREATE_FOLDER:
      d2 = dialog.input(xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30303) )
      if d2 == "": return self.selectFolder(rootFolder, ignoreSubfoldersOfThisFolder)
      newpath = os.path.join(self.path, d2)
      xbmcvfs.mkdirs(newpath)
      if not xbmcvfs.exists(newpath + "/"):
        xbmc.log("Error creating directory " + str(newpath), xbmc.LOGERROR)            
        return self.selectFolder(rootFolder, ignoreSubfoldersOfThisFolder)
      return kFolder(newpath).selectFolder(rootFolder, ignoreSubfoldersOfThisFolder)

    xbmc.log("Error in selectFolder, d= " + str(d), xbmc.LOGERROR)            
    return None


  def parseFolder(self, addon_handle, base_url, rootFolder, current_files):
        if addon_handle >= 0: xbmc.log("parseFolder: Start, path: " + str(self.path), xbmc.LOGINFO)
        onlySameTitle = True
        firstTitle = None
        recordingsList = []
        subfolderList = []
        for rec_name in self.dirs:
          if rec_name.endswith(".move"): continue
          path = os.path.join(self.path, rec_name)
          rec_timestamps, files = xbmcvfs.listdir(path)
          subContainsMovFolders = False
          subContainsNonMovFolders = False
          subfolder = True
          for rec_timestamp in rec_timestamps:
            if rec_timestamp.endswith(".move"):
              if rec_timestamp.endswith(".rec.move"): subContainsMovFolders = True
              continue
            subContainsNonMovFolders = True
            if rec_timestamp.endswith(".rec"):
              subfolder = False
              vdrRecordingFolder = vdrrecordingfolder.VdrRecordingFolder(os.path.join(path,rec_timestamp))
              if firstTitle == None:
                firstTitle = rec_name
              else:
                if rec_name != firstTitle:
                  onlySameTitle = False
              recordingsList.append(vdrRecordingFolder)
          if subfolder and (subContainsNonMovFolders or not subContainsMovFolders):
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
              TV_show_name = os.path.basename(self.path)
            season = 1
            episode = 0
            for vdrRecordingFolder in sorted(recordingsList, key=lambda rec: rec.sortRecordingTimestamp):
              year = vdrRecordingFolder.getYearR()
              finalContentType = vdrRecordingFolder.getContentType(contentType)
              if finalContentType == constants.TV_SHOWS:
# TV shows
                final_TV_show_name = vdrRecordingFolder.getName(TV_show_name)
                if year > 0: final_TV_show_name = final_TV_show_name + ' (' + str(year) + ')'
                libPath = os.path.join(constants.LIBRARY_TV_SHOWS, final_TV_show_name)
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

                se = 'S' + str(season).zfill(2) + 'E' + str(episode).zfill(2)
                vdrRecordingFolder.title = vdrRecordingFolder.title + ' ' + se
                if addon_handle == -10:
                    filename = vdrRecordingFolder.getEpisodeName(vdrRecordingFolder.subtitle)
                    if filename == "":
                      filename =  os.path.split(os.path.split(vdrRecordingFolder.path)[0])[1].replace('_', ' ').strip()
                      if filename[:1] == "%": filename = filename[1:]
                    vdrRecordingFolder.addRecordingToLibrary(libPath, filename + ' ' + se, current_files, base_url, False, vdrRecordingFolder.getDbUrl() )
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
                    filename =  vdrRecordingFolder.getName(vdrRecordingFolder.title)
                    if year > 0:
                       filename = filename + ' (' + str(year) + ')'
                    vdrRecordingFolder.addRecordingToLibrary(libPath, filename, current_files, base_url, True, vdrRecordingFolder.getDbUrl() )
                elif addon_handle >= 0:
                  if year > 0:
                     vdrRecordingFolder.title = vdrRecordingFolder.title + ' (' + str(year) + ')'
                  commands = []
                  self.addContextMenuCommandYear(commands, vdrRecordingFolder.path, year)
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
# add context menu for folders
            commands = []
            self.addContextMenuCommand(commands, 30106, constants.TV_SHOWS, pathN[0])
            self.addContextMenuCommand(commands, 30107, constants.MUSIC_VIDEOS, pathN[0])
            self.addContextMenuCommand(commands, 30108, constants.MOVIES, pathN[0])
            self.addContextMenuCommand(commands, 30109, constants.ADDALLTOLIBRARY, rootFolder, base_url)
            self.addContextMenuCommand(commands, 30111, constants.MOVE, pathN[0])
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

  def addContextMenuCommandYear(self, commands, url, year):
#   runner = "RunScript(plugin.video.vdr.recordings, Year, \"" + str(url) + "\", \"" + str(year) + "\")"
#   runner = "RunScript(plugin.video.vdr.recordings, " + str(constants.YEAR) + ", \"" + str(url) + "\", \"" + str(year) + "\")"
#   xbmc.log("runner=" + str(runner), xbmc.LOGINFO)
    commands.append((self.contextMenuCommandYearText, "RunScript(plugin.video.vdr.recordings, Year, \"" + str(url) + "\", \"" + str(year) + "\")", ))

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
