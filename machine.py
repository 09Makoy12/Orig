from threading import Thread
from serial import Serial
from arduino import Arduino
from rpi_lcd import LCD

import RPi.GPIO as GPIO
import websocket
import json
import time
import logging

class Machine:
    ARDUINO1_UUID = 'ARDUINO1'
    ARDUINO2_UUID = 'ARDUINO2'


    def __init__(self, arduino_ports: tuple = (None, None)):
        self.__initialize_logger()

        self.ws = None
        self.ws_host = "ws://192.168.254.191:8000/ws/socket-server/"
        self.ws_initialized = False
        
        common_commands = [98, 99]
        arduino_1_commands = list(range(11, 24))
        arduino_1_commands.extend(common_commands)
        arduino_2_commands = list(range(0, 8))
        arduino_2_commands.extend(common_commands)

        self.arduino1 = None
        self.arduino2 = None
        for port in arduino_ports:
            print(f'Allocating port {port}...')
            temp = Arduino(port, baudrate=9600, commands=common_commands,timeout=1)
            uuid = temp.get_uuid()
            if uuid == self.ARDUINO1_UUID and self.arduino1 is None:
                self.arduino1 = temp
                self.logger.info(f'Arduino 1 set to port {port}')
                self.arduino1.commands = arduino_1_commands
            elif uuid == self.ARDUINO1_UUID and self.arduino1 is not None:
                raise Exception(f'Arduino 1 is already set to port: {self.arduino1.port}, tried setting to {port}')
            elif uuid == self.ARDUINO2_UUID and self.arduino2 is None:
                self.arduino2 = temp
                self.logger.info(f'Arduino 2 set to port {port}')
                self.arduino2.commands = arduino_2_commands
            elif uuid == self.ARDUINO2_UUID and self.arduino2 is not None:
                raise Exception(f'Arduino 2 is already set to port: {self.arduino2.port}, tried setting to {port}')
            else:
                raise Exception(f'Error initializing port {port}')
            
        self.arduino1.reset_state()
        self.arduino2.reset_state()

        self.started = False
        self.fan_on = False
        self.start_websocket_listener()
        time.sleep(5)
        self.update_state(False)
        time.sleep(3)
        self.update_fan(False)

        self.lcd = LCD(address=0x3f)

        power_pin = 25
        fan_pin = 27
        self.green_led = 22
        self.red_led = 23
        self.fan_led_1 = 16
        self.fan_led_2 = 26
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.green_led, GPIO.OUT)
        GPIO.setup(self.red_led, GPIO.OUT)
        GPIO.setup(power_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(fan_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.fan_led_1, GPIO.OUT)
        GPIO.setup(self.fan_led_2, GPIO.OUT)
        GPIO.add_event_detect(power_pin, GPIO.RISING, callback=self._switch_state)
        GPIO.add_event_detect(fan_pin, GPIO.RISING, callback=self._switch_fan)
        self.logger.info('Machine initialized')
      


    def __initialize_logger(self):
        format = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s.')
        main_handler = logging.FileHandler('machine.log')
        main_handler.setFormatter(format)
        self.logger = logging.getLogger('machine')
        self.logger.addHandler(main_handler)
        self.logger.setLevel(logging.INFO)



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
        self.logger.info(f'GPIO trigger, machine power state switched to {self.started}')



    def _switch_fan(self, channel, update=True):
        '''
        Callback function for fan pin
        '''
        if not self.started:
            return
        
        self.fan_on = not self.fan_on
        self.turn_on_fan()if self.fan_on else self.turn_off_fan()
        self.set_fan_led(self.fan_on)
        if update:
            self.update_fan(self.fan_on)
        self.logger.info(f'GPIO trigger, machine fan state switched to {self.fan_on}')    



    def set_fan_led(self, state: bool):
        '''
        Turn on/off fan led

        Parameters:
        state (bool) : Fan led state
        '''
        if not self.started or not self.fan_on:
            return
        
        if state:
            GPIO.output(self.fan_led_1, GPIO.HIGH)
            GPIO.output(self.fan_led_2, GPIO.HIGH)
        else:
            GPIO.output(self.fan_led_1, GPIO.LOW)
            GPIO.output(self.fan_led_2, GPIO.LOW)
        self.logger.info(f'Fan LED switched to {state}')
        


    def set_green_led(self, state: bool):
        '''
        Turn on/off green led

        Parameters:
        state (bool) : On/off
        '''
        if not self.started:
            return
        
        if state:
            GPIO.output(self.green_led, GPIO.HIGH)
        else:
            GPIO.output(self.green_led, GPIO.LOW)
        self.logger.info(f'Green LED switched to {state}')



    def set_red_led(self, state: bool):
        '''
        Turn on/off red led

        Parameters:
        state (bool) : On/off
        '''
        if not self.started:
            return
        
        if state:
            GPIO.output(self.red_led, GPIO.HIGH)
        else:
            GPIO.output(self.red_led, GPIO.LOW)
        self.logger.info(f'Red LED switched to {state}')



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
        if data['type'] == 'get_notifications':
            self.logger.info(f'Got server message for notification query')
            return
        
       # if data['type'] == 'get_state':
            self.started = data['state']
        if data['type'] == 'initialize_parameters':
            if not self.ws_initialized:
                self.update_state(False)
                self.ws_initialized = True
            return
        elif data['type'] == 'get_fan':
            if data['fan'] != self.fan_on:
                self._switch_fan(None, update=False)
        self.logger.info(f'Got server message: {data}')



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
        self.logger.info(f'Sent data to server: {data}')



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
        self.logger.info(f'Sent data to server: {data}')
     


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
        self.logger.info(f'Sent data to server: {data}')



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
        self.logger.info(f'Sent data to server: {data}')


        
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
        self.logger.info(f'Sent data to server: {data}')



    def notify_pulverizer_finished(self):
        '''
        Add a new harvest record to the database

        amount (float) : Harvest amount
        last_temperature (float) : Last recorded temperature
        '''
        data = {
            'type': 'pulverizer_finished'
        }
        json_data = json.dumps(data)
        self.ws.send(json_data)
        self.logger.info(f'Sent data to server: {data}')



    #############################################
    #                                           #
    #             Arduino Functions             #
    #                                           #
    #############################################

    
    def get_temperature(self) -> float:
        '''
        Get current temperature from arduino

        Returns:
        temperature (float) : Temperature
        '''
        self.arduino1.send_command(11)
        while True:
            response = self.arduino1.get_response()
            try:
                temperature = float(response)
                break
            except:
                pass
        self.logger.info(f'Got temperature: {temperature}')
        return temperature



    def get_moisture(self) -> float:
        '''
        Get current moisture from arduino

        Returns:
        moisture (float) : Moisture
        '''
        self.arduino1.send_command(12)
        while True:
            response = self.arduino1.get_response()
            try:
                moisture = float(response)
                break
            except:
                pass
        self.logger.info(f'Got moisture: {moisture}')
        return moisture
    


    def get_weight(self) -> float:
        '''
        Get current weight from arduino

        Returns:
        weight (float) : Weight
        '''
        self.arduino1.send_command(13)
        while True:
            response = self.arduino1.get_response()
            try:
                weight = float(response)
                break
            except:
                pass
        self.logger.info(f'Got weight: {weight}')
        return weight
    


    def get_harvest_weight(self) -> float:
        '''
        Get harvest weight from arduino

        Returns:
        weight (float) : Harvest weight
        '''
        self.arduino1.send_command(14)
        while True:
            response = self.arduino1.get_response()
            try:
                weight = float(response)
                break
            except:
                pass
        self.logger.info(f'Got harvest weight: {weight}')
        return weight
    


    def extend_actuator(self, wait: bool = True):
        '''
        Explicit function for extendActuator on Arduino

        Parameters:
        wait (bool) : Wait to finish (blocking)
        '''
        self.arduino1.send_command(15)
        if wait:
            time.sleep(10.5)



    def retract_actuator(self, wait: bool = True):
        '''
        Explicit function for retractActuator on Arduino

        Parameters:
        wait (bool) : Wait to finish (blocking)
        '''
        self.arduino1.send_command(16)
        if wait:
            time.sleep(10.5)



    def turn_on_fan(self):
        '''
        Explicit function for turnOnFan on Arduino
        '''
        self.arduino1.send_command(17)



    def turn_off_fan(self):
        '''
        Explicit function for turnOffFan on Arduino
        '''
        self.arduino1.send_command(18)



    def activate_buzzer(self):
        '''
        Explicit function for activateBuzzer on Arduino
        '''
        self.arduino1.send_command(19)
        time.sleep(3.5)



    def activate_heater(self):
        '''
        Explicit function for activateHeater on Arduino
        '''
        self.arduino1.send_command(20)



    def deactivate_heater(self):
        '''
        Explicit function for deactivateHeater on Arduino
        '''
        self.arduino1.send_command(21)



    def activate_servo(self):
        '''
        Explicit function for activateServo on Arduino
        '''
        self.arduino1.send_command(22)
        time.sleep(3)



    def deactivate_servo(self):
        '''
        Explicit function for deactivateServo on Arduino
        '''
        self.arduino1.send_command(23)
        time.sleep(3)



    def activate_conveyor(self):
        '''
        Explicit function for activateConveyor on Arduino
        '''
        self.arduino2.send_command(0)



    def deactivate_conveyor(self):
        '''
        Explicit function for deactivateConveyor on Arduino
        '''
        self.arduino2.send_command(1)


    def activate_slicer(self):
        '''
        Explicit function for activateSlicer on Arduino
        '''
        self.arduino2.send_command(2)



    def deactivate_slicer(self):
        '''
        Explicit function for deactivateSlicer on Arduino
        '''
        self.arduino2.send_command(3)



    def activate_pulverizer(self):
        '''
        Explicit function for activatePulverizer on Arduino
        '''
        self.arduino2.send_command(6)



    def deactivate_pulverizer(self):
        '''
        Explicit function for deactivatePulverizer on Arduino
        '''
        self.arduino2.send_command(7)



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
            self.set_fan_led(True)
            self.update_fan(True)
        if not state and self.fan_on:
            self.fan_on = False
            self.turn_off_fan()
            self.set_fan_led(False)
            self.update_fan(False)
