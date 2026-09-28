#!/bin/bash
echo "Installing GNOME Desktop Environment..."
dnf groupinstall "Server with GUI" -y

echo "Setting graphical target as default..."
systemctl set-default graphical.target