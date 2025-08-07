import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
download_dir = Path('/Users/spensercourville-taylor/htmlfiles/RAGtest/msft_data')
download_dir.mkdir(exist_ok=True)

years = range(2016, 2026)
quarters = [1, 2, 3, 4]

for year in years:
  for quarter in quarters:
    url = f'https://www.microsoft.com/en-us/investor/earnings/FY-{year}-Q{quarter}/press-release-webcast'
    print(f'Processing {year} Q{quarter}: {url}')
    try:
      response = requests.get(url, headers=headers, timeout=30)
      if response.status_code != 200:
        print(f'Page load failed: {response.status_code}')
        continue
      soup = BeautifulSoup(response.content, 'html.parser')
      asset_link = soup.find('moray-anchor', {'aria-label': 'ASSET PACKAGE'})
      if not asset_link:
        print('Asset link not found')
        continue
      asset_url = asset_link.get('href')
      if not asset_url:
        print('No href in asset link')
        continue
      print(f'Downloading from {asset_url}')
      zip_response = requests.get(asset_url, headers=headers, stream=True)
      zip_path = download_dir / f'FY{year}Q{quarter}-earnings.zip'
      with open(zip_path, 'wb') as f:
        for chunk in zip_response.iter_content(chunk_size=8192):
          f.write(chunk)
      print(f'Downloaded to {zip_path}')
      time.sleep(2)
    except Exception as e:
      print(f'Error: {str(e)}') 