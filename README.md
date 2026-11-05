# Airzone Cloud v2 control patch

[![hacs][hacs-badge]][hacs-url]
[![GitHub release][release-badge]][release-url]
[![License][license-badge]](LICENSE)
[![Validate][validate-badge]][validate-url]

Correctif pour l'intégration officielle **[Airzone Cloud][airzone-integration]** de
Home Assistant quand le cloud Airzone répond **`402 Payment Required`** sur les
comptes **sans abonnement** — d'abord à chaque **commande** (consigne, marche/arrêt,
mode), puis aussi à la **lecture** de la config des appareils, ce qui fait carrément
**échouer le démarrage** de l'intégration (plus aucune entité : clim, température,
**batterie** des thermostats…).

> Airzone mure, sur l'hôte `m.airzonecloud.com`, les endpoints **appareils**
> (écriture **et** lecture). L'app officielle, elle, passe par l'hôte **non muré**
> `prodctrl.airzonecloud.com` ; ce composant y redirige les requêtes appareils.

---

## Le problème

Airzone paywalle progressivement les endpoints **appareils** sur
`m.airzonecloud.com`, que la librairie `aioairzone-cloud` (intégration officielle)
utilise encore. Même compte, même token — seul **l'hôte** change :

| Requête appareil | `m.airzonecloud.com` | `prodctrl.airzonecloud.com` (app) |
|---|---|---|
| Écriture `PATCH /devices/{id}` | **402** | **200 / 204** (en v2) |
| Lecture `GET /devices/{id}/config` | **402** | **200** |

La lecture `config` échoue **au démarrage** de l'intégration → le setup s'interrompt
et **toutes** les entités tombent (clim, température, batterie…).

## La solution

Ce composant remplace à chaud **deux** méthodes de `AirzoneCloudApi` :

- **`api_patch_device`** (écriture) → endpoint **v2 `prodctrl`**, avec traduction du
  corps (`{"param","value","installation_id"}` → `{"params":{…},"installationId","opts"}`)
  et choix `setpoint_air_heat` / `setpoint_air_cool` selon le mode ;
- **`api_request`** (lecture) → les requêtes **appareils** (`.../devices/{id}…`) sont
  renvoyées vers **`prodctrl`** au lieu de `m.`.

Tout le reste (authentification, installations, météo, WebSocket) reste **sur `m.`
et inchangé**.

## Prérequis

- L'intégration **[Airzone Cloud][airzone-integration]** officielle installée et
  configurée (elle fournit les entités ; la lecture doit déjà fonctionner).
- Un compte Airzone **sans** abonnement (c'est le cas où l'écriture renvoie 402).

> ⚠️ **Ne supprime pas l'intégration officielle `airzone_cloud`.** Ce composant
> ne la remplace pas, il la **complète** : il a besoin qu'elle reste installée et
> active (elle fournit l'authentification, le WebSocket et les entités). Ce patch
> se contente de **rediriger les requêtes appareils** (écriture et lecture) vers
> l'hôte non muré.

## Installation

### Via HACS (recommandé)

1. Ajoute ce dépôt comme **dépôt personnalisé** dans HACS (catégorie
   *Integration*), ou clique :

   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.][hacs-repo-badge]][hacs-repo-url]

2. Installe **Airzone Cloud v2 control patch**, puis **redémarre** Home Assistant.

### Manuelle

Copie `custom_components/airzone_cloud_patch/` dans ton dossier
`config/custom_components/`, puis redémarre Home Assistant.

## Configuration

Pas de `configuration.yaml`. Ajoute l'intégration via l'interface :

**Paramètres → Appareils et services → Ajouter une intégration → « Airzone Cloud v2 control patch »**, ou clique :

[![Add integration][config-flow-badge]][config-flow-url]

Il n'y a aucun champ à remplir : valide, c'est tout.

## Vérifier

Après ajout, le journal affiche :

```
aioairzone-cloud : controle + lecture device rediriges vers https://prodctrl.airzonecloud.com
```

L'intégration `airzone_cloud` doit alors démarrer normalement (plus de 402 au
setup), et changer une consigne depuis une carte `climate` doit fonctionner.

## Comment ça marche

| Action | Librairie (v1, muré) | Envoyé en v2 (ce patch) |
|---|---|---|
| Consigne chaud | `{"param":"setpoint","value":21}` | `{"params":{"setpoint_air_heat":21},"opts":{"units":0}}` |
| Consigne froid | `{"param":"setpoint","value":21}` | `{"params":{"setpoint_air_cool":21},"opts":{"units":0}}` |
| Marche/arrêt | `{"param":"power","value":true}` | `{"params":{"power":true}}` |
| Mode | `{"param":"mode","value":3}` | `{"params":{"mode":3}}` |

Dans tous les cas : `installationId` en camelCase et l'URL
`prodctrl.airzonecloud.com/api/v2/devices/{id}`.

Pour la **lecture**, les requêtes device-scoped (`.../devices/{id}/config`, etc.)
sont simplement renvoyées de `m.` vers `prodctrl` (même chemin), ce qui débloque le
démarrage de l'intégration et fait revenir les entités (dont la batterie).

## Limites / avertissement

- Repose sur l'API cloud **non documentée** d'Airzone ; elle peut changer sans
  préavis. Objectif : **interopérabilité avec son propre matériel**.
- Le patch suit la signature interne de `aioairzone-cloud` (testé avec la
  **v0.7.2**). Une refonte majeure de la librairie pourrait nécessiter une mise
  à jour.
- Le correctif idéal à long terme serait en amont, dans `aioairzone-cloud`.

## Crédits

- Intégration et librairie d'origine : [Noltari/aioairzone-cloud][aioairzone] et
  l'intégration [Airzone Cloud][airzone-integration] de Home Assistant.

## Licence

[MIT](LICENSE). Ce dépôt ne redistribue pas le code de `aioairzone-cloud`
(Apache-2.0) ; il le patche à l'exécution.

<!-- Liens -->
[airzone-integration]: https://www.home-assistant.io/integrations/airzone_cloud/
[aioairzone]: https://github.com/Noltari/aioairzone-cloud
[hacs-url]: https://github.com/hacs/integration
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[release-badge]: https://img.shields.io/github/v/release/Payou6994/ha-airzone-cloud-patch?style=for-the-badge
[release-url]: https://github.com/Payou6994/ha-airzone-cloud-patch/releases
[license-badge]: https://img.shields.io/github/license/Payou6994/ha-airzone-cloud-patch?style=for-the-badge
[validate-badge]: https://img.shields.io/github/actions/workflow/status/Payou6994/ha-airzone-cloud-patch/validate.yml?style=for-the-badge&label=validate
[validate-url]: https://github.com/Payou6994/ha-airzone-cloud-patch/actions/workflows/validate.yml
[hacs-repo-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[hacs-repo-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=Payou6994&repository=ha-airzone-cloud-patch&category=integration
[config-flow-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[config-flow-url]: https://my.home-assistant.io/redirect/config_flow_start/?domain=airzone_cloud_patch
