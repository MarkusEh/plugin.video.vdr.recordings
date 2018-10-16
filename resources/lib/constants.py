# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import os
import xbmc

MOVIES = "Movies"
TV_SHOWS = "TV_shows"
MUSIC_VIDEOS = "Music_videos"
ADDALLTOLIBRARY ="AddAllToLibrary"
SEASON = "Season"
EPISODE = "Episode"
YEAR = "Year"
DELETE = "Delete"
SEARCH = "Search"

LIBRARY_BASEPATH = xbmc.translatePath(
        "special://userdata/addon_data/plugin.video.vdr.recordings")
LIBRARY_MOVIES = os.path.join(LIBRARY_BASEPATH, "Movies")
LIBRARY_TV_SHOWS = os.path.join(LIBRARY_BASEPATH, "TV shows")
LIBRARY_MUSIC_VIDEOS = os.path.join(LIBRARY_BASEPATH, "Music videos")


