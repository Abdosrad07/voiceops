# Télécoms : bases pour le support de niveau 1

## Terminologie courante réseau télécom

- **APIPA** : auto-configuration (169.254.x.x) quand DHCP échoue.
- **Gateway** : passerelle par défaut, sortie vers les autres réseaux.
- **VLAN** : découpage logique d'un switch en domaines de diffusion.
- **SLA / MTTR** : indicateurs de niveau de service et délai de résolution moyen.

## Réflexes du technicien

1. Recueillir le symptôme exact, l'équipement et la localisation.
2. Vérifier la couche 1 (câble, port) avant de regarder la couche 3.
3. Vérifier l'obtention de l'IP (bail DHCP / APIPA).
4. Vérifier la passerelle par défaut, puis le DNS.
5. Vérifier le VLAN du port (cause racine fréquente).
6. Documenter la conclusion : créer un incident, générer un rapport.

## Pièges à éviter

- Conclure « panne DNS » sans vérifier la configuration IP (souvent DHCP/VLAN).
- Redémarrer un équipement avant d'avoir identifié la cause.
- Multiplier les changements sans re-tester après chaque étape.