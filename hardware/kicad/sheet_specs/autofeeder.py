"""Autofeeder schematic — single-sheet design for ESP32-C6 chicken feed dispenser.

Usage:
    PYTHONPATH=tools python3 hardware/kicad/sheet_specs/autofeeder.py

Generates hardware/kicad/autofeeder.kicad_sch
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from sch_gen import Sheet, SymbolLibrary


SCH_PATH = REPO_ROOT / "hardware/kicad/autofeeder.kicad_sch"
PROJECT_SYM = str(REPO_ROOT / "hardware/symbols/autofeeder.kicad_sym")

# Footprint constants
FP_R_0603 = "Resistor_SMD:R_0603_1608Metric"
FP_C_0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C_0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_SOIC8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_JST_XH = "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
FP_USB_C = "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
FP_PIN_1x4 = "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
FP_OLED = "autofeeder:OLED_1.3in_SSD1306_SPI"
# Compact ~4x4 SMD tactile (CK KMR2 series), matching the original board's small buttons.
# Front-only pads keep the dense back side clear; narrow pads clear the corner mounting
# holes at their measured positions.
FP_SW_TACT = "Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2"
FP_ESP = "autofeeder:ESP32_C6_Zero"    # 2.54mm TH socket for Waveshare ESP32-C6-Zero
FP_SOT23_6_HS = "Package_TO_SOT_SMD:SOT-23-6_Handsoldering"
FP_L_0805 = "Inductor_SMD:L_0805_2012Metric"
FP_WSON10_TPS63031 = "Package_SON:WSON-10-1EP_2.5x2.5mm_P0.5mm_EP1.2x2mm"


def build() -> Sheet:
    lib = SymbolLibrary(project_lib=PROJECT_SYM)
    s = Sheet(
        name="autofeeder",
        uuid="00000000-0000-0000-0000-000000000000",
        page=1,
        paper="A4",
        title="Autofeeder Controller",
        rev="1.0",
        date="2026-06-02",
        company="CoopTech",
        lib=lib,
        project_name="autofeedermod",
    )

    def label_pins(comp, labels: dict[str, str]):
        for pin_num, net_name in labels.items():
            try:
                pos = comp.pin_xy(pin_num)
                label_at(net_name, pos)
            except KeyError:
                pass

    def label_at(name: str, pos: tuple[float, float]):
        stub = (pos[0] + 1.27, pos[1])
        s.wire(pos, stub)
        s.local_label(name, stub)
        s.junction(pos)

    # ===== POWER SECTION =====

    # J1: Battery JST XH
    j1 = s.add("J1", "autofeeder:JST_XH_2P", "BATTERY", at=(30, 15), footprint=FP_JST_XH)
    label_pins(j1, {"1": "BATT_P", "2": "BATT_N"})

    # F1: PTC fuse
    f1 = s.add("F1", "Device:Polyfuse", "500mA", at=(30, 30), rotation=90,
               footprint="Fuse:Fuse_1812_4532Metric")
    label_pins(f1, {"1": "BATT_P", "2": "BATT_PROT"})

    # D1: Schottky protection
    d1 = s.add("D1", "Device:D_Schottky", "1N5817", at=(30, 45),
               footprint="Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal")
    label_pins(d1, {"1": "BATT_PROT", "2": "BATT_N"})

    # J3: USB-C
    j3 = s.add("J3", "Connector:USB_C_Receptacle_USB2.0_16P",
               "USB-C", at=(30, 65), rotation=90, footprint=FP_USB_C)
    # USB-C VBUS: A4, A9, B4, B9
    for vbus_pin in ("A4", "A9", "B4", "B9"):
        label_at("VBUS", j3.pin_xy(vbus_pin))
    # USB-C GND: A1, A12, B1, B12
    for gnd_pin in ("A1", "A12", "B1", "B12"):
        label_at("GND", j3.pin_xy(gnd_pin))
    # USB-C SHIELD → GND (reduces EMI, reference for ESD discharge path)
    label_at("GND", j3.pin_xy("S1"))
    # USB-C CC pins: 5.1k to GND
    cc1 = s.add("R_CC1", "Device:R", "5.1k", at=(40, 80), rotation=90, footprint=FP_R_0603)
    cc2 = s.add("R_CC2", "Device:R", "5.1k", at=(50, 80), rotation=90, footprint=FP_R_0603)
    label_pins(cc1, {"1": "CC1", "2": "GND"})
    label_pins(cc2, {"1": "CC2", "2": "GND"})
    label_at("CC1", j3.pin_xy("A5"))
    label_at("CC2", j3.pin_xy("B5"))
    # D+/D- no connect
    s.no_connect(j3.pin_xy("A6"))
    s.no_connect(j3.pin_xy("A7"))
    s.no_connect(j3.pin_xy("B6"))
    s.no_connect(j3.pin_xy("B7"))
    # SBU1/2 → CAN_H_PROT/L_PROT via series resistors (handled below)
    # (no direct labels here — the CAN series protection resistors R6/R10
    #  connect via CAN_H_PROT / CAN_L_PROT labels at the USB-C side)

    # U2: TP4056 charger
    u2 = s.add("U2", "autofeeder:TP4056", "TP4056", at=(55, 65), footprint=FP_SOIC8)
    label_pins(u2, {"4": "VBUS", "3": "GND", "5": "BATT_CHG",
                    "2": "PROG", "1": "CHRG_L", "7": "VBUS", "6": "TEMP_NC", "8": "STDBY_L"})

    # R2: PROG resistor (1.2k for 1A charge)
    r2 = s.add("R2_C", "Device:R", "1.2k", at=(55, 85), rotation=90, footprint=FP_R_0603)
    label_pins(r2, {"1": "PROG", "2": "GND"})

    # LED2: Charge indicator (RED, CHRG = active low)
    led2 = s.add("LED_CHG", "Device:LED", "RED", at=(35, 95), footprint="LED_SMD:LED_0603_1608Metric")
    label_pins(led2, {"1": "CHRG_L", "2": "GND"})
    # Note: CHRG is open-drain, so LED cathode goes to GND, anode to CHRG
    # Meaning: LED illuminates when CHRG pulls low (charging)

    # U3: DW01A battery protection IC (SOT-23-6, hand-solderable)
    u3 = s.add("U3", "Battery_Management:DW01A", "DW01A", at=(55, 110),
               footprint=FP_SOT23_6_HS)
    label_pins(u3, {"5": "BATT_CHG", "6": "BATT_N", "1": "OD_GATE",
                    "3": "OC_GATE", "2": "BATT_N", "4": "NC_TD"})
    s.no_connect(u3.pin_xy("4"))

    # U8: FS8205A dual NMOS (SOT-23-6) — charge/discharge protection FETs driven by DW01A
    u8 = s.add("U8", "autofeeder:FS8205A", "FS8205A", at=(55, 125),
               footprint=FP_SOT23_6_HS)
    label_pins(u8, {"1": "OD_GATE", "4": "OC_GATE",
                    "2": "BATT_N", "3": "BATT_N", "5": "GND"})
    s.no_connect(u8.pin_xy("6"))

    # U4: TPS63031DSKR buck-boost (WSON-10, fixed 3.3V output)
    # Fixed 3.3V output — no feedback resistors needed. Pinout per DSK package:
    # 1=VOUT, 2=L2, 3=PGND, 4=L1, 5=VIN, 6=EN, 7=PS/SYNC, 8=VINA, 9=GND, 10=FB, 11=EP
    u4 = s.add("U4", "autofeeder:TPS63031DSKR", "TPS63031DSKR", at=(55, 150), footprint=FP_WSON10_TPS63031)
    label_pins(u4, {"5": "BATT_PROT",   # VIN
                    "8": "BATT_PROT",   # VINA
                    "6": "BATT_PROT",   # EN (tie to input to always enable)
                    "3": "GND",         # PGND
                    "9": "GND",         # GND
                    "7": "GND",         # PS/SYNC (GND=enable power-save mode)
                    "1": "VCC_3V3",     # VOUT
                    "10": "VCC_3V3",    # FB (tie to VOUT for fixed 3.3V)
                    "4": "L1_NODE",     # L1
                    "2": "L2_NODE",     # L2
                    "11": "GND"})       # EP (exposed thermal pad, per datasheet PowerPAD)

    # L1: 4.7uH inductor for TPS63031 L1-L2 (SW node to VOUT)
    l1 = s.add("L1", "Device:L", "4.7uH", at=(35, 145), footprint=FP_L_0805)
    label_pins(l1, {"1": "L1_NODE", "2": "L2_NODE"})

    # C4, C5: TPS63031 input/output caps
    c4 = s.add("C4", "Device:C", "10uF", at=(35, 155), footprint=FP_C_0805)
    label_pins(c4, {"1": "BATT_PROT", "2": "GND"})
    c5 = s.add("C5", "Device:C", "22uF", at=(55, 165), footprint=FP_C_0805)
    label_pins(c5, {"1": "VCC_3V3", "2": "GND"})

    # R3, R4: Battery voltage divider (BAT_MON)
    r3 = s.add("R3", "Device:R", "47k", at=(75, 170), footprint=FP_R_0603)
    r4 = s.add("R4", "Device:R", "47k", at=(75, 180), footprint=FP_R_0603)
    label_pins(r3, {"1": "BATT_PROT", "2": "BAT_MON"})
    label_pins(r4, {"1": "BAT_MON", "2": "GND"})

    # ===== MCU SECTION =====

    # U1: Waveshare ESP32-C6-Zero (socketed via 2x9 2.54mm pin socket headers)
    # Powered via 3V3 pin directly from RT6150A — Zero's internal LDO is bypassed.
    # Zero's onboard USB-C handles flashing (tucked inside enclosure; open case to access).
    # Pinout confirmed from official Waveshare diagram:
    #   Left  (1-9) : 5V  GND  3V3  GP0-GP5
    #   Right (10-18): TX  RX  GP14 GP15 GP18 GP19 GP20 GP21 GP22
    #   Bottom(19-25): GP13 GP12 GP23 GP9/BOOT GP8/LED GP7 GP6
    u1 = s.add("U1", "autofeeder:ESP32_C6_Zero", "ESP32-C6-Zero",
               at=(120, 75), footprint=FP_ESP)
    # Power
    label_pins(u1, {"3": "VCC_3V3", "2": "GND"})
    s.no_connect(u1.pin_xy("1"))      # 5V: unused — main board USB-C powers TP4056
    # Buttons: GP0-GP5 on left rail (all ADC-capable, 6 buttons)
    label_pins(u1, {"4": "BUTTON_POWER", "5": "BUTTON_TIMER",
                    "6": "BUTTON_MANUAL", "7": "BUTTON_SETTINGS",
                    "8": "BUTTON_UP", "9": "BUTTON_DOWN"})
    # Motor control on TX/RX pads (right rail top 2) — repurposed from UART programming.
    # Programming is done via the Zero's own USB-C (tucked inside enclosure) or boot-ROM mode.
    label_pins(u1, {"10": "MOTOR_IN1", "11": "MOTOR_IN2"})
    # Display SPI: GP14=SCK, GP15=MOSI, GP18=CS
    # DISP_DC moved to bottom pad GP12 to resolve pin conflict with MOTOR_IN1 (both on GPIO19)
    label_pins(u1, {"12": "DISP_SCK", "13": "DISP_MOSI",
                    "14": "DISP_CS"})
    # GPIO19 (pad 15) and GPIO20 (pad 16) are NC — conflicts with MOTOR pins resolved
    s.no_connect(u1.pin_xy("15"))
    s.no_connect(u1.pin_xy("16"))
    # CAN bus: GP21=TX, GP22=RX
    label_pins(u1, {"17": "CAN_TX", "18": "CAN_RX"})
    # Bottom edge pads (19-25) — accessed via pogo pins soldered into through-holes.
    # These contact the Zero module's bottom castellated pads.
    # Pad 20 (GP12): DISP_DC (moved from conflicted GPIO19)
    # Pad 25 (GP6):  BAT_MON (moved from conflicted GPIO20, ADC-capable)
    # Pad 19 (GP13): I2C_SDA (DS3231 RTC)
    # Pad 21 (GP23): I2C_SCL (DS3231 RTC)
    # Pad 24 (GP7):  GPS_TX (UART TX to GPS module)
    # Pad 23 (GP8):  GPS_RX (UART RX from GPS module, strapping — input only)
    # Pad 22 (GP9):  NC (BOOT strapping, avoid)
    label_pins(u1, {"20": "DISP_DC", "25": "BAT_MON",
                    "19": "I2C_SDA", "21": "I2C_SCL",
                    "24": "GPS_TX", "23": "GPS_RX"})
    # GP9/BOOT — strapping, used to drive CAN_RS (SN65HVD230 standby)
    # HIGH during sleep = CAN standby mode (~1µA); LOW during active = CAN high-speed
    label_pins(u1, {"22": "CAN_RS"})

    # C1, C2: ESP32 decoupling
    c1 = s.add("C1", "Device:C", "100nF", at=(145, 60), footprint=FP_C_0603)
    label_pins(c1, {"1": "VCC_3V3", "2": "GND"})
    c2 = s.add("C2", "Device:C", "10uF", at=(145, 70), footprint=FP_C_0805)
    label_pins(c2, {"1": "VCC_3V3", "2": "GND"})

    # R9: EN pull-up removed — EN is internal on the ESP32-C6-Zero and not exposed on the socket.

    # ===== MOTOR SECTION =====
    # MX1508 dual H-bridge breakout board, connected via 2× JST XH 2-pin cables
    # Motor output connects directly from MX1508 to the motor — not on main PCB.

    # J_MOTOR_CTRL: MX1508 logic inputs from ESP32
    j_mtr_ctrl = s.add("J_MOTOR_CTRL", "autofeeder:JST_XH_2P", "MOTOR_CTRL", at=(55, 210), footprint=FP_JST_XH)
    label_pins(j_mtr_ctrl, {"1": "MOTOR_IN1", "2": "MOTOR_IN2"})

    # J_MOTOR_PWR: MX1508 power supply (battery + ground)
    j_mtr_pwr = s.add("J_MOTOR_PWR", "autofeeder:JST_XH_2P", "MOTOR_PWR", at=(55, 230), footprint=FP_JST_XH)
    label_pins(j_mtr_pwr, {"1": "BATT_PROT", "2": "GND"})

    # ===== CAN SECTION =====

    # U6: SN65HVD230 CAN transceiver
    u6 = s.add("U6", "autofeeder:SN65HVD230", "SN65HVD230", at=(150, 210), footprint=FP_SOIC8)
    label_pins(u6, {"1": "CAN_TX", "4": "CAN_RX", "8": "RS_NC",
                    "7": "CAN_H", "6": "CAN_L",
                    "5": "VREF_NC", "3": "VCC_3V3", "2": "GND"})
    s.no_connect(u6.pin_xy("5"))
    # RS pin (8) driven by GP9 for standby mode during sleep
    label_pins(u6, {"8": "CAN_RS"})

    # R5: CAN termination (120R, selectable via solder jumper)
    r5 = s.add("R5", "Device:R", "120R", at=(170, 210), footprint=FP_R_0603)
    label_pins(r5, {"1": "CAN_H", "2": "CAN_L"})

    # R6, R10: CAN series protection
    r6 = s.add("R6", "Device:R", "1k", at=(170, 195), footprint=FP_R_0603)
    r10 = s.add("R10", "Device:R", "1k", at=(170, 225), footprint=FP_R_0603)
    label_pins(r6, {"1": "CAN_H", "2": "CAN_H_PROT"})
    label_pins(r10, {"1": "CAN_L", "2": "CAN_L_PROT"})
    label_at("CAN_H_PROT", j3.pin_xy("A8"))
    label_at("CAN_L_PROT", j3.pin_xy("B8"))

    # C6: CAN decoupling
    c6 = s.add("C6", "Device:C", "100nF", at=(160, 195), footprint=FP_C_0603)
    label_pins(c6, {"1": "VCC_3V3", "2": "GND"})

    # ===== DISPLAY SECTION =====

    # DISP1: SSD1306 OLED
    disp1 = s.add("DISP1", "autofeeder:OLED_SSD1306_SPI", "OLED_SSD1306", at=(200, 40), footprint=FP_OLED)
    label_pins(disp1, {"1": "VCC_3V3", "2": "GND",
                       "3": "DISP_CS", "4": "DISP_DC",
                       "5": "DISP_RST", "6": "DISP_SCK", "7": "DISP_MOSI"})

    # C3: Display decoupling
    c3 = s.add("C3", "Device:C", "100nF", at=(200, 60), footprint=FP_C_0603)
    label_pins(c3, {"1": "VCC_3V3", "2": "GND"})

    # ===== BUTTONS =====

    btn_config = [
        ("SW1_POWER", "BUTTON_POWER", (200, 85)),
        ("SW2_TIMER", "BUTTON_TIMER", (200, 98)),
        ("SW3_MANUAL", "BUTTON_MANUAL", (200, 111)),
        ("SW4_SETTINGS", "BUTTON_SETTINGS", (200, 124)),
        ("SW5_UP", "BUTTON_UP", (200, 137)),
        ("SW6_DOWN", "BUTTON_DOWN", (200, 150)),
    ]
    for ref, net, pos in btn_config:
        sw = s.add(ref, "autofeeder:SW_ALPS_SKRPADE010", "Alps SKRPADE010",
                   at=pos, footprint=FP_SW_TACT)
        # Pins 1-2 are one switch, 3-4 are the other (4-pin tactile switch)
        # Connect P1 to the GPIO, P2 to GND (or P3/P4 respectively)
        label_at(net, sw.pin_xy("1"))
        label_at("GND", sw.pin_xy("2"))

    # ===== PROGRAMMING HEADER =====

    # J4: debug/power header (UART pads repurposed for motor; Zero's USB-C handles flashing)
    j4 = s.add("J4", "Connector_Generic:Conn_01x04", "DBG", at=(150, 250), footprint=FP_PIN_1x4)
    label_pins(j4, {"1": "VCC_3V3", "4": "GND"})
    s.no_connect(j4.pin_xy("2"))
    s.no_connect(j4.pin_xy("3"))

    # ===== RTC SECTION (DS3231 module) =====

    # J_RTC: 4-pin header for DS3231 module (ZS-042 or equivalent)
    # Pinout: VCC, GND, SDA, SCL. Module has onboard pull-ups and CR2032 holder.
    j_rtc = s.add("J_RTC", "Connector_Generic:Conn_01x04", "DS3231", at=(170, 145),
                  footprint=FP_PIN_1x4)
    label_pins(j_rtc, {"1": "VCC_3V3", "2": "GND", "3": "I2C_SDA", "4": "I2C_SCL"})

    # ===== GPS SECTION =====

    # J_GPS: 4-pin header for NEO-6M/NEO-8M GPS module
    # Pinout: VCC, GND, GPS_RX (module TX→ESP), GPS_TX (ESP→module RX)
    j_gps = s.add("J_GPS", "Connector_Generic:Conn_01x04", "GPS", at=(170, 170),
                  footprint=FP_PIN_1x4)
    label_pins(j_gps, {"1": "VCC_3V3", "2": "GND", "3": "GPS_RX", "4": "GPS_TX"})

    # ===== DISPLAY PULL-UPS =====

    # R13: DISP_RST pull-up — SSD1306 RST pin held high; no GPIO needed for hardware reset
    r13 = s.add("R13", "Device:R", "10k", at=(240, 40), footprint=FP_R_0603)
    label_pins(r13, {"1": "VCC_3V3", "2": "DISP_RST"})

    # STATUS LED: replaced by the WS2812B RGB LED built into the ESP32-C6-Zero (on IO8/pad 12).
    # No discrete LED or current-limit resistor needed on the main board.

    # ===== POWER SYMBOLS =====

    pwr_vbus = s.add("PWR_VBUS", "power:PWR_FLAG", "PWR_FLAG", at=(30, 55))
    label_at("VBUS", pwr_vbus.pin_xy("1"))

    pwr_batt = s.add("PWR_BATT", "power:PWR_FLAG", "PWR_FLAG", at=(55, 130))
    label_at("BATT_PROT", pwr_batt.pin_xy("1"))

    pwr_3v3 = s.add("PWR_3V3", "power:PWR_FLAG", "PWR_FLAG", at=(100, 155))
    label_at("VCC_3V3", pwr_3v3.pin_xy("1"))

    gnd_main = s.add("GND_MAIN", "power:GND", "GND", at=(100, 165))
    label_at("GND", gnd_main.pin_xy("1"))

    return s


def main() -> None:
    s = build()
    SCH_PATH.parent.mkdir(parents=True, exist_ok=True)
    s.check_paren_balance()
    s.write(SCH_PATH)
    print(f"wrote {SCH_PATH}")
    print(f"  components: {len(s.components)}  local labels: {len(s.local_labels)}")


if __name__ == "__main__":
    main()
