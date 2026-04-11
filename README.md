# hass-asic-rs

[![GitHub Release](https://img.shields.io/github/v/release/b-rowan/hass-asic-rs?style=for-the-badge)](https://github.com/b-rowan/hass-asic-rs/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange?style=for-the-badge)](https://my.home-assistant.io/redirect/hacs_repository/?owner=b-rowan&repository=hass-asic-rs&category=integration)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-orange?style=for-the-badge)](https://conventionalcommits.org)

A Home Assistant integration for ASIC miners, powered by [asic-rs](https://github.com/256-Foundation/asic-rs) via the `pyasic-rs` Python bindings.

## Features

- Per-miner sensors: hashrate, temperature, power, efficiency, uptime, fan RPM, pool shares
- Per-hashboard sensors: hashrate, temperatures, chip count, frequency, voltage
- Controls: fault light, mining pause/resume, power limit, restart
- Network scan during setup — pre-filled from your local subnet
- Links directly to each miner's web UI from the HA device page

---

## Installation

### Via HACS (recommended)

> HACS must be installed first. See the [HACS installation guide](https://hacs.xyz/docs/use/download/download/) if you haven't set it up yet.

1. Open HACS in Home Assistant.
2. Go to **Integrations** and click the three-dot menu in the top right.
3. Select **Custom repositories**.
4. Add `https://github.com/b-rowan/hass-asic-rs` with category **Integration**.
5. Search for **ASIC Miner** and install it.
6. Restart Home Assistant.

### Manual

1. Download the [latest release](https://github.com/b-rowan/hass-asic-rs/releases/latest).
2. Copy the `custom_components/asic_miner` folder into your HA config directory at `<config>/custom_components/asic_miner`.
3. Restart Home Assistant.

---

## Setup

After installation, go to **Settings → Devices & Services → Add Integration** and search for **ASIC Miner**.

You will be offered two setup options:

- **Enter IP address manually** — type the miner's IP and optional credentials.
- **Scan network for miners** — scans your local subnet (pre-filled, editable) and presents a list of discovered devices to choose from.

---

## Developer Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension

### Running a local HA instance

A `docker-compose.yml` is included that runs the official HA container with the integration mounted directly:

```bash
docker compose up -d
```

Open `http://localhost:8123` and add the integration from **Settings → Devices & Services**.

To pick up code changes, restart the container:

```bash
docker compose restart homeassistant
```

### Devcontainer

Open the project in VS Code and select **Reopen in Container** when prompted (or run it from the Command Palette). The devcontainer is based on the [official Home Assistant devcontainer image](https://github.com/home-assistant/devcontainer).

### Releasing

Releases are created via the **Release** workflow in GitHub Actions. Navigate to **Actions → Release → Run workflow**, enter a version number (e.g. `1.2.3`), and the workflow will:

1. Bump the version in `manifest.json` and `pyproject.toml`
2. Generate `CHANGELOG.md` and release notes via [git-cliff](https://git-cliff.org)
3. Commit, tag, and push
4. Publish a GitHub release with the generated notes
