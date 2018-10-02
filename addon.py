# Copyright: GNU GPLv3

import sys
import os
import urllib
import urlparse
import xbmcgui
import xbmcplugin
import xbmc
import xbmcaddon
import string

from resources.lib.vdrrecordingfolder import VdrRecordingFolder

#xbmc.log("sys.argv" + str(sys.argv), xbmc.LOGERROR)
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

args = urlparse.parse_qs(sys.argv[2][1:])
if addon_handle > 0:
  rootFolder = xbmcplugin.getSetting(addon_handle, "rootFolder")
  if not os.path.isdir(rootFolder):
    xbmc.executebuiltin(
      'Notification(Folder ' + rootFolder
       + ' does not exist.,Please select correct video folder in stettings., 50000)')

 

xbmcplugin.setContent(addon_handle, 'movies')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]
    
def GUIEditExportName(name):
    kb = xbmc.Keyboard('', 'Enter search string', True)
    kb.setHiddenInput(False)
    kb.doModal()
    name = kb.getText()
    return(name) 

mode = args.get('mode', ['folder'])

if mode[0] == 'folder':
    currentFolder = args.get('currentFolder', [rootFolder])[0]
# Add special (search) folder
    url = build_url({'mode': 'search', 'currentFolder': currentFolder})
    li = xbmcgui.ListItem(" search", iconImage = 'DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

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
            if vdrRecordingFolder.title <> firstTitle:
              onlySameTitle = False
          li = vdrRecordingFolder.getListitem()
          url = vdrRecordingFolder.getStackUrl()

#         xbmc.log("stack url= " + str(url), xbmc.LOGERROR)            
          xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=False)
        else:
          if len(subfolders) > 0:
            onlySameTitle = False
            url = build_url({'mode': 'folder', 'currentFolder': path})
            name = fileN.replace('_', ' ')
            li = xbmcgui.ListItem(name, iconImage = 'DefaultFolder.png')
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)

    if onlySameTitle:
      xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
    else:
      xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
      xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
#     xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
    xbmcplugin.endOfDirectory(addon_handle)

if mode[0] == 'search':
  currentFolder = args.get('currentFolder', [rootFolder])[0]
# Add special (search) folder
  url = build_url({'mode': 'search', 'currentFolder': currentFolder})
  li = xbmcgui.ListItem(" search", iconImage = 'DefaultFolder.png')
  xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)
  searchList = []
  for dirName, subdirList, fileList in os.walk(rootFolder, followlinks = True):
    if os.path.splitext(dirName)[1] == ".rec":
      vdrRecordingFolder = VdrRecordingFolder(dirName)
      searchList.append([dirName, string.lower(vdrRecordingFolder.title)])
  searchString = GUIEditExportName("Enter search string")
  xbmc.log("searchString " + str(searchString), xbmc.LOGERROR)
  searchStringL = string.lower(searchString)
  for Recording in searchList:
    if string.find(Recording[1], searchStringL) >= 0:
          vdrRecordingFolder = VdrRecordingFolder(Recording[0])
          li = vdrRecordingFolder.getListitem()
          url = vdrRecordingFolder.getStackUrl()
          xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=False)
  xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
  xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATEADDED)
  xbmcplugin.endOfDirectory(addon_handle)
