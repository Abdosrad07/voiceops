# Cisco : commandes de diagnostic équipement

## Vérification des interfaces et ports

- `show interface status` : état up/down des ports.
- `show interfaces trunk` : trunks et VLAN autorisés.
- `show vlan brief` : liste des VLAN définis sur le commutateur.

## VLAN et configuración

- `show running-config interface Gi0/12` : config complète d'un port (mode, VLAN).
- `switchport access vlan <id>` : définir le VLAN d'accès d'un port.
- `show vlan id <n>` : postes présents dans un VLAN donné.

## Routage

- `show ip route` : table de routage du routeur.
- `show ip interface brief` : états IP des interfaces.

## Lecture rapide

- Un port en état **down/down** : câble absent, poste éteint ou panne physique.
- Un port **up/down** : signal détecté mais problème de configuration (mode, VLAN).
- Une adresse **169.254.x.x** : aucun serveur DHCP joignable pour ce VLAN.