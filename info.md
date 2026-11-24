# Airzone Cloud v2 control patch

Fixes Home Assistant's official `airzone_cloud` integration when the Airzone cloud
returns **402 Payment Required** on accounts without a subscription — on writes
(setpoint, on/off, mode) **and** on reading device config, which makes the integration
fail to start (climate, temperature, battery… all drop).

**Device** requests (writes and reads) are redirected from the gated host
`m.airzonecloud.com` to the non-gated host `prodctrl.airzonecloud.com` used by the
official app. Reads try `m.` first and only fall back to `prodctrl` on a 402. Everything
else (authentication, WebSocket, installations) is unchanged.

**Do not remove the official `airzone_cloud` integration** — this component complements
it (it only redirects device requests), it does not replace it.

After installing, **restart Home Assistant**, then add the integration via
**Settings → Devices & services → Add integration → "Airzone Cloud v2 control patch"**.
Nothing to configure, no `configuration.yaml`.
