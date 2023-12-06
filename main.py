from machine import Machine
from datetime import datetime, timedelta

import time

if __name__ == '__main__':

    machine = Machine()

    initialized = False
    actuator_ready = True
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
            state = 1
            
        if machine.started and initialized:
            temperature = machine.get_temperature()
            machine.lcd.text(f'Temp: {temperature:.2f} C', 1)
            moisture = machine.get_moisture()
            machine.lcd.text(f'Moisture: {moisture:.2f} %', 2)
            time.sleep(2)

            if temperature >= 30:
                machine.set_fan(True)
            else:
                machine.set_fan(False)

            if actuator_ready \
                and datetime.now() - actuator_last_retracted >= timedelta(seconds=11):
                machine.lcd.clear()
                weight =  machine.get_weight()
                machine.lcd.text(f'Weight: {weight:.2f} kg', 1)
                time.sleep(0.1)

                if weight >= 0.9 and weight <= 1.1:
                    if not slicer_started and not conveyor_started:
                        machine.switch_arduino_2()

                        machine.activate_slicer()
                        machine.activate_conveyor()
                        machine.activate_heat()
                        machine.switch_arduino_1()
                        slicer_started = True
                        conveyor_started = True
                    
                    machine.extend_actuator()
                    actuator_ready = False
                    actuator_last_extended = datetime.now()

            if not actuator_ready \
                and datetime.now() - actuator_last_extended >= timedelta(seconds=11):
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

            harvested_amount = machine.get_harvest_weight()
            machine.update_parameters(harvested_amount, temperature)
            machine.update_moisture(moisture)

            if harvested_amount >= 15:
                machine.activate_buzzer()
                machine.spin_servo()
                machine.lcd.clear()
                machine.lcd.text('Harvest threshold reached.')
                machine.add_harvest(harvested_amount)
                machine.set_state(False)

        if not machine.started and initialized:
            pass
        