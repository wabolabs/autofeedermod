# GPIO Assignment — ESP32-C6-WROOM-1

## Pinout

| GPIO | Function | Destination | Notes |
|---|---|---|---|
| **ADC / Analog** | | | |
| GPIO2 | BUTTON_ADC | Button resistor ladder | 6 buttons via voltage divider |
| GPIO5 | BAT_MON | Battery voltage divider | 2× 10kΩ: 0-4.2V → 0-2.1V |
| **Display (SSD1306 SPI)** | | | |
| GPIO13 | DISP_CS | OLED CS | Chip select |
| GPIO14 | DISP_DC | OLED DC | Data/command |
| GPIO15 | DISP_RST | OLED RST | Reset |
| GPIO16 | DISP_SCK | OLED SCK | SPI clock |
| GPIO17 | DISP_MOSI | OLED MOSI | SPI data |
| **Motor (DRV8871)** | | | |
| GPIO9 | MOTOR_IN1 | DRV8871 IN1 | PWM capable |
| GPIO10 | MOTOR_IN2 | DRV8871 IN2 | PWM capable |
| **CAN Bus (SN65HVD230)** | | | |
| GPIO18 | CAN_TX | SN65HVD230 D | TWAI controller TX |
| GPIO21 | CAN_RX | SN65HVD230 R | TWAI controller RX |
| **Status** | | | |
| GPIO6 | STATUS_LED | LED + 330R → GND | Active high |
| **Programming UART** | | | |
| GPIO19 (TXD0) | PROG_TX | J4 pin 1 | USB-serial converter TX |
| GPIO20 (RXD0) | PROG_RX | J4 pin 2 | USB-serial converter RX |
| **Free GPIOs** | | | |
| GPIO0 | — | — | Strapping (pull-up for boot) |
| GPIO1 | — | — | Available |
| GPIO3 | — | — | Strapping (avoid if possible) |
| GPIO4 | — | — | Available |
| GPIO7 | — | — | Available |
| GPIO8 | — | — | Strapping VDD_SPI (caution) |

## Power Nets

| Net | Source | Destination | Voltage |
|---|---|---|---|
| VBUS | USB-C VBUS | TP4056 VCC, D1 anode | 5V |
| BATT+ | TP4056 BAT | DW01A BATT+, TPS63802 VIN | 3.0-4.2V |
| VCC_3V3 | TPS63802 VOUT | ESP32, OLED, CAN, pull-ups | 3.3V |
| GND | Common | All GND | 0V |

## Button ADC Thresholds (GPIO2)

Button resistor ladder from GPIO2 to GND through series resistors. No-press = 3.3V.

| Button | Approx ADC Voltage | Series Resistor |
|---|---|---|
| SW1 | 0.15V | 1kΩ |
| SW2 | 0.45V | 3.3kΩ |
| SW3 | 0.80V | 6.8kΩ |
| SW4 | 1.20V | 12kΩ |
| SW5 | 1.65V | 22kΩ |
| SW6 | 2.20V | 47kΩ |

Pull-up to 3.3V via 10kΩ. ADC reference = 3.3V.

## Strapping Pin Notes

- **GPIO0**: Pull-up for normal boot. Button to GND is OK (only matters at power-up).
- **GPIO3**: JTAG strapping. Avoid using as output.
- **GPIO8**: VDD_SPI voltage select. Do not load externally.
