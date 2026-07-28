#!/bin/bash
set -e

echo "=== Web Portal - TrueNAS Scale Installer ==="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! docker compose version &> /dev/null; then
        echo "Error: docker-compose is not installed."
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# Create config directory
CONFIG_DIR="${CONFIG_DIR:-./config}"
mkdir -p "$CONFIG_DIR"

# Copy default sites.json if it doesn't exist
if [ ! -f "$CONFIG_DIR/sites.json" ]; then
    echo "Creating default sites.json..."
    cp config/sites.json "$CONFIG_DIR/sites.json"
fi

# Build and start
echo "Building Web Portal..."
$COMPOSE_CMD build

echo "Starting Web Portal..."
$COMPOSE_CMD up -d

echo ""
echo "=== Web Portal is running! ==="
echo "Access it at: http://$(hostname -I | awk '{print $1}'):${WEBPORTAL_PORT:-8080}"
echo ""
echo "To configure sites, edit: $CONFIG_DIR/sites.json"
echo "Or use the built-in management UI in the sidebar."
echo ""
echo "To stop: $COMPOSE_CMD down"
echo "To update: $COMPOSE_CMD up -d --build"
