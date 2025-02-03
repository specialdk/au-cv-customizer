from app import app, db
from models import JobURL

def check_urls():
    with app.app_context():
        urls = JobURL.query.all()
        print(f"\nFound {len(urls)} job URLs:")
        for url in urls:
            print(f"\nID: {url.id}")
            print(f"URL: {url.url}")
            print(f"Job Title: {url.job_title}")
            print(f"Company: {url.company_name}")
            print("-" * 50)

if __name__ == "__main__":
    check_urls()
