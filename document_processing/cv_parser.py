from docx import Document
import logging
from typing import Dict, List, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CVSection:
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content
        self.subsections: List[CVSection] = []

class CVParser:
    """Parser for extracting structured content from CV documents."""
    
    # Common section titles in CVs
    SECTION_TITLES = {
        'education': ['education', 'academic background', 'qualifications'],
        'experience': ['experience', 'work experience', 'employment history', 'professional experience'],
        'skills': ['skills', 'technical skills', 'core competencies', 'key skills'],
        'summary': ['summary', 'professional summary', 'profile', 'objective'],
        'contact': ['contact', 'contact information', 'personal details'],
        'projects': ['projects', 'key projects', 'professional projects'],
        'certifications': ['certifications', 'certificates', 'professional certifications'],
        'languages': ['languages', 'language skills'],
        'interests': ['interests', 'hobbies', 'activities']
    }

    def __init__(self):
        self.sections: Dict[str, CVSection] = {}
        self.metadata: Dict[str, str] = {}

    def parse_docx(self, file_path: str) -> Dict[str, any]:
        """
        Parse a DOCX file and extract structured content.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Dictionary containing parsed CV data
        """
        try:
            logger.info(f"Starting to parse CV: {file_path}")
            doc = Document(file_path)
            
            current_section = None
            section_content = []
            
            # Extract text while preserving some formatting
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue
                
                # Check if this paragraph is a section title
                section_type = self._identify_section(text)
                
                if section_type:
                    logger.info(f"Found section: {section_type} (Title: {text})")
                    # Save previous section if it exists
                    if current_section and section_content:
                        logger.info(f"Saving section {current_section} with {len(section_content)} paragraphs")
                        self.sections[current_section] = CVSection(
                            current_section,
                            '\n'.join(section_content)
                        )
                    
                    # Start new section
                    current_section = section_type
                    section_content = []
                else:
                    # Add to current section content
                    formatted_text = self._extract_formatted_text(paragraph)
                    if current_section:
                        logger.debug(f"Adding content to section {current_section}: {formatted_text[:50]}...")
                    section_content.append(formatted_text)
            
            # Save the last section
            if current_section and section_content:
                logger.info(f"Saving final section {current_section} with {len(section_content)} paragraphs")
                self.sections[current_section] = CVSection(
                    current_section,
                    '\n'.join(section_content)
                )
            
            # Extract metadata
            self._extract_metadata()
            
            logger.info(f"CV parsing completed. Found {len(self.sections)} sections and {len(self.metadata)} metadata items")
            return self._prepare_output()
            
        except Exception as e:
            logger.error(f"Error parsing CV: {str(e)}")
            raise

    def _identify_section(self, text: str) -> Optional[str]:
        """Identify if a text is a section title."""
        # Clean the text
        text = text.strip().lower()
        
        # Skip if text is too long to be a title
        if len(text) > 50:
            return None
            
        # Skip if text contains too many words
        if len(text.split()) > 5:
            return None
        
        # Check for exact matches first
        for section_type, possible_titles in self.SECTION_TITLES.items():
            if text in possible_titles:
                return section_type
        
        # Then check for partial matches
        for section_type, possible_titles in self.SECTION_TITLES.items():
            if any(title in text for title in possible_titles):
                return section_type
                
        # Special cases
        if any(word in text for word in ['work', 'job', 'position', 'role']):
            return 'experience'
        if any(word in text for word in ['degree', 'university', 'college', 'school']):
            return 'education'
        if any(word in text for word in ['certification', 'certificate', 'qualification']):
            return 'certifications'
            
        return None

    def _extract_formatted_text(self, paragraph) -> str:
        """Extract text while preserving basic formatting."""
        formatted_parts = []
        for run in paragraph.runs:
            text = run.text.strip()
            if not text:
                continue
            
            # Preserve bold and italic formatting
            if run.bold and run.italic:
                formatted_parts.append(f"***{text}***")
            elif run.bold:
                formatted_parts.append(f"**{text}**")
            elif run.italic:
                formatted_parts.append(f"*{text}*")
            else:
                formatted_parts.append(text)
        
        return ' '.join(formatted_parts)

    def _extract_metadata(self):
        """Extract metadata from the CV content."""
        # Try to extract email
        if 'contact' in self.sections:
            content = self.sections['contact'].content
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', content)
            if email_match:
                self.metadata['email'] = email_match.group(0)
            
            # Try to extract phone number
            phone_match = re.search(r'[\+\d]?(\d{2,3}[-\.\s]??\d{2,3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})', content)
            if phone_match:
                self.metadata['phone'] = phone_match.group(0)

    def _prepare_output(self) -> Dict[str, any]:
        """Prepare the final output dictionary."""
        return {
            'metadata': self.metadata,
            'sections': {
                name: {
                    'title': section.title,
                    'content': section.content
                }
                for name, section in self.sections.items()
            }
        }

# Example usage:
# parser = CVParser()
# cv_data = parser.parse_docx('path/to/cv.docx')
