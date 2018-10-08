# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmc
import xbmcaddon
import string
import constants

from vdrrecordingfolder import VdrRecordingFolder
from bookmarks import bookmarks

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]
    
def GUIEditExportName(name):
    kb = xbmc.Keyboard('', name, True)
    kb.setHiddenInput(False)
    kb.doModal()
    if kb.isConfirmed():
      name = kb.getText()
      return name
    else:
      return None


class main:
    def __init__(self, argv):
        self.argv = argv
        self.base_url = self.argv[0]
        self.addon_handle = int(self.argv[1])
        self.args = urlparse.parse_qs(self.argv[2][1:])
        self.mode = self.args.get('mode', ['folder'])[0]
        if self.addon_handle > 0:
            self.rootFolder = xbmcplugin.getSetting(self.addon_handle, "rootFolder")
            if not os.path.isdir(self.rootFolder):
                xbmc.executebuiltin('Notification(Folder ' + self.rootFolder +
               ' does not exist.,Please select correct video folder in stettings., 50000)')

        xbmcplugin.setContent(self.addon_handle, 'movies')


    def build_url(self, query):
        return self.base_url + '?' + urllib.urlencode(query)

    def addContextMenuCommand(self, commands, name, mode, url):
        script = "special://home/addons/plugin.video.vdr.recordings/resources/lib/contextMenu.py"
        runner = "XBMC.RunScript(" + str(script)+ ", " + str(mode) + ", " + str(url) + ")"
#       xbmc.log("runner=" + str(runner), xbmc.LOGERROR)
        commands.append(( str(name), runner, ))


#if mode[0] == 'folder':
    def modeFolder(self):
        currentFolder = self.args.get('currentFolder', [self.rootFolder])[0]
# Add special (search) folder
#        url = self.build_url({'mode': 'search', 'currentFolder': currentFolder})
#        li = xbmcgui.ListItem(" search", iconImage = 'DefaultFolder.png')
#        xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=url,
#                                listitem=li, isFolder=True)
        onlySameTitle = True
        firstTitle = None
        for fileN in os.listdir(currentFolder):
          path = os.path.join(currentFolder, fileN)
          if os.path.isdir(path):
            subfolders = get_immediate_subdirectories(path)
            if len(subfolders) == 1:
              if os.path.splitext(subfolders[0])[1] == ".rec":
                path = os.path.join(path, subfolders[0])
            if os.path.splitext(path)[1] == ".rec":
              vdrRecordingFolder = VdrRecordingFolder(path)
              if firstTitle == None:
                firstTitle = vdrRecordingFolder.title
              else:
                if vdrRecordingFolder.title != firstTitle:
                  onlySameTitle = False
              vdrRecordingFolder.addDirectoryItem(self.addon_handle)
            else:
              if len(subfolders) > 0:
                onlySameTitle = False
                url = self.build_url({'mode': 'folder', 'currentFolder': path})
                name = fileN.replace('_', ' ')
    
                li = xbmcgui.ListItem(name, iconImage = 'DefaultFolder.png')
# add context menu
                commands = []
                self.addContextMenuCommand(commands, "Set content: TV shows", constants.TV_SHOWS, path)
                self.addContextMenuCommand(commands, "Set content: Music videos", constants.MUSIC_VIDEOS, path)
                self.addContextMenuCommand(commands, "Set content: Movies", constants.MOVIES, path)
                self.addContextMenuCommand(commands, "Add all recordings to Library", constants.ADDALLTOLIBRARY, self.rootFolder)
                li.addContextMenuItems( commands )
           
                xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=url,
                                    listitem=li, isFolder=True)
        if onlySameTitle:
          xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
        else:
          xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    
          xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
    #     xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
        xbmcplugin.endOfDirectory(self.addon_handle)
# if mode[0] == 'search'
    def doSearch(self, searchString):
        currentFolder = self.args.get('currentFolder', [self.rootFolder])[0]
# Add special (search) folder
#        url = self.build_url({'mode': 'search', 'currentFolder': currentFolder})
#        li = xbmcgui.ListItem(" search", iconImage = 'DefaultFolder.png')
#        xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=url,
#                                listitem=li, isFolder=True)
        searchList = []
        for dirName, subdirList, fileList in os.walk(self.rootFolder, followlinks = True):
            if os.path.splitext(dirName)[1] == ".rec":
                vdrRecordingFolder = VdrRecordingFolder(dirName)
                searchList.append([dirName, string.lower(vdrRecordingFolder.title)])

        searchStringL = string.lower(searchString)
        for Recording in searchList:
            if string.find(Recording[1], searchStringL) >= 0:
                vdrRecordingFolder = VdrRecordingFolder(Recording[0])
                vdrRecordingFolder.addDirectoryItem(self.addon_handle)                                
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addSortMethod(self.addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
        xbmcplugin.endOfDirectory(self.addon_handle)

    def modeSearch(self):
        searchStringx = GUIEditExportName("Enter search string")
        if (searchStringx == None):
            self.modeFolder()
        else:
#           xbmc.log("searchString " + str(searchStringx), xbmc.LOGERROR)
            self.doSearch(searchStringx)

