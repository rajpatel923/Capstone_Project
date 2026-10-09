/*
  FRZR BURN — Wokwi hardware simulation
  4x4 keypad entry → validates 10-digit code against backend → servo lock/unlock.
  Code format: 4-digit member ID + 6-digit TOTP (e.g. "12346789012").
  CODE :- 1234113281
  '#' submits code, '*' clears entry.
  Lock auto-relocks after UNLOCK_DURATION ms.
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_NeoPixel.h>
#include <Keypad.h>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ---- WiFi & Backend config ----
// Wokwi-GUEST is the built-in virtual network — no password needed.
// When running via wokwi-cli locally, host machine is at 10.0.2.2.
// For a deployed backend, replace BACKEND_HOST with your public URL.
#define WIFI_SSID       "Wokwi-GUEST"
#define WIFI_PASSWORD   ""
#define BACKEND_HOST    "https://ripe-trees-try.loca.lt"  // replace with your ngrok URL
#define DEVICE_ID       1
#define DEVICE_API_KEY  "ce1a968467d7eca23afa6c36bc44052a87242805b582f3f2b3ba969a1ecae113"

// ---- OLED ----
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ---- NeoPixel strip ----
#define STRIP_PIN    4
#define NUM_PIXELS   3
Adafruit_NeoPixel strip(NUM_PIXELS, STRIP_PIN, NEO_GRB + NEO_KHZ800);

// ---- 4x4 Keypad ----
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

// ---- Pins ----
#define DOOR_PIN    5
#define BUZZER_PIN  19
#define LOCK_LED    18
#define SERVO_PIN   23

// ---- Servo positions ----
#define SERVO_LOCKED    0
#define SERVO_UNLOCKED  90

// ---- Config ----
const unsigned long UNLOCK_DURATION = 3000;  // ms before auto-relock

Servo lockServo;

String enteredCode  = "";
bool   isUnlocked   = false;
bool   alarmActive  = false;
unsigned long unlockTime = 0;

// -------------------------------------------------------

void setStrip(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < NUM_PIXELS; i++)
    strip.setPixelColor(i, strip.Color(r, g, b));
  strip.show();
}

void showOLED(const char* line1, const char* line2 = "") {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(line1);
  display.println(line2);
  display.display();
}

void doLock() {
  lockServo.write(SERVO_LOCKED);
  digitalWrite(LOCK_LED, LOW);
  isUnlocked  = false;
  alarmActive = false;
  enteredCode = "";
  setStrip(0, 0, 255);          // blue = armed
  showOLED("** FRZR BURN **", "Enter code + #");
  Serial.println("[LOCK] Status: LOCKED");
}

void doUnlock() {
  lockServo.write(SERVO_UNLOCKED);
  digitalWrite(LOCK_LED, HIGH);
  isUnlocked = true;
  unlockTime = millis();
  setStrip(0, 255, 0);          // green = unlocked
  showOLED("ACCESS GRANTED", "Door unlocked");
  tone(BUZZER_PIN, 1000, 150);
  Serial.println("[LOCK] Status: UNLOCKED — auto-relocks in 3s");
}

void denyAccess(const char* reason = "Wrong code!") {
  setStrip(255, 0, 0);          // red flash
  showOLED("ACCESS DENIED", reason);
  tone(BUZZER_PIN, 300, 500);
  Serial.printf("[LOCK] Access DENIED — reason: %s\n", reason);
  delay(1000);
  setStrip(0, 0, 255);
  showOLED("** FRZR BURN **", "Enter code + #");
}

void triggerAlarm() {
  setStrip(255, 0, 0);
  showOLED("!! ALARM !!", "Forced open!");
  tone(BUZZER_PIN, 2000, 500);
  Serial.println("[LOCK] !! ALARM !! Door forced open while locked");
}

// -------------------------------------------------------

void connectWiFi() {
  showOLED("Connecting...", WIFI_SSID);
  setStrip(255, 165, 0);        // orange = connecting

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi connected: ");
    Serial.println(WiFi.localIP());
    showOLED("WiFi connected", WiFi.localIP().toString().c_str());
    setStrip(0, 0, 255);
    delay(1000);
  } else {
    Serial.println("WiFi failed — check WIFI_SSID/WIFI_PASSWORD");
    showOLED("WiFi FAILED", "Check config");
    setStrip(255, 0, 0);
    delay(2000);
  }
}

// Posts the 10-digit code to POST /devices/{id}/validate-code.
// Returns true if backend says valid=true, false otherwise.
// `reason` is populated with the backend's reason string on both outcomes.
bool validateCodeWithBackend(const String& code, String& reason) {
  if (WiFi.status() != WL_CONNECTED) {
    reason = "No WiFi";
    return false;
  }

  showOLED("Checking...", "Please wait");
  setStrip(255, 165, 0);

  WiFiClientSecure client;
  client.setInsecure();  // skip cert verification for ngrok HTTPS

  HTTPClient http;
  String url = String(BACKEND_HOST) + "/devices/" + String(DEVICE_ID) + "/validate-code";
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("x-device-key", DEVICE_API_KEY);
  http.addHeader("ngrok-skip-browser-warning", "true");  // skip ngrok interstitial page
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  http.setTimeout(8000);

  String payload = "{\"code\":\"" + code + "\"}";
  int httpCode = http.POST(payload);
  Serial.printf("POST %s → HTTP %d\n", url.c_str(), httpCode);

  bool granted = false;
  if (httpCode == 200) {
    StaticJsonDocument<128> doc;
    DeserializationError err = deserializeJson(doc, http.getString());
    if (!err) {
      granted = doc["valid"].as<bool>();
      reason  = doc["reason"].as<const char*>();
    } else {
      reason = "Parse error";
    }
  } else {
    reason = "HTTP " + String(httpCode);
  }

  http.end();
  setStrip(0, 0, 255);
  return granted;
}

// -------------------------------------------------------

void setup() {
  Serial.begin(115200);
  pinMode(DOOR_PIN,   INPUT_PULLUP);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LOCK_LED,   OUTPUT);

  lockServo.attach(SERVO_PIN);
  lockServo.write(SERVO_LOCKED);

  Wire.begin(21, 22);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  strip.begin();

  connectWiFi();
  doLock();
  Serial.println("System ready");
}

void loop() {
  // ---- Auto-relock ----
  if (isUnlocked && millis() - unlockTime >= UNLOCK_DURATION) {
    Serial.println("[LOCK] Auto-relock triggered after 3s");
    doLock();
  }

  // ---- Force-open alarm (door opened while locked) ----
  bool doorOpen = (digitalRead(DOOR_PIN) == LOW);
  if (doorOpen && !isUnlocked && !alarmActive) {
    alarmActive = true;
    triggerAlarm();
  } else if (!doorOpen && alarmActive) {
    alarmActive = false;
    setStrip(0, 0, 255);
    showOLED("** FRZR BURN **", "Enter code + #");
  }

  // ---- Keypad ----
  char key = keypad.getKey();
  if (!key) return;

  Serial.print("Key: "); Serial.println(key);

  if (key == '#') {
    Serial.printf("[KEYPAD] Code submitted: %s (%d digits)\n", enteredCode.c_str(), enteredCode.length());
    String reason;
    if (validateCodeWithBackend(enteredCode, reason)) {
      doUnlock();
    } else {
      denyAccess(reason.c_str());
    }
    enteredCode = "";

  } else if (key == '*') {
    enteredCode = "";
    showOLED("** FRZR BURN **", "Enter code + #");

  } else {
    enteredCode += key;
    String masked = "";
    for (unsigned int i = 0; i < enteredCode.length(); i++) masked += '*';
    showOLED("Enter code:", masked.c_str());
  }
}
