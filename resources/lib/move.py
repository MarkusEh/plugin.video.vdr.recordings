# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import sys
import os
import shutil
import threading
import xbmc
import xbmcgui
import xbmcvfs

src = sys.argv[1]
dest = sys.argv[2]
final = sys.argv[3]
pDialog = xbmcgui.DialogProgressBG()

def GetFolderSize(path):
    TotalSize = 0.0
    dirs, files = xbmcvfs.listdir(path)
    for dir in dirs:
        TotalSize = TotalSize + GetFolderSize(os.path.join(path, dir))
    
    for file in files:
        TotalSize = TotalSize + xbmcvfs.Stat(os.path.join(path, file)).st_size()
    return TotalSize


def move(t1, t2, tz, t3):
  xbmcvfs.rename(t1, tz)
  xbmcvfs.rename(tz, t3)
  xbmc.executebuiltin("Container.Refresh")   


tz = os.path.join(dest, os.path.split(src)[1])
t = threading.Thread(target=move, args=(src, dest, tz, final))
t.start()
pDialog.create('Move recording', src)

while t.isAlive() and not xbmc.abortRequested:
    xbmc.sleep(2000)
    s = GetFolderSize(src)
    d = GetFolderSize(tz)
    if d == 0:
        d = GetFolderSize(final)
    if s + d != 0:    
        pDialog.update(int(d * 100 / (s+d)))

pDialog.close()  