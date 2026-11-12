#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#define TFT_CS D5
#define TFT_DC D8
#define TFT_RST D9
#define TP_RST D13
#define TOUCH_ADDR 0x15
Adafruit_ST7789 tft(TFT_CS, TFT_DC, TFT_RST);
void setup() {
  Serial.begin(115200);
  pinMode(TP_RST, OUTPUT);
  digitalWrite(TP_RST, LOW); delay(20);
  digitalWrite(TP_RST, HIGH); delay(150);
  Wire.begin(); Wire.setClock(100000);
  tft.init(240, 280); tft.setRotation(0);
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextColor(ST77XX_CYAN); tft.setTextSize(2);
  tft.setCursor(20, 40); tft.println("TOUCH TEST");
  tft.drawFastHLine(20, 75, 200, ST77XX_WHITE);
}
void loop() {
  Wire.beginTransmission(TOUCH_ADDR);
  uint8_t status = Wire.endTransmission();
  tft.fillRect(10, 100, 220, 140, ST77XX_BLACK);
  if (status == 0) {
    tft.setTextColor(ST77XX_GREEN);
    tft.setCursor(30, 115); tft.println("CONNECTED");
    tft.setTextColor(ST77XX_WHITE);
    tft.setCursor(40, 160); tft.println("I2C: 0x15");
  } else {
    tft.setTextColor(ST77XX_RED);
    tft.setCursor(25, 115); tft.println("NOT FOUND");
    tft.setTextColor(ST77XX_WHITE);
    tft.setCursor(30, 160); tft.print("Error: "); tft.println(status);
  }
  delay(1000);
}
