/* Existing compatibility fallback; unchanged in COMPAT R1.
   Linked at 0x4202d87b; retains original CALL8 PC.
   Existing RETW at 0x4202d8a4 is outside replacement. */
.text
.global fallback
fallback:
    .byte 0xe5,0xfa,0xff /* RF off */
    .byte 0xe5,0xf9,0xff /* RF on */
    mov.n a10,a4
    .byte 0xa5,0xbc,0xff /* ISO15693 inventory */
    bnez.n a10,failure
    l8ui a8,a4,5
    bnei a8,1,failure
    l8ui a8,a4,6
    bnei a8,4,failure
    l8ui a8,a4,7
    movi a5,0xe0
    bne a8,a5,failure
    .byte 0x51,0x64,0x4f /* l32r -> marker */
    s32i.n a5,a4,8
    movi.n a2,0
failure: