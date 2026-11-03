# Hardware and flashing boundaries

[简体中文（默认）](04-HARDWARE-AND-FLASH.md) · English

Target: FoloToy AI Passport, ESP32-C3, 8 MB Flash, roughly 400 KB on-chip SRAM, no PSRAM, 240×320 ST7789 display and 2.4 GHz Wi-Fi / BLE. Actual board facts follow BSP and device inspection. No SIM / cellular; the passive NTAG213 is not treated as an MCU peripheral.

Pin source of truth: `controller/firmware/components/bsp/include/bsp_pins.h`. These are current source values; a replacement board requires verification:

- Display: SPI2, MOSI9, SCLK8, CS1, DC20, BL21, RST=-1 (no MCU reset pin).
- Three buttons: GPIO0 / ADC1_CH0 resistor ladder; current millivolt windows are half-open `[0,150)`, `[150,447)`, `[447,1900)`.
- I2C: SDA10, SCL7; ES8311 address 0x18, CW2017 fuel gauge 0x63.
- Audio: ES8311 / I2S, MCLK6, BCLK5, WS3, DOUT2, DIN4; PA_CTRL=-1.
- Use codec / I2S rather than assume an ESP32-C3 built-in DAC. Audio and USB drivers have specific initialization / recovery behavior and should not be casually replaced.

## Application-only write

1. Connect exactly one target by USB data cable and inspect chip / Flash / boot security state.
2. Read the complete 8 MB twice and verify matching digests; retain local private backups.
3. Read the actual partition table. Only layouts validated by the script are supported; image size, chip and boundaries must match.
4. Write only the factory application, commonly at offset 0x10000; verify by readback digest.
5. Do not overwrite NVS, identity, pairing, partition table or bootloader; no whole-chip erase.

`controller/firmware/partitions.csv` is the build capacity limit, not the device's live layout. Never use it as justification to flash the partition table. Do not run `idf.py flash` or generic multi-address `write_flash` commands printed by the build.

The previous Hello World layout had one factory partition. Permission to replace a test application did not authorize permanent deletion of original backups or whole-chip resets.

## Windows read recovery

Windows menu 7 uses `scripts/firmware_update.py` and the shared safe updater. Require original private emoji assets, matching source fingerprint, version, chip, image size and SHA-256. An old or artwork-free image is rejected before Bridge is stopped.

Full backups are read in 256 KiB blocks at 115200 baud with per-frame progress disabled. Only read operations retry, at most three attempts with final ROM fallback. Discard failed block output; never concatenate fragments. Keep the application stopped between blocks with `no_reset` so NVS does not change. Both complete backup digests must still match. No automatic write retries; retain failed backup directories.

The first Windows attempt failed with a short `Corrupt data` frame at 36% of backup 1; it had not started backup 2, writing or readback. After the fix, the user confirmed completing the update and a basic visual check. This is not complete permission-matrix, Windows 10 or long-term stability acceptance.

## Tool limitations

The sandbox previously rejected termios configuration even after serial-path access was granted. Record the exact error and run the authorized operation through the existing console in a normal Terminal; do not bypass the sandbox or record unexecuted flashing as success. Backups may take minutes and must display progress. “Reading flash twice” does not mean Flash writing has started.
