#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#define TFT_CS D5
#define TFT_DC D8
#define TFT_RST D9
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_RST);
void setup() {
  Serial.begin(115200); delay(1000);
  Serial.println("Initializing display...");
  tft.init(240, 280); tft.setRotation(0);
  tft.fillScreen(ST77XX_BLACK);
  tft.fillRect(0, 0, 80, 30, ST77XX_RED);
  tft.fillRect(80, 0, 80, 30, ST77XX_GREEN);
  tft.fillRect(160, 0, 80, 30, ST77XX_BLUE);
  tft.setTextColor(ST77XX_WHITE); tft.setTextSize(3);
  tft.setCursor(50, 95); tft.println("Hello!");
  tft.setTextSize(2); tft.setCursor(42, 150);
  tft.println("nRF52840");
  tft.setTextColor(ST77XX_CYAN); tft.setCursor(75, 200);
  tft.println("SPI OK");
  Serial.println("Display commands sent.");
}
void loop() {}
