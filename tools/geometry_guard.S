 .text
.global geometry_guard
geometry_guard:
/* Replaces 0x4202da0e..0x4202da24 (22 bytes).
   Caller already validated E00403 or E00401. A2 holds tag pointer.
   A4 is prior block-loop status and remains unchanged.
   A8 is caller-clobbered scratch. No added call, stack or ABI changes. */
    l8ui a8,a2,5
    beqi a8,1,skip_probe
    movi.n a13,4
    addi a12,a1,0x20
/* Full-width MOVI keeps CALL8 at original PC 0x4202da1e. */
    .byte 0xb2,0xa0,0x08
    mov.n a10,a2
/* Existing CALL8 at its original PC. */
    .byte 0xa5,0xa9,0xff
    _beqz a10,reject_geometry
.set skip_probe,geometry_guard+22
.set reject_geometry,geometry_guard+25