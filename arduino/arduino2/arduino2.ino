int stepCount = 500;

const int motorRelay = 2;
const int pulverizerRelay = 10;
const int heatRelay = 11;

bool conveyorOn = false;
const int pulPin1 = 6;
const int dirPin1 = 7;
const int pulPin2 = 8;
const int dirPin2 = 9;

String UUID = "ARDUINO2";
int current_command = -1;

void setup() {
  Serial.begin(9600);

  pinMode(pulPin1, OUTPUT);
  pinMode(dirPin1, OUTPUT);
  pinMode(pulPin2, OUTPUT);
  pinMode(dirPin2, OUTPUT);

  digitalWrite(dirPin1, LOW);
  digitalWrite(dirPin2, LOW);

  pinMode(motorRelay, OUTPUT);
  pinMode(pulverizerRelay, OUTPUT);
  pinMode(heatRelay, OUTPUT);
}

void loop() {
  if(current_command == -1){
    receiveCommand();
  }

  else if(current_command == 0){
    activateConveyor();
    current_command = -1;
  }

  else if(current_command == 1){
    deactivateConveyor();
    current_command = -1;
  }

  else if(current_command == 2){
    activateSlicer();
    current_command = -1;
  }

  else if(current_command == 3){
    deactivateSlicer();
    current_command = -1;
  }
  
  else if(current_command == 6){
    activatePulverizer();
    current_command = -1;
  }

  else if(current_command == 7){
    activatePulverizer();
    current_command = -1;
  }

  else if (current_command == 98) {
    resetState();
    current_command = -1;
  }

  else if (current_command == 99) {
    getUUID();
    current_command = -1;
  }

  runBackground();

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

void runBackground(){
  if(conveyorOn){
    digitalWrite(pulPin1,HIGH);
    digitalWrite(pulPin2,HIGH);
    delayMicroseconds(500);
    digitalWrite(pulPin1,LOW);
    digitalWrite(pulPin2,LOW);
    delayMicroseconds(500);
  }
}

void activateConveyor() { 
  conveyorOn = true;
}

void activateSlicer(){
  digitalWrite(motorRelay, HIGH);
}

void activatePulverizer(){
  digitalWrite(pulverizerRelay, HIGH);
}

void deactivateConveyor() { 
  conveyorOn = false;
}

void deactivateSlicer(){
  digitalWrite(motorRelay, LOW);
}

void deactivatePulverizer(){
  digitalWrite(pulverizerRelay, LOW);
}

void getUUID(){
  sendResponse(UUID);
}

void resetState(){
  deactivateConveyor();
  deactivatePulverizer();
  deactivateSlicer();
  sendResponse("reset");
}
