#!/bin/bash

# Function to set static IP
set_static_ip() {
    local interface="eth0"
    local ip_address="$1"
    local gateway="$2"

    # Check if the Ethernet interface exists
    if ! ip link show "$interface" &> /dev/null; then
        echo "Error: Ethernet interface '$interface' not found."
        exit 1
    fi

    # Check if the IP address is valid
    if ! [[ "$ip_address" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "Error: Invalid IP address format."
        exit 1
    fi

    # Check if the gateway is valid
    if ! [[ "$gateway" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "Error: Invalid gateway format."
        exit 1
    fi

    # Set the static IP address
    sudo ip addr flush dev "$interface"
    sudo ip addr add "$ip_address" dev "$interface"
    sudo ip route add default via "$gateway"

    # Check if the IP was set successfully
    if ip addr show "$interface" | grep -q "$ip_address"; then
        echo "Static IP address set successfully: $ip_address"
    else
        echo "Error: Failed to set static IP address."
        exit 1
    fi
}

# Main script
echo "Select radar option:"
echo "1. ISYS 5021 - 150m"
echo "2. ITR 3810 - 300m"
read -p "Enter your choice (1 or 2): " choice

case "$choice" in
    1)
        echo "Setting static IP for 150m radar..."
        set_static_ip "192.168.252.2" "192.168.252.1"
        ;;
    2)
        echo "Setting static IP for 300m radar..."
        # Generate a random IP in the 192.168.31.x range
        random_ip="192.168.31.$((RANDOM % 254 + 1))"
        set_static_ip "$random_ip" "192.168.31.1"
        ;;
    *)
        echo "Invalid choice. Please select 1 or 2."
        exit 1
        ;;
esac