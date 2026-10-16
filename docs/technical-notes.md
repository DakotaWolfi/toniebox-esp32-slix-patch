# COMPAT R1 technical notes

Target: ESP32-S3 Toniebox application v5.237.0. Tested layout: OTA0 at flash `0x180000` with size `0x220000`.

## Findings

- Diagnostic v2 captured 46 clean reads of blocks 0–7 followed by successful reads of block 8, rejected with reason `0x3C78` (29 distinct `E00401` UIDs).
- Another 13 reads had genuine errors within required blocks 0–7, which must remain rejected.
- Original instruction at virtual `0x4202da1e` calls block-read helper for block 8; successful read takes the rejection path.
- Earlier intermittent successes could arise from an occasional block-8 read failure followed by cache hits; this explanation is plausible, not proven.

## Patch regions in original image

| Purpose | Full flash | OTA0 relative | Bytes |
|---|---|---|---:|
| ISO15693 fallback (earlier experimental patch) | `0x1cd87b` | `0x4d87b` | 41 |
| Selective geometry guard (COMPAT R1) | `0x1cda0e` | `0x4da0e` | 22 |

Geometry guard, original:
```text
0c030c4dc2c120b2a00820a220326108a5a9ff371a02
```

Geometry guard, COMPAT R1:
```text
82020526180f0c4dc2c120b2a008ad02a5a9ff162a00
```

Conceptual logic (after validating the UID and mandatory reads):
```c
if (uid[5] != 0x01) {
    if (read_block_8() == 0) reject_geometry();
}
continue_with_existing_required_block_status();
```

Existing RF cleanup, cache, and content lookup remain unchanged. No added diagnostic hooks or enlarged stack. The builder recalculates ESP XOR checksum and embedded SHA-256 digest.

## Hardware result

All 30 SLIX tags and both original SLIX-L Tonies recognized in TeddyCloud; custom audio playback confirmed on one SLIX tag. Long-term testing and compatibility beyond this particular firmware/device are not established.

Tested COMPAT R1 output SHA-256:
```text
77ccd3bd56777038f6ed15001a0433114f1888fc15910396dbfac7d256918e63
```

Patcher aborts when required reference instruction bytes do not match, rather than guessing.