"""Patch a chaud de aioairzone-cloud : redirige controle ET lecture device vers prodctrl.

L'integration officielle `airzone_cloud` tape l'hote `m.airzonecloud.com`, que
Airzone a mure derriere un abonnement (HTTP 402) pour les endpoints device :

  - ecriture (controle)  : PATCH m.airzonecloud.com/api/v1/devices/{id}      -> 402
  - lecture de config    : GET   m.airzonecloud.com/api/v1/devices/{id}/config -> 402

L'app officielle, elle, passe par l'hote NON mure `prodctrl.airzonecloud.com`
(meme compte, meme token) :

  - ecriture : PATCH prodctrl.airzonecloud.com/api/v2/devices/{id}       (corps groupe)
  - lecture  : GET   prodctrl.airzonecloud.com/api/v1/devices/{id}/config -> 200

Ce module remplace a chaud deux methodes de `AirzoneCloudApi` :
  - `api_patch_device` : controle -> endpoint v2 prodctrl (traduction du corps).
  - `api_request`      : les requetes device-scoped (`.../devices/{id}...`) sont
                         renvoyees vers prodctrl au lieu de m. ; le reste (install.,
                         app-manager, meteo, WebSocket) reste inchange.

Sans le redirect de lecture, le setup de l'integration echoue (402 sur la config)
et TOUTES les entites tombent (y compris l'indicateur de batterie des thermostats).
"""
from __future__ import annotations

import json as _json
import logging
import re
import urllib.parse

from .const import PRODCTRL, SP_COOL, SP_HEAT, V2_BASE

_LOGGER = logging.getLogger(__name__)

# References vers les methodes d'origine, pour restauration au dechargement
_ORIG_PATCH_DEVICE = None
_ORIG_API_REQUEST = None

# Chemins "device-scoped" a renvoyer vers prodctrl (id device = 24 hex).
# Ne matche pas `devices/ws/{mac}/status` (pas 24 hex) -> reste sur m.
_DEVICE_RE = re.compile(r"devices/[0-9a-f]{24}", re.IGNORECASE)


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
        v2_param = SP_HEAT
        try:
            mode = device.get_mode()
            if mode is not None and mode.is_cool():
                v2_param = SP_COOL
        except Exception:  # noqa: BLE001 - best effort, defaut = chaud
            _LOGGER.debug("get_mode() indisponible, defaut=%s", v2_param)

    body: dict = {"params": {v2_param: value}, "installationId": inst}
    if opts is not None:
        body["opts"] = opts
    elif param == "setpoint":
        body["opts"] = {"units": 0}

    return body, device.get_id()


def apply_patch() -> bool:
    """Applique le patch (controle + lecture). Retourne True si applique."""
    global _ORIG_PATCH_DEVICE, _ORIG_API_REQUEST
    try:
        from aioairzone_cloud.cloudapi import AirzoneCloudApi
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("aioairzone-cloud introuvable, patch non applique: %s", err)
        return False

    if getattr(AirzoneCloudApi, "_prodctrl_patched", False):
        _LOGGER.debug("Patch prodctrl deja applique")
        return True

    _ORIG_PATCH_DEVICE = AirzoneCloudApi.api_patch_device
    _ORIG_API_REQUEST = AirzoneCloudApi.api_request

    async def api_patch_device_prodctrl(self, device, json):  # noqa: ANN001
        """Controle : PATCH vers l'endpoint v2 prodctrl (corps groupe)."""
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

    async def api_request_prodctrl(self, method, path, json=None):  # noqa: ANN001
        """Lecture : requetes device-scoped renvoyees vers prodctrl (non mure)."""
        if _DEVICE_RE.search(path):
            url = f"{PRODCTRL}/{path}"
            _LOGGER.debug("lecture device redirigee vers prodctrl: %s %s", method, url)
            async with self._api_semaphore:
                async with self.session.request(
                    method,
                    url,
                    headers=self.token.headers(),
                    json=json,
                    raise_for_status=True,
                    timeout=self._api_timeout,
                ) as resp:
                    try:
                        return await resp.json(content_type=None)
                    except Exception:  # noqa: BLE001 - corps vide (ex. 304)
                        return {}
        # tout le reste : comportement d'origine (hote m.)
        return await _ORIG_API_REQUEST(self, method, path, json)

    AirzoneCloudApi.api_patch_device = api_patch_device_prodctrl
    AirzoneCloudApi.api_request = api_request_prodctrl
    AirzoneCloudApi._prodctrl_patched = True
    _LOGGER.info(
        "aioairzone-cloud : controle + lecture device rediriges vers %s", PRODCTRL
    )
    return True


def remove_patch() -> None:
    """Restaure les methodes d'origine (au dechargement de l'integration)."""
    global _ORIG_PATCH_DEVICE, _ORIG_API_REQUEST
    try:
        from aioairzone_cloud.cloudapi import AirzoneCloudApi
    except Exception:  # noqa: BLE001
        return
    if getattr(AirzoneCloudApi, "_prodctrl_patched", False):
        if _ORIG_PATCH_DEVICE is not None:
            AirzoneCloudApi.api_patch_device = _ORIG_PATCH_DEVICE
        if _ORIG_API_REQUEST is not None:
            AirzoneCloudApi.api_request = _ORIG_API_REQUEST
        AirzoneCloudApi._prodctrl_patched = False
        _ORIG_PATCH_DEVICE = None
        _ORIG_API_REQUEST = None
        _LOGGER.info("aioairzone-cloud : methodes d'origine restaurees")
