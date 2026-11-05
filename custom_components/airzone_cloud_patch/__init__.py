"""Airzone Cloud v2 control patch.

L'integration officielle `airzone_cloud` (via la librairie aioairzone-cloud)
envoie les commandes de controle sur l'ancien endpoint :

    PATCH https://m.airzonecloud.com/api/v1/devices/{id}

Airzone a mure cet endpoint derriere un abonnement payant (HTTP 402). L'app
officielle, elle, controle via un nouvel endpoint NON mure :

    PATCH https://prodctrl.airzonecloud.com/api/v2/devices/{id}

Ce composant remplace a chaud la methode `AirzoneCloudApi.api_patch_device`
pour rediriger les commandes vers l'endpoint v2 (voir patch.py). La LECTURE
(WebSocket, etats) reste 100% native et inchangee : on ne touche qu'a
l'ecriture.

Configuration : via l'UI (Parametres > Appareils et services > Ajouter une
integration > "Airzone Cloud v2 control patch"). Aucune ligne dans
configuration.yaml.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .patch import apply_patch, remove_patch


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Applique le patch quand l'integration est ajoutee / au demarrage."""
    apply_patch()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Restaure la methode d'origine au dechargement."""
    remove_patch()
    return True
