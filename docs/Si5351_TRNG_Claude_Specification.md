# Si5351 / PICAXE-08M2 Hardware TRNG — Firmware Handoff Specification

**Status:** Engineering specification for Claude; not a claim of validated entropy.  
**Goal:** Build a low-fuss, power-up-and-run hardware true-random-number generator using parts already on hand. Claude is responsible for implementing and reviewing the PICAXE BASIC firmware. Avoid manual tuning, repeated circuit redesign, and speculative changes.

## 1. Project overview

Two **separate, free-running Si5351 frequency-generator boards**, each with its own crystal reference, generate digital clocks. One clock feeds the D input of the first flip-flop in a **74HCT74**; the other clocks it. The second flip-flop acts as a PICAXE-controlled snapshot/holding register. A **PICAXE-08M2** configures both Si5351 devices through an **AITRIP TCA9548A eight-channel I²C multiplexer**, pulses the second flip-flop, reads the captured bit, and ultimately emits conditioned random bytes.

Physical timing jitter in the independent oscillators is the *candidate entropy source*. Frequency difference and phase drift alone are deterministic, not proof of entropy. The hardware is an experimental entropy source until raw-bit data and its predictability have been assessed. Do not claim cryptographic-grade TRNG performance on the basis of simple frequency selection or a balanced bitstream.

## 2. Firm user requirements

- **PICAXE-08M2**, not 14M2. PICAXE performs all configuration and normal operation.
- Claude writes the firmware; this document specifies behavior, hardware assumptions, and acceptance tests.
- User's system is **5 V**. Use **74HCT74** for TTL-compatible HIGH thresholds with 3.3 V-class Si5351 outputs. Do not assume a Si5351 silicon clock output is 5 V merely because its module accepts 5 V power.
- Two Si5351 modules already available; **TCA9548A breakout already available**.
- **No analog trimming, potentiometer adjustment, frequency hunting by hand, or extra hardware unless a demonstrated electrical constraint requires it.**
- Favor fixed initial frequencies, deterministic startup, simple diagnostic mode, and unattended operation.
- Initial target collection rate: **approximately 100 raw bits/s**. This is a collection-rate target, not a guaranteed entropy rate.

## 3. Hardware signal path

```
Si5351 A CLK0 ───────> 74HCT74 D1 (pin 2)
Si5351 B CLK0 ───────> 74HCT74 CLK1 (pin 3)
74HCT74 Q1 (pin 5) ──> 74HCT74 D2 (pin 12)
PICAXE C.0 ──────────> 74HCT74 CLK2 (pin 11)
74HCT74 Q2 (pin 9) ──> PICAXE C.3 (input-only)
```

74HCT74 DIP pinout: pin 1 /CLR1 HIGH, pin 4 /PRE1 HIGH, pin 10 /PRE2 HIGH, pin 13 /CLR2 HIGH; pin 14 VCC +5 V, pin 7 GND; unused /Q outputs pins 6 and 8 unconnected. Fit **100 nF decoupling** between pins 14 and 7 near the IC. All grounds common. The second stage is a holding register, **not a guaranteed metastability synchronizer**. Pulse CLK2, allow settling, then read Q2. Asynchronous capture has nonzero metastability risk.

### PICAXE-08M2 proposed logical allocation (verify package pins and firmware command support)

| PICAXE signal | Role |
|---|---|
| C.0 | Digital output: CLK2 capture pulse |
| C.1 | Bidirectional software-I²C SDA |
| C.2 | Software-I²C SCL output |
| C.3 | Input-only: captured bit from Q2 |
| C.4 | Optional diagnostic serial output |

**Important:** PICAXE-08M2 does not offer the hardware-I²C master interface assumed in an earlier 14M2 draft. Claude must implement or verify a correct **open-drain-style software I²C master**, including SDA release/high-impedance, START, STOP, ACK/NACK, address byte and register transactions. Do not drive a logic HIGH against a slave holding SDA LOW. Verify the actual C.1/C.2 electrical capabilities, `input`/`low` syntax and PICAXE-08M2 compiler behavior against PICAXE documentation before treating this pin allocation as final. If the selected 08M2 cannot meet the requirements, report the precise limitation rather than silently changing MCU.

