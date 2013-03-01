import ConfigParser
import numpy as np
import time


class Regulator:
    def __init__(self):
        self.initialize()

    def close(self):
        """ Called upon ending of the program. Put anything in that has to
        be done in the end, for instance closing a serial port """
        print "Closing t255"

    def initialize(self):
        """ Put everything in this method that is needed to initialize the device"""
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
    with T255ControllerSim('Comb_baseplate_chiller') as t255:
        print "Press + to increase temperature\npress - to decrease, x to stop"
        stop = False
        while stop is False:
            try :
                command = raw_input()
                if command is '+':
                    t255.perform_positive_feedback()
                elif command is '-':
                    t255.perform_negative_feedback()
                elif command is 'x':
                    exit(0)
            except HighTemperatureException:
                print "High temperature reached. Not doing it."
            except LowTemperatureException:
                print "Low temperature reached, not doing it."
            print 'T: ', t255.get_value()
            print 'T_set:', t255.get_set_value()

