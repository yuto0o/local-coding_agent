#!/bin/bash
uv sync
uv run python -m agent.main "$@"