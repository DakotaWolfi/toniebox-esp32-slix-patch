# Toniebox ESP32-S3 ICODE SLIX compatibility patch

**Independent community reverse-engineering project. Not affiliated with Boxine, tonies, TeddyCloud, or RevvoX.**

A reproducible **binary patcher**, not a redistributed firmware image, for ESP32-S3 Toniebox application **v5.237.0**. It supports ordinary NXP ICODE SLIX (`E00401`) tags alongside original SLIX-L (`E00403`) tags and preserves TeddyCloud integration.

## Hardware results

Tested on **one** ESP32-S3 Toniebox:
- **30/30** ordinary SLIX tags appeared in TeddyCloud.
- **2/2** original Tonies continued to work.
- Custom audio playback confirmed on an ordinary SLIX tag.
- Long-term endurance, other firmware versions and board revisions have **not** been tested.

Not intended for CC3200 Tonieboxes.

## Why this works

The existing reader performs a SLIX-L-specific memory-size check: block 8 should not be readable because SLIX-L has user blocks 0–7. Ordinary SLIX has a readable block 8, so normal successful reading of that block causes rejection.

COMPAT R1 retains the previous ISO15693 fallback for type `E00401` but **skips the block-8 geometry probe for those validated tags**. It keeps mandatory block 0–7 validation and the original SLIX-L path. See [technical notes](docs/technical-notes.md).

## Contents

- [`tools/patch_ota0.py`](tools/patch_ota0.py): patch your **own** compatible OTA0 firmware, using Python's standard library.
- [`tools/fallback.S`](tools/fallback.S) and [`tools/geometry_guard.S`](tools/geometry_guard.S): annotated replacement instructions.
- [`docs/technical-notes.md`](docs/technical-notes.md): offsets, research and limits.

**No third-party firmware, keys, certificates, Wi-Fi settings or personal flash dumps are distributed.**

## Backup before modifying anything

Incorrect flashing can prevent normal boot. Ensure you can enter ROM download mode and recover your own original firmware. The tested ESP32-S3 had Secure Boot and Flash Encryption disabled; other devices may differ.

```powershell
py -m pip install esptool
py -m esptool --chip esp32s3 --port COM49 get-security-info
py -m esptool --chip esp32s3 --port COM49 --baud 921600 read-flash 0x0 0x800000 device_backup.bin
py -m esptool --chip esp32s3 --port COM49 --baud 921600 read-flash 0x180000 0x220000 original_ota0.bin
```

Replace COM49 with your port. Keep backups safely **off GitHub**. Verify your own partition layout before trusting these offsets. If your layout differs, stop.

## Patch your own OTA0 image

```powershell
py .\tools\patch_ota0.py .\original_ota0.bin .\patched_ota0.bin
```

The patcher refuses unknown NFC code bytes, mismatched sizes or version, invalid checksums/digests, and overwrite of an existing output. It outputs source and result hashes.

The tested device produced this COMPAT R1 SHA-256:
```text
77ccd3bd56777038f6ed15001a0433114f1888fc15910396dbfac7d256918e63
```

**Your hash can differ** because of configuration or other differences. A successful patch command is not itself proof that an image is safe to flash.

## Flash — experimental, at your own risk

Only after checking your own firmware version, security state, partition layout and recovery backup:

```powershell
py -m esptool --chip esp32s3 --port COM49 --baud 921600 write-flash 0x180000 .\patched_ota0.bin
```

esptool automatically verifies the write. Restart normally and test an original Tonie first.

### Restore original firmware

```powershell
py -m esptool --chip esp32s3 --port COM49 --baud 921600 write-flash 0x180000 .\original_ota0.bin
```

Never flash another user's complete dump or device-specific certificates/settings.

## Limitations and reports

This specific patch **does not enable ISO14443-A or MIFARE Classic** on the Toniebox TRF7962A reader. Please report issues with version, chip type and sanitized logs — not whole dumps, credentials or private keys.

## Credits and licensing

Community reverse engineering and hardware testing with assistance from ChatGPT Work. TeddyCloud and RevvoX are separate projects; their software and trademarks remain their owners'. Our original scripts and documentation are available under [MIT](LICENSE), **not** the third-party firmware itself.
