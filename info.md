# Airzone Cloud v2 control patch

Répare l'intégration officielle `airzone_cloud` quand le cloud Airzone renvoie
**402 Payment Required** sur les comptes sans abonnement — à l'écriture (consigne,
marche/arrêt, mode) **et** à la lecture de la config des appareils, ce qui fait
échouer le démarrage de l'intégration (clim, température, batterie… qui tombent).

Les requêtes **appareils** (écriture et lecture) sont redirigées de l'hôte muré
`m.airzonecloud.com` vers l'hôte non muré `prodctrl.airzonecloud.com` utilisé par
l'app officielle. Le reste (authentification, WebSocket, installations) reste
inchangé.

**Ne supprime pas l'intégration officielle `airzone_cloud`** : ce composant la
complète (il redirige seulement les requêtes appareils), il ne la remplace pas.

Après installation, **redémarre Home Assistant**, puis ajoute l'intégration via
**Paramètres → Appareils et services → Ajouter une intégration → « Airzone Cloud
v2 control patch »**. Aucune configuration à saisir, aucune ligne dans
`configuration.yaml`.
