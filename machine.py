from threading import Thread
from serial import Serial
from rpi_lcd import LCD

import RPi.GPIO as GPIO
import websocket
import json
import time

class Machine:

    def __init__(self):
        self.ws = None
        self.ws_host = "ws://192.168.1.32:8000/ws/socket-server/"
        self.ws_initialized = False
        
        self.arduino = Serial('/dev/ttyACM0', 9600, timeout = 1)
        self.arduino.reset_input_buffer()

        self.started = False
        self.fan_on = False
        self.start_websocket_listener()

        self.lcd = LCD()

        power_pin = 25
        fan_pin = 17
        self.green_led = 26
        self.red_led = 16
        self.fan_led_1 = 23
        self.fan_led_2 = 22
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.green_led, GPIO.OUT)
        GPIO.setup(self.red_led, GPIO.OUT)
        GPIO.setup(power_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(fan_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.fan_led_1, GPIO.OUT)
        GPIO.setup(self.fan_led_2, GPIO.OUT)
        GPIO.add_event_detect(power_pin, GPIO.RISING, callback=self._switch_state)
        GPIO.add_event_detect(fan_pin, GPIO.RISING, callback=self._switch_fan)
      


    #############################################
    #                                           #
    #               GPIO Functions              #
    #                                           #
    #############################################


    def _switch_state(self, channel):
        '''
        Callback function for power pin
        '''
        self.started = not self.started
        self.update_state(self.started)
        print(self.started)



    def _switch_fan(self, channel):
        '''
        Callback function for fan pin
        '''
        self.fan_on = not self.fan_on
        self.turn_on_fan()if self.fan_on else self.turn_off_fan()
        self._set_fan_led(self.fan_on)
        self.update_fan(self.fan_on)
        print(self.fan_on)



    def _set_fan_led(self, state: bool):
        '''
        Turn on/off fan led

        Parameters:
        state (bool) : Fan led state
        '''
        if state:
            GPIO.output(self.fan_led_1, GPIO.HIGH)
            GPIO.output(self.fan_led_2, GPIO.HIGH)
        else:
            GPIO.output(self.fan_led_1, GPIO.LOW)
            GPIO.output(self.fan_led_2, GPIO.LOW)
        


    def set_green_led(self, state: bool):
        '''
        Turn on/off green led

        Parameters:
        state (bool) : On/off
        '''
        if state:
            GPIO.output(self.green_led, GPIO.HIGH)
        else:
            GPIO.output(self.green_led, GPIO.LOW)



    def set_red_led(self, state: bool):
        '''
        Turn on/off red led

        Parameters:
        state (bool) : On/off
        '''
        if state:
            GPIO.output(self.red_led, GPIO.HIGH)
        else:
            GPIO.output(self.red_led, GPIO.LOW)


    #############################################
    #                                           #
    #              Server Functions             #
    #                                           #
    #############################################


    def start_websocket_listener(self):
        '''
            Start the websocket listener on another thread
        '''
        def _start():
            self.ws = websocket.WebSocketApp(self.ws_host,
                                        on_open = lambda ws: print('Starting websocket listener...'),
                                        on_message=lambda ws, message: self._parse_websocket_message(ws, message),
                                        on_error=lambda ws, error: print(error),
                                        on_close=lambda ws, close_status_code, close_msg: print('Server closing'))
            self.ws.run_forever()
        Thread(target=_start).start()



    def _parse_websocket_message(self, ws, message):
        '''
        Parse the websocket message.
        Mainly for listening to state updates
        '''
        data = json.loads(message)
        print(data)
        if data['type'] == 'get_state':
            self.started = data['state']
        elif data['type'] == 'initialize_parameters':
            if not self.ws_initialized:
                self.update_state(False)
                self.ws_initialized = True



    def update_state(self, state: bool):
        '''
        Update state and send to server

        Parameters:
        state (bool) : New current state
        '''
        data = {
            'type': 'update_state',
            'state': state
        }
        json_data = json.dumps(data)
        self.ws.send(json_data)



    def update_parameters(self, harvested: float, temperature: float):
        '''
        Update parameters and send to server

        Parameters:
        harvested (float) : Amount currently processed
        temperature (float) : Current temperature
        '''
        data = {
            'type': 'update_parameter',
            'harvested': harvested,
            'temperature': temperature
        }
        json_data = json.dumps(data)
        self.ws.send(json_data)
     


    def update_moisture(self, moisture: float):
        '''
        Update moisture and send to server

        Parameters:
        moisture (float) : Current moisture level
        '''
        data = {
            'type': 'update_moisture',
            'moisture': moisture
        }
        json_data = json.dumps(data)
        self.ws.send(json_data)



    def update_fan(self, state: float):
        '''
        Update fan state on database

        state (bool) : Fan state
        '''
        data = {
            'type': 'update_fan',
            'value': state
        }
        json_data = json.dumps(data)
        self.ws.send(json_data)


        
    def add_harvest(self, amount: float, last_temperature: float):
        '''
        Add a new harvest record to the database

        amount (float) : Harvest amount
        last_temperature (float) : Last recorded temperature
        '''
        data = {
            'type': 'update_harvest',
            'amount': amount,
            'last_temperature': last_temperature
        }
        json_data = json.dumps(data)
        self.ws.send(json_data)



    #############################################
    #                                           #
    #             Arduino Functions             #
    #                                           #
    #############################################


    def switch_arduino_1(self): 
        '''
        Switch current to Arduino 1
        '''
        self.arduino.close()
        self.arduino = Serial('/dev/ttyACM0', 9600, timeout = 1)
        self.arduino.flush()



    def switch_arduino_2(self): 
        '''
        Switch current to Arduino 2
        '''
        self.arduino.close()
        self.arduino = Serial('/dev/ttyACM1', 9600, timeout = 1)
        self.arduino.flush()



    def send_command(self, command: int):
        '''
        Send command to arduino

        Parameters:
        command (int) : Command to send
        '''
        while True:
            self.arduino.write(bytes(str(command)+'\n','utf-8'))
            response = self.get_arduino_response()
            if(response == 'ok'):
                break
 


    def get_arduino_response(self) -> str:
        '''
        Get response from arduino

        Returns:
        response (str) : Arduino response
        '''
        try:
            response = self.arduino.readline().decode('utf-8').rstrip()
        except UnicodeDecodeError:
            response = self.arduino.readline().decode('utf-8').rstrip()
        print(response)
        return response
    

    
    def get_temperature(self) -> float:
        '''
        Get current temperature from arduino

        Returns:
        temperature (float) : Temperature
        '''
        self.send_command(11)
        response = self.get_arduino_response()
        while not response:
            response = self.get_arduino_response()
        temperature = float(response)
        return temperature



    def get_moisture(self) -> float:
        '''
        Get current moisture from arduino

        Returns:
        moisture (float) : Moisture
        '''
        self.send_command(11)
        response = self.get_arduino_response()
        while not response:
            response = self.get_arduino_response()
        moisture = float(response)
        return moisture
    


    def get_weight(self) -> float:
        '''
        Get current weight from arduino

        Returns:
        weight (float) : Weight
        '''
        self.send_command(13)
        response = self.get_arduino_response()
        while not response:
            response = self.get_arduino_response()
        weight = float(response)
        return weight
    

    def get_harvest_weight(self) -> float:
        '''
        Get harvest weight from arduino

        Returns:
        weight (float) : Harvest weight
        '''
        self.send_command(14)
        response = self.get_arduino_response()
        while not response:
            response = self.get_arduino_response()
        weight = float(response)
        return weight
    


    def extend_actuator(self, wait: bool = False):
        '''
        Explicit function for extendActuator on Arduino

        Parameters:
        wait (bool) : Wait to finish (blocking)
        '''
        self.send_command(15)
        if wait:
            time.sleep(10.5)



    def retract_actuator(self, wait: bool = False):
        '''
        Explicit function for retractActuator on Arduino

        Parameters:
        wait (bool) : Wait to finish (blocking)
        '''
        self.send_command(16)
        if wait:
            time.sleep(10.5)



    def turn_on_fan(self):
        '''
        Explicit function for turnOnFan on Arduino
        '''
        self.send_command(17)



    def turn_off_fan(self):
        '''
        Explicit function for turnOffFan on Arduino
        '''
        self.send_command(18)



    def activate_buzzer(self):
        '''
        Explicit function for activateBuzzer on Arduino
        '''
        self.send_command(19)
        time.sleep(3.5)



    def activate_heater(self):
        '''
        Explicit function for activateHeater on Arduino
        '''
        self.send_command(20)



    def deactivate_heater(self):
        '''
        Explicit function for deactivateHeater on Arduino
        '''
        self.send_command(21)



    def spin_servo(self):
        '''
        Explicit function for spinServo on Arduino
        '''
        self.send_command(22)
        time.sleep(6)



    def activate_conveyor(self):
        '''
        Explicit function for activateConveyor on Arduino
        '''
        self.send_command(0)



    def deactivate_conveyor(self):
        '''
        Explicit function for deactivateConveyor on Arduino
        '''
        self.send_command(1)


    def activate_slicer(self):
        '''
        Explicit function for activateSlicer on Arduino
        '''
        self.send_command(2)



    def deactivate_slicer(self):
        '''
        Explicit function for deactivateSlicer on Arduino
        '''
        self.send_command(3)



    def activate_pulverizer(self):
        '''
        Explicit function for activatePulverizer on Arduino
        '''
        self.send_command(6)



    def deactivate_pulverizer(self):
        '''
        Explicit function for deactivatePulverizer on Arduino
        '''
        self.send_command(7)



    #############################################
    #                                           #
    #             Derived Functions             #
    #                                           #
    #############################################


    def set_state(self, state: bool):
        '''
        Set power state.
        Has no effect if already set as state

        Parameters:
        state (bool) : Power state
        '''
        if state and not self.started:
            self.started = True
            self.update_state(True)
        if not state and self.started:
            self.started = False
            self.update_state(False)



    def set_fan(self, state: bool):
        '''
        Set fan state.
        Has no effect if already set as state

        Parameters:
        state (bool) : Fan state
        '''
        if state and not self.fan_on:
            self.fan_on = True
            self.turn_on_fan()
            self._set_fan_led(True)
            self.update_fan(True)
        if not state and self.fan_on:
            self.fan_on = False
            self.turn_off_fan()
            self._set_fan_led(False)
            self.update_fan(False)
