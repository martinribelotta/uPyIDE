#!/usr/bin/env python3
import tendo.singleton
import os
import re
import sys
import base64
import glob

import pyqode.python.backend.server as server
import pyqode.python.widgets as widgets
import pyqode.core.widgets as wcore
import pyqode.qt.QtCore as QtCore
import pyqode.qt.QtWidgets as QtWidgets
import pyqode.qt.QtGui as QtGui
import pyqode_i18n
import termWidget
import xml.etree.ElementTree as ElementTree
from docutils.parsers.rst.directives import path


me = tendo.singleton.SingleInstance()

__version__ = '1.0'


def i18n(s):
    return pyqode_i18n.tr(s)

    
def executable_path():
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(sys.argv[0])

def share():
    return os.path.abspath(os.path.join(executable_path(),
                                        '..', 'share', 'uPyIDE'))


def icon(name):
    path = os.path.join(share(), 'images', '{}.png'.format(name))
    return QtGui.QIcon(path)


def backend_interpreter():
    if getattr( sys, 'frozen', False ) :
        return ''
    else:
        return sys.executable


def completion_server():
    if getattr( sys, 'frozen', False ) :
        server_path = os.path.join(executable_path(), 'server.exe')
        print(server_path)
        return server_path
    else:
        return server.__file__


class WidgetSpacer(QtWidgets.QWidget):
    def __init__(self, parent, wmax=None):
        super(WidgetSpacer, self).__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        if wmax:
            self.setMaximumWidth(wmax)


class PortSelector(QtWidgets.QComboBox):
    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)
        self.widget = parent
        portList = termWidget.serial_ports()
        print(portList)
        self.addItems(portList)
        self.currentIndexChanged.connect(self.onChange)
        self.setCurrentIndex(0)
        # self.onChange(0)

    @QtCore.Slot(int)
    def onChange(self, n):
        if self.currentText():
            port = self.currentText()
            self.widget.setPort(port)


