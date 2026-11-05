"""Airzone Cloud v2 control patch.

L'integration officielle `airzone_cloud` (via la librairie aioairzone-cloud)
envoie les commandes de controle sur l'ancien endpoint :

    PATCH https://m.airzonecloud.com/api/v1/devices/{id}
    body  {"param": <nom>, "value": <v>, "installation_id": <inst>, "opts": {...}}

Airzone a mure cet endpoint derriere un abonnement payant (HTTP 402). L'app
officielle, elle, controle via un nouvel endpoint NON mure :

    PATCH https://prodctrl.airzonecloud.com/api/v2/devices/{id}
    body  {"params": {<nom_v2>: <v>}, "installationId": <inst>, "opts": {...}}

Ce composant remplace a chaud la methode `AirzoneCloudApi.api_patch_device`
pour rediriger les commandes vers l'endpoint v2, en traduisant le corps.
La LECTURE (WebSocket, etats) reste 100% native et inchangee : on ne touche
qu'a l'ecriture.

Installation : copier ce dossier dans config/custom_components/ puis ajouter
    airzone_cloud_patch:
dans configuration.yaml et redemarrer Home Assistant.
"""
from __future__ import annotations

import json as _json
import logging
import urllib.parse

_LOGGER = logging.getLogger(__name__)

DOMAIN = "airzone_cloud_patch"

V2_BASE = "https://prodctrl.airzonecloud.com/api/v2"

# Noms de parametres cote v2 (captures depuis l'app officielle)
SP_HEAT = "setpoint_air_heat"
SP_COOL = "setpoint_air_cool"


async def async_setup(hass, config) -> bool:
    """Applique le patch au demarrage de Home Assistant."""
    _apply_patch()
    return True


def _to_v2_body(device, v1_json: dict) -> tuple[dict, str]:
    """Traduit le corps v1 (un seul param) vers le corps v2 (params groupes).

    v1 : {"param": p, "value": v, "installation_id": inst, "opts": {...}?}
    v2 : {"params": {p2: v}, "installationId": inst, "opts": {...}?}
    """
    param = v1_json.get("param")
    value = v1_json.get("value")
    inst = v1_json.get("installation_id")
    opts = v1_json.get("opts")

    v2_param = param
    if param == "setpoint":
        # Choix heat/cool selon le mode courant du device
        v2_param = SP_HEAT
        try:
            mode = device.get_mode()
            if mode is not None and mode.is_cool():
                v2_param = SP_COOL
        except Exception:  # noqa: BLE001 - best effort, on retombe sur heat
            _LOGGER.debug("Impossible de lire get_mode(), defaut=%s", v2_param)

    body: dict = {
        "params": {v2_param: value},
        "installationId": inst,
    }
    if opts is not None:
        body["opts"] = opts
    elif param == "setpoint":
        body["opts"] = {"units": 0}

    return body, device.get_id()


def _apply_patch() -> None:
    try:
        from aioairzone_cloud.cloudapi import AirzoneCloudApi
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("aioairzone-cloud introuvable, patch non applique: %s", err)
        return

    if getattr(AirzoneCloudApi, "_v2_control_patched", False):
        _LOGGER.debug("Patch v2 deja applique")
        return

    async def api_patch_device_v2(self, device, json):  # noqa: ANN001
        """Remplacement : PATCH vers l'endpoint v2 prodctrl."""
        body, dev_id = _to_v2_body(device, json)
        url = f"{V2_BASE}/devices/{urllib.parse.quote(dev_id)}"
        _LOGGER.debug("v2 PATCH %s body=%s", url, body)

        async with self._api_semaphore:
            async with self.session.request(
                "PATCH",
                url,
                headers=self.token.headers(),
                json=body,
                raise_for_status=True,
                timeout=self._api_timeout,
            ) as resp:
                text = await resp.text()
        if not text:
            return {}
        try:
            return _json.loads(text)
        except ValueError:
            return {}

    AirzoneCloudApi.api_patch_device = api_patch_device_v2
    AirzoneCloudApi._v2_control_patched = True
    _LOGGER.info(
        "aioairzone-cloud : controle redirige vers l'endpoint v2 (%s)", V2_BASE
    )
