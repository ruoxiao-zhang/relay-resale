"""Turn tools/purr_probe.json into sources.json entries.

Keeps pages with a median, a retail price, at least MIN_N data points and a plausible
retention, skips slugs already in sources.json, and appends the rest as `purr` items.
Usage: python tools/add_purr.py [--dry-run] [--only slug1,slug2,...]
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MIN_N = 25
RET_RANGE = (0.12, 3.0)

BRANDS = {
    "herm-s": ("Hermès", "爱马仕"), "chanel": ("Chanel", "香奈儿"), "louis-vuitton": ("Louis Vuitton", "路易威登"),
    "dior": ("Dior", "迪奥"), "celine": ("Celine", "思琳"), "loewe": ("Loewe", "罗意威"), "prada": ("Prada", "普拉达"),
    "fendi": ("Fendi", "芬迪"), "saint-laurent": ("Saint Laurent", "圣罗兰"), "bottega-veneta": ("Bottega Veneta", "葆蝶家"),
    "the-row": ("The Row", "The Row"), "goyard": ("Goyard", "戈雅"), "gucci": ("Gucci", "古驰"),
    "miu-miu": ("Miu Miu", "缪缪"), "balenciaga": ("Balenciaga", "巴黎世家"),
}
NOTE = {"en": "Aggregate of resale listings across Rebag, The RealReal, Vestiaire Collective and eBay, all sizes and materials combined. Retail is the source’s figure and can lag recent price rises, which flatters retention.",
        "zh": "汇总自 Rebag、The RealReal、Vestiaire Collective 和 eBay 的二手挂牌，合并全部尺寸和材质。公价取自来源，可能没跟上最近的涨价，保值率会因此偏高。"}
only = None
if "--only" in sys.argv:
    only = set(sys.argv[sys.argv.index("--only") + 1].split(","))

probe = json.loads((ROOT / "tools" / "purr_probe.json").read_text(encoding="utf-8"))
src = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
have = {i.get("url", "").rstrip("/").split("/bags/")[-1] for i in src["items"] if i.get("source") == "purr"}
ids = {i["id"] for i in src["items"]}

added, skipped = [], []
for p in probe:
    s = p["slug"]
    if s in have or s.split("/")[0] not in BRANDS or (only is not None and s not in only):
        continue
    mid, retail, n = p.get("mid"), p.get("retail"), p.get("n") or 0
    if not (mid and retail) or n < MIN_N or not (RET_RANGE[0] <= mid / retail <= RET_RANGE[1]):
        skipped.append(f"{s}: mid={mid} retail={retail} n={n}")
        continue
    brand, zhb = BRANDS[s.split("/")[0]]
    model = p.get("title", s).replace(brand, "").strip() or s.split("/")[1]
    iid = s.replace("/", "-")
    if iid in ids:
        continue
    added.append({"id": iid, "sec": "bag", "brand": brand, "zhb": zhb, "name": model, "zh": model,
                  "source": "purr", "url": f"https://www.bypurr.com/bags/{s}",
                  "src": [f"Purr · {brand} {model}", f"https://www.bypurr.com/bags/{s}"], "note": NOTE})

print(f"add {len(added)}, skip {len(skipped)}")
for a in added:
    print("  +", a["id"])
for s in skipped:
    print("  -", s)
if "--dry-run" not in sys.argv:
    # keep bags together: insert after the last existing bag
    last_bag = max(k for k, i in enumerate(src["items"]) if i["sec"] == "bag")
    src["items"][last_bag + 1:last_bag + 1] = added
    (ROOT / "sources.json").write_text(json.dumps(src, ensure_ascii=False, indent=1), encoding="utf-8")
