from arduino import Arduino

arduino = Arduino('/dev/ttyACM0',baudrate=9600, commands=[98,99])
arduino.reset_state()