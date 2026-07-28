# Web Portal for TrueNAS Scale

A customizable web portal that embeds external websites via iframes, designed to run as a TrueNAS Scale app.

## Features

- **Sidebar navigation** with categorized site links
- **Iframe-based viewing** - browse external sites within the portal
- **Built-in site manager** - add, edit, and delete sites from the UI
- **Search/filter** - quickly find sites by name, URL, or category
- **Config file support** - pre-configure sites via `config/sites.json`
- **Persistent storage** - sites saved in browser localStorage + optional config file
- **Dark theme** - clean, modern dark UI

## Quick Start (Docker)

```bash
# Clone or copy this directory to your TrueNAS SCALE system
cd webportal-app

# Copy and edit the environment file
cp .env.example .env

# Run the install script
./install.sh
```

Then open `http://YOUR_TRUENAS_IP:8080` in your browser.

## Configuration

### Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBPORTAL_PORT` | `8080` | Port to expose the portal on |
| `TZ` | `UTC` | Timezone |
| `WEBPORTAL_CONFIG` | `./config` | Path to config directory |

### Sites Configuration (config/sites.json)

Pre-configure sites that load as defaults when no user data exists:

```json
[
  {
    "name": "My NAS",
    "url": "https://192.168.1.100:8443",
    "icon": "N",
    "category": "Infrastructure"
  }
]
```

### TrueNAS Scale App Install

For installing as a TrueNAS SCALE app:

1. Copy the `ix_chart/` directory to your TrueNAS app catalog
2. Build the Docker image: `docker build -t webportal .`
3. Install via the TrueNAS Apps UI using the Helm chart

Alternatively, use the Docker Compose method above - it works perfectly on TrueNAS SCALE with Docker installed.

## Managing Sites

1. Click **"Manage Sites"** in the sidebar
2. Fill in the form: Name, URL, Icon (emoji/letter), Category
3. Click Add or Update
4. Sites persist in browser localStorage

## File Structure

```
webportal-app/
  app/
    index.html          # Main HTML
    css/style.css       # Styles
    js/app.js           # Application logic
  config/
    sites.json          # Default site configuration
  nginx/
    default.conf        # Nginx server config
  ix_chart/             # TrueNAS Scale Helm chart
    Chart.yaml
    values.yaml
    templates/
  Dockerfile
  docker-compose.yml
  install.sh
  app.yaml              # TrueNAS app metadata
```

## Stopping

```bash
docker-compose down
```
