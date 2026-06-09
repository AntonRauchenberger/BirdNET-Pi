#!/bin/bash

echo "Starting hardware setup for BirdNET-Pi..."

# 1. Acitavate SPI interface (for e-Paper display)
sudo raspi-config nonint do_spi 0
echo "SPI activated"

# 2. Activate I2C interface (for GPS)
sudo raspi-config nonint do_i2c 0
echo "I2C activated"

# 3. Activate Serial Hardware and disable Serial Console (for GPS)
sudo raspi-config nonint do_serial_hw 0
sudo raspi-config nonint do_serial_cons 1

# Make sure no login getty keeps UART busy.
sudo systemctl disable --now serial-getty@ttyS0.service 2>/dev/null || true
sudo systemctl disable --now serial-getty@serial0.service 2>/dev/null || true

# Ensure the interactive user can access /dev/ttyS0.
if [ -n "$USER" ]; then
	sudo usermod -aG dialout "$USER" || true
fi

echo "Serial Hardware activated / Serial Console disabled"

echo "Hardware setup completed"