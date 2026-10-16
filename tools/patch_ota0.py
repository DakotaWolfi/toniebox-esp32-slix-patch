#!/usr/bin/env python3
"""Patch a user's own v5.237.0 Toniebox ESP32-S3 OTA0 image. No flashing.

Accepts an OTA0 0x220000-byte image extracted from the device. Refuses code
mismatches, unexpected partitions, and invalid ESP image integrity data.
"""
import argparse
import hashlib
import struct
from pathlib import Path

SIZE = 0x220000
FALLBACK_AT = 0x4D87B
GUARD_AT = 0x4DA0E
ORIGINAL_FALLBACK = bytes.fromhex('31d85cb1675642030031d75c8044113203002c3530442031d45c005511a21300b0b42050aa202588dd')
FALLBACK = bytes.fromhex('e5faffe5f9ffad04a5bcffdcaa82040566181582040666480f82040752a0e057980651644f59240c02')
ORIGINAL_GUARD = bytes.fromhex('0c030c4dc2c120b2a00820a220326108a5a9ff371a02')
GUARD = bytes.fromhex('82020526180f0c4dc2c120b2a008ad02a5a9ff162a00')

def sha(x):
    return hashlib.sha256(x).hexdigest()

def layout(data):
    if len(data) != SIZE or data[0] != 0xE9 or not (0 < data[1] <= 16) or data[23] != 1:
        raise ValueError('Not the expected ESP32 OTA0 image format/size')
    pos, xor = 24, 0xEF
    for _ in range(data[1]):
        if pos + 8 > len(data): raise ValueError('Invalid segment header')
        _, count = struct.unpack_from('<II',data,pos)
        pos += 8
        if count > len(data) - pos: raise ValueError('Invalid segment length')
        for val in data[pos:pos+count]: xor ^= val
        pos += count
    checksum_pos = ((pos+16)&~15)-1
    digest_pos = checksum_pos + 1
    if digest_pos + 32 > len(data): raise ValueError('Invalid digest offset')
    if data[checksum_pos] != xor: raise ValueError('ESP checksum does not match')
    if data[digest_pos:digest_pos+32] != hashlib.sha256(data[:digest_pos]).digest():
        raise ValueError('ESP image digest does not match')
    return checksum_pos, digest_pos

def patch(src):
    checksum_pos, digest_pos = layout(src)
    if b'v5.237.0' not in src[:0x8000]:
        raise ValueError('Expected firmware version v5.237.0 not found')
    if src[FALLBACK_AT:FALLBACK_AT+len(ORIGINAL_FALLBACK)] not in (ORIGINAL_FALLBACK,FALLBACK):
        raise ValueError('NFC fallback code does not match known baseline')
    if src[GUARD_AT:GUARD_AT+len(ORIGINAL_GUARD)] != ORIGINAL_GUARD:
        raise ValueError('NFC geometry code does not match known baseline')
    result=bytearray(src)
    result[FALLBACK_AT:FALLBACK_AT+len(FALLBACK)] = FALLBACK
    result[GUARD_AT:GUARD_AT+len(GUARD)] = GUARD
    # Recompute Espressif's XOR checksum and SHA-256 app digest.
    pos, xor = 24, 0xEF
    for _ in range(result[1]):
        _, count=struct.unpack_from('<II',result,pos)
        pos += 8
        for val in result[pos:pos+count]: xor ^= val
        pos += count
    result[checksum_pos] = xor
    result[digest_pos:digest_pos+32] = hashlib.sha256(result[:digest_pos]).digest()
    layout(result)
    allowed=lambda i: FALLBACK_AT<=i<FALLBACK_AT+len(FALLBACK) or GUARD_AT<=i<GUARD_AT+len(GUARD) or i==checksum_pos or digest_pos<=i<digest_pos+32
    if any(not allowed(i) for i,(a,b) in enumerate(zip(src,result)) if a!=b):
        raise ValueError('Unexpected modification outside patch and integrity regions')
    return bytes(result)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path,help='Your own OTA0 firmware image (0x220000 bytes)')
    p.add_argument('output',type=Path,help='New patched OTA0 file (must not exist)')
    args=p.parse_args()
    if args.output.exists(): p.error('Output already exists; refusing overwrite')
    original=args.input.read_bytes()
    patched=patch(original)
    args.output.write_bytes(patched)
    print(f'Input SHA256:  {sha(original)}')
    print(f'Output SHA256: {sha(patched)}')
    print(f'Wrote: {args.output} ({len(patched)} bytes)')
    if sha(original)=='7da294327f1eca783139c9d7ff1e02ef4349bf2e383f409b69184fb058c06ddc':
        assert sha(patched)=='77ccd3bd56777038f6ed15001a0433114f1888fc15910396dbfac7d256918e63', 'Known baseline regression'
        print('Matches hardware-tested COMPAT R1 reference')

if __name__=='__main__': main()