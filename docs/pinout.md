# GPIO Assignment — ESP32-C6-Zero

## Pinout

ESP32-C6-Zero socket pinout per Waveshare diagram. Bottom edge pads accessed via pogo pins.

| GPIO | Function | Destination | Notes |
|---|---|---|---|
| **Buttons (left rail, GP0–GP5)** | | | |
| GP0 | BUTTON_POWER | SW1 to GND | |
| GP1 | BUTTON_TIMER | SW2 to GND | |
| GP2 | BUTTON_MANUAL | SW3 to GND | |
| GP3 | BUTTON_SETTINGS | SW4 to GND | |
| GP4 | BUTTON_UP | SW5 to GND | |
| GP5 | BUTTON_DOWN | SW6 to GND | |
| **Motor (right rail, TX/RX)** | | | |
| GPIO19 (TX) | MOTOR_IN1 | DRV8871 IN1 | PWM capable |
| GPIO20 (RX) | MOTOR_IN2 | DRV8871 IN2 | PWM capable |
| **Display (right rail + bottom edge)** | | | |
| GP14 | DISP_SCK | OLED SCK | SPI clock |
| GP15 | DISP_MOSI | OLED MOSI | SPI data |
| GP18 | DISP_CS | OLED CS | Chip select |
| GP12 (bottom pad 20) | DISP_DC | OLED DC | Data/command (via pogo pin) |
| — | DISP_RST | Pull-up 10k to 3.3V | No GPIO — R13 holds high |
| **CAN Bus** | | | |
| GP21 | CAN_TX | SN65HVD230 D | TWAI controller TX |
| GP22 | CAN_RX | SN65HVD230 R | TWAI controller RX |
| **Battery Monitor (bottom edge)** | | | |
| GP6 (bottom pad 25) | BAT_MON | Voltage divider 2×10k | ADC-capable, 0–4.2V → 0–2.1V (via pogo pin) |
| **I2C (RTC DS3231)** | | | |
| GP13 (bottom pad 19) | I2C_SDA | DS3231 module SDA | Pogo pin |
| GP23 (bottom pad 21) | I2C_SCL | DS3231 module SCL | Pogo pin |
| **GPS UART** | | | |
| GP7 (bottom pad 24) | GPS_TX | GPS module RX | UART TX output (pogo pin) |
| GP8 (bottom pad 23) | GPS_RX | GPS module TX | UART RX input — strapping, input only (pogo pin) |
| **Unused** | | | |
| GP9 (bottom pad 22) | — | — | BOOT strapping, leave NC |
| **Status LED** | | | |
| GPIO6 | STATUS_LED | LED + 330R → GND | Also available on Zero's onboard WS2812 (GPIO8) |
| **Free GPIOs** | | | |
| GPIO0 | — | — | Strapping (pull-up for boot), used as BUTTON_POWER |
| GPIO3 | — | — | JTAG strapping, used as BUTTON_SETTINGS |
| GPIO8 | — | — | Strapping VDD_SPI, used as GPS_RX (input only) |

## Power Nets

| Net | Source | Destination | Voltage |
|---|---|---|---|
| VBUS | USB-C VBUS | TP4056 VCC, D1 anode | 5V |
| BATT+ | TP4056 BAT | DW01A BATT+, TPS63031 VIN | 3.0–4.2V |
| VCC_3V3 | TPS63031 VOUT | ESP32, OLED, CAN, RTC, GPS, pull-ups | 3.3V |
| GND | Common | All GND | 0V |

## Strapping Pin Notes

- **GPIO0**: Pull-up for normal boot. Button to GND is OK (only sampled at power-up).
- **GPIO3**: JTAG strapping. Avoid using as output (used as input button only).
- **GPIO8**: VDD_SPI voltage select. Used as GPS_RX input only — do not drive externally at boot.
- **GPIO9**: BOOT strapping. Leave NC.
