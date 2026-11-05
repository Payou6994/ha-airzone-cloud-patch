# Airzone Cloud v2 control patch

Répare le **contrôle** de l'intégration officielle `airzone_cloud` quand le
cloud Airzone renvoie **402 Payment Required** à l'écriture (consigne,
marche/arrêt, mode) sur les comptes sans abonnement.

La **lecture** des états reste native et inchangée ; seul l'appel d'écriture est
redirigé de l'ancien endpoint muré `m.airzonecloud.com/api/v1/devices` vers le
nouvel endpoint `prodctrl.airzonecloud.com/api/v2/devices` utilisé par l'app
officielle.

Après installation, ajoute dans `configuration.yaml` :

```yaml
airzone_cloud_patch:
```

puis redémarre Home Assistant.
