"""One-off: write the retail prices checked on 2026-09-27 into sources.json.

`retail` overrides the scraped retail; `retail_ambiguous` hides retention when no single
retail fits a pooled listing; `retail_src` / `retail_note` explain where the number came from.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
P = ROOT / "sources.json"
CHECKED = "2026-09-27"

FIXES = {
    "bottega-veneta-hop": dict(retail=4600, retail_src=["FWRD · Bottega Veneta Hop", "https://www.fwrd.com/brand-bottega-veneta-bags-hobos/2cb362/"],
        retail_note={"en": "Retail is the medium Hop at $4,600; the small is $5,000.", "zh": "公价取中号 Hop 4600 美元；小号 5000 美元。"}),
    "celine-cabas-thais": dict(retail=1800, retail_src=["ASC Resale · Small Cabas Thais retail", "https://asecondchanceresale.com/products/celine-striped-canvas-small-cabas-thais-bag"],
        retail_note={"en": "Retail is the small Cabas Thais at $1,800; some versions list at $2,000.", "zh": "公价取小号 1800 美元；部分款式为 2000 美元。"}),
    "prada-explore": dict(retail=3750, retail_src=["Prada Explore price guide", "https://collectorscage.com/blogs/guides/prada-bag-prices-2026-full-price-guide-us-europe-and-why-pre-owned-win"],
        retail_note={"en": "Retail is the medium in nappa leather ($3,750). The Re-Nylon version is $2,550, so listings that mix both skew the figure.", "zh": "公价取小羊皮中号 3750 美元。尼龙款为 2550 美元，挂牌混合两种材质会有偏差。"}),
    "saint-laurent-loulou": dict(retail=2850, retail_src=["Loulou review 2026", "https://www.lifewithmar.com/fashion/saint-laurent-loulou-review"],
        retail_note={"en": "Retail is the medium at $2,850; the updated version lists at $3,200.", "zh": "公价取中号 2850 美元；新版为 3200 美元。"}),
    "gucci-sukey": dict(retail=990, retail_src=["Sukey (discontinued)", "https://www.collectorsquare.com/en/bags/gucci/sukey/"],
        retail_note={"en": "Discontinued. Retail is the last medium price, $990.", "zh": "已停产，公价为停产前中号售价 990 美元。"}),
    "the-row-marlo": dict(retail=4900, retail_src=["The Row · Marlo 12", "https://www.therow.com/products/marlo-12-black-ans"],
        retail_note={"en": "Retail is the Marlo 12 at $4,900; the 17 is about $5,800. Listings pool all sizes.", "zh": "公价取 Marlo 12 的 4900 美元；17 号约 5800 美元。挂牌合并了各尺寸。"}),
    "goyard-bellechasse": dict(retail=2275, retail_src=["Goyard price list 2026", "https://collectorscage.com/blogs/guides/goyard-bag-prices-2026-full-price-guide-us-europe-and-why-pre-owned-wi"],
        retail_note={"en": "Goyard publishes no prices; $2,275 is the reported PM boutique price. Goyard is one of the few brands that routinely resells above retail (Rebag’s 2025 Clair Report: 132% average).", "zh": "Goyard 不公开价格，2275 美元为报道的 PM 门店价。Goyard 是少数常年二手高于公价的品牌（Rebag 2025 报告平均 132%）。"}),
    "margaux": dict(retail=4700, retail_src=["The Row bag prices 2026", "https://streetstylis.com/the-row-bag-prices/"],
        retail_note={"en": "Retail is the Margaux 15 in leather ($4,700). The Margaux left third-party stores in 2025 and now sells only in The Row’s boutiques, which keeps resale high.", "zh": "公价取皮革 Margaux 15 的 4700 美元。Margaux 2025 年起只在 The Row 自营门店销售，二手价因此偏高。"}),
    "the-row-margaux-10": dict(retail=3650, retail_src=["The Row bag prices 2026", "https://streetstylis.com/the-row-bag-prices/"],
        retail_note={"en": "Retail is $3,650. The Margaux now sells only in The Row’s own boutiques and resells well above retail.", "zh": "公价 3650 美元。Margaux 现在只在 The Row 自营门店销售，二手价明显高于公价。"}),
    "louis-vuitton-pochette-hills": dict(retail_ambiguous=True, retail_src=["Louis Vuitton · Pochette Hills", "https://us.louisvuitton.com/eng-us/products/pochette-hills-monogram-nvprod7280238v/M27509"],
        retail_note={"en": "Retail runs from $1,860 (denim) and $1,900 (monogram) to $2,990 (leather), and the listings mix all of them, so no single retention figure is meaningful.", "zh": "公价从 1860 美元（牛仔）、1900 美元（老花）到 2990 美元（皮革）不等，挂牌混合了各版本，无法给出有意义的保值率。"}),
    "celine-triomphe-besace": dict(retail_ambiguous=True, retail_src=["Celine · Mini Besace Triomphe", "https://www.celine.com/en-us/celine-shop-women/mini-bags/triomphe-canvas/mini-besace-in-triomphe-canvas-and-calfskin-196702BZJ.04LU.html"],
        retail_note={"en": "The mini is $1,300–1,350 and larger sizes cost more; the listings pool all sizes, so no single retention figure is meaningful.", "zh": "迷你款 1300–1350 美元，大尺寸更贵；挂牌合并了各尺寸，无法给出有意义的保值率。"}),
}

src = json.loads(P.read_text(encoding="utf-8"))
done = set()
for it in src["items"]:
    f = FIXES.get(it["id"])
    if f:
        it.update(f)
        it["retail_checked"] = CHECKED
        done.add(it["id"])
missing = set(FIXES) - done
P.write_text(json.dumps(src, ensure_ascii=False, indent=1), encoding="utf-8")
print("updated", len(done), "missing", sorted(missing))
