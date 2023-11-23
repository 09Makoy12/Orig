from signal import signal, SIGTERM, SIGHUP
from threading import Thread
from serial import Serial
import websocket
import json
from rpi_lcd import LCD
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)

lcd = LCD() 

class Machine:

    def __init__(self):
        # Change self.ws_host to server IP address
        self.ws = None
        self.ws_host = "ws://192.168.1.25:8000/ws/socket-server/"
        self.ws_initialized = False
        
        self.arduino = Serial('/dev/ttyUSB0', 9600, timeout = 1)
        self.arduino.reset_input_buffer()
        self.weight = '0'
        self.temperature = '0'
        self.start_websocket_listener()
        self.started = False
      

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
            Parse the websocket message\n
            Just mainly for listening to state updates
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
            Update parameters and send to server
        '''
        data = {
            'type': 'update_state',
            'state': state
        }
        json_data = json.dumps(data)
        self.ws.send(json_data)
        self.started = state

    def update_parameters(self, harvested: float, temperature: float):
        '''
            Update parameters and send to server
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
        '''
        data = {
            'type': 'update_moisture',
            'moisture': moisture
        }
        json_data = json.dumps(data)
        self.ws.send(json_data)

    def update_harvest(self, amount: float, last_temperature: float):
        '''
            Add a new harvest record to the database
        '''
        data = {
            'type': 'update_harvest',
            'amount': amount,
            'last_temperature': last_temperature
        }
        json_data = json.dumps(data)
        self.ws.send(json_data)

    def safe_exit(signum, frame): 
        exit(1)

    def button_callback(self, channel):
        self.started = not self.started
        self.update_state(self.started)

    def send_command(self, command: int):
        while True:
            self.arduino.write(bytes(str(command)+'\n','utf-8'))
            response = self.get_arduino_response()
            if(response == 'ok'):
                break
 
    def get_arduino_response(self):
        try:
            response = self.arduino.readline().decode('utf-8').rstrip()
        except UnicodeDecodeError:
            response = self.arduino.readline().decode('utf-8').rstrip()
        print(response)
        return response
 
    def lcd_show(self, message1, message2):
        signal(SIGTERM, self.safe_exit)
        signal(SIGHUP, self.safe_exit)
        self.lcd.clear()

    def get_weight(self):
        self.send_command(1)
        response = self.get_arduino_response()
        while not response:
            response = self.get_arduino_response()
        weight = float(response)
        return weight
    
    def get_temperature(self):
        self.send_command(3)
        temperature = float(self.get_arduino_response())
        return temperature
    
    def activate_actuator(self):
        self.send_command(2)

    def activate_slicer(self):
        self.send_command(4)

    def activate_conveyor(self):
        self.send_command(5)

    def activate_pulvurizer(self):
        self.send_command(6)

    def get_moisture(self):
        self.send_command(7)

    def activate_extraheat(self):
        self.send_command(8)

    def off_pulvurizer(self):
        self.send_command(9)

    def retract_actuator(self):
        self.send_command(10)

    def get_wfinish(self):
        self.send_command(12)
        #finish

    def switch_arduino_1(self): 
        self.arduino.close()
        self.arduino = Serial('/dev/ttyUSB1', 9600, timeout = 1)
        self.arduino.flush()

    def switch_arduino_0(self): 
        self.arduino.close()
        self.arduino = Serial('/dev/ttyUSB0', 9600, timeout = 1)
        self.arduino.flush()