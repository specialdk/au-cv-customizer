import os
from dotenv import load_dotenv
from cv_parser import analyze_cv_pro

# Load environment variables
load_dotenv()

def main():
    # Path to your CV document
    cv_path = 'path/to/your/cv.docx'
    
    # Optional: Job description for targeted analysis
    job_description = """
    Senior Software Engineer
    We are looking for an experienced Python developer with strong 
    machine learning and AI background. Proficiency in data analysis, 
    scikit-learn, and OpenAI integration is required.
    """
    
    # Get OpenAI API key from environment
    openai_key = os.getenv('OPENAI_API_KEY')
    
    # Perform Pro CV Analysis
    try:
        analysis_result = analyze_cv_pro(
            cv_path, 
            job_description, 
            openai_key
        )
        
        # Pretty print analysis results
        import json
        print(json.dumps(analysis_result, indent=2))
    
    except Exception as e:
        print(f"CV Analysis Error: {e}")

if __name__ == '__main__':
    main()
