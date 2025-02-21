#!/bin/bash

echo "Starting Update Script..."

echo "Bringing down eth0..."
sudo ifconfig eth0 down
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to bring down eth0. Check permissions or network configuration."
    exit 1
fi

echo "Pulling latest changes from Git..."
git pull
if [ $? -ne 0 ]; then
    echo "[ERROR] Git pull failed. Check internet connection, repository status, or authentication."
    sudo ifconfig eth0 up
    exit 1
fi

echo "Bringing eth0 back up..."
sudo ifconfig eth0 up
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to bring up eth0. Manual intervention required."
    exit 1
fi

echo "Update Completed Successfully!"
exit 0
