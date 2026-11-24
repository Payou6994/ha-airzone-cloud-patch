# Airzone Cloud v2 control patch

[![hacs][hacs-badge]][hacs-url]
[![GitHub release][release-badge]][release-url]
[![License][license-badge]](LICENSE)
[![Validate][validate-badge]][validate-url]

A fix for Home Assistant's official **[Airzone Cloud][airzone-integration]** integration
when the Airzone cloud returns **`402 Payment Required`** on **accounts without a
subscription** — first on every **command** (setpoint, on/off, mode), and then also on
**reading** device config, which makes the integration **fail to start** altogether (no
entities at all: climate, temperature, thermostat **battery**…).

> Airzone is gating the **device** endpoints on the `m.airzonecloud.com` host (both
> **writes and reads**). The official app instead goes through the **non-gated** host
> `prodctrl.airzonecloud.com`; this component redirects device requests there.

---

## The problem

Airzone is progressively paywalling the **device** endpoints on `m.airzonecloud.com`,
which the `aioairzone-cloud` library (official integration) still uses. Same account,
same token — only the **host** changes:

| Device request | `m.airzonecloud.com` | `prodctrl.airzonecloud.com` (app) |
|---|---|---|
| Write `PATCH /devices/{id}` | **402** | **200 / 204** (v2) |
| Read `GET /devices/{id}/config` | **402** | **200** |

When the config read fails **at startup**, setup aborts and **all** entities drop
(climate, temperature, battery…).

> **Note — the gating is account-specific.** On some free accounts the config read still
> works on `m.` (200), and `prodctrl` then *rejects* that same request with **422**. The
> patch handles both cases (see below).

## The solution

This component hot-patches **two** methods of `AirzoneCloudApi`:

- **`api_patch_device`** (write) → **v2 `prodctrl`** endpoint, translating the body
  (`{"param","value","installation_id"}` → `{"params":{…},"installationId","opts"}`)
  and picking `setpoint_air_heat` / `setpoint_air_cool` based on the current mode;
- **`api_request`** (read) → for **device** requests (`.../devices/{id}…`) it tries
  `m.` **first** and only falls back to **`prodctrl`** **if `m.` returns 402**. Accounts
  gated on `m.` fall back to `prodctrl`; accounts still served on `m.` stay there (no 422).

Everything else (authentication, installations, weather, WebSocket) stays **on `m.`
and unchanged**.

## Requirements

- The official **[Airzone Cloud][airzone-integration]** integration installed and
  configured (it provides the entities).
- An Airzone account **without** a subscription (the case where the cloud returns 402).

> ⚠️ **Do not remove the official `airzone_cloud` integration.** This component does not
> replace it, it **complements** it: it needs it installed and active (it provides
> authentication, the WebSocket and the entities). The patch only **redirects device
> requests** (writes and reads) to the non-gated host.

## Installation

### Via HACS (recommended)

1. Add this repository as a **custom repository** in HACS (category *Integration*), or
   click:

   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.][hacs-repo-badge]][hacs-repo-url]

2. Install **Airzone Cloud v2 control patch**, then **restart** Home Assistant.

### Manual

Copy `custom_components/airzone_cloud_patch/` into your `config/custom_components/`
folder, then restart Home Assistant.

## Configuration

No `configuration.yaml`. Add the integration from the UI:

**Settings → Devices & services → Add integration → "Airzone Cloud v2 control patch"**,
or click:

[![Add integration][config-flow-badge]][config-flow-url]

There is nothing to fill in: submit and you're done.

## Verify

After adding it, the `airzone_cloud` integration should start normally (no more 402 — or
422 — at setup), and changing a setpoint from a `climate` card should work. The component
also logs a line at startup confirming the patch is active.

## How it works

| Action | Library (v1, gated) | Sent as v2 (this patch) |
|---|---|---|
| Heat setpoint | `{"param":"setpoint","value":21}` | `{"params":{"setpoint_air_heat":21},"opts":{"units":0}}` |
| Cool setpoint | `{"param":"setpoint","value":21}` | `{"params":{"setpoint_air_cool":21},"opts":{"units":0}}` |
| On/off | `{"param":"power","value":true}` | `{"params":{"power":true}}` |
| Mode | `{"param":"mode","value":3}` | `{"params":{"mode":3}}` |

In every case: `installationId` in camelCase and the URL
`prodctrl.airzonecloud.com/api/v2/devices/{id}`.

For **reads**, device-scoped requests (`.../devices/{id}/config`, etc.) are tried on `m.`
first and only sent to `prodctrl` (same path) when `m.` returns 402 — which unblocks the
integration's startup and brings the entities back (battery included).

## Caveats / disclaimer

- Relies on Airzone's **undocumented** cloud API; it may change without notice. Goal:
  **interoperability with your own hardware**.
- The patch follows `aioairzone-cloud`'s internals (tested with **v0.7.2**). A major
  library rework may require an update.
- The ideal long-term fix would be upstream, in `aioairzone-cloud`.

## Credits

- Original integration and library: [Noltari/aioairzone-cloud][aioairzone] and Home
  Assistant's [Airzone Cloud][airzone-integration] integration.

## License

[MIT](LICENSE). This repository does not redistribute `aioairzone-cloud`'s code
(Apache-2.0); it patches it at runtime.

<!-- Links -->
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
