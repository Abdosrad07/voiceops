# Passerelle par défaut et routage

## Rôle de la passerelle

La passerelle par défaut (ex. 192.168.20.1) permet au poste d'atteindre les réseaux
distants (hors de son réseau local). Sans elle, le trafic vers l'extérieur est perdu.

## Symptômes d'une passerelle injoignable

- Ping des postes du même VLAN OK, mais aucune requête externe.
- APIPA ou IP correcte mais aucune route vers l'extérieur.
- Le routeur cœur (RTR-CORE) ne répond pas au ping.

## Causes fréquentes

- IP statique avec mauvaise passerelle.
- Interface routeur down ou trunk cassé entre switch et routeur.
- Conflit d'adresse IP sur la passerelle.

## Contrôles

1. `ping RTR-CORE` (192.168.20.1) depuis le poste.
2. Vérifier l'état de l'interface du routeur (`show interface`).
3. Vérifier la configuration IP du poste (masque + passerelle cohérents).
4. Vérifier le trunk switch ↔ routeur (VLAN autorisés).