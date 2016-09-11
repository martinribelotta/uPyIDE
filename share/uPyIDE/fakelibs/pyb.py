'''
Created on 28 de ago. de 2016

@author: martin
'''


def delay(milis):
    pass


class LED:
    def __init__(self, led_id):
        pass

    def intensity(self, value=0):
        pass

    def on(self):
        pass

    def off(self):
        pass

    def toggle(self):
        pass


class Switch:
    def __init__(self, switch_id):
        pass

    def __call__(self):
        pass

    def callback(self, func):
        pass


class UART:
    RTS = None
    CTS = None

    def __init__(self, uart_id):
        pass

    def init(self, baud=115200, bits=8, parity=None, stop=1, timeout=1000,
             timeout_char=1000, read_buf_len=64, packet=False):
        pass

    def deinit(self):
        pass

    def read(self, nbytes=None):
        pass

    def readall(self):
        pass

    def readline(self):
        pass

    def readinto(self, buffer, nbytes=None):
        pass

    def any(self):
        pass

    def write(self, data):
        pass

    def readchar(self):
        pass

    def writechar(self):
        pass

    def sendbreack(self):
        pass


class Pin:
    IN = None
    OUT_PP = None
    OUT_OD = None
    AF_PP = None
    AF_OD = None
    ANALOG = None

    PULL_NONE = None
    PULL_UP = None
    PULL_DOWN = None

    def __init__(self, pin_id):
        pass

    def init(self, mode, pull=PULL_NONE, af=-1):
        pass

    def value(self, value=None):
        pass

    def __str__(self):
        pass

    def af(self):
        pass

    def gpio(self):
        pass

    def mode(self):
        pass

    def name(self):
        pass

    def names(self):
        pass

    def pin(self):
        pass

    def port(self):
        pass

    def pull(self):
        pass


class ExtInt:
    IRQ_FALLING = None
    IRQ_RISING = None
    IRQ_RISING_FALLING = None

    def __init__(self, pin, mode, pull, callback):
        pass

    def enable(self):
        pass

    def disable(self):
        pass

    def swint(self):
        pass


class DAC:
    NORMAL = None
    CIRCULAR = None

    def __init__(self, dac_line, bits=10):
        pass

    def init(self, bits=10):
        pass

    def noise(self):
        pass

    def triangle(self):
        pass

    def write(self, value):
        pass

    def write_timed(self, data, frec, *, mode=DAC_NORMAL):
        pass


class Timer:
    def __init__(self, timer_id):
        pass

    def init(self, *, frec, prescaler, period):
        pass

    def deinit(self):
        pass

    def callback(self, fun):
        pass

    def interval(self, period, func):
        pass

    def timeout(self, period, func):
        pass

    def counter(self, value=None):
        pass

    def freq(self, value=None):
        pass

    def period(self, value=None):
        pass

    def prescaler(self, value=None):
        pass

    def source_freq(self, value=None):
        pass


class PWM:
    @staticmethod
    def set_frecuency(frec):
        pass

    def __init__(self, channel):
        pass

    def duty_cycle(self, duty):
        pass


class ADC:
    def __init__(self, channel):
        pass

    def read(self):
        pass


class EEPROM:
    def __init__(self):
        pass

    def read_byte(self):
        pass

    def read_int(self):
        pass

    def read_float(self):
        pass

    def write_byte(self, val):
        pass

    def write_int(self, val):
        pass

    def write_float(self, val):
        pass

    def write(self, val):
        pass

    def readall(self):
        pass


class SPI:
    def __init__(self, bits, mode, bitrate):
        pass

    def write(self, data, length):
        pass

    def read(self, length):
        pass

    def readinto(self, buffer):
        pass

    def write_read_into(self, wbuff, rbuff):
        pass


class RTC:
    MASK_SEC = 1 << 0
    MASK_MIN = 1 << 1
    MASK_HR = 1 << 2
    MASK_DAY = 1 << 3
    MASK_MON = 1 << 4
    MASK_YR = 1 << 6
    MASK_DOW = 1 << 7

    def __init__(self):
        pass

    def datetime(self, dt_tuple=None):
        pass

    def alarm_datetime(self, dt_tuple=None, alarmMask=None):
        pass

    def alarm_disable(self):
        pass

    def callback(self, functor):
        pass

    def read_bkp_reg(self, addr):
        pass

    def write_bkp_reg(self, addr, value):
        pass

    def calibration(self, value):
        pass


class I2C:
    def __init__(self, frec):
        pass

    def write(self, data, length):
        pass

    def read(self, length):
        pass

    def readinto(self, buffer):
        pass

    def slave_addr(self, addr=None):
        pass

