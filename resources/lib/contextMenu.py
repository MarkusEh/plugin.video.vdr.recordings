# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import sys
import subprocess
import os
import shutil
import threading
import urllib
import time
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import json
import kfolder
import vdrrecordingfolder
import constants

def GUIEditExportName(name):
    kb = xbmc.Keyboard('', name, False)
    kb.doModal()
    if kb.isConfirmed():
      return kb.getText()
    else:
      return None

def recursive_delete_dir(fullpath):
    '''helper to recursively delete a directory, including all files'''
    dirs, files = xbmcvfs.listdir(fullpath)
    for file in files:
        xbmcvfs.delete(os.path.join(fullpath, file))
    for directory in dirs:
        recursive_delete_dir(os.path.join(fullpath, directory))
    xbmcvfs.rmdir(fullpath)

def recursive_delete_empty_dirs(fullpath):
    '''helper to recursively delete all empty directories'''
    empty = True
    dirs, files = xbmcvfs.listdir(fullpath)
    for directory in dirs:
        empty_this = recursive_delete_empty_dirs(os.path.join(fullpath, directory))
        empty = empty and empty_this
    if not empty or len(files) > 0: return False
    xbmcvfs.rmdir(fullpath)
    return True 

def recursive_add_files(fullpath, files_dict):
    '''helper to recursively add all files in directory'''
# note: ignore .edl files
    dirs, files = xbmcvfs.listdir(fullpath)
    for file in files:
        if os.path.splitext(file)[1] != '.edl':
          files_dict[os.path.join(fullpath, file)] = True
    for directory in dirs:
        recursive_add_files(os.path.join(fullpath, directory), files_dict)
    return

def waitForScan():
  jsonCommand = {'jsonrpc': '2.0', 'method': 'XBMC.GetInfoBooleans', 'params': {"booleans":["Library.IsScanningVideo"]}, 'id': "waitForScan"}
  while True:
    time.sleep (1)
    result = xbmc.executeJSONRPC(json.dumps(jsonCommand))
    jresult = json.loads(result)
    if "error" in jresult or "result" not in jresult:
       xbmc.log("Error waiting for scan, error = " + str(result), xbmc.LOGERROR)
       return
    bresult = jresult["result"]["Library.IsScanningVideo"]
    if not bresult: return

def getRootFolder():
    rootFolder = xbmcaddon.Addon('plugin.video.vdr.recordings').getSetting("rootFolder")
    lastChar = rootFolder[-1] 
    if lastChar == '/' or lastChar == '\\':
        rootFolder = rootFolder[:-1]
    return rootFolder

def scanIfRequired(rootFolder, changedDirs, text):
    for dir in changedDirs.keys():
      if dir.find(rootFolder) >= 0:
        waitForScan()
        xbmc.log("ADDALLTOLIBRARY, VideoLibrary.Scan, " + text + " dir = " + str(rootFolder), xbmc.LOGINFO)
        xbmc.executebuiltin('Notification(VDR Recordings, ' + xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30200) + ' ' + str(os.path.basename(rootFolder)) + ')', False)
        xbmc.executebuiltin('UpdateLibrary(video,'+ str(rootFolder) + ')', True)
        waitForScan()
        return

def scan(rootFolder, dirs, text, forceCompleteScan):
    numChangedFolders = len(dirs.keys() )
    if numChangedFolders == 0: return
    if numChangedFolders > 4 or forceCompleteScan:
# update compleate library
      xbmc.log("ADDALLTOLIBRARY, before scanning all " + text + " folders, number of paths = " + str(numChangedFolders), xbmc.LOGINFO)
      scanIfRequired(rootFolder, dirs, text)
    else:
      xbmc.log("ADDALLTOLIBRARY, before scanning changed " + text + " folders, number of paths = " + str(numChangedFolders), xbmc.LOGINFO)
      xbmc.executebuiltin('Notification(VDR Recordings, ' + xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30201) + ' ' + str(os.path.basename(rootFolder)) + ')', False)
      for dir in dirs.keys():
