# Airzone Cloud v2 control patch

Répare le **contrôle** de l'intégration officielle `airzone_cloud` quand le
cloud Airzone renvoie **402 Payment Required** à l'écriture (consigne,
marche/arrêt, mode) sur les comptes sans abonnement.

La **lecture** des états reste native et inchangée ; seul l'appel d'écriture est
redirigé de l'ancien endpoint muré `m.airzonecloud.com/api/v1/devices` vers le
nouvel endpoint `prodctrl.airzonecloud.com/api/v2/devices` utilisé par l'app
officielle.

Après installation, **redémarre Home Assistant**, puis ajoute l'intégration via
**Paramètres → Appareils et services → Ajouter une intégration → « Airzone Cloud
v2 control patch »**. Aucune configuration à saisir, aucune ligne dans
`configuration.yaml`.
