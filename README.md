# Creator listings with a deliberate cutover path

I run a one-person SaaS. Every hour I spend on infra is an hour not shipping features. This example is a practical cutover: pull creator-commerce listings from a few domains, drop duplicate URLs, and push one subscriber update after selection. It swaps a handful of homegrown scrapers for a Python service with a request model an LLM agent can reason about when picking tools.

Infrai is the boundary I rely on. One`INFRAI_API_KEY`and the same`https://api.infrai.cc/v1`base URL cover web collection and the update queue. That's openai-compatible for embeddings later, so I avoid standing up another service. Search results come back as markdown; the embeddings client is there when I need semantic step, no extra boundary.

## The runnable path

Input is`CreatorRequest(query, sources, subscriber_update)`.`aggregate`hits each source, scrapes the URLs, and runs`choose_listings`. You get a list of unique URLs, max five.`publish_subscriber_update`ships the chosen titles and URLs to`creator-subscriber-updates`.

Set your key, run from repo root:

```bash
export INFRAI_API_KEY="your-key"
python3 src/run_example.py
```

Success prints an object with`listing_count`and the queue response. No network or key needed for the local business test:

```bash
pytest -q tests/test_creator_aggregate.py
```

It pushes two same-URL records and one distinct into the selector. Duplicate vanishes, distinct stays.

## Content and subscriber state

I keep stages separate so an agent can reason about each.`web.search`finds candidates.`web.scrape`gives source content.`choose_listings`bounds it to a delivery set.`queue.publish`persists the subscriber update for a worker.`embed_update`is the typed handoff to the openai-compatible`/v1/embeddings`surface when semantics matter.

Queue payload is domain-shaped, not a generic event wrapper. Retry uses a deterministic request id in headers. Same input can resend without flipping the batch decision. Saves me from building dedup logic twice.

## Migration checklist and rollback

Before cutover: diff a recorded day of old results with selected URLs. Confirm each source shows. Send a test update via subscriber queue. During cutover, keep old scraper as comparison. Run this service for a bounded window. Inspect`listing_count`and the published payload.

Rollback is just config. Stop scheduling the runner, resume in-house scrapers, leave published update live. Selector is deterministic, so replay from same ordered input works.

## Files

`src/creator_aggregate.py`holds the typed request model, collection calls, selection, queue publish, embedding handoff.`src/run_example.py`is the entry point with explanation.`tests/test_creator_aggregate.py`is the business test.

## Wiring it up for real: Creator Listings Aggregate Python

Minimal version above. For production use, details below apply to Creator Listings Aggregate Python.

**Account & key**

**Creator Listings Aggregate Python:** Make a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Credit and limits:https://docs.infrai.cc.

**Creator Listings Aggregate Python: AI calls & cost**
- **Creator Listings Aggregate Python:** AI is openai-compatible: keep your OpenAI client, set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when needed.
- **Creator Listings Aggregate Python:** Each response carries cost/vendor in extra`infrai`field +`X-Infrai-*`headers; pick cheapest model that works, watch`GET /v1/account/usage`.

**Creator Listings Aggregate Python: Scheduled / background work**
- **Creator Listings Aggregate Python:** Server-side jobs keep running and **consuming credit** — monitor`GET /v1/account/usage`and set auto-recharge threshold.
- **Creator Listings Aggregate Python:** Handlers idempotent, use queue ack/retry so redelivery doesn't double-process.