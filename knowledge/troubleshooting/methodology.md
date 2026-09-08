# Démarche de troubleshooting réseau

## Ordre de diagnostic conseillé

1. **Identifier l'équipement** : quel poste, quel étage, quel VLAN attendu ?
2. **Configuration IP** : le poste a-t-il une IP valide, ou une adresse APIPA
   (169.254.x.x = échec DHCP) ?
3. **Passerelle** : la passerelle par défaut répond-elle ?
4. **DHCP** : le bail a-t-il été obtenu normalement ?
5. **VLAN** : le port est-il dans le bon VLAN ? (cause racine fréquente des pannes DHCP)
6. **DNS** : les noms résolvent-ils ?

## Causes racines typiques en environnement simulé

| Symptôme                          | Cause probable                   |
| --------------------------------- | -------------------------------- |
| APIPA (169.254.x.x)               | Échec DHCP (souvent VLAN erroné) |
| IP correcte mais aucune passerelle | VLAN mismatch ou trunk cassé     |
| Connectivité OK mais pas de DNS    | Serveur DNS injoignable          |
| Poste isolé                       | Interface down / port down       |

## Bonnes pratiques

- Ne changer qu'**un paramètre à la fois** puis re-tester.
- Toujours vérifier la couche physique avant le reste.
- Documenter chaque résultat d'outil (créer un incident puis un rapport).