#!/bin/bash

echo "Stopping hotspot mode..."
bash ../scripts/deactivate_hotspot.sh

echo "Bringing LAN interface back up..."
sudo ip link set eth0 up

echo "Restarting NetworkManager..."
sudo systemctl restart NetworkManager

echo "Pi is now back online"