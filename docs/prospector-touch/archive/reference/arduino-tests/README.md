# Legacy Arduino smoke tests

These sketches reproduce early *already-successful* tests. They are **not** the production ZMK firmware or an instruction to downgrade. They are useful only if you intentionally need to validate display SPI or touch I²C outside Zephyr. In the Arduino core D5/D8/D9 mapped to tested LCD control GPIO; D6/D7 to SDA/SCL as wired. Never assume a different Arduino Core has identical D maps.