class SnipplerWidget(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super(SnipplerWidget, self).__init__(i18n('Snipplets'), parent)
        self.setWindowTitle(i18n("Snipplets"))
        self.snippletView = QtWidgets.QListWidget(self)
        self.setWidget(self.snippletView)
        self.loadSnipplets()
        self.snippletView.itemDoubleClicked.connect(self._insertToParent)

    def _insertToParent(self, item):
        if self.parent().tabber.active_editor:
            self.parent().tabber.active_editor.insertPlainText(item.toolTip())

    def addSnipplet(self, description, contents):
        item = QtWidgets.QListWidgetItem(self.snippletView)
        item.setText(description)
        item.setToolTip(contents)

    def loadSnippletFrom(self, inp):
        xml = ElementTree.fromstring(inp) if type(inp) is str else \
            ElementTree.parse(inp).getroot()
        for child in xml:
            self.addSnipplet(child.attrib["name"], child.text)

    def loadCodeSnipplet(self, source):
        with open(source) as f:
            s = f.read()
            r = re.compile(r'^# Description: (.*)[\r\n]*')
            description = ''.join(re.findall(r, s))
            contents = re.sub(r, '', s)
            if description and contents:
                self.addSnipplet(description, contents)

    @QtCore.Slot()
    def loadSnipplets(self):
        self.snippletView.setStyleSheet('''QToolTip {
            font-family: "monospace";
        }''')
        with open(os.path.join(share(), 'snipplet', 'snipplets.xml')) as f:
            self.loadSnippletFrom(f)
        snipplet_glob = os.path.join(share(), 'snipplet', '*.py')
        for source in glob.glob(snipplet_glob):
            self.loadCodeSnipplet(source)


class MainWindow(QtWidgets.QMainWindow):
    onListDir = QtCore.Signal(str)

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle(i18n("Edu CIAA MicroPython"))
        self.cwd = QtCore.QDir.homePath()
        self.tabber = wcore.TabWidget(self)
        self.term = termWidget.Terminal(self)
        self.outline = widgets.PyOutlineTreeWidget()
        self.dock_outline = QtWidgets.QDockWidget(i18n('Outline'))
        self.dock_outline.setWidget(self.outline)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_outline)
        self.snippler = SnipplerWidget(self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.snippler)
        self.stack = QtWidgets.QStackedWidget(self)
        self.stack.addWidget(self.tabber)
        self.stack.addWidget(self.term)
        self.setCentralWidget(self.stack)
        self.makeAppToolBar()
        self.resize(800, 600)
        self.onListDir.connect(lambda l: self._showDir(l))
        self.tabber.currentChanged.connect(self.actualizeOutline)
        self.fileNew()
        self.portSelector.onChange(0)

    def actualizeOutline(self, n):
        self.outline.set_editor(self.tabber.active_editor)
        self.i18n()

    def i18n(self, actions=None):
        if not self.tabber.active_editor:
            return
        if not actions:
            actions = self.tabber.active_editor.actions()
        for action in actions:
            if not action.isSeparator():
                action.setText(pyqode_i18n.tr(action.text()))
            if action.menu():
                self.i18n(action.menu().actions())

    def terminate(self):
        self.term.close()

    def makeAppToolBar(self):
        bar = QtWidgets.QToolBar(self)
        bar.setIconSize(QtCore.QSize(48, 48))
        bar.addAction(icon("document-new"), i18n("New"), self.fileNew)
        bar.addAction(icon("document-open"), i18n("Open"), self.fileOpen)
        bar.addAction(icon("document-save"), i18n("Save"), self.fileSave)
        bar.addWidget(WidgetSpacer(self))
        bar.addWidget(QtWidgets.QLabel(i18n("Serial Port:")))
        bar.addWidget(WidgetSpacer(self, 12))
        self.portSelector = PortSelector(self)
        bar.addWidget(self.portSelector)
        self.portSelector.setToolTip(i18n("Select Serial Port"))
        self.runAction = bar.addAction(icon("run"), i18n("Run"), self.progRun)
        self.runAction.setEnabled(False)
        self.dlAction = bar.addAction(icon("download"), i18n("Download"),
                                      self.progDownload)
        self.dlAction.setEnabled(False)
        self.termAction = bar.addAction(icon("terminal"), i18n("Terminal"),
                                        self.openTerm)
        self.termAction.setEnabled(False)
        self.termAction.setCheckable(True)
        self.addToolBar(bar)

    def terminalMenu(self):
        m = QtWidgets.QMenu(self)
        g = QtWidgets.QActionGroup(m)
        g.triggered.connect(lambda a: self.setPort(a.text()))
        for s in termWidget.serial_ports():
            a = m.addAction(s)
            g.addAction(a)
            a.setCheckable(True)
        if g.actions():
            g.actions()[0].setChecked(True)
            self.setPort(g.actions()[0].text())
        return m

    def setPort(self, port):
        en = self.term.open(port, 115200)
        [i.setEnabled(en) for i in (self.dlAction,
                                    self.runAction,
                                    self.termAction)]

    def closeEvent(self, event):
        self.tabber.closeEvent(event)
        if event.isAccepted():
            self.terminate()

    def fileNew(self):
        code_edit = widgets.PyCodeEdit(interpreter=backend_interpreter(),
                                       server_script=completion_server())
        i = self.tabber.add_code_edit(code_edit, i18n("NewFile.py (%d)"))
        self.tabber.setCurrentIndex(i)

    def dirtySaveDischartCancel(self):
        d = QtWidgets.QMessageBox()
        d.setWindowTitle(i18n("Question"))
        d.setText(i18n("Document was modify"))
        d.setInformativeText(i18n("Save changes?"))
        d.setIcon(QtWidgets.QMessageBox.Question)
        d.setStandardButtons(QtWidgets.QMessageBox.Save | 
                             QtWidgets.QMessageBox.Discard | 
                             QtWidgets.QMessageBox.Cancel)
        return d.exec_()

    def dirtySaveCancel(self):
        d = QtWidgets.QMessageBox()
        d.setWindowTitle(i18n("Question"))
        d.setText(i18n("Document was modify"))
        d.setInformativeText(i18n("Save changes?"))
        d.setIcon(QtWidgets.QMessageBox.Question)
        d.setStandardButtons(QtWidgets.QMessageBox.Save | 
                             QtWidgets.QMessageBox.Cancel)
        return d.exec_()

    def fileOpen(self):
        name, dummy = QtWidgets.QFileDialog.getOpenFileName(
            self, i18n("Open File"), self.cwd,
            i18n("Python files (*.py);;All files (*)"))
        if name:
            code_edit = widgets.PyCodeEdit(server_script=server.__file__)
            code_edit.file.open(name)
            i = self.tabber.add_code_edit(code_edit)
            self.tabber.setCurrentIndex(i)
            self.cwd = os.path.dirname(name)

    def fileSave(self):
        ed = self.tabber.active_editor
        if not ed:
            return False
        is_new = ed.file.path.startswith(i18n('NewFile.py (%d)')
                                         .replace(' (%d)', ''))
        if not ed.file.path or is_new:
            path, dummy = QtWidgets.QFileDialog. \
                getSaveFileName(self, i18n("Save File"), self.cwd,
                                i18n("Python files (*.py);;All files (*)"))
        else:
            path = ed.file.path
        if not path:
            return False
        old = self.tabber.currentIndex()
        self.tabber.setCurrentWidget(ed)
        self.tabber.save_current(path)
        self.tabber.setCurrentIndex(old)
        return True

    def openTerm(self):
        if self.termAction.isChecked():
            self.stack.setCurrentIndex(1)
            self.term.setFocus()
            # self.term.remoteExec(b'\x04')
        else:
            self.stack.setCurrentIndex(0)

    def progRun(self):
        self._targetExec(self.tabber.active_editor.toPlainText())
        self.termAction.setChecked(True)
        self.openTerm()

    def _targetExec(self, script, continuation=None):
        def progrun2(text):
            # print("{} {}".format(4, progrun2.text))
            progrun2.text += text
            if progrun2.text.endswith(b'\x04>'):
                # print("{} {}".format(5, progrun2.text))
                if callable(continuation):
                    continuation(progrun2.text)
                return True
            return False

        def progrun1(text):
            progrun1.text += text
            # print("{} {}".format(2, progrun1.text))
            if progrun1.text.endswith(b'to exit\r\n>'):
                progrun2.text = b''
                # print("{} {}".format(3, progrun1.text))
                cmd = 'print("\033c")\r{}\r\x04\x02'.format(script)
                # print("{} {}".format(3.5, cmd))
                self.term.remoteExec(bytes(cmd, 'utf-8'), progrun2)
                return True
            return False
        progrun1.text = b''
        # print(1)
        self.term.remoteExec(b'\r\x03\x03\r\x01', progrun1)

    def showDir(self):
        def finished(raw):
            text = ''.join(re.findall(r"(\[.*?\])", raw.decode()))
            print(raw, text)
            self.onListDir.emit(text)
        self._targetExec('print(os.listdir())', finished)

    def _showDir(self, text):
        items = eval(text)
        d = QtWidgets.QDialog(self)
        l = QtWidgets.QVBoxLayout(d)
        h = QtWidgets.QListWidget(d)
        l.addWidget(h)
        h.addItems(items)
        h.itemClicked.connect(d.accept)
        d.exec_()

    def _writeRemoteFile(self, local_name):
        def finished(raw):
            print('_writeRemoteFile terminated: ', raw)
        name = os.path.basename(local_name)
        name, ok = QtWidgets.QInputDialog.getText(self, i18n("Download"),
                                                  i18n("Remote Name"),
                                                  text=name)
        if not ok:
            return
        remote_name = '/flash/{}'.format(name)
        if os.path.exists(local_name):
            with open(local_name, 'rb') as f:
                data = base64.b16encode(f.read())
        else:
            data = self.tabber.active_editor.toPlainText()
        cmd = "import ubinascii\r" \
              "with open(\"{}\", 'wb') as f:\r" \
              "    f.write(ubinascii.unhexlify({}))".format(remote_name, data)
        print("Writing remote to ", remote_name, data)
        print("--------------\n", cmd, "\n--------------")
        self._targetExec(cmd, finished)

    def progDownload(self):
        self._writeRemoteFile(self.tabber.active_editor.file.path)

global app


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    splash = QtWidgets.QSplashScreen()
    splash.setPixmap(QtGui.QPixmap(os.path.join(share(), 'images',
                                                'splash.png')))
    splash.show()

    def do_app():
        splash.close()
        w = MainWindow()
        w.show()
    QtCore.QTimer.singleShot(2000, do_app)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
