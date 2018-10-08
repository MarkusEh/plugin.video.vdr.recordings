# -*- coding: utf-8 -*-
# Copyright: GNU GPLv3

import sys
from main import main

oMain = main(sys.argv)
if oMain.mode == 'folder':
    oMain.modeFolder()

if oMain.mode == 'search':
  oMain.modeSearch()