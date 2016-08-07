#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This setup script build a frozen distribution of the application (with the
python interpreter and 3rd party libraries embedded) for Windows.

Run the following command to freeze the app (the frozen executable can be
found in the bin folder::

    python freeze_setup.py build

"""
import os
import sys
from cx_Freeze import setup, Executable
import shutil
from pyqode.core.api.syntax_highlighter import get_all_styles
from pyqode.python.backend import server

# from src.uPyIDE import __version__

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import uPyIDE

# automatically build when run without arguments
if len(sys.argv) == 1:
    sys.argv.append("build")

# collect pygments styles
pygments_styles = []
for s in get_all_styles():
    module = 'pygments.styles.%s' % s.replace('-', '_')
    try:
        __import__(module)
    except ImportError:
        pass
    else:
        pygments_styles.append(module)
print('pygment styles', pygments_styles)


# Build options
options = {
    "excludes": ["PyQt5.uic.port_v3", "tcltk", "jedi"],
    "namespace_packages": ["pyqode"],
    "include_msvcr": True,
    "build_exe": "bin",
    "includes": ["pkg_resources", "PySide.QtCore", 'PySide.QtGui',
                 'PySide.QtNetwork', 'pydoc'] + pygments_styles
}


# Run the cxFreeze setup
setup(name="uPyIDE",
      version='1.0',  #__version__,
      options={"build_exe": options},
      executables=[
          Executable(uPyIDE.__file__.replace('.pyc', '.py'),
                     targetName="uPyIDE.exe",
                     packages='uPyIDE',
                     icon='share/uPyIDE/images/uPyIDE.ico',
                     base="Win32GUI"),
          Executable(server.__file__.replace('.pyc', '.py'),
                     targetName="server.exe")])


# NOTE: if you are using PyQt5, you will have to copy libEGL.dll manually
try:
    import PyQt5
except ImportError:
    pass  # pyqt4 or pyqside
else:
    shutil.copy(os.path.join(os.path.dirname(PyQt5.__file__), 'libEGL.dll'), 'bin')


# cx_freeze has some issues embedding the jedi package, let's do it ourself
import jedi
try:
    shutil.copytree(os.path.dirname(jedi.__file__), 'bin/jedi')
except OSError:
    pass

# also copy server.py in order to be able to run on external interpreters
shutil.copy(server.__file__, 'bin')
