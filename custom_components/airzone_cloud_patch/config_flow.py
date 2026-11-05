"""Config flow (ajout via l'UI, aucune saisie requise)."""
from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class AirzoneCloudPatchConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration mono-instance, sans parametre."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Etape unique : confirmation puis creation de l'entree."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user")

        return self.async_create_entry(
            title="Airzone Cloud v2 control patch", data={}
        )
