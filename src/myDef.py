#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 25 00:22:16 2017

@author: coolshou
"""
import pyqode_i18n
import locale

def i18n(s):
    lang, encode = locale.getdefaultlocale()
    return pyqode_i18n.tr(s, lang=lang)

