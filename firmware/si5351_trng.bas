; =====================================================================================
; Si5351_TRNG  firmware rev 1        PICAXE-08M2 (default 4 MHz)
; Two Si5351 modules (own crystals) -> 74HCT74 FF1 (A on D1, B on CLK1) -> FF2 snapshot
; PICAXE pulses FF2 clock on C.4 and reads Q2 on C.3.  All serial through the download
; socket: sertxd on C.0 (4800 baud at 4 MHz), serin on C.5 (not used by this version).
; Hardware I2C master: C.1 = SCL, C.2 = SDA.  TCA9548A module at 0x70 (write address $E0),
; both Si5351 at 0x60 (write address $C0).  [newslave] is X2-only, so each address change
; is a new hi2csetup.
;
; MODE (edit the line 'runmode = 0' in startup):  0 = RAW TEST (raw captured bits, no conditioning)
;                                 1 = CONDITIONED (Von Neumann pairs: 01 -> 0, 10 -> 1, 00/11 dropped)
; Output lines (ASCII, CR LF):
;   I:text            information
;   E:code chip       error, program stops (capture clock left LOW)
;   D:<hex bytes>     16 raw bytes per line (MODE 0), bits packed MSB first
;   C:<hex bytes>     16 conditioned bytes per line (MODE 1)
;   S:r=.. a=.. d=.. o=.. t=..   status every 16 data lines:
;        r raw bits sampled, a pairs accepted, d pairs discarded (MODE 1 only), o bytes output,
;        t seconds since start.  r, a, d, o are 16-bit and wrap at 65536.
; Error codes: 1 TCA9548A write/readback failed   2 Si5351 not out of init (SYS_INIT)
;              3 Si5351 register readback mismatch   4 Si5351 status: PLLA not locked / crystal lost
; This firmware makes no claim that the bits are random: it only collects them.
; =====================================================================================
#picaxe 08m2

symbol runmode = b20         ; set in the line 'runmode = 0' below:  0 = RAW TEST, 1 = CONDITIONED
symbol SPAUSE = 8            ; ms pause after each sample; actual rate must be measured (see notes)

symbol CAP    = C.4          ; capture clock to 74HCT74 CLK2 (FF2)
symbol Q2     = pinC.3       ; FF2 Q2 output

symbol tmp     = b0
symbol tmp2    = b1
symbol chip    = b2          ; 0 = Si5351 A (TCA channel 0), 1 = Si5351 B (TCA channel 1)
symbol tries   = b3
symbol acc     = b4          ; byte accumulator
symbol nbits   = b5
symbol s1      = b6
symbol s2      = b7
symbol linecnt = b8
symbol stat    = b9
symbol rawcnt  = w5          ; b10:b11
symbol okcnt   = w6          ; b12:b13
symbol dis     = w7          ; b14:b15
symbol outcnt  = w8          ; b16:b17
symbol errc    = b18
symbol tries2  = b19

; ---------------- startup ----------------
runmode = 0                  ; 0 = RAW TEST, 1 = CONDITIONED (Von Neumann)
low CAP                      ; safe state: capture clock LOW
pause 1000                   ; let supplies and modules settle
sertxd("I:SI5351TRNG fw1 08M2 mode=")
if runmode = 0 then
  sertxd("RAW",13,10)
else
  sertxd("VN",13,10)
endif

chip = 0
cfg_next:
tries2 = 0
cfg_try:
errc = 0
gosub tca_select
if errc = 0 then
  gosub cfg_si
