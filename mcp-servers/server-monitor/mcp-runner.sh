#!/bin/bash
cd /opt/server-monitor
exec node src/mcp-server.js "$@"
