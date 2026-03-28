#!/usr/bin/env python3
"""
Test script using Lens API official documentation - searching by IDs field
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
LENS_API_KEY = os.getenv('LENS_API_KEY')

if not LENS_API_KEY:
    print("❌ LENS_API_KEY not found in .env file!")
    exit(1)

print(f"✅ Using Lens API Key: {LENS_API_KEY[:20]}...")

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {LENS_API_KEY}'
}

# According to docs, the "ids" field supports:
# "EP_0227762_B1_19900411", "EP 0227762 B1", "EP_0227762_B1", "EP0227762B1", "EP0227762"
# "US 7,654,321 B2", "7,654,321", "US 2021/0191781 A1"
# "145-564-229-856-440" (Lens ID)

test_ids = [
    "FR20210002119",
    "FR 20210002119",
    "FR_20210002119",
    "EP4301213",
    "EP 4301213",
    "EP_4301213",
    "CN121190407",
    "CN 121190407",
    "CN_121190407",
    "CA3241308",
    "CA 3241308",
    "CA_3241308",
]

print("\n" + "="*80)
print("Testing patent searches using 'ids' field (official Lens API method)")
print("="*80)

for patent_id in test_ids:
    print(f"\n🔍 Searching for ID: {patent_id}")
    print("-" * 80)
    
    # Use the official "ids" field approach
    search_request = {
        "query": {
            "match": {
                "ids": patent_id
            }
        },
        "size": 1,
        "from": 0,
        "_source": {
            "includes": ["lens_id", "country", "doc_number", "kind", "biblio.invention_title"]
        }
    }
    
    try:
        response = requests.post(
            'https://api.lens.org/patent/search',
            json=search_request,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            patents = data.get('data', [])
            total = data.get('total', 0)
            
            if patents:
                print(f"✅ FOUND {len(patents)} result(s) out of {total} total")
                for idx, patent in enumerate(patents, 1):
                    lens_id = patent.get('lens_id', 'N/A')
                    country_code = patent.get('country', 'N/A')
                    doc_num = patent.get('doc_number', 'N/A')
                    kind = patent.get('kind', 'N/A')
                    title = patent.get('biblio', {}).get('invention_title', [{}])[0].get('text', 'N/A') if isinstance(patent.get('biblio', {}).get('invention_title'), list) else 'N/A'
                    
                    print(f"   Lens ID: {lens_id}")
                    print(f"   Full ID: {country_code}{doc_num}{kind}")
                    print(f"   Title: {title[:60]}...")
            else:
                print(f"❌ No results")
        else:
            print(f"❌ API Error {response.status_code}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")

print("\n" + "="*80)