# Airzone Cloud v2 control patch

Petit composant Home Assistant qui **répare le contrôle** de l'intégration
officielle `airzone_cloud` quand le cloud Airzone renvoie **HTTP 402 Payment
Required** à l'écriture (changement de consigne, marche/arrêt, mode).

## Le problème

L'intégration officielle `airzone_cloud` (librairie `aioairzone-cloud`) envoie
les commandes sur l'ancien endpoint :

```
PATCH https://m.airzonecloud.com/api/v1/devices/{id}
```

Airzone a placé cet endpoint derrière un abonnement payant → **402**. Résultat :
la **lecture** des états continue de fonctionner, mais toute **commande** échoue.

L'app officielle Airzone, elle, pilote via un nouvel endpoint **non muré** :

```
PATCH https://prodctrl.airzonecloud.com/api/v2/devices/{id}
```

## Ce que fait ce composant

Il remplace à chaud la seule méthode d'écriture de la librairie
(`AirzoneCloudApi.api_patch_device`) pour :

1. rediriger la commande vers l'endpoint **v2 `prodctrl`** ;
2. traduire le corps `{"param","value","installation_id"}` (v1) en
   `{"params": {...}, "installationId", "opts"}` (v2) ;
3. choisir `setpoint_air_heat` ou `setpoint_air_cool` selon le mode courant.

La lecture (WebSocket, états, entités) reste **100 % native et inchangée**. On
ne touche qu'à l'écriture.

## Installation

### Manuelle
1. Copier `custom_components/airzone_cloud_patch/` dans
   `config/custom_components/`.
2. Ajouter dans `configuration.yaml` :
   ```yaml
   airzone_cloud_patch:
   ```
3. Redémarrer Home Assistant.

### Via HACS (dépôt personnalisé)
HACS → ⋮ → *Dépôts personnalisés* → ajouter l'URL de ce dépôt, catégorie
*Integration* → installer → ajouter la ligne `airzone_cloud_patch:` dans
`configuration.yaml` → redémarrer.

## Vérifier

Après redémarrage, les logs doivent montrer :

```
aioairzone-cloud : controle redirige vers l'endpoint v2 (https://prodctrl.airzonecloud.com/api/v2)
```

Changer une consigne depuis une carte climate doit maintenant fonctionner
(plus de 402).

## Limites / avertissement

- Repose sur l'API cloud **non documentée** d'Airzone ; elle peut changer sans
  préavis. Objectif : interopérabilité avec son propre matériel.
- Le patch suit la signature interne de `aioairzone-cloud` (testé avec la
  **v0.7.2**). Une refonte majeure de la librairie pourrait nécessiter une mise
  à jour du patch.
- Le vrai correctif à long terme serait en amont, dans `aioairzone-cloud`.

## Licence

MIT. Le code référencé de `aioairzone-cloud` est sous Apache-2.0 (non inclus).
