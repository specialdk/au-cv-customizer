import os
import json
from job_scraper import JobScraper

def test_job_scraper():
    # Test with a real job posting URL from our database
    test_url = "https://www.seek.com.au/job/81587432/apply?sol=85faf37ebb620733fe426b1bbbc779a3231d9ad18"  # Customer Service Officer at Trinity Fire
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scraper_output.txt')
    print(f"\nTesting job scraper...")
    print(f"Testing URL: {test_url}")
    print(f"Output will be written to: {output_path}")
    
    try:
        # Initialize scraper
        scraper = JobScraper()
        
        # Test the URL
        try:
            print(f"\nScraping: {test_url}")
            job_data = scraper.scrape_job_posting(test_url)
            
            # Write output to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("Job Scraper Test Results\n")
                f.write("=" * 22 + "\n\n")
                
                f.write(f"URL: {test_url}\n")
                f.write("-" * (len(test_url) + 5) + "\n")
                
                if job_data:
                    f.write(f"Title: {job_data['title']}\n")
                    f.write(f"Company: {job_data['company']}\n")
                    f.write(f"Location: {job_data['location']}\n")
                    f.write("\nSections:\n")
                    for section, content in job_data['sections'].items():
                        f.write(f"\n{section.upper()}\n")
                        f.write("=" * len(section) + "\n")
                        f.write(content + "\n")
                else:
                    f.write("No data extracted from job posting\n")
                
                f.write("\n" + "=" * 80 + "\n\n")
            
            print(f"\nScraper test completed. Check {output_path} for results.")
            return True
            
        except Exception as e:
            print(f"Error scraping {test_url}: {str(e)}")
            return False
        
    except Exception as e:
        print(f"\nError testing job scraper: {str(e)}")
        return False

if __name__ == "__main__":
    test_job_scraper()
