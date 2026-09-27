#!/usr/bin/env python3
"""Refresh the Relay resale ledger.

Reads sources.json, scrapes the automated sources (Rolex Radar, Purr), keeps the
last good value when a page fails to parse, appends every fresh reading to
data/history.jsonl and writes data.json for the page to load.

Standard library only. Run:  python scrape.py
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parent
SOURCES = ROOT / "sources.json"
DATA = ROOT / "data.json"
HISTORY = ROOT / "data" / "history.jsonl"
LOG = ROOT / "data" / "scrape.log"

UA = "Mozilla/5.0 (compatible; RelayResaleLedger/1.0; personal weekly price tracker)"
DELAY_S = 3            # pause between requests to the same site
JUMP_WARN = 0.40       # flag a reading that moves more than this vs the last one
HISTORY_KEEP = 104     # points per item shipped to the page (two years of weekly runs)

_robots = {}
_last_hit = {}


def allowed(url):
    parts = urlsplit(url)
    base = f"{parts.scheme}://{parts.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser(base + "/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None
        _robots[base] = rp
    rp = _robots[base]
    return True if rp is None else rp.can_fetch(UA, url)


def get(url):
    if not allowed(url):
        raise RuntimeError("blocked by robots.txt")
    host = urlsplit(url).netloc
    wait = DELAY_S - (time.time() - _last_hit.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    finally:
        _last_hit[host] = time.time()


def money(s):
    return int(s.replace(",", ""))


# ---- parsers: each returns {mid, lo, hi, n, retail, chg, asof}; missing fields are None ----

def parse_rolexradar(page, ref):
    def field(name):
        m = re.search(rf'data-rr-ref="{re.escape(ref)}"\s+data-rr-field="{name}"[^>]*>([^<]*)<', page)
        return html.unescape(m.group(1)).strip() if m else None

    mid = field("mid")
    if not mid or not re.search(r"\d", mid):
        raise ValueError("no mid price field")
    out = {"mid": money(re.search(r"([\d,]+)", mid).group(1)), "lo": None, "hi": None, "n": None,
           "retail": None, "chg": None, "asof": None}
    rng = field("range")
    if rng:
        nums = re.findall(r"US\$([\d,]+)", rng)
        if len(nums) == 2:
            out["lo"], out["hi"] = money(nums[0]), money(nums[1])
    c30 = field("change30d")
    if c30:
        m = re.search(r"([+\-−])\s*([\d.]+)%", c30)
        if m:
            out["chg"] = round(float(m.group(2)) / 100 * (-1 if m.group(1) != "+" else 1), 4)
    m = re.search(r"Retail MSRP[^<]*</span>\s*<span[^>]*>US\$([\d,]+)", page)
    if m:
        out["retail"] = money(m.group(1))
    m = re.search(r"weekly snapshots[^<]*?through (\d{1,2} \w{3} \d{4})", page)
    if m:
        out["asof"] = dt.datetime.strptime(m.group(1), "%d %b %Y").date().isoformat()
    return out


def parse_purr(page):
    out = {"mid": None, "lo": None, "hi": None, "n": None, "retail": None, "chg": None, "asof": None}
    m = re.search(r'bp-figure">~(?:<!-- -->)?\$([\d,]+)', page)
    if not m:
        raise ValueError("no median figure")
    out["mid"] = money(m.group(1))
    m = re.search(r"of today&#x27;s (?:<!-- -->)?\$([\d,]+)(?:<!-- -->)?\s*retail", page)
    if m:
        out["retail"] = money(m.group(1))
    m = re.search(r'<script type="application/ld\+json">(\{"@context":"https://schema.org","@type":"Product".*?)</script>', page)
    if m:
        offers = json.loads(m.group(1)).get("offers") or {}
        out["lo"], out["hi"], out["n"] = offers.get("lowPrice"), offers.get("highPrice"), offers.get("offerCount")
    return out


def scrape(item):
    if item["source"] == "rolexradar":
        return parse_rolexradar(get(f"https://rolexradar.watch/models/{item['ref']}"), item["ref"])
    if item["source"] == "purr":
        return parse_purr(get(item["url"]))
    raise ValueError(f"unknown source {item['source']}")


def sane(r):
    if not r["mid"] or r["mid"] <= 0:
        return "median missing"
    if r["lo"] is not None and r["hi"] is not None and r["lo"] > r["hi"]:
        return "low above high"
    return None


def load_history():
    rows = []
    if HISTORY.exists():
        for line in HISTORY.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main():
    today = dt.date.today().isoformat()
    cfg = json.loads(SOURCES.read_text(encoding="utf-8"))["items"]
    prev = {}
    if DATA.exists():
        prev = {i["id"]: i for i in json.loads(DATA.read_text(encoding="utf-8"))["items"]}
    history = load_history()
    seen = {(h["id"], h["d"]) for h in history}
    new_rows, report, out_items = [], [], []

    for c in cfg:
        item = {k: v for k, v in c.items() if k not in ("url", "ref", "checked")}
        if c["source"] == "manual":
            item["asof"] = c.get("checked")
            item["auto"] = False
        else:
            item["type"] = {"rolexradar": "mkt", "purr": "list"}[c["source"]]
            item["auto"] = True
            try:
                r = scrape(c)
                problem = sane(r)
                if problem:
                    raise ValueError(problem)
                old = prev.get(c["id"], {}).get("mid")
                if old and abs(r["mid"] / old - 1) > JUMP_WARN:
                    report.append(f"CHECK  {c['id']}: {old} -> {r['mid']} (moved more than {JUMP_WARN:.0%})")
                for k in ("mid", "lo", "hi", "n", "chg"):
                    item[k] = r[k]
                if c.get("retail") is None and r["retail"]:
                    item["retail"] = r["retail"]
                item["asof"] = r["asof"] or today
                item["fetched"] = today
                item["stale"] = False
                if (c["id"], item["asof"]) not in seen:
                    row = {"id": c["id"], "d": item["asof"], "mid": r["mid"], "lo": r["lo"], "hi": r["hi"]}
                    new_rows.append(row)
                    seen.add((c["id"], item["asof"]))
                report.append(f"OK     {c['id']}: ${r['mid']:,}  ({item['asof']})")
            except (urllib.error.URLError, ValueError, RuntimeError, TimeoutError) as e:
                p = prev.get(c["id"])
                if p:
                    for k in ("mid", "lo", "hi", "n", "chg", "retail", "asof", "fetched"):
                        if k in p and not (k == "retail" and c.get("retail") is not None):
                            item[k] = p[k]
                item["stale"] = True
                report.append(f"FAIL   {c['id']}: {e}  (kept last good value)" if p else f"FAIL   {c['id']}: {e}  (no previous value)")
        if item.get("ret") is None and item.get("mid") and item.get("retail"):
            item["ret"] = round(item["mid"] / item["retail"], 4)
        if item.get("ret") is None:
            report.append(f"SKIP   {c['id']}: no price yet, left off the page")
            continue
        out_items.append(item)

    if new_rows:
        HISTORY.parent.mkdir(exist_ok=True)
        with HISTORY.open("a", encoding="utf-8") as f:
            for row in new_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        history += new_rows

    by_id = {}
    for h in sorted(history, key=lambda h: h["d"]):
        by_id.setdefault(h["id"], []).append({"d": h["d"], "mid": h["mid"]})
    for item in out_items:
        item["history"] = by_id.get(item["id"], [])[-HISTORY_KEEP:]

    DATA.write_text(json.dumps({"generated": dt.datetime.now().astimezone().isoformat(timespec="minutes"),
                                "items": out_items}, ensure_ascii=False, indent=1), encoding="utf-8")

    fails = sum(1 for r in report if r.startswith("FAIL"))
    summary = f"{today}: {len(out_items)} items written, {len(new_rows)} new history rows, {fails} failed"
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(summary + "\n" + "".join("  " + r + "\n" for r in report if not r.startswith("OK")))
    print("\n".join(report))
    print(summary)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
