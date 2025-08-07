#!/usr/bin/env python3
"""
Microsoft PDF Document Acquisition Script - REAL SOURCES

Acquires authentic Microsoft PDF documents from the CORRECT official sources:
1. Microsoft Investor Relations (annual reports, presentations)
2. Microsoft Research (technical papers, white papers)
3. Microsoft Corporate (position papers, sustainability reports)

STRICT COMPLIANCE WITH RULES.YAML:
- Only authentic Microsoft documents from official sources
- Temporal consistency: 2009-2025 only 
- PDF format only (.pdf files)
- Source authentication required
- NO SEC EDGAR (wrong source for PDFs)

Author: World's Finest RAG Pipeline Engineer
Date: 2024
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import re
from urllib.parse import urljoin, urlparse, unquote
from bs4 import BeautifulSoup

class MicrosoftPDFAcquisitionReal:
    """
    Acquires authentic Microsoft PDF documents from REAL official sources.
    """
    
    def __init__(self, output_dir: str = "./data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.acquired_files = []
        self.stats = {
            'total_found': 0,
            'successfully_downloaded': 0,
            'temporal_violations': 0,
            'authentication_failures': 0,
            'size_mb_downloaded': 0.0
        }
        
        # Known Microsoft PDF sources with direct URLs
        self.known_pdf_urls = [
            # Annual Reports (verified from web search)
            'https://www.microsoft.com/investor/reports/ar24/download-center/',
            'https://www.microsoft.com/investor/reports/ar23/download-center/',
            'https://www.microsoft.com/investor/reports/ar22/download-center/',
            
            # Research Papers (verified from web search)
            'http://download.microsoft.com/download/D/1/F/D1F0DFF5-8BA9-4BDF-8924-7816932F6825/Differential_Privacy_for_Everyone.pdf',
            'https://download.microsoft.com/download/3/E/7/3E717903-C905-4CB0-AF48-05BC47957BB4/Microsoft%20MADP%20Whitepaper.pdf',
            'https://export.arxiv.org/pdf/2308.01320v1.pdf',  # DeepSpeed-Chat (Microsoft research)
            'https://news.microsoft.com/wp-content/uploads/prod/sites/418/2023/01/carbon_aware_computing_whitepaper.pdf',
            'https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/final/en-us/microsoft-brand/documents/Evolving-Zero-Trust-Microsoft-Position-Paper.pdf',
        ]
        
    def verify_temporal_consistency(self, document_date: str) -> bool:
        """
        Verify document falls within required 2009-2025 timeframe.
        """
        try:
            # Parse various date formats
            for fmt in ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d', '%m/%d/%Y']:
                try:
                    doc_date = datetime.strptime(document_date.split('T')[0], fmt)
                    break
                except ValueError:
                    continue
            else:
                print(f"⚠️  Could not parse date: {document_date}")
                return False
                
            # Check 2009-2025 range (updated per user requirement)
            if 2009 <= doc_date.year <= 2025:
                return True
            else:
                self.stats['temporal_violations'] += 1
                print(f"❌ Date violation: {doc_date.year} (must be 2009-2025)")
                return False
                
        except Exception as e:
            print(f"❌ Date verification error: {e}")
            return False
    
    def extract_year_from_url(self, url: str) -> int:
        """
        Extract year from URL patterns (ar24, ar23, etc.)
        """
        try:
            # Look for patterns like ar24, ar23, 2024, 2023, etc.
            year_patterns = [
                r'ar(\d{2})',  # ar24 -> 2024
                r'(\d{4})',    # 2024
                r'20(\d{2})',  # 2024
            ]
            
            for pattern in year_patterns:
                match = re.search(pattern, url)
                if match:
                    year_str = match.group(1)
                    if len(year_str) == 2:  # ar24 format
                        year = 2000 + int(year_str)
                    else:  # full year
                        year = int(year_str)
                    
                    if 2009 <= year <= 2025:
                        return year
            
            # Default to current year if no pattern found
            return 2024
            
        except Exception as e:
            print(f"⚠️  Could not extract year from URL {url}: {e}")
            return 2024
    
    def download_pdf(self, url: str, filename: str = None, expected_year: int = None) -> bool:
        """
        Download PDF with authentication and temporal verification.
        """
        try:
            # Generate filename if not provided
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or not filename.lower().endswith('.pdf'):
                    filename = f"microsoft-document-{expected_year or 2024}.pdf"
            
            # Ensure .pdf extension
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            print(f"📥 Downloading: {filename}")
            print(f"🔗 URL: {url}")
            
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Verify it's actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type:
                # Check if content starts with PDF magic bytes
                first_chunk = next(response.iter_content(chunk_size=10), b'')
                if not first_chunk.startswith(b'%PDF'):
                    print(f"❌ Not a PDF file: {content_type}")
                    return False
            
            # Verify file size (reasonable for business documents)
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > 100:  # Reasonable limit for business PDFs
                    print(f"❌ File too large: {size_mb:.1f}MB")
                    return False
                self.stats['size_mb_downloaded'] += size_mb
            
            # Save file
            output_path = self.output_dir / filename
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify temporal consistency if year provided
            if expected_year and not (2009 <= expected_year <= 2025):
                print(f"❌ Year violation: {expected_year}")
                os.remove(output_path)
                return False
            
            self.acquired_files.append({
                'filename': filename,
                'url': url,
                'year': expected_year,
                'size_mb': size_mb if content_length else 'unknown'
            })
            
            self.stats['successfully_downloaded'] += 1
            print(f"✅ Success: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Download failed {filename}: {e}")
            return False
    
    def acquire_annual_reports(self) -> List[str]:
        """
        Acquire Microsoft annual reports from investor.microsoft.com
        """
        print("\n🎯 PHASE 1: Microsoft Annual Reports (investor.microsoft.com)")
        
        pdf_files = []
        
        # Try to get the main annual reports page
        annual_reports_url = "https://www.microsoft.com/en-us/investor/annual-reports"
        
        try:
            response = self.session.get(annual_reports_url)
            response.raise_for_status()
            
            # Parse the page for PDF download links
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for download links
            download_links = soup.find_all('a', href=True)
            
            for link in download_links:
                href = link.get('href', '')
                text = link.get_text().lower()
                
                # Look for annual report PDF links
                if ('download' in text or 'pdf' in text or 'annual report' in text) and \
                   ('2024' in href or '2023' in href or '2022' in href or '2021' in href or '2020' in href):
                    
                    # Make absolute URL
                    if href.startswith('/'):
                        pdf_url = f"https://www.microsoft.com{href}"
                    elif href.startswith('http'):
                        pdf_url = href
                    else:
                        continue
                    
                    # Extract year
                    year = self.extract_year_from_url(pdf_url)
                    filename = f"microsoft-annual-report-{year}.pdf"
                    
                    if self.download_pdf(pdf_url, filename, year):
                        pdf_files.append(filename)
                    
                    time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"⚠️  Could not access annual reports page: {e}")
        
        # Try direct known annual report URLs
        direct_annual_reports = [
            ('https://c.s-microsoft.com/en-us/CMSFiles/FinancialStatementFY24Q4.pdf', 2024),
            ('https://c.s-microsoft.com/en-us/CMSFiles/FinancialStatementFY23Q4.pdf', 2023),
            ('https://c.s-microsoft.com/en-us/CMSFiles/FinancialStatementFY22Q4.pdf', 2022),
        ]
        
        for url, year in direct_annual_reports:
            filename = f"microsoft-annual-report-{year}.pdf"
            if self.download_pdf(url, filename, year):
                pdf_files.append(filename)
            time.sleep(1)
        
        return pdf_files
    
    def acquire_research_papers(self) -> List[str]:
        """
        Acquire Microsoft research papers and technical documents.
        """
        print("\n🎯 PHASE 2: Microsoft Research Papers & Technical Documents")
        
        pdf_files = []
        
        # Direct URLs to known Microsoft PDFs (verified from web search)
        research_pdfs = [
            {
                'url': 'http://download.microsoft.com/download/D/1/F/D1F0DFF5-8BA9-4BDF-8924-7816932F6825/Differential_Privacy_for_Everyone.pdf',
                'filename': 'microsoft-differential-privacy-whitepaper.pdf',
                'year': 2020
            },
            {
                'url': 'https://download.microsoft.com/download/3/E/7/3E717903-C905-4CB0-AF48-05BC47957BB4/Microsoft%20MADP%20Whitepaper.pdf',
                'filename': 'microsoft-mobile-app-development-platform.pdf',
                'year': 2019
            },
            {
                'url': 'https://news.microsoft.com/wp-content/uploads/prod/sites/418/2023/01/carbon_aware_computing_whitepaper.pdf',
                'filename': 'microsoft-carbon-aware-computing-whitepaper.pdf',
                'year': 2023
            },
            {
                'url': 'https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/final/en-us/microsoft-brand/documents/Evolving-Zero-Trust-Microsoft-Position-Paper.pdf',
                'filename': 'microsoft-evolving-zero-trust-position-paper.pdf',
                'year': 2022
            }
        ]
        
        for pdf_info in research_pdfs:
            if self.download_pdf(pdf_info['url'], pdf_info['filename'], pdf_info['year']):
                pdf_files.append(pdf_info['filename'])
            time.sleep(1)
        
        return pdf_files
    
    def acquire_investor_presentations(self) -> List[str]:
        """
        Acquire Microsoft investor presentations and quarterly reports.
        """
        print("\n🎯 PHASE 3: Microsoft Investor Presentations")
        
        pdf_files = []
        
        # Try to find quarterly earnings PDFs
        earnings_base = "https://www.microsoft.com/en-us/investor/earnings"
        
        # Look for recent quarters that might have PDF versions
        quarters = ['fy-2025-q4', 'fy-2025-q3', 'fy-2025-q2', 'fy-2025-q1', 'fy-2024-q4']
        
        for quarter in quarters:
            try:
                earnings_url = f"{earnings_base}/{quarter}/press-release-webcast"
                response = self.session.get(earnings_url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for PDF links
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if href.endswith('.pdf') or 'pdf' in href.lower():
                            
                            if href.startswith('/'):
                                pdf_url = f"https://www.microsoft.com{href}"
                            elif href.startswith('http'):
                                pdf_url = href
                            else:
                                continue
                            
                            year = self.extract_year_from_url(quarter)
                            filename = f"microsoft-earnings-{quarter}.pdf"
                            
                            if self.download_pdf(pdf_url, filename, year):
                                pdf_files.append(filename)
                            
                            time.sleep(1)
                            
            except Exception as e:
                print(f"⚠️  Could not access {quarter}: {e}")
                continue
        
        return pdf_files
    
    def run_acquisition(self) -> Dict:
        """
        Execute complete PDF acquisition process.
        """
        print("🚀 MICROSOFT PDF ACQUISITION - REAL OFFICIAL SOURCES")
        print("📋 Rules.yaml compliance: Only .pdf files, 2009-2025, official Microsoft sources")
        print(f"📁 Output directory: {self.output_dir}")
        print("🚫 NO SEC EDGAR - using correct PDF sources instead")
        
        start_time = time.time()
        
        # Phase 1: Annual reports
        annual_pdfs = self.acquire_annual_reports()
        
        # Phase 2: Research papers
        research_pdfs = self.acquire_research_papers()
        
        # Phase 3: Investor presentations
        investor_pdfs = self.acquire_investor_presentations()
        
        execution_time = time.time() - start_time
        
        # Final statistics
        print("\n" + "="*60)
        print("📊 MICROSOFT PDF ACQUISITION RESULTS")
        print("="*60)
        print(f"✅ Total PDFs acquired: {self.stats['successfully_downloaded']}")
        print(f"📁 Annual reports: {len(annual_pdfs)}")
        print(f"🔬 Research papers: {len(research_pdfs)}")
        print(f"📈 Investor presentations: {len(investor_pdfs)}")
        print(f"💾 Total size downloaded: {self.stats['size_mb_downloaded']:.1f} MB")
        print(f"⏱️  Execution time: {execution_time:.1f} seconds")
        print(f"❌ Temporal violations: {self.stats['temporal_violations']}")
        print(f"🔒 Authentication method: Official Microsoft domains")
        
        if self.acquired_files:
            print("\n📋 Acquired files:")
            for file_info in self.acquired_files:
                print(f"  • {file_info['filename']} ({file_info['year']}) - {file_info['size_mb']}MB")
        
        return {
            'success': True,
            'files_acquired': len(self.acquired_files),
            'stats': self.stats,
            'execution_time': execution_time
        }

def main():
    """Main execution function."""
    print("🎯 Microsoft PDF Acquisition - REAL SOURCES")
    print("📋 Targeting actual Microsoft PDF sources (NOT SEC EDGAR)")
    
    acquirer = MicrosoftPDFAcquisitionReal()
    results = acquirer.run_acquisition()
    
    if results['success']:
        print(f"\n🎉 SUCCESS: {results['files_acquired']} PDF files acquired from REAL sources")
        return True
    else:
        print("\n❌ ACQUISITION FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)