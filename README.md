# Airzone Cloud v2 control patch

[![hacs][hacs-badge]][hacs-url]
[![GitHub release][release-badge]][release-url]
[![License][license-badge]](LICENSE)
[![Validate][validate-badge]][validate-url]

Correctif pour l'intégration officielle **[Airzone Cloud][airzone-integration]** de
Home Assistant quand le cloud Airzone répond **`402 Payment Required`** à chaque
commande (changement de consigne, marche/arrêt, mode) sur les comptes **sans
abonnement**.

> **La lecture des états fonctionne toujours** nativement — c'est seulement
> l'**écriture** (le contrôle) qui est cassée. Ce composant ne corrige que ça.

---

## Le problème

Airzone a déplacé l'endpoint de contrôle derrière un abonnement payant. La
librairie `aioairzone-cloud` utilisée par l'intégration officielle envoie encore
les commandes sur l'ancienne adresse :

```
PATCH https://m.airzonecloud.com/api/v1/devices/{id}   →  402 Payment Required
```

L'application mobile officielle, elle, pilote via un nouvel endpoint **non muré** :

```
PATCH https://prodctrl.airzonecloud.com/api/v2/devices/{id}   →  204 No Content
```

## La solution

Ce composant remplace à chaud la **seule** méthode d'écriture de la librairie
(`AirzoneCloudApi.api_patch_device`) pour :

1. rediriger la commande vers l'endpoint **v2 `prodctrl`** ;
2. traduire le corps `{"param", "value", "installation_id"}` → `{"params": {…}, "installationId", "opts"}` ;
3. choisir `setpoint_air_heat` / `setpoint_air_cool` selon le mode courant.

Tout le reste (authentification, WebSocket, états, entités `climate`) reste
**natif et inchangé**.

## Prérequis

- L'intégration **[Airzone Cloud][airzone-integration]** officielle installée et
  configurée (elle fournit les entités ; la lecture doit déjà fonctionner).
- Un compte Airzone **sans** abonnement (c'est le cas où l'écriture renvoie 402).

> ⚠️ **Ne supprime pas l'intégration officielle `airzone_cloud`.** Ce composant
> ne la remplace pas, il la **complète** : il a besoin qu'elle reste installée et
> active (elle fournit l'authentification, le WebSocket, les entités et toute la
> lecture). Ce patch ne corrige **que l'écriture**.

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
aioairzone-cloud : controle redirige vers l'endpoint v2 (https://prodctrl.airzonecloud.com/api/v2)
```

Change une consigne depuis une carte `climate` : la commande passe maintenant
(plus de 402).

## Comment ça marche

| Action | Librairie (v1, muré) | Envoyé en v2 (ce patch) |
|---|---|---|
| Consigne chaud | `{"param":"setpoint","value":21}` | `{"params":{"setpoint_air_heat":21},"opts":{"units":0}}` |
| Consigne froid | `{"param":"setpoint","value":21}` | `{"params":{"setpoint_air_cool":21},"opts":{"units":0}}` |
| Marche/arrêt | `{"param":"power","value":true}` | `{"params":{"power":true}}` |
| Mode | `{"param":"mode","value":3}` | `{"params":{"mode":3}}` |

Dans tous les cas : `installationId` en camelCase et l'URL
`prodctrl.airzonecloud.com/api/v2/devices/{id}`.

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
