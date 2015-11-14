'''
Created on 6 de nov. de 2015

@author: martin
'''

from pyqode.qt import QtWidgets, QtCore

import serial
import threading
import pyte

class Terminal(QtWidgets.QWidget):
    '''
    classdocs
    '''
         
    def __init__(self, parent):
        '''
        Constructor
        '''
        super(self.__class__, self).__init__(parent)
        self.setFont(QtWidgets.QFont('Monospace', 10))
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setStyleSheet("background-color : black; color : #cccccc;");
        self.serial = None
        self.thread = None
        self.stream = pyte.Stream()
        self.vt = pyte.Screen(80, 24)
        self.stream.attach(self.vt)
        
    def resizeEvent(self, event):
        charSize = self.textRect(' ').size()
        lines = int(event.size().height() / charSize.height())
        columns = int(event.size().width() / charSize.width())
        self.vt.resize(lines, columns)
        self.vt.reset()
        
    def focusNextPrevChild(self, n):
        return False
        
    def open(self, port, speed):
        '''
            Open serial 'port' as speed 'speed'
        '''
        if self.serial is serial.Serial:
            self.serial.close()
        try:
            self.serial = serial.Serial(port, speed, timeout=0)
            self._startThread()
        except serial.SerialException as e:
            print(e)
    
    def _startThread(self):
        if self.thread and self.thread.isAlive():
            self.thread.join()
            self.thread = None
        self.thread = threading.Thread(target=self._readThread)
        self.thread.setDaemon(1)
        self.thread.start()
        
    def _readThread(self):
        while self.serial.isOpen():
            text = self.serial.read(1)
            if text:
                n = self.serial.inWaiting()
                if n:
                    text = text + self.serial.read(n)
                self.stream.feed(text.decode(errors='ignore'))
                self.update()
        
    def paintEvent(self, event):
        p = QtWidgets.QPainter()
        p.begin(self)
        pal = self.palette()
        p.fillRect(QtCore.QRect(QtCore.QPoint(), self.size()), 
                   pal.color(pal.Background))
        textSize = self.textRect(' ' * self.vt.size[1]).size()
        bound = QtCore.QRect(QtCore.QPoint(), textSize)
        flags = QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom
        for line in self.vt.display:
            p.drawText(bound, flags, line)
            bound.translate(0, bound.height())
        p.fillRect(self.cursorRect(), pal.color(pal.Foreground))
        p.end()

    def textRect(self, text):
        textSize = QtWidgets.QFontMetrics(self.font()).size(0, text)
        return QtCore.QRect(QtCore.QPoint(), textSize)
        
    def cursorRect(self):
        r = self.textRect(' ')
        r.moveTopLeft(QtCore.QPoint(0,0) + 
                      QtCore.QPoint(self.vt.cursor.x * r.width(),
                                    self.vt.cursor.y * r.height()))
        return r
    
    def keyPressEvent(self, event):
        if self.serial and self.serial.isOpen():
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
                self.serial.write(text)
            event.accept()
