---
name: resale-refresh
description: Refresh the Relay pre-owned luxury price ledger (C:\Users\lily1\relay-resale) — pull the repo, re-check hand-maintained prices that have gone stale, add or remove items, and push so GitHub Pages redeploys. Use when the user asks to update / refresh / 更新 the resale site, 二手奢侈品行情, or the Relay ledger.
---

# Refresh the Relay resale ledger

Live site: https://ruoxiao-zhang.github.io/relay-resale/ (GitHub Pages from `main`, linked from the user's portfolio)
Repo: https://github.com/ruoxiao-zhang/relay-resale (public) · Local copy: `C:\Users\lily1\relay-resale`

**GitHub `main` is the single source of truth (since 2026-10-02).** The workflow `.github/workflows/refresh.yml` runs Mondays 01:00 UTC (09:00 Asia/Shanghai): it runs `scrape.py`, refuses to commit if more than 10 items FAIL, commits `data.json` + `data/history.jsonl` as github-actions[bot], then marks the run failed if any CHECK line (>40% move) appeared, so GitHub emails the user to confirm those on the source pages. Pages redeploys on each push.

The old claude.ai artifact (https://claude.ai/artifact/8s3Twh1ajkrEErnRqQsQ9A) and its Claude routine `trig_016y8JjNX9vdeWjQgBYMGA4Q` are retired (routine disabled); don't publish there or re-enable it, or the history forks.

| File | Role |
|---|---|
| `index.html` | The page; loads `data.json` at runtime. |
| `data.json` | Current values + per-item history, written by the scraper. |
| `data/history.jsonl` | Every reading ever taken. |
| `scrape.py` | Scraper (Rolex Radar, Purr). Keeps the last good value on failure. |
| `sources.json` | Item list. `source` = `rolexradar`, `purr` or `manual` (values + `checked` date). |

The local Windows task `RelayResaleScrape` is disabled on purpose; running it would fork the history.

## Steps

1. **Sync down.** `git pull` in the project folder (git lives at `C:\Program Files\Git\cmd`; prepend it to `$env:Path` if `git` isn't found). The weekly workflow commits there.

2. **Scrape** (optional; the workflow does this weekly). `python -X utf8 scrape.py` in the project folder. Read every line.
   - `FAIL`: the site changed or blocked the request. Fetch the page, find where the number moved, fix the matching `parse_*` function in `scrape.py`, and rerun. Respect robots.txt and keep the delay; never switch to a site's private API.
   - `CHECK`: a price moved more than 40% since the last run. Confirm it on the source page before pushing; fix the parser if it's a parsing error.
   - `SKIP`: no price or retail. Tell the user.

3. **Refresh stale manual items.** For every `manual` item in `sources.json` whose `checked` date is more than 30 days old, look for a newer dated figure with WebSearch / WebFetch (dealer listings, WatchCharts, price guides dated this year). Only change a value when you find a dated source; update `mid` / `lo` / `hi` / `retail` / `n`, the `src`, both `note` languages if the context changed, and `checked`. If nothing newer exists, leave it and say so. Rerun `scrape.py` so `data.json` picks up the edits.

4. **Adding or removing items** (only when the user asks). Purr pages are listed in https://bypurr.com/sitemap.xml under `/bags/<brand>/<model>`; Rolex Radar references are at `https://rolexradar.watch/models/<ref>`.
   - Bulk bags: `python -X utf8 tools/probe_purr.py <brand-slug> ...` (slow: ~7 pages a minute; run it in the background) writes `tools/purr_probe.json`. Review it, then `python -X utf8 tools/add_purr.py --only slug1,slug2,...` appends the chosen ones. Don't pipe its output through `Select-Object -First`; that breaks the pipe before the file is written.
   - Curate by hand: drop duplicate pages of the same bag (keep the one with the most data points), vague catch-all pages ("Shoulder Bag", "Tote"), and pages whose retail is clearly wrong. Purr's retail is unreliable for Chanel and Hermès (stale or mixing exotics), so those brands stay manual except the Classic Flap.
   - Rolex Radar's retail for 126334 is wrong ($6,700); it stays out. Check retail for any new reference.
   - **Retention sanity (user's rule of thumb, confirmed 2026-09-27):** outside Hermès, Chanel and LV, bags almost never resell above retail. Goyard and The Row's Margaux are the documented exceptions. When a Purr bag comes out at ≥100%, look up the brand's current US retail and set it in `sources.json` as `retail` with `retail_src` [label, url], `retail_note` {en, zh} (which size/material) and `retail_checked`. If no single retail fits because the listings pool sizes or materials with very different prices, set `retail_ambiguous: true` instead; the page then shows "公价不确定" and leaves the item out of retention stats.
   - `scrape.py` sets `retail_unverified` automatically when Purr's median equals its own retail exactly; those items show "公价待核实" and are also left out of stats. The page marks every Purr retention ≥100% with `*` and a caveat. `tools/apply_retail_fixes.py` shows the shape of a bulk retail update.
   - Give each new item `sec` (`bag`, `wj` or `rtw`), English and Chinese names, and notes in both languages.

5. **Commit and push.** Copy this skill file to `skill/SKILL.md` if it changed, then `git add -A`, commit with a one-line message saying what changed (e.g. `Re-sourced Santos, Love`), and `git push` (`git pull --rebase` first if rejected). Pages redeploys within a minute or two.

6. **Report** in the user's language: items updated, the biggest movers (from history), anything that failed or looked wrong, and which manual items you re-sourced (with links).

## Debugging the weekly workflow

List runs: `GET /repos/ruoxiao-zhang/relay-resale/actions/workflows/refresh.yml/runs` (token from `git credential fill`; no `gh` CLI here) and read the Scrape step's log. FAIL on every item usually means a site started blocking GitHub's runner IPs or changed its markup; fetch a page locally to tell which. To run it outside the schedule, POST a `workflow_dispatch` to the same workflow.
