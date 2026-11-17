# Si5351 / PICAXE-08M2 TRNG — project notes (17 Nov 2026)

Status: schematic V6 (V1-V5 kept; V6 = V5 with R1 standing beside the signal row (rule A8) and the date as 11/26 (rule A9a), same netlist; verify with `python3 schematic/verify_netlist_v2.py schematic/trng_v6_netlist.xml`). Earlier note: schematic V5 ( V5 = V4 pulled together onto an A4 sheet, same netlist, RST tie label hidden because it sat on the SCL wire). V4 draws the 74HCT74 as one box with its real DIP pin numbers (no separate power unit); V3 had moved U5C next to the flip-flops. Check netlist with `python3 schematic/verify_netlist_v2.py schematic/trng_v5_netlist.xml`. Firmware rev 1 written and compiled (not downloaded or run): see `firmware/FIRMWARE_NOTES.md` for the wiring list, register notes, test procedure and risks. Open item (closed in practice): the user reports having programmed and used these boards with the 08M2 many times; the seller also says the Si5351 boards level-shift I2C and have a 3.3 V LDO, so 5 V on the multiplexer should be fine; confirm with one measurement (risk 1 there).

## V2 change (from V1)
All serial goes through the one download socket J2: sertxd out on C.0, serin/serrxd in on C.5 (fixed 4800 baud at 4 MHz, 9600 at 8 MHz, per PICAXE manual 2). The separate diagnostic connector J3 is gone. The FF2 capture clock moved from C.0 to C.4 (pin 3), so nothing shares the programming pin any more. ERC 0 errors; verify_netlist_v2.py: 16 nets MATCH.

## Folder
- `docs/` spec (from Chat), PICAXE manuals 1 and 2 (manual 2 is v7.9.2, 2015), PICAXE M2 summary, PIC12F1822 datasheet, Si5351 datasheet and AN619, TCA9548A datasheet.
- `71YAEIWKbXL...avif` Si5351 module photo, `619KXtz5D0L...avif` multiplexer photo (both supplied by the user).
- `schematic/trng_v1.*` schematic (kicad_sch, pdf, 300 dpi png), ERC report, netlist, generator `trng_sch.py` + `kisch.py`, `verify_netlist.py`.

## Verified from documents
- 08M2 physical pins: 1 +V, 2 C.5 serial in, 3 C.4, 4 C.3 (input only, TTL level), 5 C.2, 6 C.1, 7 C.0 serial out, 8 0V.
- The 08M2 HAS hardware I2C master (hi2csetup/hi2cin/hi2cout): C.1 = SCL, C.2 = SDA. The spec says it does not and puts SDA on C.1 / SCL on C.2; the spec is wrong on both.
- On the 08M2 the `[newslave]` option of hi2cin/hi2cout is X2-only, so switching between the TCA (0xE0) and an Si5351 (0xC0) means a new `hi2csetup` each time.
- TCA9548A supply is 1.65 to 5.5 V (TI datasheet), not 1.65 to 3.6 V as in the spec. The board chip marking in the photo looks like PCA9548A (2.3 to 5.5 V); both accept 5 V.
- Si5351 board: 25 MHz crystal printed on it, 10k ("103") resistors and what look like a regulator and two level-shift transistors on it (not confirmed).
- Download circuit (22k, 10k, 100 nF) is the PICAXE manual 1 minimum circuit.

## Baseline netlist (verify_netlist.py: 16 nets, MATCH)
+5V: J1.1 U1.1 C1.1 U2.VIN U2.RST U3.VIN U4.VIN U5.14 C2.1 U5.1 U5.4 U5.10 U5.13
0V: J1.2 J2.3 J3.2 R2.2 U1.8 C1.2 U2.GND U2.A0 U2.A1 U2.A2 U3.GND U4.GND U5.7 C2.2
SDA U1.5(C.2) - U2.SDA ; SCL U1.6(C.1) - U2.SCL
ch0: U2.SD0 - U3.SDA, U2.SC0 - U3.SCL ; ch1: U2.SD1 - U4.SDA, U2.SC1 - U4.SCL
CLK A: U3 "0" (CLK0) - U5.2 (D1) ; CLK B: U4 "0" (CLK0) - U5.3 (CLK1)
Q1: U5.5 - U5.12 ; capture: U1.7 (C.0) - U5.11 (CLK2) - J2.2 ; Q2: U5.9 - U1.4 (C.3)
download: J2.1 - R1 (22k) - U1.2 - R2 (10k) - 0V ; diag: U1.3 (C.4) - J3.1

## Open facts (need the real boards)
1. (closed, user confirmed 17 Nov 2026) Si5351 header holes 0, 1, 2 are the CLK0, CLK1, CLK2 outputs; hole 0 = CLK0.
2. Multiplexer RST and A0-A2: the schematic ties RST to +5V and A0-A2 to 0V (spec: address 0x70). Check whether the HW-617 already has pull-ups/pull-downs on them.
3. (closed, user said so repeatedly) I2C pull-ups: the user has used these boards on the 08M2's I2C with no problem and no added parts, so none are needed or drawn.
4. Both modules' VIN assumed 5 V (system is 5 V). Confirm the Si5351 board's onboard regulator before powering.
5. (V1 only, resolved in V2) C.0 was shared between serial out and the capture clock.
