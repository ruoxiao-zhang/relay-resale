"""Probe Purr model pages and list which ones have a usable median + retail.

Usage: python tools/probe_purr.py brand1 brand2 ...   (brand slugs as in the Purr sitemap)
Writes tools/purr_probe.json.
"""
import json, pathlib, re, sys, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scrape  # reuse get() (robots + delay) and parse_purr()

brands = set(sys.argv[1:])
sm = scrape.get("https://bypurr.com/sitemap.xml")
slugs = [m for m in re.findall(r"<loc>https://bypurr.com/bags/([^/<]+/[^/<]+)</loc>", sm) if m.split("/")[0] in brands]
out = []
for s in slugs:
    url = f"https://www.bypurr.com/bags/{s}"
    try:
        page = scrape.get(url)
        r = scrape.parse_purr(page)
        t = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
        r["title"] = re.sub(r"<!-- -->|<[^>]+>", "", t.group(1)).strip() if t else s
    except Exception as e:
        r = {"error": str(e)}
    r["slug"] = s
    out.append(r)
    print(s, r.get("mid"), r.get("retail"), r.get("n"), r.get("error", ""), flush=True)
pathlib.Path(__file__).with_name("purr_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