# new files -> update library
        waitForScan()
        xbmc.log("ADDALLTOLIBRARY, VideoLibrary.Scan, dir = " + str(dir), xbmc.LOGINFO)
        xbmc.executebuiltin('UpdateLibrary(video,'+ str(dir) + ')', True)
        waitForScan()
    xbmc.log("ADDALLTOLIBRARY, after scanning changed " + text + " folders", xbmc.LOGINFO)
    xbmc.executebuiltin('Notification(VDR Recordings, ' + xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30202) + ' ' + str(os.path.basename(rootFolder)) + ')', False)

def check_dir_not_exists(dir, context, messageNumber):
    if not xbmcvfs.exists(dir + "/"): return True
    xbmc.log("ERROR: " + dir + " already exists!, context: " + context, xbmc.LOGERROR)
    xbmc.executebuiltin('Notification(VDR Recordings, ' + xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30224) + ')', False)
    return False

def move_dir(source, destination):
  xbmc.log("contextMenu move_dir, source = " + source + " destination = " + destination, xbmc.LOGINFO)
  if not xbmcvfs.exists(source + "/"):
    xbmc.log("ERROR: contextMenu move_dir, source = " + source + " does not exist!", xbmc.LOGERROR)
    return False
  if xbmcvfs.exists(destination + "/"):
    xbmc.log("ERROR: contextMenu move_dir, destination = " + destination + " already exists!", xbmc.LOGERROR)
    return False
  if xbmcvfs.rename(source, destination) == True:
    return True
  if source.startswith('/') and destination.startswith('/'):
    try:
      shutil.move(source, destination)
      return True
    except Error as err:
      xbmc.log("ERROR contextMenu move_dir, shutil.move, source = " + source + " destination = " + destination, xbmc.LOGERROR)
      return False
  return False

def move(src, t1, t2, final):
  if move_dir(src, t1) == False: return
  xbmc.executebuiltin("Container.Refresh")       
  if move_dir(t1 , t2) == False:
    move_dir(t1, src)
    return
  if move_dir(t2 , final) == False:
    if move_dir(t2, t1): move_dir(t1, src)
    return

def GetFolderSize(path):
    TotalSize = 0.0
    dirs, files = xbmcvfs.listdir(path)
    for dir in dirs:
      TotalSize = TotalSize + GetFolderSize(os.path.join(path, dir))

    for file in files:
      TotalSize = TotalSize + xbmcvfs.Stat(os.path.join(path, file)).st_size()
    return TotalSize

#xbmc.log("contextMenu: sys.argv=" + str(sys.argv), xbmc.LOGERROR)
mode = sys.argv[1]
#xbmc.log("mode=" + str(mode), xbmc.LOGERROR)

if mode == constants.ADDALLTOLIBRARY:
    rootFolder = sys.argv[2]
    base_url   = sys.argv[3]
    xbmc.log("Start of ADDALLTOLIBRARY, rootFolder=" + str(rootFolder), xbmc.LOGINFO)
    xbmc.executebuiltin('Notification(VDR Recordings, ' + xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30109) + ')', False)
# create list of old files
    old_files = {}
    recursive_add_files(constants.LIBRARY_MOVIES, old_files)
    recursive_add_files(constants.LIBRARY_TV_SHOWS, old_files)
    recursive_add_files(constants.LIBRARY_MUSIC_VIDEOS, old_files)
# make directories (if required)
    xbmcvfs.mkdirs(constants.LIBRARY_MOVIES)
    xbmcvfs.mkdirs(constants.LIBRARY_TV_SHOWS)
    xbmcvfs.mkdirs(constants.LIBRARY_MUSIC_VIDEOS)
# add current (new) files
    new_files = {}
    xbmc.log("ADDALLTOLIBRARY, before adding all files", xbmc.LOGINFO)
    kfolder.kFolder(rootFolder).parseFolder(-10, base_url, rootFolder, new_files)
    xbmc.log("ADDALLTOLIBRARY, after adding all files", xbmc.LOGINFO)
## compare list of old files with list of new files, clean up library for files which do no longer exist
    for file in old_files.keys() - new_files.keys():
# files do no longer exist -> delete
      xbmcvfs.delete(file)
      file_base, ext = os.path.splitext(file)
      if ext != ".strm" and ext != ".nfo": xbmcvfs.delete(file_base + ".edl")
