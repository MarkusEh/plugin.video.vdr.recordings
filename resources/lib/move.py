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

src = sys.argv[1]
dest = sys.argv[2]
final = sys.argv[3]
pDialog = xbmcgui.DialogProgressBG()

def GetFolderSize(path):
    TotalSize = 0.0
    for item in os.walk(path):
        for file in item[2]:
            try:
                TotalSize = TotalSize + os.path.getsize(os.path.join(item[0], file))
            except:
                print("error with file:  " + os.path.join(item[0], file))
    return TotalSize

def move(t1, t2, tz, t3):
  shutil.move(t1, t2)
  shutil.move(tz, t3)
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