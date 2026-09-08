# VLAN : principes et dépannage

## Qu'est-ce qu'un VLAN ?

Un VLAN (Virtual Local Area Network) découpe logiquement un même commutateur en plusieurs
réseaux de diffusion (broadcast domains) distincts. Les trames d'un VLAN ne sont visibles
que par les ports appartenant au même VLAN (ou après traversée d'un trunk).

## Pourquoi un poste n'accède plus au réseau ?

Les causes courantes d'un poste « sans réseau » liées au VLAN :

- Port du switch configuré dans un VLAN différent de celui attendu (mismatch).
- VLAN non défini ou supprimé sur le commutateur.
- Port en mode access incorrect, ou trunk cassé (encapsulation 802.1Q absente).
- Le VLAN natif diffère entre les deux extrémités d'un trunk.

## Contrôles recommandés

1. Identifier le VLAN attendu pour le poste (table de référence / plage d'adresses).
2. Vérifier le `switchport access vlan` sur le port du poste.
3. Vérifier la présence du VLAN dans la base (`show vlan brief`).
4. Vérifier les trunks entre switch et routeur si le VLAN est routé.

## Symptômes types

- Pas de DHCP, adresse APIPA (169.254.x.x).
- Aucune passerelle joignable.
- Postes du même étage toujours en panne (panne de port/vlan).