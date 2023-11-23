from signal import signal, SIGTERM, SIGHUP
from rpi_lcd import LCD 
from serial import Serial
import RPi.GPIO as GPIO
import time
from time import sleep
import datetime
import websocket # pip install websocket-client
from machine import Machine
import RPi.GPIO as GPIO
import time
from time import sleep
import datetime

lcd = LCD() 

if __name__ == '__main__':

    machine = Machine()

    actuator_ready = True
    slicer_started = False
    conveyor_started = False
    pulverizer_started = False
    
    actuator_start_time = datetime.datetime.now()
    pulverizer_start_time = datetime.datetime.now()

    start = datetime.datetime.now()
    true_start = datetime.datetime.now()

    lcd.text("Press the Button", 1)

    GPIO.setup(10, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.add_event_detect(10, GPIO.RISING, callback = machine.button_callback)
    flag = 0
    state = 0
    while True:
             
       if machine:

            if machine.started:
                if state == 0:
                    lcd.text("System", 1)
                    lcd.text("Initializing...", 2)
                    time.sleep(2)
                    lcd.clear()
                    state = 1
                
                if state == 1:
                    if actuator_ready:
                        weight =  machine.get_weight()                        
                        disweight = "Weight: " + '{:1.2f}'.format(weight) + " kg" 
                        lcd.text(disweight, 1)

                        temperature = machine.get_temperature()
                        distemp = "Temp: " + '{:1.2f}'.format(temperature)  + " C"
                        lcd.text(distemp, 2)
                        
                        sleep(0.1)

                        if weight >= 0.9 and weight <= 1.1:

                            if not slicer_started and not conveyor_started:
                                machine.switch_arduino_1()

                                machine.activate_slicer()
                                machine.activate_conveyor()
                                slicer_started = True
                                conveyor_started = True

                                machine.switch_arduino_0()
                                machine.activate_actuator()
                                machine.retract_actuator()
                                                        
                            actuator_ready = False
                            actuator_start_time = datetime.datetime.now()

                    if not actuator_ready and datetime.datetime.now() - actuator_start_time >= datetime.timedelta(seconds=10):
                        actuator_ready = True

                    if datetime.datetime.now() - start >= datetime.timedelta(minutes=30) and not pulverizer_started:
                        machine.activate_pulvurizer()
                        # start pulvurizer
                        pulverizer_started = True
                        pulverizer_start_time = datetime.datetime.now()

                        parameters = machine.get_parameters()
                        machine.update_parameters(parameters)

                        moisture = machine.get_moisture()
                        machine.update_moisture(moisture)

                        harvest = machine.get_harvest()
                        machine.update_harvest(harvest)
                        

                    if pulverizer_started and datetime.datetime.now() - pulverizer_start_time >= datetime.timedelta(minutes=10):
                        machine.off_pulvurizer()
                        # stop pulverizer
                        pulverizer_started = False
                        start = datetime.datetime.now()

                        weight2 = machine.get_wfinish()
                        if weight2 == 0.8:
                            machine.get_wfinish()


                # send to server
                else:
                    pass