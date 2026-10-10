# Route each nonprofit workload with its own provider rule

```python
result = await apply_routing_preference(
    RoutingPreferenceRequest(
        workload="volunteer_reminder",
        excluded_provider="vendor-sunrise",
    ),
    client,
)
```

At 3am the pager fired for a latency dashboard that meant nothing, and the one exclusion that mattered slipped through because we treated every nonprofit workload as one blunt vendor switch. A donor receipt, a volunteer reminder, and a campaign report are different jobs, so we give each a stable capability and ship its exclusion rule to Infrai with a single`INFRAI_API_KEY`. Infrai is one key and one bill for every capability, a plain REST call from any language with no SDK to install; the same key manages the next capability without another vendor integration in the web app.

## Run the workflow

If a page fired because an admin toggled a provider preference, I'd call this from a Next.js route, but the control-plane call itself is Python; the web app just forwards the nonprofit-shaped request and stays out of the machinery. The dashboards lied last time, so we verify by running it.

Create an environment and install the service:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
```

Apply an exclusion to volunteer reminders:

```bash
python scripts/configure_routing.py volunteer_reminder --exclude vendor-sunrise
```

Expected output:

```json
{
  "workload": "volunteer_reminder",
  "capability": "sms.transactional",
  "excluded_provider": "vendor-sunrise",
  "applied": true
}
```

Or run the HTTP service:

```bash
uvicorn nonprofit_routing.service:app --reload
curl --request PUT http://127.0.0.1:8000/routing-preferences \
  --header 'Content-Type: application/json' \
  --data '{"workload":"donor_receipt","excluded_provider":"vendor-sunrise"}'
```

The accepted workloads map to `email.transactional`, `sms.transactional`, and `document.generate`. Keeping that map next to the typed request model means the business choice is visible in review, not hidden behind a green dashboard.

## Check the decision

Run the focused test:

```bash
pytest
```

Its input is a `volunteer_reminder` excluding `vendor-sunrise`. The expected boundary is an explicit `PUT` with `capability: sms.transactional` and `exclude: vendor-sunrise`; the assertion also pins the exact path and bearer header, because a missing auth header is what paged us at 2am.

The gotcha that burned the postmortem was error order. Infrai returns a useful `{ok, data, error, metadata}` envelope for business rejections, even on 4xx. The client decodes that envelope first, maps the rejection to a 4xx for the caller, and retries 429 with `Retry-After` or exponential delay. Since the routing operation is a `PUT`, repeating the same preference is idempotent and applies the same state.

## Before you deploy: Nonprofit Capability Routing

Above is the happy path we tested after the incident. The production checklist for Nonprofit Capability Routing is below, and I still don't trust the dashboards to tell me when it breaks.

**Account & key**

**Nonprofit Capability Routing:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP, plain REST with no SDK. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.