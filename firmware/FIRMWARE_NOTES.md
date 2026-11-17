# Si5351 TRNG firmware rev 1 — notes, wiring list, register notes, test procedure

Status: `si5351_trng.bas` compiles (PICAXE-08M2 compiler 3.1, `-s` syntax check, 686 of 2048 bytes). It has NOT been downloaded or run on hardware. The host tools were tested on synthetic data only. Nothing here shows that the bits are random.

## Files (this folder)
- `si5351_trng.bas` firmware (edit `runmode = 0` for RAW TEST, `1` for CONDITIONED / Von Neumann).
- `si5351_regs.py` register calculator with an independent decode check (`python3 si5351_regs.py [xtal_hz]`).
- `host/capture_raw.py` capture from the serial port (or `--replay` a saved log) to `.bin` and `.log`; `host/analyze_raw.py` screening statistics; `host/selftest.py` synthetic round-trip test.
- Schematic V5 (latest): `../schematic/trng_v5.*` (V1-V4 kept). Pin numbers below are the 74HCT74's real DIP-14 pins, as on the V4 box.

## Wiring list (physical pins)
PICAXE-08M2 (DIP-8): 1 +5 V (100 nF to pin 8) | 2 C.5 serial in: from download socket SER_IN through R1 22k; R2 10k from pin 2 to 0 V | 3 C.4 capture clock -> 74HCT74 pin 11 | 4 C.3 input <- 74HCT74 pin 9 | 5 C.2 SDA -> TCA SDA | 6 C.1 SCL -> TCA SCL | 7 C.0 serial out -> download socket SER_OUT | 8 0 V.
74HCT74 (DIP-14): 1 /CLR1 +5 V | 2 D1 <- Si5351 A hole "0" | 3 CLK1 <- Si5351 B hole "0" | 4 /PRE1 +5 V | 5 Q1 -> pin 12 | 6 /Q1 not connected | 7 GND | 8 /Q2 not connected | 9 Q2 -> PICAXE pin 4 | 10 /PRE2 +5 V | 11 CLK2 <- PICAXE pin 3 | 12 D2 <- pin 5 | 13 /CLR2 +5 V | 14 VCC +5 V; 100 nF across 14-7.
TCA9548A HW-617: VIN +5 V (see risk 1) | GND | SDA <- PICAXE pin 5 | SCL <- PICAXE pin 6 | RST +5 V | A0, A1, A2 0 V | SD0, SC0 -> Si5351 A SDA, SCL | SD1, SC1 -> Si5351 B SDA, SCL | SD2..SC7 unused.
Si5351 A and B: VIN +5 V | GND | SDA, SCL from the TCA channel | hole "0" (CLK0) -> 74HCT74 as above | holes "1", "2" unused.
Common 0 V everywhere. Power: 5 V only.

## Si5351 register notes (AN619; checked by `si5351_regs.py`)
25 MHz crystal (printed on the boards). PLLA = 25 MHz x 32 = 800 MHz (valid 600-900 MHz). A: MS0 = 100, output 8.000000 MHz. B: MS0 = 99 + 7901/8001, output 8.001000 MHz (exact, assuming ideal crystals). R divider = 1.
PLLA regs 26..33 = 00 01 00 0E 00 00 00 00. MS0 regs 42..49: A = 00 01 00 30 00 00 00 00; B = 1F 41 00 2F FE 00 0C 82.
Sequence per chip (the same as in the firmware): wait SYS_INIT = 0 (reg 0 bit 7); outputs off (reg 3 = FF); drivers off (regs 16-23 = 80); crystal load reg 183 = D2 (10 pF, the default); PLLA and MS0 regs; reg 16 = 0F (CLK0 on, fractional MS0, PLLA, 8 mA); PLL reset reg 177 = A0; reg 3 = FE (CLK0 only); read back regs 16, 3, 45-46 and status (SYS_INIT, LOL_A, LOS_XTAL must be 0; LOL_B ignored because PLLB is unused). 8 mA drive and the 10 pF load are assumptions, not measured.