# delete all empty directries
    recursive_delete_empty_dirs(constants.LIBRARY_MOVIES)
    recursive_delete_empty_dirs(constants.LIBRARY_TV_SHOWS)
    recursive_delete_empty_dirs(constants.LIBRARY_MUSIC_VIDEOS)
# clean up library
    xbmc.log("ADDALLTOLIBRARY, before clean up library", xbmc.LOGINFO)
    xbmc.executebuiltin('Notification(VDR Recordings, ' + xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30203) + ')', False)
    xbmc.executebuiltin('CleanLibrary(video,false)', True)
# we cannot scrap / scan files. Create a list of dirs (don't scan the same dir 2 times ...)
    dirs = {}
    for file in new_files.keys() - old_files.keys():
      xbmc.log("ADDALLTOLIBRARY, new file: " + str(file), xbmc.LOGINFO)
      dirs[os.path.dirname(file)] = True
    dirs_movies = {}
    dirs_tv_shows = {}
    dirs_music_videos = {}
# create list of dirs belonging to each of LIBRARY_MOVIES, LIBRARY_TV_SHOWS, LIBRARY_MUSIC_VIDEOS
    for dir in dirs.keys():
      xbmc.log("ADDALLTOLIBRARY, new folder: " + str(dir), xbmc.LOGINFO)
      if dir.find(constants.LIBRARY_MOVIES) >= 0: dirs_movies[dir] = True
      if dir.find(constants.LIBRARY_TV_SHOWS) >= 0: dirs_tv_shows[dir] = True
      if dir.find(constants.LIBRARY_MUSIC_VIDEOS) >= 0: dirs_music_videos[dir] = True
# special check for tv shows: if there is a new tv show (not a new episode), a complete scan is required (KODI bug)
    scanCompleteTvShows = False
    numChangedFolders = len(dirs_tv_shows.keys() )
    if numChangedFolders > 4:
      scanCompleteTvShows = True
    else:
      for dir in dirs_tv_shows.keys():
        existed = False
        for file in old_files.keys():
          if file.find(dir) >= 0:
            existed = True
            break
        if not existed:
          scanCompleteTvShows = True
          break
      if scanCompleteTvShows:
        xbmc.log("ADDALLTOLIBRARY, completely new tv show " + str(dir), xbmc.LOGINFO)
      else:
        xbmc.log("ADDALLTOLIBRARY, no completely new tv show", xbmc.LOGINFO)
              
# update LIBRARY
    scan(constants.LIBRARY_MOVIES, dirs_movies, "movies", False)
    scan(constants.LIBRARY_TV_SHOWS, dirs_tv_shows, "tv shows", scanCompleteTvShows)
    scan(constants.LIBRARY_MUSIC_VIDEOS, dirs_music_videos, "music videos", False)

if mode == constants.TV_SHOWS:
    recordingFolderPath = sys.argv[2]
    k_Folder = kfolder.kFolder(recordingFolderPath)    
    k_Folder.setContentType(constants.TV_SHOWS)

if mode == constants.MOVIES:
    recordingFolderPath = sys.argv[2]
#   xbmc.log("contextMenu, movies" + str(recordingFolderPath), xbmc.LOGINFO)    
    k_Folder = kfolder.kFolder(recordingFolderPath)    
    k_Folder.setContentType(constants.MOVIES)    

if mode == constants.MUSIC_VIDEOS:
    recordingFolderPath = sys.argv[2]
    k_Folder = kfolder.kFolder(recordingFolderPath)    
    k_Folder.setContentType(constants.MUSIC_VIDEOS)   

if mode == constants.EPISODE:
    recordingFolderPath = sys.argv[2]
    episode = sys.argv[3]
    k_Folder = kfolder.kFolder(recordingFolderPath)
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(0, xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30210), str(k_Folder.getEpisode(episode)))
    if d != '':
        k_Folder.setEpisode(int(d))
        xbmc.executebuiltin("Container.Refresh")

