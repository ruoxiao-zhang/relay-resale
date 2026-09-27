"""Print what Rolex Radar reports for the given references. Usage: python tools/probe_rr.py 124300 326934"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scrape

for ref in sys.argv[1:]:
    try:
        print(ref, scrape.parse_rolexradar(scrape.get(f"https://rolexradar.watch/models/{ref}"), ref))
    except Exception as e:
        print(ref, "ERROR", e)
