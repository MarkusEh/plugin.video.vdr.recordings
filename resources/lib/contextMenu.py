# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import sys
import os
import shutil
import urllib
import xbmc
import xbmcgui
from kfolder import kFolder
import constants

def GUIEditExportName(name):
    kb = xbmc.Keyboard('', name, False)
    kb.doModal()
    if kb.isConfirmed():
      return kb.getText()
    else:
      return None

#xbmc.log("contextMenu: sys.argv=" + str(sys.argv), xbmc.LOGERROR)
mode = sys.argv[1]
#xbmc.log("mode=" + str(mode), xbmc.LOGERROR)

if mode == constants.ADDALLTOLIBRARY:
    rootFolder = sys.argv[2]
#   xbmc.log("rootFolder=" + str(rootFolder), xbmc.LOGERROR)
    try: shutil.rmtree(constants.LIBRARY_MOVIES)
    except: pass
    try: shutil.rmtree(constants.LIBRARY_TV_SHOWS)
    except: pass
    try: shutil.rmtree(constants.LIBRARY_MUSIC_VIDEOS)
    except: pass
    os.makedirs(constants.LIBRARY_MOVIES)
    os.makedirs(constants.LIBRARY_TV_SHOWS)
    os.makedirs(constants.LIBRARY_MUSIC_VIDEOS)
    kFolder(rootFolder).parseFolder(-10, '', rootFolder)
  
if mode == constants.TV_SHOWS:
    recordingFolderPath = sys.argv[2]
    k_Folder = kFolder(recordingFolderPath)    
    k_Folder.setContentType(constants.TV_SHOWS)

if mode == constants.MOVIES:
    recordingFolderPath = sys.argv[2]
#   xbmc.log("contextMenu, movies" + str(recordingFolderPath), xbmc.LOGERROR)    
    k_Folder = kFolder(recordingFolderPath)    
    k_Folder.setContentType(constants.MOVIES)    

if mode == constants.MUSIC_VIDEOS:
    recordingFolderPath = sys.argv[2]
    k_Folder = kFolder(recordingFolderPath)    
    k_Folder.setContentType(constants.MUSIC_VIDEOS)   

if mode == constants.EPISODE:
    recordingFolderPath = sys.argv[2]
    episode = sys.argv[3]
    k_Folder = kFolder(recordingFolderPath)
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(0, 'Enter episode number', str(k_Folder.getEpisode(episode)))
    if d != '':
        k_Folder.setEpisode(int(d))
        xbmc.executebuiltin("Container.Refresh")

if mode == constants.SEASON:
    recordingFolderPath = sys.argv[2]
    season = sys.argv[3]
    k_Folder = kFolder(recordingFolderPath)
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(0, 'Enter season number', str(k_Folder.getSeason(season)))
    if d != '':
        k_Folder.setSeason(int(d))
        xbmc.executebuiltin("Container.Refresh")

if mode == constants.YEAR:
    recordingFolderPath = sys.argv[2]
    year = sys.argv[3]
    if int(year) <= 0:
        year = ''
    k_Folder = kFolder(recordingFolderPath)
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(0, 'Enter year', year)
    if d != '':
        k_Folder.setYear(int(d))
        xbmc.executebuiltin("Container.Refresh")


if mode == constants.DELETE:
    recordingFolderPath = sys.argv[2]
    ps = os.path.splitext(recordingFolderPath)
    if ps[1] == ".rec":
        os.rename(recordingFolderPath, ps[0] + '.del')
        xbmc.executebuiltin("Container.Refresh")       

if mode == constants.SEARCH:
    rootFolder = sys.argv[2]
    base_url = sys.argv[3]
    sString = GUIEditExportName("Enter search string")
    if sString != None:
       p_url = base_url + '?' + urllib.urlencode({'mode': 'search', 'searchString': sString})
#     xbmc.log("p_url=" + str(p_url), xbmc.LOGERROR)
       runner = "ActivateWindow(10025," + str(p_url) + ",return)"
       xbmc.executebuiltin(runner)   
 
    


