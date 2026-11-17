# Si5351 TRNG

An experimental **hardware true-random-number generator** built from parts on hand: two free-running **Si5351 clock-generator boards**, a **74HCT74** dual D flip-flop, a **TCA9548A I2C multiplexer board** and a **PICAXE-08M2**.

**This is an experiment. Nothing here claims that the output is random.** The point of the project is to build the source, collect raw bits, and find out.

## What we are trying to do

1. Two Si5351 boards, each with its own 25 MHz crystal, are programmed over I2C (through the TCA9548A, so one PICAXE can talk to both at the same address) to nominal **8.000 MHz** and **8.001 MHz**.
2. The 8.000 MHz clock goes to the D input of the first flip-flop of a 74HCT74 and the 8.001 MHz clock clocks it. The two clocks beat at about 1 kHz, so the flip-flop samples a continuously sliding phase.
3. The second flip-flop is a snapshot register. The PICAXE pulses its clock (C.4), waits, and reads Q2 (C.3) at roughly **100 bits per second**.
4. The PICAXE packs the bits into bytes (MSB first) and sends them as ASCII hex lines out the PICAXE download socket (4800 baud). A host script captures them and runs screening statistics.
5. The candidate entropy is **phase noise and drift between the two independent crystals**. The frequency offset alone is deterministic, so a balanced bit histogram proves nothing. The host analysis is aimed at the likely failure, a periodic or aliased beat pattern (see the next section).

The firmware has two build modes: RAW TEST (raw captured bits, no conditioning) and CONDITIONED (Von Neumann pairs: 01 -> 0, 10 -> 1, 00/11 dropped). Start with raw.

## How the jitter technique works, and where it can fail

**The idea.** Two independent oscillators never keep perfect time against each other. Their edges wander by tens of picoseconds (jitter) and drift slowly with temperature. If one clock samples the other, the exact moment the sampling edge lands against the sampled edge is slightly unpredictable. A flip-flop turns that tiny timing uncertainty into a 0 or a 1, but only when the two edges land very close together.

**What this circuit does.** FF1 samples clock A (8.000 MHz) on every rising edge of clock B (8.001 MHz). B is 1 kHz faster, so each B edge lands about 15.6 ps later against A than the one before (125 ns x 1 kHz / 8 MHz). After about 8000 B edges (1 ms) the sampling point has slid through a whole A cycle. FF1's output Q1 is therefore high while B's edges land in A's high half and low while they land in A's low half: roughly a 1 kHz square wave, with noisy edges.

**Where jitter matters.** Only near the two transitions per beat, where B's edge is within a jitter-width of an A edge, does Q1 depend on jitter. The Si5351 datasheet gives typical period jitter of 70 ps peak-to-peak (155 ps maximum) for the 10-MSOP part at the default drive strength. For two independent clocks that makes each transition region span roughly 5 to 15 B edges. Out of 8000 edges per beat, that is a fraction of a percent of the time. (This is a back-of-envelope estimate from datasheet numbers, assuming 50% duty cycles and independent jitter. It has not been measured.)

**What the PICAXE does.** FF2 takes a snapshot of Q1 at an instant the PICAXE chooses (a pulse on C.4), about 100 times a second. The PICAXE runs from its own resonator, unrelated to the two crystals, so each read lands on a different point of the beat.

**Where it can fail**

1. Most reads land on a plateau of Q1, far from a transition. The bit is then set by where in the 1 ms beat the read happened, not by jitter. If the read timing is steady, the stored sequence is a regular alias of the beat. Whatever randomness remains comes from the PICAXE's own timing wandering against the beat, which is not the effect the technique is meant to rely on.
2. Only a fraction of a percent of reads (estimate above) fall in a jitter-dependent window, so the real entropy per bit could be far below one bit, even if the bit stream looks balanced.
3. A 10 ms read interval is nominally ten beat periods. The PICAXE is not locked to the Si5351 crystals, so the phase of successive reads creeps slowly, which can produce long runs or a slow repeating pattern.
4. FF2 is a snapshot register, not a designed synchronizer. A read very close to a Q1 transition can be metastable. That is the same rare event as point 2.
5. Crystal drift is smooth and partly predictable, so it is a weak source over short times.

**What the data will tell us.** The host analysis looks first for exactly these patterns: strong autocorrelation, spectral lines, a skewed two-bit pattern count. If it finds them, the likely cause is the plateau effect above, and that would be a design finding about what the PICAXE samples, not a bug in the code. Nothing has been measured yet.

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
