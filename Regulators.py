import numpy as np

class Regulator:
    def __init__(self):
        self.name = "Override me"

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        """ Called upon ending of the program. Put anything in that has to
        be done in the end, for instance closing a serial port """
        print "Closing t255"

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

class T255ControllerSim(Regulator):
    def __init__(self):
        self.current_temperature = 19.1
        self.max_temperature = 19.3
        self.min_temperature = 18.9
        self.stepsize = 0.1

    def perform_positive_feedback(self):
        self.increase_temperature(self.stepsize)

    def perform_negative_feedback(self):
        self.decrease_temperature(self.stepsize)

    def increase_temperature(self, amount):
        if(self.current_temperature + amount > self.max_temperature):
            raise HighTemperatureException(self.current_temperature)
        else:
            self.current_temperature += amount

    def decrease_temperature(self, amount):
        if self.current_temperature - amount < self.min_temperature:
            raise LowTemperatureException(self.current_temperature)
        else:
            self.current_temperature -= amount

    def get_value(self):
        return self.current_temperature + np.random.rand()

    def get_set_value(self):
        return self.current_temperature

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
    with T255ControllerSim() as t255:
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
            print "Current temp: " , t255.current_temperature

