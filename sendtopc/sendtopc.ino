#include <Wire.h>
#include <Adafruit_ADS1015.h>

unsigned long timer = 0;
long loopTime = 5000;   // microseconds

Adafruit_ADS1115 ads(0x48);
 
void setup(void)
{
Serial.begin(9600);
ads.begin();
ads.setGain(GAIN_ONE);
timer = micros();
}
 
void loop(void)
{
timeSync(loopTime);
int16_t adc0, adc1, adc2, adc3;
float v0, v1, v2, v3;

adc0 = ads.readADC_SingleEnded(0);
adc1 = ads.readADC_SingleEnded(1);
adc2 = ads.readADC_SingleEnded(2);
adc3 = ads.readADC_SingleEnded(3);

v0 = 2*4.096 * (adc0 / 65536.0);
v1 = 2*4.096 * (adc1 / 65536.0);
v2 = 2*4.096 * (adc2 / 65536.0);
v3 = 2*4.096 * (adc3 / 65536.0);

//Serial.print("V0: ");
//Serial.println(v0);
//Serial.print("V1: ");
//Serial.println(v1);
//Serial.print("V2: ");
//Serial.println(v2);
//Serial.print("V3: ");
//Serial.println(v3);
//Serial.println(" "); 

sendToPC(&v0, &v1, &v2, &v3);
//delay(1000);

}

void timeSync(unsigned long deltaT)
{
  unsigned long currTime = micros();
  long timeToDelay = deltaT - (currTime - timer);
  if (timeToDelay > 5000)
  {
    delay(timeToDelay / 1000);
    delayMicroseconds(timeToDelay % 1000);
  }
  else if (timeToDelay > 0)
  {
    delayMicroseconds(timeToDelay);
  }
  else
  {
      // timeToDelay is negative so we start immediately
  }
  timer = currTime + timeToDelay;
}

void sendToPC(int* data0, int* data1, int* data2, int* data3)
{
  byte* byteData0 = (byte*)(data0);	
  byte* byteData1 = (byte*)(data1);
  byte* byteData2 = (byte*)(data2);
  byte* byteData3 = (byte*)(data3);
  byte buf[8] = {byteData0[0], byteData0[1],
		 byteData1[0], byteData1[1],
                 byteData2[0], byteData2[1],
                 byteData3[0], byteData3[1]};
  Serial.write(buf, 8);
}
 
void sendToPC(float* data0, float* data1, float* data2, float* data3)
{
  byte* byteData0 = (byte*)(data0);	
  byte* byteData1 = (byte*)(data1);
  byte* byteData2 = (byte*)(data2);
  byte* byteData3 = (byte*)(data3);
  byte buf[16] = {byteData0[0], byteData0[1], byteData0[2], byteData0[3],
       	         byteData1[0], byteData1[1], byteData1[2], byteData1[3],
                 byteData2[0], byteData2[1], byteData2[2], byteData2[3],
                 byteData3[0], byteData3[1], byteData3[2], byteData3[3]};
  Serial.write(buf, 16);
}
