import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging
from typing import Dict, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobScraper:
    """Scraper for extracting job descriptions from various job posting sites."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Common job description section identifiers
        self.job_section_keywords = {
            'requirements': ['requirements', 'qualifications', 'what you need', 'what we\'re looking for'],
            'responsibilities': ['responsibilities', 'duties', 'what you\'ll do', 'role description', 'about the role'],
            'benefits': ['benefits', 'perks', 'what we offer', 'why join us'],
            'about': ['about us', 'about the company', 'who we are']
        }

    def scrape_job_posting(self, url: str) -> Dict[str, any]:
        """
        Scrape job posting content from the given URL.
        
        Args:
            url: URL of the job posting
            
        Returns:
            Dictionary containing structured job posting data
        """
        try:
            logger.info(f"Starting to scrape job posting: {url}")
            
            # Determine the appropriate scraper based on the domain
            domain = urlparse(url).netloc.lower()
            
            # Get the page content
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Parse based on the domain
            if 'seek.com.au' in domain:
                return self._parse_seek(soup)
            elif 'linkedin.com' in domain:
                return self._parse_linkedin(soup)
            elif 'indeed.com' in domain:
                return self._parse_indeed(soup)
            else:
                return self._parse_generic(soup)
                
        except Exception as e:
            logger.error(f"Error scraping job posting: {str(e)}")
            raise

    def _parse_seek(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Parse Seek job postings."""
        data = {
            'title': self._extract_text(soup, ['[data-automation="job-detail-title"]', 'h1.jobtitle', '.job-title']),
            'company': self._extract_text(soup, ['[data-automation="advertiser-name"]', '.company-name', '.employer-name']),
            'location': self._extract_text(soup, ['[data-automation="job-detail-location"]', '.location']),
            'description': self._extract_text(soup, ['[data-automation="jobAdDetails"]', '.job-details', '#jobDescription']),
            'sections': {}
        }
        
        # Extract structured sections
        description_div = soup.find('div', {'data-automation': 'jobAdDetails'}) or \
                         soup.find('div', {'class': 'job-details'}) or \
                         soup.find('div', {'id': 'jobDescription'})
        
        if description_div:
            data['sections'] = self._extract_sections(description_div.get_text())
            
        return data

    def _parse_linkedin(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Parse LinkedIn job postings."""
        data = {
            'title': self._extract_text(soup, ['h1.job-title', '.job-details-jobs-unified-top-card__job-title']),
            'company': self._extract_text(soup, ['.company-name', '.employer-name', '.job-details-jobs-unified-top-card__company-name']),
            'location': self._extract_text(soup, ['.job-location', '.location', '.job-details-jobs-unified-top-card__bullet']),
            'description': self._extract_text(soup, ['#job-details', '.description__text', '.job-details-jobs-unified-top-card__description-container']),
            'sections': {}
        }
        
        # Extract structured sections
        description_div = soup.find('div', {'class': 'description__text'}) or \
                         soup.find('div', {'id': 'job-details'})
        if description_div:
            data['sections'] = self._extract_sections(description_div.get_text())
            
        return data

    def _parse_indeed(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Parse Indeed job postings."""
        data = {
            'title': self._extract_text(soup, ['h1.jobsearch-JobInfoHeader-title']),
            'company': self._extract_text(soup, ['.jobsearch-InlineCompanyRating-companyHeader', '.company-name']),
            'location': self._extract_text(soup, ['.jobsearch-JobInfoHeader-subtitle', '.location']),
            'description': self._extract_text(soup, ['#jobDescriptionText', '.job-description']),
            'sections': {}
        }
        
        # Extract structured sections
        description_div = soup.find('div', {'id': 'jobDescriptionText'}) or \
                         soup.find('div', {'class': 'job-description'})
        if description_div:
            data['sections'] = self._extract_sections(description_div.get_text())
            
        return data

    def _parse_generic(self, soup: BeautifulSoup) -> Dict[str, any]:
        """Parse job postings from unknown sources using common patterns."""
        data = {
            'title': self._extract_text(soup, ['h1', '.job-title', '.position-title']),
            'company': self._extract_text(soup, ['.company', '.organization', '.employer']),
            'location': self._extract_text(soup, ['.location', '.job-location', '.workplace']),
            'description': self._extract_text(soup, ['.description', '.job-description', '#job-details']),
            'sections': {}
        }
        
        # Try to find the main job description container
        description_div = soup.find(['div', 'section'], {'class': ['description', 'job-description']}) or \
                         soup.find('div', {'id': 'job-details'})
        if description_div:
            data['sections'] = self._extract_sections(description_div.get_text())
            
        return data

    def _extract_text(self, soup: BeautifulSoup, selectors: list) -> Optional[str]:
        """Extract text content using a list of possible selectors."""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
            except Exception as e:
                logger.warning(f"Error extracting text with selector {selector}: {str(e)}")
        return None

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract common sections from job description text."""
        sections = {}
        current_section = 'description'
        current_content = []
        
        # First split by common section markers
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                # Split by bullet points and numbering
                if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                    lines.extend([l.strip() for l in line[1:].split('\n') if l.strip()])
                else:
                    lines.append(line)
        
        for line in lines:
            # Check if this line is a section header
            section_type = self._identify_section(line)
            
            if section_type:
                # Save the previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                # Start new section
                current_section = section_type
                current_content = []
            else:
                current_content.append(line)
        
        # Save the last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
            
        # If no sections were found, put everything in description
        if len(sections) <= 1:
            sections = {'description': text}
            
        return sections

    def _identify_section(self, text: str) -> Optional[str]:
        """Identify if a text is a section header."""
        text = text.lower()
        
        # Skip if text is too long to be a header
        if len(text) > 50:
            return None
            
        # Check each section type
        for section_type, keywords in self.job_section_keywords.items():
            if any(keyword in text for keyword in keywords):
                return section_type
                
        return None
