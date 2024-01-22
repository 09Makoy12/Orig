from machine import Machine
from datetime import datetime, timedelta

import time

if __name__ == '__main__':
    machine = Machine(arduino_ports=('/dev/ttyACM0', '/dev/ttyACM1'))
    
    temperature = machine.get_temperature()
    
    print(temperature)
