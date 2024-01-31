from machine import Machine
from datetime import datetime, timedelta
import time

if __name__ == '__main__':
    machine = Machine(arduino_ports=('/dev/ttyACM0', '/dev/ttyACM1'))

    # Introduce a delay to allow time for the machine to gather the data
    time.sleep(2)  # You may adjust the delay time based on your machine's response time
    
    # Call the deactivate_servo method
    machine.retract_actuator()
    
    print()
