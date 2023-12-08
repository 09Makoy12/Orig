#define pulPin1 6
#define dirPin1 7
#define pulPin2 8
#define dirPin2 9

int stepCount = 500;

const int motorRelay = 2;
const int pulverizerRelay = 10;
const int heatRelay = 11;

String command = "";
int current_command = -1;

void setup() {
  Serial.begin(9600);

  pinMode(pulPin1, OUTPUT);
  pinMode(dirPin1, OUTPUT);
  pinMode(pulPin2, OUTPUT);
  pinMode(dirPin2, OUTPUT);

  digitalWrite(dirPin1, HIGH);
  digitalWrite(dirPin2, HIGH);

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

void activateConveyor() { 
  digitalWrite(pulPin1, HIGH);
  digitalWrite(pulPin2, HIGH);
}

void activateSlicer(){
  digitalWrite(motorRelay, HIGH);
}

void activateHeat(){
  digitalWrite(heatRelay, HIGH);
}

void activatePulverizer(){
  digitalWrite(pulverizerRelay, HIGH);
}

void deactivateConveyor() { 
  digitalWrite(pulPin1, LOW);
  digitalWrite(pulPin2, LOW);
}

void deactivateSlicer(){
  digitalWrite(motorRelay, LOW);
}

void deactivateHeat(){
  digitalWrite(heatRelay, LOW);
}

void deactivatePulverizer(){
  digitalWrite(pulverizerRelay, LOW);
}
