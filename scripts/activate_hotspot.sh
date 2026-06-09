#!/bin/bash

# Configuration
SSID="MyBirdNETPiHotspot"
PASSWORD="MyPassword123"
IP_ADDR="192.168.4.1/24"
CON_NAME="Hotspot"
HOTSPOT_IP="192.168.4.1"
HOTSPOT_DOMAIN="192-168-4-1.sslip.io"
NM_DNSMASQ_SHARED_DIR="/etc/NetworkManager/dnsmasq-shared.d"
NM_DNSMASQ_SHARED_FILE="${NM_DNSMASQ_SHARED_DIR}/90-birdnet-offline.conf"

wait_for_networkmanager() {
    local retries=20
    local count=0

    while [ "$count" -lt "$retries" ]; do
        if nmcli -t -f RUNNING general 2>/dev/null | grep -q "running"; then
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    return 1
}

activate_hotspot_connection() {
    local retries=4
    local count=1

    while [ "$count" -le "$retries" ]; do
        echo "Activating hotspot (attempt ${count}/${retries})..."
        sudo nmcli radio wifi on > /dev/null 2>&1 || true

        if sudo nmcli connection up "$CON_NAME" ifname wlan0; then
            return 0
        fi

        sleep 2
        count=$((count + 1))
    done

    return 1
}

ensure_offline_dns_override() {
    echo "Configuring NetworkManager shared dnsmasq for offline DNS..."
    sudo mkdir -p "$NM_DNSMASQ_SHARED_DIR"
    sudo tee "$NM_DNSMASQ_SHARED_FILE" > /dev/null <<EOF
# BirdNET-Pi offline authoritative DNS mapping for hotspot clients
domain-needed
bogus-priv
no-resolv
local=/sslip.io/
address=/${HOTSPOT_DOMAIN}/${HOTSPOT_IP}
host-record=${HOTSPOT_DOMAIN},${HOTSPOT_IP}
EOF

    if ! grep -q "${HOTSPOT_DOMAIN}" /etc/hosts; then
        echo "${HOTSPOT_IP} ${HOTSPOT_DOMAIN}" | sudo tee -a /etc/hosts > /dev/null
    fi
}

# Check if hotspot profile already exists, if not create it
if ! nmcli connection show "$CON_NAME" > /dev/null 2>&1; then
    echo "Creating hotspot profile..."
    sudo nmcli device wifi hotspot ssid "$SSID" password "$PASSWORD" ifname wlan0 con-name "$CON_NAME"
else
    echo "Hotspot profile already exists."
fi

sudo nmcli connection modify "$CON_NAME" \
    ipv4.addresses "$IP_ADDR" \
    ipv4.method shared \
    ipv4.ignore-auto-dns yes \
    ipv4.never-default yes \
    ipv6.method disabled

sudo nmcli connection modify "$CON_NAME" connection.autoconnect yes
sudo nmcli connection modify "$CON_NAME" connection.autoconnect-priority 50

ensure_offline_dns_override

# Disconnect existing wlan connections to prevent conflicts
echo "Disconnecting wlan0 from current networks..."
sudo nmcli device disconnect wlan0 > /dev/null 2>&1

# Turn on hotspot
echo "Preparing NetworkManager..."
sudo systemctl restart NetworkManager

if ! wait_for_networkmanager; then
    echo "NetworkManager did not become ready in time."
    exit 1
fi

if ! activate_hotspot_connection; then
    echo "Failed to activate hotspot after multiple attempts."
    exit 1
fi

sudo nmcli connection modify "$CON_NAME" connection.zone trusted

# Activate kernel routing
sudo sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1

echo "Restarting Caddy to bind TLS certificate to Hotspot IP..."
sudo systemctl restart caddy

echo "Hotspot is up, DNS is updated and Caddy is ready!"