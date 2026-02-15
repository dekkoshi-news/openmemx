#!/bin/bash
# Local development start script
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ensure src is in python path
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run the MCP server module directly
python -m openmemx.mcp_server
