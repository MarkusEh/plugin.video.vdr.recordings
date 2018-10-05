# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3
# pylint: disable=E0401
# Disable import error: E0401

import sys
from resources.lib.main import main

oMain = main(sys.argv)
if oMain.mode == 'folder':
    oMain.modeFolder()

if oMain.mode == 'search':
  oMain.modeSearch()