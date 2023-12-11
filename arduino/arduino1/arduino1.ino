#include "max6675.h"
#include <Wire.h>
#include <Servo.h>
#include "HX711.h"

HX711 scale1(3, 2);
HX711 scale2(12, 13);
Servo myservo;

float calibrationFactor1 = -412;
float calibrationFactor2 = -440;

// Heater 
const int heatRelay1 = 8;
const int heatRelay2 = 9;

// Fan
const int fanRelay1 = 10;
const int fanRelay2 = 11;

// Buzzer
const int buzzer = 7;

const int enaPin = A0; // the Arduino pin connected to the EN1 pin L298N
const int in1Pin = 6;  // the Arduino pin connected to the IN1 pin L298N
const int in2Pin = 5;  // the Arduino pin connected to the IN2 pin L298N

// Thermo
const int thermoDO = A1;
const int thermoCS = A2;
const int thermoCLK = A3;

MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);

int current_command = -1;

void setup() {
  Serial.begin(9600);

  scale1.set_scale(calibrationFactor1);
  scale2.set_scale(calibrationFactor2);
  scale1.tare();
  scale2.tare();

  // Actuator 
  pinMode(enaPin, OUTPUT);
  pinMode(in1Pin, OUTPUT);
  pinMode(in2Pin, OUTPUT);

  digitalWrite(enaPin, HIGH);

  myservo.attach(4);

  // Buzzer 
  pinMode(buzzer, OUTPUT);

  // LED 
  pinMode(greenLed, OUTPUT);
  pinMode(redLed, OUTPUT);

  // LED FAN
  pinMode(fanRelay1, OUTPUT);
  pinMode(fanRelay2, OUTPUT);

  pinMode(heatRelay1, OUTPUT);
  pinMode(heatRelay2, OUTPUT);
}

void loop() {
  if (current_command == -1) {
    receiveCommand();
  } 
  
  else if (current_command == 11) {
    getTemp();
    current_command = -1;
  } 
  
  else if (current_command == 12) {
    getMoisture();
    current_command = -1;
  } 
  
  else if (current_command == 13) {
    getWeight(1);
    current_command = -1;
  } 

  else if (current_command == 14) {
    getWeight(2);
    current_command = -1;
  } 

  else if (current_command == 15) {
    extendActuator();
    current_command = -1;
  } 

  else if (current_command == 16) {
    retractActuator();
    current_command = -1;
  } 
  
  else if (current_command == 17) {
    turnOnFan();
    current_command = -1;
  } 
  
  else if (current_command == 18) {
    turnOffFan();
    current_command = -1;
  }

  else if (current_command == 19) {
    activateBuzzer();
    current_command = -1;
  } 

  else if(current_command == 20){
    activateHeat();
    current_command = -1;
  }

  else if(current_command == 21){
    deactivateHeat();
    current_command = -1;
  }

  else if (current_command == 22) {
    spinServo();
    current_command = -1;
  } 
}

void sendResponse(String response) {
  Serial.println(response);
}

void receiveCommand() {
  if (Serial.available()) {
    int sent = Serial.readStringUntil('\n').toInt();
    Serial.println("ok");
    current_command = sent;
  }
}

void getTemp() {
  float heater = thermocouple.readCelsius();
  sendResponse(String(heater));
}

void getMoisture() {
  int airValue = 620; 
  int waterValue = 310; 
  int soilMoistureValue = analogRead(A4);
  int soilMoisturePercent = map(soilMoistureValue, airValue, waterValue, 0, 100);
  sendResponse(String(soilMoisturePercent));
}

void getWeight(int scale) {
  float units = 0.00;
  if(scale == 1) {
    units = scale1.get_units(), 10;
  }
  else if(scale == 2) {
    units = scale1.get_units(), 10;
  }
  else {
    units = scale1.get_units(), 10;
  }

  if (units < 0) {
    units = 0.00;
  }
  float weight = units * 0.001;
  sendResponse(String(weight));
}

void extendActuator() {
  digitalWrite(in1Pin, HIGH);
  digitalWrite(in2Pin, LOW);
  delay(10000);
}

void retractActuator() {
  digitalWrite(in1Pin, LOW);
  digitalWrite(in2Pin, HIGH);
  delay(10000);
}

void spinServo() {
  int pos = 0;
  for (pos = 0; pos <= 180; pos += 1) {
    myservo.write(pos);
    delay(15);
  }
  for (pos = 180; pos >= 0; pos -= 1) {
    myservo.write(pos);
    delay(15);
  }
}

void activateBuzzer() {
  tone(buzzer, 5000);
  delay(3000);
  noTone(buzzer);
}

void turnOnFan() {
  digitalWrite(fanRelay1, HIGH);
  digitalWrite(fanRelay2, HIGH);
}

void turnOffFan() {
  digitalWrite(fanRelay1, LOW);
  digitalWrite(fanRelay2, LOW);
}

void activateHeat(){
  digitalWrite(heatRelay1, HIGH);
  digitalWrite(heatRelay2, HIGH);
}

void deactivateHeat(){
  digitalWrite(heatRelay1, LOW);
  digitalWrite(heatRelay2, LOW);
}