if mode == constants.SEASON:
    recordingFolderPath = sys.argv[2]
    season = sys.argv[3]
    k_Folder = kfolder.kFolder(recordingFolderPath)
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(0, xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30211), str(k_Folder.getSeason(season)))
    if d != '':
        k_Folder.setSeason(int(d))
        xbmc.executebuiltin("Container.Refresh")

if mode == constants.YEAR:
    recordingFolderPath = sys.argv[2]
    year = sys.argv[3]
    if int(year) <= 0:
        year = ''
    k_Folder = kfolder.kFolder(recordingFolderPath)
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(0, xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30212), year)
    if d != '':
        k_Folder.setYear(int(d))
        xbmc.executebuiltin("Container.Refresh")


if mode == constants.DELETE:
    recordingFolderPath = sys.argv[2]
    ps = os.path.splitext(recordingFolderPath)
    if ps[1] == ".rec":
# Confirmation dialog
        dialog = xbmcgui.Dialog()
        rf = vdrrecordingfolder.VdrRecordingFolder(recordingFolderPath)
        d = dialog.yesno(xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30220), xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30221) + ' "'
            + rf.title
            + '"?')
        if d == True:    
            recursive_delete_dir(recordingFolderPath)
        xbmc.executebuiltin("Container.Refresh")       

def do_move():
    recordingFolderPath = sys.argv[2]
    if os.path.splitext(recordingFolderPath)[1] == ".rec":
        fp = os.path.split(recordingFolderPath)[0]
    else:
        fp = recordingFolderPath
    (fd, fn) = os.path.split(fp)
    k_Folder = kfolder.kFolder(fd)
    dest = k_Folder.selectFolder(getRootFolder())
    xbmc.log("constants.MOVE, dest = " + str(dest), xbmc.LOGINFO) 
    if dest == None: return
# fp: source file name (with    path)
# fn: source file name (without path)
# dest: Destination folder
# Create the following "helpers" ++++++
#  d1: first  intermediate file, in same file system as source, with extension .move
#  d2: second intermediate file, in same file system as destination, with extension .move
#  dfin: destination file name (with path)
    dfin = os.path.join(dest, fn)
    d1 = fp + ".move"
    d2 = dfin + ".move"
# verify that these don't extist. Note: if any of them exists, something will go wrong. So abort in this case.
    if check_dir_not_exists(dfin, "contextMenu constants.MOVE dfin", 30224) == False: return
    if check_dir_not_exists(d1  , "contextMenu constants.MOVE d1  ", 30224) == False: return
    if check_dir_not_exists(d2  , "contextMenu constants.MOVE d2  ", 30224) == False: return
# now do the move, async
    xbmc.executebuiltin("RunScript(plugin.video.vdr.recordings, " + str(constants.MOVE_INTERNAL) + ", \"" + fp + "\", \"" + d1 + "\", \"" + d2 + "\", \"" + dfin + "\")")

if mode == constants.MOVE:
   do_move()

if mode == constants.MOVE_INTERNAL:
  src = sys.argv[2]
  d1 = sys.argv[3]
  d2 = sys.argv[4]
  final = sys.argv[5]
  pDialog = xbmcgui.DialogProgressBG()

  t = threading.Thread(target=move, args=(src, d1, d2, final))
  t.start()
  pDialog.create(xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30222), src)

  while t.is_alive() and not xbmc.Monitor().abortRequested():
      xbmc.sleep(2000)
      s = GetFolderSize(d1)
      d = GetFolderSize(d2)
      if d == 0:
        d = GetFolderSize(final)
      if s + d != 0:
        pDialog.update(int(d * 100 / (s+d)))

  pDialog.close()

if mode == constants.SEARCH:
    rootFolder = sys.argv[2]
    base_url = sys.argv[3]
    sString = GUIEditExportName(xbmcaddon.Addon('plugin.video.vdr.recordings').getLocalizedString(30223))
    if sString != None:
       p_url = base_url + '?' + urllib.parse.urlencode({'mode': 'search', 'searchString': sString})
#     xbmc.log("p_url=" + str(p_url), xbmc.LOGERROR)
       runner = "ActivateWindow(10025," + str(p_url) + ",return)"
       xbmc.executebuiltin(runner)   
 
if mode == constants.REFRESH:
    xbmc.executebuiltin("Container.Refresh")  