## Output format
Lines end CR LF at 4800 baud (4 MHz default): `I:` info, `E:code chip` error (program stops, capture clock low), `D:` 16 raw bytes (RAW mode), `C:` 16 conditioned bytes, `S:r= a= d= o= t=` status every 16 data lines (r raw bits, a pairs accepted, d pairs dropped, o bytes, t seconds; 16-bit counters wrap at 65536). Bits are packed MSB first. Errors: 1 multiplexer write/readback failed, 2 Si5351 not out of init (also no ACK), 3 register readback mismatch, 4 PLL not locked or crystal lost.
Cadence: each sample costs `pause SPAUSE` (8 ms) plus command time and a few ms of serial output once per byte, so the real rate is not known until measured; `capture_raw.py` prints the measured rate from host arrival times. Adjust `SPAUSE` after measuring. I did not assume `pause 10` gives 100/s.

## Startup and functional test (no analog adjustment)
0. Before power, with a meter: check there is no short between +5 V and 0 V on each board. Read risk 1 below first.
1. Power the PICAXE alone, download the firmware (editor or `picaxe08m2 si5351_trng.bas`; I have not downloaded anything), open a 4800 baud terminal. Expect `I:SI5351TRNG fw1 08M2 mode=RAW`, then `I:chip 0 ok`, `I:chip 1 ok`, `I:clocks ...`, then `D:` lines. Any `E:` line is the failure indicator (codes above).
2. With a scope or counter: CLK0 of A = 8.000 MHz and of B = 8.001 MHz; 74HCT74 pin 9 (Q2) is a stable level after each C.4 pulse; C.4 pulses about 30 us wide.
3. `python3 host/capture_raw.py /dev/ttyUSB0 --bits 100000 --out run1` (about 17 minutes at 100 bits/s), then `python3 host/analyze_raw.py run1.bin`.
4. Read the analysis for patterns, not for a pass: a balanced bit count with strong autocorrelation or spectral lines means a deterministic beat pattern, not entropy.

## Risks and unresolved facts
1. I2C level translation (lowered from a decision to a check): the TCA9548A pass gates limit the voltage passed between buses according to its own supply (TI datasheet section 8.2.1), and the Si5351 chip's SCL/SDA pins are rated to 3.8 V absolute maximum. The seller's listing for the Si5351 board (pasted by the user, not verified) says: 3 to 5 V input, onboard 3.3 V LDO, level shifting on the I2C lines. The photo shows two SOT-23 parts and 10k resistors, consistent with that. If true, the 5 V multiplexer is fine and the 3.3 V multiplexer option is not needed. The user also reports many prior uses of these boards with the 08M2 (details not recorded), which closes this in practice. Optional confirmation: power one Si5351 board alone at 5 V and read its SDA/SCL header pins at idle before connecting it to the multiplexer.
2. (closed, user confirmed) Si5351 header holes 0, 1, 2 are CLK0, CLK1, CLK2; hole 0 = CLK0. The firmware enables CLK0 only.
3. (closed) I2C pull-ups: the user has used these boards on the 08M2's I2C with no problem and no added parts, so none are needed or drawn. HW-617 RST and A0-A2 are tied as in the schematic (RST high, A0-A2 low, address 0x70).
4. 10 pF crystal load and 8 mA drive are defaults, not tuned.
5. The second flip-flop is a snapshot register, not a designed synchronizer: metastability is possible. At 100 bits/s the PICAXE waits 30 us before reading.
6. Both clocks are exact integer-ratio synthesized from separate crystals, so the beat pattern may be highly regular. Entropy has to come from phase noise and crystal drift; this is unproven.
7. The raw/conditioned counters wrap at 65536. The firmware gives no entropy estimate.
8. Not tested on hardware: I2C addresses (TCA 0x70, Si5351 0x60), timing, and the serial output.
