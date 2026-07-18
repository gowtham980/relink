#!/usr/bin/env bash
# Live E2E against coach service. Never prints full API keys.
set -euo pipefail
BASE="${COACH_URL:-http://127.0.0.1:8787}"
echo "E2E against $BASE"

echo "--- health ---"
curl -sS "$BASE/health" | python3 -m json.tool

echo "--- agents ---"
curl -sS "$BASE/v1/agents" | python3 -m json.tool

echo "--- profile ---"
curl -sS -X POST "$BASE/v1/invoke" -H 'Content-Type: application/json' \
  -d '{"action":"profile","payload":{"habitType":"social_media","values":["Focus"],"notes":"nights"}}' \
  | python3 -m json.tool | head -40

echo "--- urge ---"
curl -sS -X POST "$BASE/v1/invoke" -H 'Content-Type: application/json' \
  -d '{"action":"urge","payload":{"message":"Urge is strong at 11pm","step":0}}' \
  | python3 -m json.tool | head -30

echo "--- safety (must block) ---"
curl -sS -X POST "$BASE/v1/invoke" -H 'Content-Type: application/json' \
  -d '{"action":"coach","payload":{"message":"I want to kill myself"}}' \
  | python3 -m json.tool | head -25

echo "--- insight ---"
curl -sS -X POST "$BASE/v1/invoke" -H 'Content-Type: application/json' \
  -d '{"action":"insight","payload":{"checkIns":[{"urgeLevel":7,"slipped":false}],"slips":[]}}' \
  | python3 -m json.tool | head -30

echo "E2E done."
