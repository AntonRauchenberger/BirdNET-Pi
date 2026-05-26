#!/bin/bash

echo "Starting hotspot via main script..."
bash ../scripts/activate_hotspot.sh

echo "Waiting for NetworkManager to settle..."
sleep 1

echo "Simulating REAL forest offline mode..."
sudo ip link set eth0 down

echo "Pi is now completely offline and running in hotspot mode"