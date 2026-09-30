/*
  FRZR BURN — Wokwi hardware simulation skeleton
  Maps directly to diagram.json. Swap validateCode() for a real
  HTTPS call to your backend once the flag-vs-TOTP decision is made
  (see the WiFi block commented out below).
*/

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_NeoPixel.h>
#include <Keypad.h>

// ---- OLED ----
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ---- LED strip (blue = armed, red = forced open, green = secure) ----
#define STRIP_PIN 4
#define NUM_PIXELS 3
Adafruit_NeoPixel strip(NUM_PIXELS, STRIP_PIN, NEO_GRB + NEO_KHZ800);

// ---- Keypad (4x4) ----
const byte ROWS = 4, COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {13, 12, 14, 27};
byte colPins[COLS] = {26, 25, 33, 32};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// ---- Door sensor (slide switch stands in for the magnetic reed switch) ----
#define DOOR_PIN 5

// ---- Buzzer + lock indicator ----
#define BUZZER_PIN 19
#define LOCK_PIN 18

String enteredCode = "";
bool armed = true;

void setLedState(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < NUM_PIXELS; i++) strip.setPixelColor(i, strip.Color(r, g, b));
  strip.show();
}

void showMessage(const char* line1, const char* line2 = "") {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(line1);
  display.println(line2);
  display.display();
}

// Placeholder — this is the function you replace once you've decided
// flag-is-credential vs. rotating TOTP code. Right now it just checks
// against a hardcoded test code so the rest of the circuit is provable.
bool validateCode(String code) {
  return code == "1234";
}

void setup() {
  Serial.begin(115200);
  pinMode(DOOR_PIN, INPUT_PULLUP);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LOCK_PIN, OUTPUT);

  Wire.begin(21, 22);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  strip.begin();

  showMessage("FRZR BURN", "Enter code:");
  setLedState(0, 0, 255); // blue = armed

  /*
  // Once the backend is deployed to a public URL (Render/Fly.io/ngrok),
  // uncomment this to call it instead of validateCode() locally:
  #include <WiFi.h>
  #include <HTTPClient.h>
  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) delay(100);
  HTTPClient http;
  http.begin("https://your-backend.example.com/devices/validate-code");
  http.addHeader("Content-Type", "application/json");
  int code = http.POST("{\"code\":\"" + enteredCode + "\"}");
  */
}

void loop() {
  char key = keypad.getKey();
  if (key) {
    if (key == '#') {
      bool ok = validateCode(enteredCode);
      if (ok) {
        showMessage("Access granted", "Door unlocked");
        setLedState(0, 255, 0); // green = secure opening
        digitalWrite(LOCK_PIN, HIGH);
        tone(BUZZER_PIN, 1000, 150);
      } else {
        showMessage("Access denied", "Try again");
        tone(BUZZER_PIN, 300, 400);
      }
      enteredCode = "";
    } else if (key == '*') {
      enteredCode = "";
      showMessage("FRZR BURN", "Enter code:");
    } else {
      enteredCode += key;
      showMessage("FRZR BURN", enteredCode.c_str());
    }
  }

  bool doorOpen = digitalRead(DOOR_PIN) == HIGH;
  if (doorOpen && digitalRead(LOCK_PIN) == LOW) {
    // Door opened without a valid code first — force-opened state
    setLedState(255, 0, 0); // red
    tone(BUZZER_PIN, 2000, 500);
  }

  delay(50);
}
