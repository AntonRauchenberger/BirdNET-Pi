#!/usr/bin/env bash
source /etc/birdnet/birdnet.conf

if [ -z "$1" ]; then
  echo "Usage: $0 '<SQL query>'"
  exit 1
fi

sqlite3 -header -column "$HOME/bachelorarbeit/BirdNET-Pi/scripts/birds.db" "$1"
