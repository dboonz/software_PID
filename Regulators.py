import serial
import binascii
import ConfigParser
import numpy as np
import time


def hex2Ascii(hexStr):
    """ Convert hex to ascii string """
    asciiStr = ''
    for i in range(len(hexStr)/2):
            asciiStr += binascii.a2b_hex(hexStr[2*i] + hexStr[2*i+1])
    return asciiStr


def ascii2Hex(asciiStr):
        hexStr = ''
        for i in range(len(asciiStr)):
                hexStr += hex(ord(asciiStr[i]))
        return hexStr


class Regulator:
    def __init__(self, *args, **kwargs):
        self.configparser = ConfigParser.SafeConfigParser()
        self.configparser.read('Regulators.ini')

        self.initialize(*args, **kwargs)

    def readIniField(self, optionname):
        """ Read option. Return answer """
        return self.configparser.get(self.section_name, optionname)

    def close(self):
        """ Called upon ending of the program. Put anything in that has to
        be done in the end, for instance closing a serial port """
        print "Closing t255"

    def initialize(self):
        """ Put everything in this method that is needed to initialize the
        device"""
        pass

    def perform_positive_feedback(self):
        pass

    def perform_negative_feedback(self):
        pass

    def get_value(self):
        """ Return the current value of the regulator """
        pass

    def get_set_value(self):
        """ Return the current set value of the regulator """
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


class T255Controller(Regulator):
    """ T255 temperature controller regulator """

    commands = {
        'read_coolant_temperature': hex2Ascii('2E4937370D'),
        'read_set_temperature': hex2Ascii('2E483041360D')
               }

    def initialize(self, section_name):
        print "Section name: %s" % section_name
        self.section_name = section_name

        # connect to the device
        self.comport = self.readIniField('comport')
        try:
            self.serial = serial.Serial(self.comport, timeout=0.7)
        except serial.serialutil.SerialException as s:
            print "Could not connect!"
            # right now we only want to test, so it's not a problem
    
    def close(self):
        self.serial.close()
    
    def readCoolantTemperature(self):
        """ Return coolant temperature """
        command = self.commands['read_coolant_temperature']
        return self.ask(command)

    def ask(self, command):
        self.write(command)
        return self.readline()

    def readline(self):
        try:
            return self.serial.readline()
        except:
            print "Error reading serial device"

    def read(self):
        try:
            return self.serial.read()
        except:
            print "Error reading serial device"

    def readSetTemperature(self):
        """ Return set temperature """
        command = self.commands['read_set_temperature']
        return self.ask(command)

    def setTemperature(self, temperature):
        """ Set the temperature to temperature degrees """
        temp = int(round(10*temperature))
        
        # split up in three parts
        temp10 = str(temp/100%10) # temperature in tens of degrees
        temp1  = str(temp/10%10)  # one degrees
        temp01 = str(temp%10)     # .1 degrees

        # calculate checksum
        checksum_int =  (46 + 77 +  43 + ord(temp10) +  ord(temp1) +  ord(temp01))%256

        set_temperature_command = '.M+' + str(temp) + hex(checksum_int)[2:] + '\r'
        # write command
        self.write(set_temperature_command)


    def write(self, command):
        try:
            self.serial.write(command)
        except:
            print "Error writing. "


class T255ControllerSim(Regulator):
    """ Simulator for the T255 controller """
    def __init__(self, section_name):
        print "Section name: %s" % section_name
        self.section_name = section_name
        Regulator.__init__(self)

    def initialize(self):
        """ Read in configuration """
        self.configparser = ConfigParser.SafeConfigParser()
        self.configparser.read("Regulators.ini")

        get = lambda s:self.configparser.get(self.section_name,s)
        getfloat = lambda s:self.configparser.getfloat(self.section_name, s)
        getint = lambda s:self.configparser.getint(self.section_name, s)

        self.unit = get('unit')
        self.comport = getint('comport')
        self.timeout = getfloat('timeout')

        self.current_temperature = getfloat('start_temperature')
        self.stepsize = getfloat('stepsize')
        self.current_set_temperature = self.current_temperature
        self.current_set_temperature_t0 = time.time()
        self.change_temperature(+3)


    def change_temperature(self, amount):
        """ Change the temperature by amount (positive is increasing """
        self.current_temperature = self.get_temperature()
        self.current_set_temperature += 5.*amount
        self.current_set_temperature_t0 = time.time()

    def get_temperature(self):
        cur_temp = self.current_temperature
        cur_set_temp = self.current_set_temperature
        dtemp = cur_temp - cur_set_temp
        dt = time.time() - self.current_set_temperature_t0
        # slowly converge to the new temperature
        cur_temp = cur_temp - (1.-np.exp(-dt/10.))*dtemp
        return cur_temp

    def get_value(self):
        """ Override abstract class """
        return self.get_temperature()

    def get_set_value(self):
        """ Override abstract class """
        return self.current_set_temperature

    def perform_positive_feedback(self):
        self.change_temperature(self.stepsize)

    def perform_negative_feedback(self):
        self.change_temperature(-self.stepsize)


class HighTemperatureException(Exception):
    def __init__(self, temperature):
        self.temperature = temperature

    def __str__(self):
        return "High temperature reached for t=%f" % self.temperature


class LowTemperatureException(Exception):
    def __init__(self, temperature):
        self.temperature = temperature

    def __str__(self):
        return "Low temperature reached for t=%f" % self.temperature

if __name__ == '__main__':

    with T255Controller('T255') as t255:
        print t255.setTemperature(32.4)

#    with T255Controller('T255') as t255:
#        print "Press + to increase temperature\npress - to decrease, x to stop"
#        stop = False
#        while stop is False:
#            try :
#                command = raw_input()
#                if command is '+':
#                    t255.perform_positive_feedback()
#                elif command is '-':
#                    t255.perform_negative_feedback()
#                elif command is 'x':
#                    exit(0)
#            except HighTemperatureException:
#                print "High temperature reached. Not doing it."
#            except LowTemperatureException:
#                print "Low temperature reached, not doing it."
#            print 'T: ', t255.get_value()
#            print 'T_set:', t255.get_set_value()
#
