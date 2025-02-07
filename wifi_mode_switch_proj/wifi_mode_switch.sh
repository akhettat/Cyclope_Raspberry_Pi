#!/bin/bash


MODE=$1

if [[ "$MODE" == "ap" ]]; then
	echo "Passage en mode Point d'accès..."
	sudo systemctl stop NetworkManager

	sudo systemctl stop wpa_supplicant
	sudo systemctl disable wpa_supplicant
	sudo systemctl stop dhcpcd

	sudo ip link set wlan0 down
	sudo ip addr flush dev wlan0
	sudo ip link set wlan0 up
	sudo ip addr add 192.168.4.1/24 dev wlan0

	sudo systemctl start hostapd
	sudo systemctl start dnsmasq
	echo "Mode point d'accès activé."
elif [[ "$MODE" == "managed" ]]; then
        echo "Passage en mode managed"
        sudo systemctl stop hostapd
        sudo systemctl stop dnsmasq

	sudo systemctl unmask wpa_supplicant
	sudo systemctl enable wpa_supplicant
	sudo systemctl start wpa_supplicant

        sudo ip link set wlan0 down
        sudo ip addr flush dev wlan0
        sudo ip link set wlan0 up
        sudo systemctl enable NetworkManager
	sudo systemctl start NetworkManager
        echo "Mode Managed activé."
else
	echo "Usage : $0 [ap|managed]"
	echo " ap    : Passer en mode point d'accès"
	echo " managed : Passer en mode Managed"
	exit 1
fi
