# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import xbmcvfs

MOVIES = "Movies"
TV_SHOWS = "TV_shows"
MUSIC_VIDEOS = "Music_videos"
ADDALLTOLIBRARY ="AddAllToLibrary"
SEASON = "Season"
EPISODE = "Episode"
YEAR = "Year"
DELETE = "Delete"
RENAME = "Rename"
MOVE = "Move"
MOVE_INTERNAL = "Move_internal"
SEARCH = "Search"
REFRESH = "Refresh"

ADDON_NAME = "plugin.video.vdr.recordings"
BASE_URL = "plugin://" + ADDON_NAME + "/"
LIBRARY_BASEPATH = xbmcvfs.translatePath("special://userdata/addon_data/" + ADDON_NAME)
LIBRARY_MOVIES = os.path.join(LIBRARY_BASEPATH, "Movies/")
LIBRARY_TV_SHOWS = os.path.join(LIBRARY_BASEPATH, "TV shows/")
LIBRARY_MUSIC_VIDEOS = os.path.join(LIBRARY_BASEPATH, "Music videos/")


