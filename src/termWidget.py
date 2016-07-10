#!/usr/bin/env python3
import glob
import pyte
import serial
import sys
import threading
import time

import pyqode.qt.QtWidgets as QtWidgets
import pyqode.qt.QtCore as QtCore
import pyqode.qt.QtGui as QtGui


def serial_ports():
    """ Lists serial port names
        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class Terminal(QtWidgets.QWidget):
    '''
    classdocs
    '''
    def __init__(self, parent=None):
        '''
        Constructor
        '''
        super(self.__class__, self).__init__(parent)
        self.setFont(QtGui.QFont({
            'win32': 'Consolas',
            'linux': 'Monospace',
            'darwin': 'Andale Mono'
        }.get(sys.platform, 'Courier'), 10))
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setStyleSheet("background-color : black; color : #cccccc;")
        self._workers = []
        self._serial = None
        self._thread = None
        self._stream = pyte.Stream()
        self._vt = pyte.Screen(80, 24)
        self._stream.attach(self._vt)
        self._workers.append(self._processText)
        self._stop = threading.Event()

    def resizeEvent(self, event):
        charSize = self.textRect(' ').size()
        lines = int(event.size().height() / charSize.height())
        columns = int(event.size().width() / charSize.width())
        self._vt.resize(lines, columns)
        self._vt.reset()

    def focusNextPrevChild(self, n):
        return False

    def close(self):
        self._stop.set()
        if self._thread and self._thread.isAlive():
            self._thread.join()
            self._thread = None
        if self._serial:
            self._serial.close()

    def open(self, port, speed):
        self._stopThread()
        if type(self._serial) is serial.Serial:
            self._serial.close()
        try:
            self._serial = serial.Serial(port, speed, timeout=0.5)
            self._startThread()
            return True
        except serial.SerialException as e:
            print(e)
            return False

    def remoteExec(self, cmd, interceptor=None):
        if interceptor:
            self._workers.append(interceptor)
        cmd_b = cmd if isinstance(cmd, bytes) else bytes(cmd, encoding='utf8')
        # write command
        for i in range(0, len(cmd_b), 256):
            self._serial.write(cmd_b[i:min(i + 256, len(cmd_b))])
            time.sleep(0.01)

    def _stopThread(self):
        self._stop.set()
        if self._thread and self._thread.isAlive():
            self._thread.join()
            self._thread = None

    def _startThread(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._readThread)
        self._thread.setDaemon(1)
        self._thread.start()

    def _readThread(self):
        try:
            while not self._stop.is_set():
                text = self._serial.read(self._serial.inWaiting() or 1)
                if text:
                    self._workers = [w for w in self._workers if not w(text)]
        except Exception as e:
            print(e)

    def _processText(self, text):
        self._stream.feed(text.decode(errors='ignore'))
        self.update()
        return False

    def focusInEvent(self, event):
        self.repaint()

    def focusOutEvent(self, event):
        self.repaint()

    def paintEvent(self, event):
        p = QtGui.QPainter()
        p.begin(self)
        pal = self.palette()
        p.fillRect(QtCore.QRect(QtCore.QPoint(), self.size()),
                   pal.color(pal.Background))
        textSize = self.textRect(' ' * self._vt.size[1]).size()
        bound = QtCore.QRect(QtCore.QPoint(), textSize)
        flags = QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom
        for line in self._vt.display:
            p.drawText(bound, flags, line)
            bound.translate(0, bound.height())
        if self.hasFocus():
            p.fillRect(self.cursorRect(), pal.color(pal.Foreground))
        else:
            p.drawRect(self.cursorRect())
        p.end()

    def textRect(self, text):
        textSize = QtGui.QFontMetrics(self.font()).size(0, text)
        return QtCore.QRect(QtCore.QPoint(), textSize)

    def cursorRect(self):
        r = self.textRect(' ')
        r.moveTopLeft(QtCore.QPoint(0, 0) +
                      QtCore.QPoint(self._vt.cursor.x * r.width(),
                                    self._vt.cursor.y * r.height()))
        return r

    def keyPressEvent(self, event):
        if self._serial and self._serial.isOpen():
            try:
                text = {
                    QtCore.Qt.Key_Tab: lambda x: b"\t",
                    QtCore.Qt.Key_Backspace: lambda x: b"\x7f",
                    QtCore.Qt.Key_Up: lambda x: b"\033[A",
                    QtCore.Qt.Key_Down: lambda x: b"\033[B",
                    QtCore.Qt.Key_Left: lambda x: b"\033[D",
                    QtCore.Qt.Key_Right: lambda x: b"\033[C",
                }[event.key()](event.key())
            except KeyError:
                text = bytes(event.text(), 'utf-8')
            if text:
                self._serial.write(text)
            event.accept()


def selectPort():
    d = QtWidgets.QDialog()
    l = QtWidgets.QVBoxLayout(d)
    combo = QtWidgets.QComboBox(d)
    combo.addItems(serial_ports())
    ok = QtWidgets.QPushButton("Ok", d)
    ok.clicked.connect(d.close)
    l.addWidget(combo)
    l.addWidget(ok)
    d.exec_()
    return combo.currentText()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = Terminal()
    w.resize(640, 480)
    w.show()
    w.open(selectPort(), 115200)
    w.remoteExec('\x04')
    app.exec_()

if __name__ == "__main__":
    main()
