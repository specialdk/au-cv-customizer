import requests
from bs4 import BeautifulSoup
import re

def scrape_job_details(url):
    """
    Scrape job details from a given URL.
    Returns a tuple of (job_title, company_name)
    """
    try:
        # Send a GET request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find job title - look for common patterns
        job_title = None
        title_candidates = [
            soup.find('h1', class_=re.compile(r'job.*title|position.*title', re.I)),
            soup.find('h1', class_=re.compile(r'title', re.I)),
            soup.find('title'),
        ]
        for candidate in title_candidates:
            if candidate and candidate.text.strip():
                job_title = candidate.text.strip()
                break
        
        # Try to find company name - look for common patterns
        company = None
        company_candidates = [
            soup.find(class_=re.compile(r'company.*name|organization', re.I)),
            soup.find('meta', property='og:site_name'),
            soup.find(class_=re.compile(r'employer|company', re.I))
        ]
        for candidate in company_candidates:
            if candidate:
                if isinstance(candidate, type(soup.find('meta'))):
                    company = candidate.get('content', '').strip()
                else:
                    company = candidate.text.strip()
                if company:
                    break
        
        return job_title, company
        
    except Exception as e:
        print(f"Error scraping job details: {str(e)}")
        return None, None
