#include "max6675.h"
#include<Wire.h>
#include <Servo.h>
#include "HX711.h"
#define NUM_R4 4


const int AirValue = 620;   //you need to replace this value with Value_1
const int WaterValue = 310;  //you need to replace this value with Value_2
int soilMoistureValue = 0;
int soilmoisturepercent=0;

HX711 scale1(3, 2);
HX711 scale2(12, 13);
Servo myservo;

float calibration_factor = -412;
float calibration_factor2 = -440;
float units;
float weight;
float units2;
float weight2;

int pos = 0;

//LED 
int greenled = A5;
const int redled = 1;

//buzzer
const int buzzer = 7;

const int ENA_PIN = A0; // the Arduino pin connected to the EN1 pin L298N
const int IN1_PIN = 6; // the Arduino pin connected to the IN1 pin L298N
const int IN2_PIN = 5; // the Arduino pin connected to the IN2 pin L298N

//thermo
int thermoDO = A1;
int thermoCS = A2; 
int thermoCLK = A3; 

MAX6675 thermocouple(thermoCLK, thermoCS, thermoDO);

//heaterANDfan
const int inArr[NUM_R4] = {8, 9 , 10, 11};

int current_command = -1;

void setup() {
  Serial.begin(9600);
  
  scale1.set_scale(calibration_factor);
  scale2.set_scale(calibration_factor2);
  scale1.tare();
  scale2.tare();

  //actuator 
  pinMode(ENA_PIN, OUTPUT);
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);

  digitalWrite(ENA_PIN, HIGH);

  myservo.attach(4);

  //buzzer 
  pinMode(buzzer, OUTPUT);

//led 
  pinMode(greenled, OUTPUT);
  pinMode(redled, OUTPUT);

  for(int i=0; i<NUM_R4; i++) {
    pinMode(inArr[i], OUTPUT);
  }
  for (int i=0; i<NUM_R4; i++) { 
    digitalWrite(inArr[i], HIGH);
  }

}

void loop() {
  if(current_command == -1){
    receiveCommand();
  }
 
  else if(current_command == 1){
    getWeight();
    current_command = -1;
  }

  else if(current_command == 10){
    activateActuator();
    current_command = -1;
  }

  else if(current_command == 3){
    getTemp();
    current_command = -1;
  }

  else if(current_command == 7){
    getMoisture();
    current_command = -1;
  }

  else if(current_command == 2){
    retractActuator();
    current_command = -1;
  }

   else if(current_command == 11){
   turn_on_fan1();
   current_command = -1;
  }

   else if(current_command == 12){
   turn_off_fan1();
   current_command = -1;
  }

   else if(current_command == 13){
   turn_on_fan2();
   current_command = -1;
  }

   else if(current_command == 14){
   turn_off_fan2();
   current_command = -1;
  }


//  else if(current_command == 12){
//    getWfinish();
//    current_command = -1;
//  }
  
  else{
    current_command = -1;
  }
}

void sendResponse(String response){
  Serial.println(response);  
}
 
void receiveCommand(){
  if(Serial.available()){
    int sent = Serial.readStringUntil('\n').toInt();
    Serial.println("ok"); 
    current_command = sent;   
  }
}

void getWeight(){
  units = scale1.get_units(),10;
  if (units < 0)
  {
    units = 0.00;
  }
  weight = units * 0.001;  
  if (weight >= 0.9 && weight <= 1.1) {
    ledgo();
    servo();
    activateActuator();
  }
  else if (weight >= 0.5 && weight <= 0.8) { 
    lednogo();
  }
  else if (weight >= 1.2) { 
    lednogo();
  }
  sendResponse(String(weight));
  delay(1000);
}

void getTemp() {

  float heater = thermocouple.readCelsius();
        
  if (heater >= 30) {
    for(int i = 0; i < NUM_R4; i++){
      digitalWrite(inArr[i], LOW); 
    }
  }
  else if (heater >=45) {
    for(int i = 0; i < NUM_R4; i++){
      digitalWrite(inArr[i], HIGH);
    }
  }
  sendResponse(String(heater));
  delay(1000);
}


void activateActuator() {
  digitalWrite(IN1_PIN, HIGH);
  digitalWrite(IN2_PIN, LOW);
  delay(10000);
}

void retractActuator() {
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, HIGH);
  delay(10000);
}

void servo() {
  for (pos = 0; pos <= 180; pos += 1) { // goes from 0 degrees to 180 degrees
    // in steps of 1 degree
    myservo.write(pos);              // tell servo to go to position in variable 'pos'
    delay(15);                       // waits 15ms for the servo to reach the position
  }
  for (pos = 180; pos >= 0; pos -= 1) { // goes from 180 degrees to 0 degrees
    myservo.write(pos);              // tell servo to go to position in variable 'pos'
    delay(15);                       // waits 15ms for the servo to reach the position
  }
}

void buzzerks() { 
  tone(buzzer, 5000);
  delay(3000);
  noTone(buzzer);
}

void ledgo() {
  digitalWrite(greenled, HIGH);
  delay(2000);
  digitalWrite(greenled, LOW);
}

void lednogo() {
  analogWrite(redled, 247);
  buzzerks();
  delay(3000);
  analogWrite(redled, LOW);
}

void getMoisture() { 
  soilMoistureValue = analogRead(A4);  //put Sensor insert into soil
  soilmoisturepercent = map(soilMoistureValue, AirValue, WaterValue, 0, 100);
  if(soilmoisturepercent >= 100)
    {
      Serial.println("100 %");
    }
  else if(soilmoisturepercent <=0)
    {
      Serial.println("0 %");
    }
  else if(soilmoisturepercent >0 && soilmoisturepercent < 100)
    {
      Serial.print(soilmoisturepercent);
      Serial.println("%");  
  }
  sendResponse(String(soilmoisturepercent));
  delay(1000);
  
} 

void turn_on_fan1() {
  digitalWrite(10, HIGH);
  }

void turn_off_fan1(){
  digitalWrite(10, LOW);
  }

void turn_on_fan2() {
  digitalWrite(11, HIGH);
  }

void turn_off_fan2(){
  digitalWrite(11, LOW);
  }
//float getWfinish(){
//  units2 = scale2.get_units(), 1;
//  if (units2 < 0)
//  {
//    units2 = 0.00;
//  }
//  weight2 = units2 * 0.001; 
//  if (weight2 >= 0.79 && weight2 <= 0.81 ) {
//    buzzerks();
//  }
//  else if (weight2 >= 5.00 && weight2 <= 5.01) { 
//    ledgo();
//  }
//  sendResponse(String(weight2));
//
//  return weight2;
//  delay(1000);
//}
