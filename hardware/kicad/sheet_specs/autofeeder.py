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
FP_OLED = "Display:SSD1306_128x64_SPI"


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
    # USB-C SHIELD
    s.no_connect(j3.pin_xy("S1"))
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
    # SBU1/2 → CAN_H/L
    label_at("CAN_H", j3.pin_xy("A8"))
    label_at("CAN_L", j3.pin_xy("B8"))

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

    # U3: DW01A+FS8205A battery protection
    u3 = s.add("U3", "autofeeder:DW01A_FS8205A", "DW01A+FS8205A", at=(55, 110), footprint="")
    label_pins(u3, {"B+": "BATT_CHG", "B-": "BATT_N", "P+": "BATT_PROT", "P-": "GND"})

    # U4: TPS63802 buck-boost
    u4 = s.add("U4", "autofeeder:TPS63802", "TPS63802", at=(55, 150), footprint="")
    label_pins(u4, {"7": "BATT_PROT", "1": "VCC_3V3", "9": "VCC_3V3",
                    "2": "FB", "6": "EN_3V3", "3": "EN_3V3",
                    "4,10": "GND", "8": "SW"})

    # C4, C5: TPS63802 caps
    c4 = s.add("C4", "Device:C", "10uF", at=(35, 150), footprint=FP_C_0805)
    label_pins(c4, {"1": "BATT_PROT", "2": "GND"})
    c5 = s.add("C5", "Device:C", "22uF", at=(75, 150), footprint=FP_C_0805)
    label_pins(c5, {"1": "VCC_3V3", "2": "GND"})

    # R3, R4: Battery voltage divider (BAT_MON)
    r3 = s.add("R3", "Device:R", "10k", at=(75, 170), footprint=FP_R_0603)
    r4 = s.add("R4", "Device:R", "10k", at=(75, 180), footprint=FP_R_0603)
    label_pins(r3, {"1": "BATT_PROT", "2": "BAT_MON"})
    label_pins(r4, {"1": "BAT_MON", "2": "GND"})

    # ===== MCU SECTION =====

    # U1: ESP32-C6-WROOM-1
    u1 = s.add("U1", "autofeeder:ESP32-C6-WROOM-1", "ESP32-C6-WROOM-1", at=(120, 75))
    label_pins(u1, {"24": "VCC_3V3", "25": "EN_3V3", "1": "GND", "26": "GND"})
    # Display GPIOs
    label_pins(u1, {"16": "DISP_CS", "17": "DISP_DC", "13": "DISP_RST",
                    "18": "DISP_SCK", "19": "DISP_MOSI"})
    # Motor GPIOs
    label_pins(u1, {"14": "MOTOR_IN1", "11": "MOTOR_IN2"})
    # CAN GPIOs
    label_pins(u1, {"21": "CAN_TX", "22": "CAN_RX"})
    # Buttons GPIOs
    label_pins(u1, {"4": "BUTTON_POWER", "5": "BUTTON_TIMER",
                    "7": "BUTTON_MANUAL", "8": "BUTTON_SETTINGS",
                    "9": "BUTTON_UP", "10": "BUTTON_DOWN"})
    # Battery ADC
    label_pins(u1, {"6": "BAT_MON"})
    # Status LED
    label_pins(u1, {"2": "STATUS_LED"})
    # TXD0/RXD0 (programming UART)
    label_pins(u1, {"2": "PROG_TX", "3": "PROG_RX"})

    # C1, C2: ESP32 decoupling
    c1 = s.add("C1", "Device:C", "100nF", at=(145, 60), footprint=FP_C_0603)
    label_pins(c1, {"1": "VCC_3V3", "2": "GND"})
    c2 = s.add("C2", "Device:C", "10uF", at=(145, 70), footprint=FP_C_0805)
    label_pins(c2, {"1": "VCC_3V3", "2": "GND"})

    # R9: EN pull-up to 3V3
    r9 = s.add("R9", "Device:R", "10k", at=(120, 95), footprint=FP_R_0603)
    label_pins(r9, {"1": "EN_3V3", "2": "VCC_3V3"})

    # ===== MOTOR SECTION =====

    # U5: DRV8871 H-bridge
    u5 = s.add("U5", "autofeeder:DRV8871", "DRV8871", at=(55, 210), footprint=FP_SOIC8)
    label_pins(u5, {"1": "MOTOR_IN1", "2": "MOTOR_IN2",
                    "7": "M1_P", "8": "M1_N",
                    "3": "VREF_NC", "4": "IPROPI_NC",
                    "6": "BATT_PROT", "5": "GND"})
    s.no_connect(u5.pin_xy("3"))
    s.no_connect(u5.pin_xy("4"))

    # J2: Motor JST
    j2 = s.add("J2", "autofeeder:JST_XH_2P", "MOTOR", at=(55, 240), footprint=FP_JST_XH)
    label_pins(j2, {"1": "M1_P", "2": "M1_N"})

    # ===== CAN SECTION =====

    # U6: SN65HVD230 CAN transceiver
    u6 = s.add("U6", "autofeeder:SN65HVD230", "SN65HVD230", at=(150, 210), footprint=FP_SOIC8)
    label_pins(u6, {"1": "CAN_TX", "4": "CAN_RX", "8": "RS_NC",
                    "7": "CAN_H", "6": "CAN_L",
                    "5": "VREF_NC", "3": "VCC_3V3", "2": "GND"})
    s.no_connect(u6.pin_xy("5"))
    s.no_connect(u6.pin_xy("8"))

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
                   at=pos, footprint="Button_Switch_SMD:SW_SPST_SKRPADE010")
        # Pins 1-2 are one switch, 3-4 are the other (4-pin tactile switch)
        # Connect P1 to the GPIO, P2 to GND (or P3/P4 respectively)
        label_at(net, sw.pin_xy("1"))
        label_at("GND", sw.pin_xy("2"))

    # ===== PROGRAMMING HEADER =====

    j4 = s.add("J4", "Connector_Generic:Conn_01x04", "PROG", at=(150, 250), footprint=FP_PIN_1x4)
    label_pins(j4, {"1": "VCC_3V3", "2": "PROG_TX", "3": "PROG_RX", "4": "GND"})

    # ===== STATUS LED =====

    led1 = s.add("LED_STATUS", "Device:LED", "GREEN", at=(100, 95), footprint="LED_SMD:LED_0603_1608Metric")
    r7 = s.add("R7", "Device:R", "330R", at=(100, 105), footprint=FP_R_0603)
    label_pins(r7, {"1": "STATUS_LED", "2": "LED_L"})
    label_pins(led1, {"1": "VCC_3V3", "2": "LED_L"})

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
