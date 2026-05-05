#!/bin/bash

echo "Starting hardware setup for BirdNET-Pi..."

# 1. Acitavate SPI interface (for e-Paper display)
sudo raspi-config nonint do_spi 0
echo "SPI activated"

# 2. Activate I2C interface (for GPS)
sudo raspi-config nonint do_i2c 0
echo "I2C activated"

# 3. Activate Serial Hardware and activate Serial Console (for GPS)
sudo raspi-config nonint do_serial_hw 0
sudo raspi-config nonint do_serial_cons 0
echo "Serial Hardware activated / Serial Console activated"

echo "Hardware setup completed"