## 4. I²C architecture and supply validation

PICAXE SDA/SCL connect to TCA9548A upstream SDA/SCL. Channel 0 SD0/SC0 connects to Si5351 A SDA/SCL; channel 1 SD1/SC1 to Si5351 B. Tie TCA A0/A1/A2 LOW for default 7-bit address **0x70** (PICAXE 8-bit write address **0xE0**). Both standard Si5351A devices use 7-bit address **0x60** (PICAXE 8-bit write address **0xC0**). Channel mask **0x01** selects A, **0x02** selects B, **0x00** deselects all. Confirm the actual Si5351 variant and module before finalizing register programming.

**Safety-critical check before powering:** TCA9548A *chip* supply rating is **1.65–3.6 V**; its I²C bus pins can tolerate up to 5.5 V under specified conditions. The advertised AITRIP breakout's claimed “1.65–5.5 V” must not be assumed to mean its bare IC VCC accepts 5 V. Inspect the exact board for an onboard regulator, wiring, and pull-up arrangement. Likewise verify Si5351 module regulator and I²C pull-ups. Maintain a 5 V system supply while respecting component-level rails. Do not connect 5 V directly to an IC VCC rated for 3.6 V. Check that downstream/upstream pull-ups and selected channels cannot backfeed 3.3 V devices or violate pin ratings. No arbitrary level-shifting parts should be added without this verification.

## 5. Initial clock configuration

- Si5351 A CLK0: **8,000,000 Hz**.
- Si5351 B CLK0: **8,001,000 Hz**.
- Two independent crystal references; do not derive both clocks from one chip.
- Frequencies are **initial functional-test settings**, not proven optimal for entropy extraction.
- Enable CLK0 on each board; disable unused outputs if appropriate; configure output drive consistently. Use documented Si5351 register/PLL/multisynth programming with valid divider constraints, PLL reset, output enable, and lock/stabilization handling. Claude must calculate and verify actual register values; no placeholders.
- The nominal 1 kHz offset creates a nominal relative phase sweep every ~1 ms, but crystal tolerances alter the actual offset and do not establish entropy.

## 6. Firmware responsibilities and operation

**Startup:**
1. Initialize PICAXE I/O in safe states; capture clock LOW; initialize software I²C.
2. Select TCA channel 0; configure Si5351 A; verify ACKs and, where practical, readback/status.
3. Select TCA channel 1; configure Si5351 B; verify ACKs and status.
4. Deselect channels if desired; wait for clocks to stabilize.
5. Enter acquisition mode; do not reprogram frequencies during routine sampling.

**Acquisition:**
1. Issue a LOW→HIGH transition on C.0 to clock the second 74HCT74.
2. Wait a conservative settling interval (initially **10 µs or more**, subject to actual PICAXE timing and instruction overhead).
3. Read C.3; return C.0 LOW; ensure sufficient low time before next capture.
4. Target approximately **100 samples/s**. Document actual cadence, including serial-transmission overhead. Prefer a reproducible interval; avoid assuming `pause 10` yields exactly 100 Hz after overhead.
5. Pack raw bits into bytes in a defined bit order (e.g., MSB first), with explicit framing when sending to a host.

**Output modes:**
- **RAW TEST:** Transmit raw captured bytes without conditioning, with a reliable binary framing protocol or explicitly documented ASCII hex diagnostic stream. Provide enough data for offline analysis (e.g., at least 100,000 raw bits if feasible). Avoid altering sample timing unpredictably during transmission; use buffering or a well-documented throughput limitation.
- **CONDITIONED:** After raw-source evaluation, implement an optional Von Neumann pair extractor: 00/11 discard, 01→0, 10→1. Pack resulting bits into bytes. **This removes bias only under assumptions about pairwise stationarity and independence; it does not manufacture entropy or guarantee cryptographic security.**
- **STATUS:** Expose I²C initialization failure, oscillator-status issues, number of raw bits collected, extractor accept/discard counts, and output-byte count, to the extent practical on 08M2 RAM/program memory.

