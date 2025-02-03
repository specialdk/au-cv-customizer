import os
import json
from cv_parser import CVParser

def test_cv_parser():
    # Get the absolute path to the test CV
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cv_path = os.path.join(base_dir, 'uploads', '1', 'Duane_Kuru_CV.docx')
    output_path = os.path.join(base_dir, 'document_processing', 'parser_output.txt')
    
    print(f"\nTesting CV parser with file: {cv_path}")
    print(f"Output will be written to: {output_path}")
    
    try:
        # Initialize parser
        parser = CVParser()
        
        # Parse the CV
        cv_data = parser.parse_docx(cv_path)
        
        # Write output to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"CV Parser Test Results\n")
            f.write("=" * 20 + "\n\n")
            
            # Write metadata
            f.write("METADATA\n")
            f.write("-" * 8 + "\n")
            if cv_data['metadata']:
                for key, value in cv_data['metadata'].items():
                    f.write(f"{key.title()}: {value}\n")
            else:
                f.write("No metadata found\n")
            
            # Write sections
            f.write("\nSECTIONS\n")
            f.write("-" * 8 + "\n")
            if cv_data['sections']:
                for section_name, section_data in cv_data['sections'].items():
                    f.write(f"\n{section_data['title'].upper()}\n")
                    f.write("=" * len(section_data['title']) + "\n")
                    f.write(section_data['content'].strip() + "\n")
                    f.write("-" * 80 + "\n")
            else:
                f.write("No sections found\n")
        
        print(f"\nParser test completed successfully. Check {output_path} for results.")
        return True
        
    except Exception as e:
        print(f"\nError testing CV parser: {str(e)}")
        return False

if __name__ == "__main__":
    test_cv_parser()
