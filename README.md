# Relay · 流转

A bilingual (English / 中文) ledger of pre-owned luxury prices in three sections: handbags, jewellery & watches, and ready-to-wear. For each item it shows retail, typical resale price, range, retention and, for scraped items, weekly price history.

Live page: https://claude.ai/artifact/8s3Twh1ajkrEErnRqQsQ9A

## How it works

| File | Role |
|---|---|
| `sources.json` | The item list. `source` is `rolexradar` or `purr` (scraped every run) or `manual` (values kept here with a `checked` date). |
| `scrape.py` | Scrapes Rolex Radar (weekly Chrono24 averages) and Purr (resale listings pooled from Rebag, The RealReal, Vestiaire Collective and eBay). Respects robots.txt, waits 3 s between requests, keeps the last good value when a page fails, flags moves over 40%. Standard library only. |
| `data.json` | Output read by the page: current values plus per-item history. |
| `data/history.jsonl` | Every reading taken, one JSON object per line. |
| `index.html` | The page. Loads `data.json` at runtime. |
| `tools/` | `probe_purr.py` checks which Purr pages have usable data; `add_purr.py` appends chosen ones to `sources.json`; `probe_rr.py` checks Rolex Radar references. |
| `skill/SKILL.md` | The Claude Code skill (`/resale-refresh`) used to maintain the ledger. |

```
python scrape.py            # refresh data.json and history
python -m http.server       # then open http://localhost:8000 to preview
```

Opening `index.html` straight from disk won't load `data.json`; serve the folder as above.

## Updates

A Claude Code cloud routine runs every Monday at 09:00 (Asia/Shanghai). It reads the working files stored with the published page, runs `scrape.py` and republishes. The published page is the source of truth for data; this repository holds the code and a snapshot of the data.

## Data caveats

- Asking prices sit above what things actually sell for; estimates are the source's own judgement. Each item is labelled with its data type.
- Purr's retail figures can lag brand price rises, which flatters retention. Chanel and Hermès pages on Purr are unreliable and are kept manual (except the Classic Flap).
- Ready-to-wear data is thin; treat that section as a rough guide.
