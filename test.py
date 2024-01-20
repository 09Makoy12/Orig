from serial import Serial

arduino1 = Serial('/dev/ttyACM0', 9600, timeout=1)
arduino2 = Serial('/dev/ttyACM1', 9600, timeout=1)