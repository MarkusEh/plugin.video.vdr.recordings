# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import urlparse
import string
import xbmcgui
import xbmcplugin
import xbmc
import xbmcaddon
import constants

from vdrrecordingfolder import VdrRecordingFolder
from bookmarks import bookmarks
from kfolder import kFolder

    
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

    def modeFolder(self):
        currentFolder = self.args.get('currentFolder', [self.rootFolder])[0]
        kf = kFolder(currentFolder)
        kf.parseFolder(self.addon_handle, self.base_url, self.rootFolder)
# Add special (search) folder
#        url = self.build_url({'mode': 'search', 'currentFolder': currentFolder})
#        li = xbmcgui.ListItem(" search", iconImage = 'DefaultFolder.png')
#        xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=url,
#                                listitem=li, isFolder=True)

    def doSearch(self, searchString):
#        currentFolder = self.args.get('currentFolder', [self.rootFolder])[0]
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

