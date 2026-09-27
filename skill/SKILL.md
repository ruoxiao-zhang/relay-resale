---
name: resale-refresh
description: Refresh the Relay pre-owned luxury price ledger (C:\Users\lily1\relay-resale) — sync its working files from the live artifact, re-check hand-maintained prices that have gone stale, add or remove items, and republish. Use when the user asks to update / refresh / 更新 the resale site, 二手奢侈品行情, or the Relay ledger.
---

# Refresh the Relay resale ledger

Live page: https://claude.ai/artifact/8s3Twh1ajkrEErnRqQsQ9A
Local copy: `C:\Users\lily1\relay-resale` (git repo → https://github.com/ruoxiao-zhang/relay-resale)

**The artifact is the source of truth.** A cloud routine ("Relay resale ledger – weekly refresh", `trig_016y8JjNX9vdeWjQgBYMGA4Q`, Mondays 09:00 Asia/Shanghai) reads the working files out of the artifact, runs the scraper and republishes them. The local copy can be behind, so always sync first and always publish the working files back.

| Published path | Local file | Role |
|---|---|---|
| (page) | `index.html` | The page; loads `data.json` at runtime. |
| `data.json` | `data.json` | Current values + per-item history, written by the scraper. |
| `data/history.jsonl` | `data/history.jsonl` | Every reading ever taken. |
| `src/scrape.py` | `scrape.py` | Scraper (Rolex Radar, Purr). Keeps the last good value on failure. |
| `src/sources.json` | `sources.json` | Item list. `source` = `rolexradar`, `purr` or `manual` (values + `checked` date). |
| `src/index.html.txt` | `index.html` | Copy of the page source for the cloud routine. |

The local Windows task `RelayResaleScrape` is disabled on purpose; running it would fork the history.

## Steps

1. **Sync down.** First `Artifact` action `read` with just the url (no path), so the live page counts as viewed; publishing is refused otherwise. Then `read` with the url and `paths`: `["data.json", "data/history.jsonl", "src/sources.json", "src/scrape.py", "src/index.html.txt"]`. Copy each saved file over its local counterpart (table above). If the cloud routine changed nothing you care about, this is still required: the publish in step 5 overwrites everything.

2. **Scrape** (optional; the routine does this weekly). `python -X utf8 scrape.py` in the project folder. Read every line.
   - `FAIL`: the site changed or blocked the request. Fetch the page, find where the number moved, fix the matching `parse_*` function in `scrape.py`, and rerun. Respect robots.txt and keep the delay; never switch to a site's private API.
   - `CHECK`: a price moved more than 40% since the last run. Confirm it on the source page before publishing; fix the parser if it's a parsing error.
   - `SKIP`: no price or retail. Tell the user.

3. **Refresh stale manual items.** For every `manual` item in `sources.json` whose `checked` date is more than 30 days old, look for a newer dated figure with WebSearch / WebFetch (dealer listings, WatchCharts, price guides dated this year). Only change a value when you find a dated source; update `mid` / `lo` / `hi` / `retail` / `n`, the `src`, both `note` languages if the context changed, and `checked`. If nothing newer exists, leave it and say so. Rerun `scrape.py` so `data.json` picks up the edits.

4. **Adding or removing items** (only when the user asks). Purr pages are listed in https://bypurr.com/sitemap.xml under `/bags/<brand>/<model>`; Rolex Radar references are at `https://rolexradar.watch/models/<ref>`.
   - Bulk bags: `python -X utf8 tools/probe_purr.py <brand-slug> ...` (slow: ~7 pages a minute; run it in the background) writes `tools/purr_probe.json`. Review it, then `python -X utf8 tools/add_purr.py --only slug1,slug2,...` appends the chosen ones. Don't pipe its output through `Select-Object -First`; that breaks the pipe before the file is written.
   - Curate by hand: drop duplicate pages of the same bag (keep the one with the most data points), vague catch-all pages ("Shoulder Bag", "Tote"), and pages whose retail is clearly wrong. Purr's retail is unreliable for Chanel and Hermès (stale or mixing exotics), so those brands stay manual except the Classic Flap.
   - Rolex Radar's retail for 126334 is wrong ($6,700); it stays out. Check retail for any new reference.
   - **Retention sanity (user's rule of thumb, confirmed 2026-09-27):** outside Hermès, Chanel and LV, bags almost never resell above retail. Goyard and The Row's Margaux are the documented exceptions. When a Purr bag comes out at ≥100%, look up the brand's current US retail and set it in `sources.json` as `retail` with `retail_src` [label, url], `retail_note` {en, zh} (which size/material) and `retail_checked`. If no single retail fits because the listings pool sizes or materials with very different prices, set `retail_ambiguous: true` instead; the page then shows "公价不确定" and leaves the item out of retention stats.
   - `scrape.py` sets `retail_unverified` automatically when Purr's median equals its own retail exactly; those items show "公价待核实" and are also left out of stats. The page marks every Purr retention ≥100% with `*` and a caveat. `tools/apply_retail_fixes.py` shows the shape of a bulk retail update.
   - Give each new item `sec` (`bag`, `wj` or `rtw`), English and Chinese names, and notes in both languages.

5. **Publish everything back.** `Artifact` publish, `url` above, `file_path` = `C:\Users\lily1\relay-resale\index.html`, no `icon`, and
   `files` = `{"data.json": "C:\\Users\\lily1\\relay-resale\\data.json", "data/history.jsonl": {"from": "C:\\Users\\lily1\\relay-resale\\data\\history.jsonl", "contentType": "text/plain"}, "src/scrape.py": {"from": "C:\\Users\\lily1\\relay-resale\\scrape.py", "contentType": "text/plain"}, "src/sources.json": "C:\\Users\\lily1\\relay-resale\\sources.json", "src/index.html.txt": {"from": "C:\\Users\\lily1\\relay-resale\\index.html", "contentType": "text/plain"}}`.
   Leaving out a `src/` file after changing it means next Monday's routine runs the old version.

6. **Commit to GitHub.** The project folder is a git repo pushed to https://github.com/ruoxiao-zhang/relay-resale (private). Git lives at `C:\Program Files\Git\cmd` (prepend it to `$env:Path` if `git` isn't found). Copy this skill file to `skill/SKILL.md` if it changed, then `git add -A`, commit with a one-line message saying what changed (e.g. `Weekly data 2026-10-05; re-sourced Santos, Love`), and `git push`. The weekly cloud routine does not touch GitHub, so this step is what keeps the repo current.

7. **Report** in the user's language: items updated, the biggest movers (from history), anything that failed or looked wrong, and which manual items you re-sourced (with links).

## Debugging the weekly routine

Load `RemoteTrigger` (ToolSearch `select:RemoteTrigger`), then `list_runs` with `trigger_id` `trig_016y8JjNX9vdeWjQgBYMGA4Q` and `get_run_log` on the run. If curl shows `connect_rejected` from the agent proxy, the cloud environment's network settings are blocking `bypurr.com` / `rolexradar.watch`; the user has to allow those domains for the "Default" environment in claude.ai/code. Routines can't be deleted through the API; the user manages them at https://claude.ai/code/routines.
