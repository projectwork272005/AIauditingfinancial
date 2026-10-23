# Run status

## 2026-10-23 - Step 0 environment check: BLOCKED

The experiment was not executed. No API call was made, and no fund data, model output or result was produced. Nothing in outputs/ or data/ was changed.

### What passed
- `python -m pip install -r requirements.txt`: OK.
- `python -m pytest -q tests`: 11 passed.

### What is missing

1. Environment variables (checked by name only with `env | cut -d= -f1`):
   - `AI_agents` (Volcano Engine Ark Agent Plan key): NOT SET.
   - `fuyao` (Tonghuashun data API key for fuyao.aicubes.cn): NOT SET.

2. Network access: the environment's network policy denies both hosts. The egress proxy answers HTTP 403 to the CONNECT request (curl HTTP code 000, "CONNECT tunnel failed, response 403"):
   - `ark.cn-beijing.volces.com` (port 443)
   - `fuyao.aicubes.cn` (port 443)

### What to change in the cloud environment settings
Open the cloud environment menu in the session's title bar, then Edit:
- Network access: add `ark.cn-beijing.volces.com` and `fuyao.aicubes.cn` under Allowed domains (keep Allow package managers ticked), or choose a broader access level. Steps: https://code.claude.com/docs/en/cloud-environments#network-access
- Add the two keys as environment variables (or Network secrets, where offered) named exactly `AI_agents` and `fuyao`.

A new session picks up the changes. Then rerun the task from Step 0.

Steps 1-6 (fund data, model listing, pilot, main run, analysis) were not started.
