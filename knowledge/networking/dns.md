# DNS : fonctionnement et dépannage

## Le rôle du DNS

Le DNS (Domain Name System) traduit les noms de domaines en adresses IP. Toute navigation
ou accès applicatif repose dessus ; un DNS défaillant bloque l'accès aux ressources bien
que la connectivité IP soit correcte.

## Symptômes d'une panne DNS

- Ping par IP fonctionne, mais les noms ne résolvent pas.
- Le poste a bien une adresse IP (pas d'APIPA) mais aucun site ne s'ouvre.
- Erreurs « nom de serveur introuvable ».

## Causes fréquentes

- Serveur DNS injoignable (réseau ou pare-feu).
- Mauvaise adresse DNS dans le bail DHCP ou en configuration manuelle.
- Résolution côté serveur en échec (forwarder cassé, domaine introuvable).

## Étapes de vérification

1. Tester la résolution : `nslookup <nom>`.
2. Tester la connectivité vers le serveur DNS (10.10.0.53 pour VoiceOps).
3. Comparer DNS reçu (DHCP) vs DNS configuré manuellement.
4. Vérifier le cache local (`ipconfig /flushdns`) avant de conclure.