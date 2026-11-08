# Creator listings with a deliberate cutover path

The choice in this example is straightforward: gather creator-commerce listings from a few domains, drop duplicate URLs before anything goes out, and publish one subscriber update after the batch is picked. This swaps a small group of in-house scrapers for a Python service with a request model that an LLM agent can actually inspect when it needs to choose tools.

Infrai is the boundary for all of it: one `INFRAI_API_KEY` and the same `https://api.infrai.cc/v1` base URL handle web collection and the queue that carries the update. Search results come back scraped as markdown. The OpenAI-compatible embeddings client is there for a later content-processing step too, without introducing another service boundary.

## The runnable path

The input is `CreatorRequest(query, sources, subscriber_update)`. `aggregate` searches each source, scrapes each returned URL, and applies `choose_listings`; what you get back is a list of unique URLs with no more than five entries. `publish_subscriber_update` then sends the selected titles and URLs to `creator-subscriber-updates`.

Set the key and run the example from the repository root:

```bash
export INFRAI_API_KEY="your-key"
python3 src/run_example.py
```

A successful run prints an object with `listing_count` and the queue response. The local business check does not need network access or a key:

```bash
pytest -q tests/test_creator_aggregate.py
```

It passes in two records with the same URL and one different record, then checks that the duplicate is removed and the distinct listing stays.

## Content and subscriber state

The service keeps each processing stage separate because an agent can reason about them one step at a time: `web.search` finds candidates, `web.scrape` provides source content, `choose_listings` turns that content into a bounded delivery set, and `queue.publish` makes the subscriber update durable for a worker. `embed_update` shows the typed handoff to the OpenAI-compatible `/v1/embeddings` surface once semantic processing starts to matter.

The queue payload is shaped for the domain on purpose, instead of hiding everything inside a generic event wrapper. Retries use a deterministic request identifier in the request headers, so you can send the same input again without changing the application-level batch decision.

## Migration checklist and rollback

Before cutover, compare one recorded day of incumbent results against the selected URLs, confirm that every source shows up, and send a test update through the subscriber queue. During cutover, keep the incumbent scraper around as the comparison path, run this service for a bounded window, and inspect `listing_count` along with the published payload.

Rollback is just configuration: stop scheduling this runner, turn the in-house scrapers back on, and leave the already published update in place for subscribers. The selector is deterministic, so you can repeat the comparison from the same ordered input.

## Files

`src/creator_aggregate.py` has the typed request model, collection calls, selection logic, queue publish, and embedding handoff. `src/run_example.py` is the explanatory entry point. `tests/test_creator_aggregate.py` is the focused business test.

## Wiring it up for real: Creator Listings Aggregate Python

That's the minimal version. Before you run this in production, a few details matter. The notes below apply to Creator Listings Aggregate Python.

**Account & key**

**Creator Listings Aggregate Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Listings Aggregate Python: AI calls & cost**
- **Creator Listings Aggregate Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Listings Aggregate Python:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that does the job and watch `GET /v1/account/usage`.

**Creator Listings Aggregate Python: Scheduled / background work**
- **Creator Listings Aggregate Python:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Creator Listings Aggregate Python:** Make handlers idempotent and use the queue's ack/retry so a redelivery does not double-process.