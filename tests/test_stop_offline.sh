#!/bin/bash

echo "Stopping hotspot mode..."
bash ../scripts/deactivate_hotspot.sh

echo "Re-enabling network interfaces and fetching internet routing..."
sudo systemctl restart NetworkManager

echo "Pi is now back online"