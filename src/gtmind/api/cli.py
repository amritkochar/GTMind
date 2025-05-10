import sys
from pprint import pprint

from gtmind.core.search import search_sync

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "AI in retail"
    results = search_sync(query)
    pprint([r.model_dump() for r in results])
