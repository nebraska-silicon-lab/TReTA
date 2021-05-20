#include <Wire.h>
#include <Adafruit_ADS1X15.h>

unsigned long timer = 0;
long loopTime = 50000;   // microseconds

Adafruit_ADS1115  ads;

bool debug = false;

void setup(void) {
  Serial.begin(9600);
  if (debug) {
    Serial.println("Program Start");
  }
  ads.begin(0x48);
  ads.setGain(GAIN_ONE);
  timer = micros();
}
 
void loop(void) {
  timeSync(loopTime);
  int16_t adc0, adc1, adc2, adc3;
  float v0, v1, v2, v3;

  adc0 = ads.readADC_SingleEnded(0);
  adc1 = ads.readADC_SingleEnded(1);
  adc2 = ads.readADC_SingleEnded(2);
  adc3 = ads.readADC_SingleEnded(3);
  
//  v0 = 2*4.096 * (adc0 / 65536.0);
//  v1 = 2*4.096 * (adc1 / 65536.0);
//  v2 = 2*4.096 * (adc2 / 65536.0);
//  v3 = 2*4.096 * (adc3 / 65536.0);
  
  v0 = ads.computeVolts(adc0);
  v1 = ads.computeVolts(adc1);
  v2 = ads.computeVolts(adc2);
  v3 = ads.computeVolts(adc3);

  if (debug) {
    Serial.print("V0: ");
    Serial.println(v0);
    Serial.print("V1: ");
    Serial.println(v1);
    Serial.print("V2: ");
    Serial.println(v2);
    Serial.print("V3: ");
    Serial.println(v3);
    Serial.println(" "); 
  } else {
    Serial.print(v0, 6);
    Serial.print(" ");
    Serial.print(v1, 6);
    Serial.print(" ");
    Serial.print(v2, 6);
    Serial.print(" ");
    Serial.print(v3, 6);
    Serial.println();
  }
}

void timeSync(unsigned long deltaT) {
  unsigned long currTime = micros();
  long timeToDelay = deltaT - (currTime - timer);
  if (timeToDelay > 5000) {
    delay(timeToDelay / 1000);
    delayMicroseconds(timeToDelay % 1000);
  }
  else if (timeToDelay > 0) {
    delayMicroseconds(timeToDelay);
  }
  else {
      // timeToDelay is negative so we start immediately
  }
  timer = currTime + timeToDelay;
}
