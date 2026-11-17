# Si5351 TRNG

An experimental **hardware true-random-number generator** built from parts on hand: two free-running **Si5351 clock-generator boards**, a **74HCT74** dual D flip-flop, a **TCA9548A I2C multiplexer board** and a **PICAXE-08M2**.

**This is an experiment. Nothing here claims that the output is random.** The point of the project is to build the source, collect raw bits, and find out.

## What we are trying to do

1. Two Si5351 boards, each with its own 25 MHz crystal, are programmed over I2C (through the TCA9548A, so one PICAXE can talk to both at the same address) to nominal **8.000 MHz** and **8.001 MHz**.
2. The 8.000 MHz clock goes to the D input of the first flip-flop of a 74HCT74 and the 8.001 MHz clock clocks it. The two clocks beat at about 1 kHz, so the flip-flop samples a continuously sliding phase.
3. The second flip-flop is a snapshot register. The PICAXE pulses its clock (C.4), waits, and reads Q2 (C.3) at roughly **100 bits per second**.
4. The PICAXE packs the bits into bytes (MSB first) and sends them as ASCII hex lines out the PICAXE download socket (4800 baud). A host script captures them and runs screening statistics.
5. The candidate entropy is **phase noise and drift between the two independent crystals**. The frequency offset alone is deterministic, so a balanced bit histogram proves nothing. The host analysis is aimed at the likely failure, a periodic or aliased beat pattern.

The firmware has two build modes: RAW TEST (raw captured bits, no conditioning) and CONDITIONED (Von Neumann pairs: 01 -> 0, 10 -> 1, 00/11 dropped). Start with raw.

## Status

| Part | State |
|---|---|
| Schematic (KiCad, V6) | done: ERC 0 errors, netlist checked against the baseline |
| PICAXE-08M2 firmware | written and compiled (syntax check, 686 of 2048 bytes); **not run on hardware** |
| Host capture / analysis tools | written, tested on synthetic data only |

## Hardware

- PICAXE-08M2 (hardware I2C: **C.1 = SCL, C.2 = SDA**), C.4 = capture clock, C.3 = Q2 input, C.0 / C.5 = serial out / in through the download socket.
- 74HCT74 (HCT so the 3.3 V Si5351 outputs clear the 5 V logic threshold).
- HW-617 TCA9548A board (address 0x70), two Si5351 boards (address 0x60 each, behind channels 0 and 1).
- 5 V supply. Pin-to-pin wiring list: `firmware/FIRMWARE_NOTES.md`.

## Layout of this repository

- `schematic/` KiCad schematic V6 (`trng_v6.kicad_sch`, PDF, PNG), exported netlist, ERC report, the Python that generates it, and `verify_netlist_v2.py` (checks the exported netlist against the baseline).
- `firmware/` `si5351_trng.bas` (PICAXE-08M2 BASIC), `si5351_regs.py` (register calculator with an independent decode check), `FIRMWARE_NOTES.md` (wiring list, register notes, test procedure, risks), `host/` (`capture_raw.py`, `analyze_raw.py`, `selftest.py`).
- `docs/` the original specification and links to the datasheets.
- `NOTES.md` working notes and the open items list.

Earlier schematic revisions (V1-V5) are kept outside this repository; this one tracks V6 onward in git history.

## Quick start

```
picaxe08m2 -s firmware/si5351_trng.bas       # syntax check only (PICAXE Linux compiler)
python3 firmware/si5351_regs.py              # Si5351 register values, with decode check
python3 firmware/host/selftest.py            # host tools on synthetic data (run inside firmware/host)
python3 firmware/host/capture_raw.py /dev/ttyUSB0 --bits 100000 --out run1
python3 firmware/host/analyze_raw.py run1.bin
```
Edit `runmode = 0` (RAW) or `1` (CONDITIONED) near the top of the firmware. The real sample rate is not known until it is measured on the board; `capture_raw.py` prints it, and `SPAUSE` in the firmware is the knob.

## Known risks and open items

See `NOTES.md` and `firmware/FIRMWARE_NOTES.md`. Main points: the second flip-flop is a snapshot register, not a designed synchronizer, so metastability is possible; the sampled bits may follow a regular beat pattern; nothing has been run on hardware yet.

## Credit and license

Ethelbert Design, 11/26. No license has been chosen yet; until one is added, all rights are reserved.
