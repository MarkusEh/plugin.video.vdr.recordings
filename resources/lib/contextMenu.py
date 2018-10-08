# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import sys
import xbmc
from kodilibrary import kodiLibrary
from kfolder import kFolder
import constants

xbmc.log("contextMenu: sys.argv=" + str(sys.argv), xbmc.LOGERROR)
mode = sys.argv[1]

xbmc.log("mode=" + str(mode), xbmc.LOGERROR)

if mode == constants.ADDALLTOLIBRARY:
    rootFolder = sys.argv[2]
    xbmc.log("rootFolder=" + str(rootFolder), xbmc.LOGERROR)
    kodilibrary = kodiLibrary(rootFolder)
    kodilibrary.addAllRecordings(rootFolder)
  
if mode == constants.TV_SHOWS:
    recordingFolderPath = sys.argv[2]
    k_Folder = kFolder(recordingFolderPath)    
    k_Folder.setContentType(constants.TV_SHOWS)

if mode == constants.MOVIES:
    recordingFolderPath = sys.argv[2]
    k_Folder = kFolder(recordingFolderPath)    
    k_Folder.setContentType(constants.MOVIES)    

if mode == constants.MUSIC_VIDEOS:
    recordingFolderPath = sys.argv[2]
    k_Folder = kFolder(recordingFolderPath)    
    k_Folder.setContentType(constants.MUSIC_VIDEOS)    
    
