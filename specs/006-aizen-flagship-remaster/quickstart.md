# Quickstart

1. Copy `.env.example` to `.env` and configure one live provider.
2. Run `uv sync` and `uv run dvc pull`.
3. Run `uv run python scripts/preflight.py`.
4. Start `docker compose up --build -d`.
5. Open `http://localhost:5173`, choose a preset, and select **Find matching homes**. Interpretation and the live run happen as one action.

The first full run is live and may take longer while the selected model loads. **Edit brief** opens a disposable correction drawer; **Apply & rerun** starts another live run. A provider failure never returns a saved response.
