"""Patch a chaud de aioairzone-cloud : redirige le controle vers l'endpoint v2.

L'integration officielle `airzone_cloud` envoie les commandes sur l'ancien
endpoint `m.airzonecloud.com/api/v1/devices` (desormais 402 Payment Required).
On remplace la methode `AirzoneCloudApi.api_patch_device` pour taper le nouvel
endpoint `prodctrl.airzonecloud.com/api/v2/devices` et traduire le corps.
La lecture (WebSocket, etats) reste native et inchangee.
"""
from __future__ import annotations

import json as _json
import logging
import urllib.parse

from .const import SP_COOL, SP_HEAT, V2_BASE

_LOGGER = logging.getLogger(__name__)

# Reference vers la methode d'origine, pour pouvoir la restaurer
_ORIGINAL = None


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
    """Applique le patch. Retourne True si applique (ou deja applique)."""
    global _ORIGINAL
    try:
        from aioairzone_cloud.cloudapi import AirzoneCloudApi
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("aioairzone-cloud introuvable, patch non applique: %s", err)
        return False

    if getattr(AirzoneCloudApi, "_v2_control_patched", False):
        _LOGGER.debug("Patch v2 deja applique")
        return True

    _ORIGINAL = AirzoneCloudApi.api_patch_device

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
    _LOGGER.info("aioairzone-cloud : controle redirige vers l'endpoint v2 (%s)", V2_BASE)
    return True


def remove_patch() -> None:
    """Restaure la methode d'origine (au dechargement de l'integration)."""
    global _ORIGINAL
    try:
        from aioairzone_cloud.cloudapi import AirzoneCloudApi
    except Exception:  # noqa: BLE001
        return
    if _ORIGINAL is not None and getattr(AirzoneCloudApi, "_v2_control_patched", False):
        AirzoneCloudApi.api_patch_device = _ORIGINAL
        AirzoneCloudApi._v2_control_patched = False
        _ORIGINAL = None
        _LOGGER.info("aioairzone-cloud : methode de controle d'origine restauree")
