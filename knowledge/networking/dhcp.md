# DHCP : fonctionnement et dépannage

## Le protocole DHCP

DHCP (Dynamic Host Configuration Protocol) attribue automatiquement une adresse IP, un
masque, une passerelle et les serveurs DNS à un poste. Le serveur répond via DORA :
Discover, Offer, Request, Ack.

## L'adresse APIPA

Lorsque le serveur DHCP ne répond pas, un poste Windows s'attribue seul une adresse
**APIPA** (Automatic Private IP Addressing) dans la plage **169.254.0.0/16**
(typiquement 169.254.x.x). C'est le symptôme n°1 d'un échec DHCP.

## Causes fréquentes d'un échec DHCP

- Port du switch en VLAN incorrect (le serveur n'est pas joignable dans le même domaine).
- Pool d'adresses épuisé.
- Serveur DHCP injoignable (firewall, routage, interface down).
- Détection de port « DHCP snooping » qui bloque le poste.

## Piste de résolution

1. Vérifier le VLAN du port (tout mismatch DHCP/VLAN se traite à la racine).
2. Vérifier la présence d'adresses dans le pool.
3. Vérifier la joignabilité du serveur DHCP depuis le switch.
4. Tester une IP statique temporaire pour isoler le DHCP.