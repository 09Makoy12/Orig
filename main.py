
from machine import Machine
from datetime import datetime, timedelta

import time

if __name__ == '__main__':

    machine = Machine(arduino_ports=(
        '/dev/ttyACM0', '/dev/ttyACM1'
    ))

    initialized = False
    actuator_ready = True
    servo_open = False
    slicer_started = False
    conveyor_started = False
    pulverizer_started = False
    
    actuator_last_extended = datetime.now() 
    actuator_last_retracted = datetime.now() - timedelta(seconds=10)
    pulverizer_last_started = datetime.now() 
    pulverizer_last_stopped = datetime.now() - timedelta(minutes=10)

    machine.lcd.text("Press the Button", 1)
    
    while True: 
        if machine.started and not initialized:
            machine.lcd.text("System", 1)
            machine.lcd.text("Initializing...", 2)
            time.sleep(2)
            machine.lcd.clear()
            initialized = True
            
        if machine.started and initialized:
            temperature = machine.get_temperature()
            moisture = machine.get_moisture()
            machine.lcd.clear()
            machine.lcd.text(f'Temp: {temperature:.2f} C', 1)
            machine.lcd.text(f'Moisture: {moisture} %', 2)
            time.sleep(1)

            if not conveyor_started:
                machine.activate_conveyor()
                conveyor_started = True

            if not slicer_started:
                machine.activate_slicer()
                slicer_started = True

            if temperature >= 30:
                machine.set_fan(True)
                machine.activate_heater()
            else:
                machine.set_fan(False)
                machine.deactivate_heater()

            if actuator_ready and datetime.now() - actuator_last_retracted >= timedelta(seconds=5):
                weight =  machine.get_weight()
                machine.lcd.clear()
                machine.lcd.text(f'Weight: {weight:.2f} kg', 1)
                time.sleep(0.1)
                
                print(f'Weight: {weight}')
                if weight >= 0.01 and weight <= 1.1:
                    print('triggered')
                    machine.set_green_led(True)
                    machine.set_red_led(False)

                    machine.activate_servo()
                    time.sleep(0.1) 
                    machine.deactivate_servo()
                    machine.extend_actuator()
                    time.sleep(5)
                    actuator_ready = False
                    actuator_last_extended = datetime.now()
                else:
                    machine.set_green_led(False)
                    machine.set_red_led(True)
                    

            if not actuator_ready \
                and datetime.now() - actuator_last_extended >= timedelta(seconds=5):
                machine.retract_actuator()
                actuator_ready = True
                actuator_last_retracted = datetime.now()

            if not pulverizer_started \
                and datetime.now() - pulverizer_last_stopped >= timedelta(minutes=10):
                machine.activate_pulverizer()
                pulverizer_started = True
                pulverizer_last_started = datetime.now()

            if pulverizer_started and datetime.now() - pulverizer_last_started >= timedelta(minutes=10):
                machine.deactivate_pulverizer()
                pulverizer_started = False
                pulverizer_last_stopped = datetime.now()
                machine.notify_pulverizer_finished()

            harvested_amount = machine.get_harvest_weight()
            machine.update_parameters(harvested_amount, temperature)
            machine.update_moisture(moisture)
            
            print(harvested_amount)
            if harvested_amount >= 2.00:
                machine.activate_buzzer()
                machine.lcd.clear()
                machine.lcd.text('Harvest threshold reached.', 1)
                machine.add_harvest(harvested_amount,temperature)
                machine.set_state(False)

        if not machine.started and initialized:
            if conveyor_started:
                machine.deactivate_conveyor()
                conveyor_started = False
            
            if slicer_started:
                machine.deactivate_slicer()
                slicer_started = False
