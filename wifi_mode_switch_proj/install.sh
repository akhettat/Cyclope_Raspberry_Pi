#!/bin/bash

# Vérifie si le script est exécuté avec sudo
if [ "$EUID" -ne 0 ]; then
  echo "Veuillez exécuter ce script avec sudo."
  exit 1
fi

echo "Copie des fichiers de configuration dans les répertoires système..."

# Copier directement les fichiers de configuration avec sudo
sudo cp hostapd.conf /etc/hostapd/hostapd.conf
sudo cp dnsmasq.conf /etc/dnsmasq.conf
sudo cp dhcpcd.conf /etc/dhcpcd.conf

# Redémarrage des services
echo "Redémarrage des services..."
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
sudo systemctl restart dhcpcd

echo "Installation terminée ! Vous pouvez utiliser le script wifi_mode_switch.sh."

