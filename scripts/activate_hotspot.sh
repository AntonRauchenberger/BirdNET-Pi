#!/bin/bash

# Configuration
SSID="MyBirdNETPiHotspot"
PASSWORD="MyPassword123"
IP_ADDR="192.168.4.1/24"
CON_NAME="Hotspot"

# Check if hotspot profile already exists, if not create it
if ! nmcli connection show "$CON_NAME" > /dev/null 2>&1; then
    echo "Creating hotspot profile..."
    sudo nmcli device wifi hotspot ssid "$SSID" password "$PASSWORD" ifname wlan0 con-name "$CON_NAME"
    sudo nmcli connection modify "$CON_NAME" ipv4.addresses "$IP_ADDR" ipv4.method shared
    
    sudo nmcli connection modify "$CON_NAME" ipv4.dns "192.168.4.1"
    sudo nmcli connection modify "$CON_NAME" ipv4.ignore-auto-dns yes
    
    sudo nmcli connection modify "$CON_NAME" connection.autoconnect yes
    sudo nmcli connection modify "$CON_NAME" connection.autoconnect-priority 50
else
    echo "Hotspot profile already exists."
    sudo nmcli connection modify "$CON_NAME" ipv4.dns "192.168.4.1"
    sudo nmcli connection modify "$CON_NAME" ipv4.ignore-auto-dns yes
fi

# Disconnect existing wlan connections to prevent conflicts with hotspot activation
echo "Disconnecting wlan0 from current networks..."
sudo nmcli device disconnect wlan0 > /dev/null 2>&1

# Turn on hotspot
echo "Activating hotspot..."
sudo nmcli connection up "$CON_NAME"

echo "Restarting Caddy to bind TLS certificate to Hotspot IP..."
sudo systemctl restart caddy

echo "Hotspot is up and Caddy is ready"