endif
if errc = 0 then cfg_ok
tries2 = tries2 + 1
if tries2 < 3 then cfg_try
sertxd("E:",#errc," ",#chip,13,10)
low CAP
end
cfg_ok:
sertxd("I:chip ",#chip," ok",13,10)
chip = chip + 1
if chip < 2 then cfg_next

; deselect all TCA channels: no I2C activity during sampling
hi2csetup i2cmaster, $E0, i2cslow, i2cbyte
hi2cout ($00)
sertxd("I:clocks A=8.000 B=8.001 MHz nominal, run",13,10)
pause 500                    ; clocks stabilise before the first sample

rawcnt = 0 : okcnt = 0 : dis = 0 : outcnt = 0
acc = 0 : nbits = 0 : linecnt = 0 : stat = 0
time = 0

if runmode = 1 then vn_loop

; ---------------- RAW TEST ----------------
raw_loop:
gosub get_bit
acc = acc * 2 + s1
nbits = nbits + 1
rawcnt = rawcnt + 1
if nbits = 8 then
  gosub emit_byte
endif
pause SPAUSE
goto raw_loop

; ---------------- CONDITIONED (Von Neumann) ----------------
vn_loop:
gosub get_bit
s2 = s1                      ; first bit of the pair
pause SPAUSE
gosub get_bit                ; second bit in s1
rawcnt = rawcnt + 2
if s1 <> s2 then
  okcnt = okcnt + 1
  acc = acc * 2 + s2         ; 01 -> 0 , 10 -> 1  (= first bit)
  nbits = nbits + 1
  if nbits = 8 then
    gosub emit_byte
  endif
else
  dis = dis + 1
endif
pause SPAUSE
goto vn_loop

; ---------------- subroutines ----------------
get_bit:                     ; pulse FF2 clock, wait, read Q2 -> s1
high CAP
pauseus 3                    ; 30 us settling (spec: 10 us or more)
s1 = 0
if Q2 = 1 then
  s1 = 1
endif
low CAP
pauseus 3                    ; clock LOW time before the next capture
return

emit_byte:                   ; send acc as two hex digits; line of 16 bytes
if linecnt = 0 then
  if runmode = 0 then
    sertxd("D:")
  else
    sertxd("C:")
  endif
endif
tmp = acc / 16
gosub nib
tmp = acc & $0F
gosub nib
linecnt = linecnt + 1
outcnt = outcnt + 1
acc = 0
nbits = 0
if linecnt = 16 then
  sertxd(13,10)
  linecnt = 0
  stat = stat + 1
  if stat = 16 then
    stat = 0
    sertxd("S:r=",#rawcnt," a=",#okcnt," d=",#dis," o=",#outcnt," t=",#time,13,10)
  endif
endif
return

nib:                         ; tmp = 0..15 -> ASCII hex digit
if tmp > 9 then
  tmp = tmp + 55
else
  tmp = tmp + 48
endif
sertxd(tmp)
return

tca_select:                  ; select TCA channel 'chip', verify by reading the control register
tmp = 1
if chip = 1 then
  tmp = 2
endif
hi2csetup i2cmaster, $E0, i2cslow, i2cbyte
hi2cout (tmp)
hi2cin (tmp2)
if tmp2 <> tmp then
  errc = 1
endif
return

cfg_si:                      ; program the Si5351 behind the selected channel
hi2csetup i2cmaster, $C0, i2cslow, i2cbyte
tries = 0
wait_init:
hi2cin 0,(tmp)
tmp = tmp & %10000000        ; SYS_INIT must be 0 before writing
if tmp = 0 then init_done
tries = tries + 1
if tries > 100 then
  errc = 2
  return
endif
pause 10
goto wait_init
init_done:
hi2cout 3,($FF)              ; all outputs disabled
hi2cout 16,($80,$80,$80,$80,$80,$80,$80,$80)   ; CLK0..7 drivers powered down
hi2cout 183,($D2)            ; crystal load 10 pF (default), reserved bits 010010b
hi2cout 26,($00,$01,$00,$0E,$00,$00,$00,$00)   ; PLLA = 25 MHz x 32 = 800 MHz
if chip = 0 then
  hi2cout 42,($00,$01,$00,$30,$00,$00,$00,$00) ; MS0 = 100        -> 8.000 MHz
else
  hi2cout 42,($1F,$41,$00,$2F,$FE,$00,$0C,$82) ; MS0 = 99+7901/8001 -> 8.001 MHz
endif
hi2cout 16,($0F)             ; CLK0 on, fractional MS0, source PLLA, MS0 output, 8 mA
hi2cout 177,($A0)            ; reset PLLA and PLLB
pause 50
hi2cout 3,($FE)              ; enable CLK0 only
pause 50
hi2cin 16,(tmp)
if tmp <> $0F then
  errc = 3
  return
endif
hi2cin 3,(tmp)
if tmp <> $FE then
  errc = 3
  return
endif
hi2cin 45,(tmp,tmp2)         ; MS0 P1[15:8], P1[7:0]
if chip = 0 then
  if tmp <> $30 or tmp2 <> $00 then
    errc = 3
    return
  endif
else
  if tmp <> $2F or tmp2 <> $FE then
    errc = 3
    return
  endif
endif
hi2cin 0,(tmp)
tmp = tmp & %10101000        ; SYS_INIT, LOL_A, LOS_XTAL (PLLB is unused, so LOL_B is ignored)
if tmp <> 0 then
  errc = 4
endif
return
