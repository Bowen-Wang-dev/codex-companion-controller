# Token and pricing model

[简体中文（默认）](05-TOKEN-AND-PRICING.md) · English

## Non-overlapping display rows

- Uncached input = total API input − cache reads − cache writes.
- Cache reads and cache writes have separate rows and rates.
- Non-reasoning output = total API output − reasoning.
- Reasoning has its own row and uses the output rate under the recorded OpenAI rules. It is already included in API output and is counted once.
- Display total is the sum of those five disjoint rows. Do not add cache or reasoning to API totals again.

Missing API breakdowns must remain explicitly unknown. The current provider CSV lacks reasoning; the older adapter fills it with 0. This is a recorded source-completeness limitation, not proof that reasoning was absent.

## Two rate modes

Configuration: `controller/private/token_rates.json`, matched by exact model ID.

- `custom`: user-defined base prices × multiplier. Missing multiplier in old files means 1; preserve existing discounted values and do not automatically multiply by 0.18 again.
- `openai`: built-in verified-at-the-time prices × multiplier, default 1. Never substitute a similar model's price.
- Source currently includes `gpt-6.1-sol`; other models use custom prices or a future verified addition. Prices are historical snapshots, not permanently current facts. A gateway's claim of “official prices” is not independent verification.

Built-in Sol snapshot, USD per million tokens: ordinary input 2, cache read 0.1, cache write 2.5, output 10; long-context input 4, cache read 0.2, cache write 5, output 15. The program does not refresh this card live. Metering lacks cache-TTL breakdowns and cannot guarantee other cache pricing schemes. Recheck applicable sources before changing it.

Long-context condition: each request's input, including cache, is strictly greater than 272000. The entire request, including output, uses that tier; this is not marginal pricing of only the excess. Do not use output count, turn total, daily total or context-window capacity to choose the tier. Determine tiers request by request, then aggregate; reasoning and output share the corresponding tier's output rate.

## Sources and persistence

- App Server numeric events and completed local records have different cumulative histories; do not add them directly.
- The ledger stores thread / turn / model, original cumulative baselines and per-response IDs / boundaries. Replay, recovery and reconnect must deduplicate.
- Compaction calls can be absent from ordinary events; incremental local completed numeric records supplement them.
- Provider CSV / TSV adds missing requests only when uniquely attributable to known turns. A later local record removes its supplement.
- Reset clears only local accumulation, preserving replay baselines; provider bills, chats and accounts do not change.
- Missing request boundaries cannot be guessed from a cumulative total as one long-context request; large historical cost estimates may remain unknown.
- CSV `Input Tokens` means uncached input, unlike Responses `input_tokens`, which includes cache. `Billed Cost` already includes the multiplier and must not be discounted again.

## Earlier actual reconciliation

Private user exports were compared request by request. A single-tier estimate understated mixed ordinary / long-context usage; per-request dual-tier calculation reduced differences to per-request rounding. Actual rows, IP addresses, API-key labels and totals were not copied into public handoff documents.

Historical source references, to recheck before future price changes: [model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [reasoning](https://developers.openai.com/api/docs/guides/reasoning), [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching). These links do not claim that this documentation-only phase revalidated live prices.
