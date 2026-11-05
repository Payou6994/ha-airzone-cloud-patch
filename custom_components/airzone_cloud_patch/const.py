"""Constantes du patch Airzone Cloud v2."""

DOMAIN = "airzone_cloud_patch"

# Hote non mure utilise par l'app officielle (controle ET lecture device)
PRODCTRL = "https://prodctrl.airzonecloud.com"

# Nouvel endpoint de controle utilise par l'app officielle (non mure)
V2_BASE = f"{PRODCTRL}/api/v2"

# Noms de parametres cote v2 (captures depuis l'app officielle)
SP_HEAT = "setpoint_air_heat"
SP_COOL = "setpoint_air_cool"
