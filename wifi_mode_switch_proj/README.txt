Voici comment installer et utiliser le script wifi_mode_switch.sh pour gérer le mode réseau de ton Raspberry Pi (mode Point d'accès ou mode Managed). 
Suis bien ces étapes :

Dans ton dossier de projet, tu devras avoir ces fichiers :

wifi_mode_switch.sh : Le script principal pour passer du mode AP au mode Managed.
hostapd.conf, dnsmasq.conf, dhcpcd.conf : Ces fichiers de configuration sont essentiels pour que le script fonctionne correctement.
install.sh : Un script qui copie automatiquement ces fichiers dans les répertoires système.

Il faudra également que tu modifies le fichier wpa_supplicant.conf ( je n'ai pas les droits pour le copier) qui se trouve dans /etc/wpa_supplicant.
Pour cela il faudra que tu tapes : 
sudo nano /etc/wpa_suppicant/wpa_supplicant.conf

et que tu rentres ces lignes de code : 

ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="Nom_du_Réseau"   # Remplace par le SSID du réseau Wi-Fi
    psk="Mot_de_passe"      # Remplace par le mot de passe du réseau Wi-Fi
    key_mgmt=WPA2-PSK       # Utilise WPA2 pour la sécurité
}

Ouvre un terminal et va dans le dossier où tu as mis tous les fichiers (avec la commande cd). Ensuite, exécute le script install.sh en utilisant les droits administrateur pour que les fichiers de configuration soient copiés dans les bons répertoires système :

sudo ./install.sh
Ce script va :

Copier les fichiers de configuration (hostapd.conf, dnsmasq.conf, etc.) dans leurs répertoires respectifs sous /etc/.
Redémarrer les services nécessaires comme hostapd, dnsmasq, et dhcpcd pour appliquer la nouvelle configuration.

Une fois l’installation terminée, tu peux utiliser le script wifi_mode_switch.sh pour passer en mode Point d'accès ou Managed. Pour le faire, il suffit de passer l’argument approprié :

Pour passer en mode Point d'accès, lance cette commande :

sudo ./wifi_mode_switch.sh ap

Pour revenir en mode Managed, lance celle-ci :

sudo ./wifi_mode_switch.sh managed
Le script va automatiquement ajuster la configuration réseau de ton Raspberry Pi sans que tu aies à intervenir manuellement.

Si tu veux vérifier que ton Raspberry Pi est bien dans le mode que tu souhaites, tu peux utiliser des commandes comme ifconfig ou ip a pour voir l'état des interfaces réseau et leur configuration.

PS : Il se peut que lorsque tu exécutes la commande en mode AP, la raspberry reste en mode managed. Pour contrer cela, il te suffit de lancer la commande pour le mode managed et d'ensuite relancer la commande en AP.