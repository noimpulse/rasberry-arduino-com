#include <Wire.h>

#define I2C_ADDR 0x23 // поменяй под нужную зону

uint8_t command = 0;
uint8_t status = 0x00; // 0x00 – всё ок

void setup()
{
  Wire.begin(I2C_ADDR);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
  Serial.begin(9600);
}

void loop()
{
  delay(100);
}

void receiveEvent(int howMany)
{
  if (Wire.available())
  {
    command = Wire.read();

    // Тут выполняем действие в зависимости от команды
    if (command == 0x05)
    {
      digitalWrite(13, HIGH);
      delay(500);
      digitalWrite(13, LOW);
      status = 0x00;
    }
    else
    {
      status = 0x03; // неизвестная команда
    }
  }
}

void requestEvent()
{
  Wire.write(status);
}

