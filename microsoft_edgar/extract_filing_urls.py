#!/usr/bin/env python3
import re
import os
from pathlib import Path

def extract_urls_from_html(html_file, filing_type):
    """Extract direct filing URLs from SEC EDGAR search HTML"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # SEC EDGAR URL pattern for direct document access
    # Pattern: /Archives/edgar/data/789019/XXXXXXXXXXXXXXXXXX/filename.htm
    url_pattern = r'/Archives/edgar/data/789019/[0-9]+/[^"]+\.htm'
    urls = re.findall(url_pattern, content)
    
    # Convert to full URLs
    full_urls = [f"https://www.sec.gov{url}" for url in urls]
    
    return full_urls

# Process all search HTML files
filing_types = ['10k', '10q', '8k', 'def14a']
all_urls = {}

for filing_type in filing_types:
    all_urls[filing_type] = []
    
    # Find all HTML files for this filing type
    pattern = f"raw_html/msft_{filing_type}_search_*.html"
    html_files = [f for f in os.listdir('raw_html') if f.startswith(f'msft_{filing_type}_search_')]
    
    for html_file in html_files:
        urls = extract_urls_from_html(f'raw_html/{html_file}', filing_type)
        all_urls[filing_type].extend(urls)
        print(f"📄 {html_file}: {len(urls)} URLs extracted")

# Write URL lists to files for bulk download
for filing_type, urls in all_urls.items():
    with open(f'{filing_type}_urls.txt', 'w') as f:
        for url in urls:
            f.write(f"{url}\n")
    print(f"✅ {filing_type.upper()}: {len(urls)} filing URLs ready for download")

print(f"\n📊 TOTAL SEC FILINGS IDENTIFIED: {sum(len(urls) for urls in all_urls.values())}")
