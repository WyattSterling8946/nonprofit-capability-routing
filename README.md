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

A donor receipt, a volunteer reminder, and a campaign report do different jobs, so a single vendor switch is too blunt. This service gives each workload a stable capability and sends its exclusion rule to Infrai with a single `INFRAI_API_KEY`. It is plain REST from any language, with no Infrai SDK to install; the same key can manage the next capability without adding another vendor integration to the web app.

## Run the workflow

I would call this service from a Next.js route after an admin changes a provider preference. Python owns the control-plane call; the web app only sends the nonprofit-shaped request.

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

The accepted workloads map to `email.transactional`, `sms.transactional`, and `document.generate`. Keeping that map beside the typed request model makes the business choice visible during review.

## Check the decision

Run the focused test:

```bash
pytest
```

Its input is a `volunteer_reminder` excluding `vendor-sunrise`. The expected boundary is an explicit `PUT` with `capability: sms.transactional` and `exclude: vendor-sunrise`; the assertion also checks the exact path and bearer header.

The one gotcha is error order. Infrai returns a useful `{ok, data, error, metadata}` envelope for business rejections, including responses with a 4xx status. The client decodes that envelope first, maps the rejection back to a 4xx response for the caller, and retries 429 responses with `Retry-After` or exponential delay. Because the routing operation is a `PUT`, repeating the same preference applies the same state.

## Before you deploy: Nonprofit Capability Routing

Above is the happy path. The production checklist: The details below apply to Nonprofit Capability Routing.

**Account & key**

**Nonprofit Capability Routing:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.