**Recovery:** On I²C NACK, stuck bus, or failed oscillator configuration, report a clear error and retry in a bounded way or stop safely. Do not silently emit purported random data when setup fails.

## 7. Technical cautions Claude must address

1. **Software I²C:** Verify whether the 08M2 has sufficient pin and memory resources, and that software I²C correctly handles register addressing, ACK, and repeated START where required. PICAXE 8-bit I²C address conventions must not be confused with 7-bit addresses.
2. **Si5351 setup:** A usable frequency is not enough; PLL and multisynth settings must be valid and independently initialized per board. Do not assume both boards have address jumpers.
3. **Sampling timing:** The first flip-flop samples continuously at ~8 MHz; the PICAXE does not read those millions of intermediate samples. The observed 100-bit/s sequence can be strongly correlated or deterministic even if its histogram looks balanced.
4. **Metastability:** A second asynchronous flip-flop clocked by the PICAXE is a snapshot register, not a formally designed two-stage synchronizer. Wait before reading; do not claim absolute protection.
5. **Raw entropy:** Von Neumann output is not proof of unpredictability. No entropy-rate guarantee is presently established. Avoid calling the result cryptographically secure until appropriate characterization and conditioning are justified.
6. **Resource limits:** Explicitly check 08M2 program memory, RAM, baud rate, and practical raw-data throughput. No pseudocode presented as complete working firmware.
7. **Board voltage:** Confirm exact AITRIP and Si5351 breakout circuits before wiring their VCC pins. “5 V system” does not override IC absolute maximum ratings.

## 8. Deliverables requested from Claude

1. **Complete, compilable PICAXE-08M2 BASIC source** with software I²C, TCA9548A channel selection, Si5351 register configuration for both frequencies, and sampling/byte assembly.
2. Clearly marked **RAW TEST / CONDITIONED** build-time mode or equivalent, with output format specified.
3. Verified **pin-to-pin wiring list**, including the actual 08M2 physical pin numbers, 74HCT74, TCA9548A and Si5351 modules; identify any unresolved board-specific supply questions before connecting power.
4. **Si5351 register-value calculation notes** and a check that both frequencies are synthesizable with the chosen clock reference (typically 25 MHz; verify actual crystals).
5. **Concise startup and functional test procedure**, with expected signals and error indicators, requiring no analog adjustment.
6. A short list of **specific unresolved facts** (if any), rather than silently assuming them.

## 9. Acceptance criteria

- The code compiles for **PICAXE-08M2**, not a different PICAXE model.
- Both Si5351 modules are initialized through separate TCA9548A channels at the same Si5351 I²C address.
- Each CLK0 runs at its programmed nominal frequency, verified with a frequency counter/scope if available.
- 74HCT74 Q2 is readable as a stable digital level after each PICAXE capture pulse.
- Raw data are emitted without hidden whitening; output order and cadence are documented.
- Optional conditioning is distinct from raw capture, with measured throughput.
- No claim that entropy has been proven merely because bits vary or statistical tests pass.
- No manual trimming, trial-and-error hardware modifications, or new chips beyond the existing design unless a concrete compatibility/safety defect is demonstrated.

## 10. Immediate instruction to Claude

**Implement the firmware and verify the hardware assumptions.** Do not redesign the entropy source or propose exploratory frequency sweeps as the default. Start with the fixed frequencies and raw-test mode. Before claiming completion, check PICAXE-08M2 instruction support, physical pin mapping, TCA9548A power requirements on the exact breakout, and Si5351 register programming. Report any genuine blocker succinctly and propose the smallest safe correction.
