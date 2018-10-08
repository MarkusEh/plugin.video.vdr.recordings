# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import string
import xbmcgui
import xbmc
import xbmcplugin
from vdrrecordingfolder import VdrRecordingFolder
from kfolder import kFolder
import constants

def get_immediate_subdirectories(a_dir):
    try:
        return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]
    except:
        pass
        return []


class kodiLibrary:
    def __init__(self, baseFolderVDR):
        self.baseFolderVDR = baseFolderVDR
        self.basePath = xbmc.translatePath(
            "special://userdata/addon_data/plugin.video.vdr.recordings")
        self.Movies = os.path.join(self.basePath, "Movies")
        if not os.path.exists(self.Movies): os.makedirs(self.Movies)
        self.TV_shows = os.path.join(self.basePath, "TV shows")
        if not os.path.exists(self.TV_shows): os.makedirs(self.TV_shows)
        self.Music_videos = os.path.join(self.basePath, "Music videos")
        if not os.path.exists(self.Music_videos): os.makedirs(self.Music_videos)

    def addAllRecordings(self, currentFolderVdr):
        onlySameTitle = True
        firstTitle = None
        recList = []
        for fileN in os.listdir(currentFolderVdr):
          path = os.path.join(currentFolderVdr, fileN)
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
              recList.append(vdrRecordingFolder)
            else:
              if len(subfolders) > 0:
                onlySameTitle = False
                self.addAllRecordings(path)
# find folder where we add the strm files
        oFolder = kFolder(currentFolderVdr)
        relPath = currentFolderVdr[len(self.baseFolderVDR):]
        if onlySameTitle and len(recList) > 1:
            contentType = oFolder.getContentType(constants.TV_SHOWS)
        else:
            contentType = oFolder.getContentType(constants.MOVIES)
        
        if contentType == constants.TV_SHOWS:
            libPath = os.path.join(self.TV_shows, relPath)
        elif contentType == constants.MUSIC_VIDEOS:
            libPath = os.path.join(self.Music_videos, relPath)
        else:
            libPath = os.path.join(self.Movies, relPath)                        

        for rec in recList:
            rec.addRecordingToLibrary(libPath)