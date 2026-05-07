#!/bin/bash

CON_NAME="Hotspot"

# Check if hotspot is active, if yes deactivate it
if nmcli connection show --active | grep -q "$CON_NAME"; then
    echo "Deactivating hotspot..."
    sudo nmcli connection down "$CON_NAME"
    
    # Force WLAN scan to reconnect to home Wi-Fi faster
    echo "Searching for known Wi-Fi networks..."
    sudo nmcli device wifi rescan
else
    echo "Hotspot is not active."
fi