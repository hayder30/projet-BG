#!/bin/sh
# Writes config.js from the API_URL environment variable, then lets nginx start.
set -e
echo "window.API_URL = \"${API_URL:-http://localhost:8000/api}\";" > /usr/share/nginx/html/config.js
