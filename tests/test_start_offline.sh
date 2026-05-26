#!/bin/bash

echo "Starting hotspot via main script..."
bash ../scripts/activate_hotspot.sh

echo "Waiting for NetworkManager to settle..."
sleep 1

echo "Simulating total offline mode (deleting default internet route)..."
sudo ip route del default

echo "Offline mode active"