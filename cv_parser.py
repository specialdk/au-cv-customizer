import docx
import re
import spacy
from typing import Dict, List, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai

class CVParser:
    def __init__(self):
        # Load spaCy model for NER and text analysis
        self.nlp = spacy.load("en_core_web_sm")

    def parse_docx(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a .docx CV file and extract key information
        """
        doc = docx.Document(file_path)
        full_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        # Use spaCy for named entity recognition
        parsed_doc = self.nlp(full_text)
        
        return {
            "raw_text": full_text,
            "entities": {
                "persons": [ent.text for ent in parsed_doc.ents if ent.label_ == "PERSON"],
                "organizations": [ent.text for ent in parsed_doc.ents if ent.label_ == "ORG"],
                "locations": [ent.text for ent in parsed_doc.ents if ent.label_ == "GPE"]
            },
            "sections": self._extract_sections(full_text)
        }

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract key sections from CV text
        """
        sections = {
            "contact_info": self._extract_contact_info(text),
            "summary": self._extract_summary(text),
            "work_experience": self._extract_work_experience(text),
            "education": self._extract_education(text),
            "skills": self._extract_skills(text)
        }
        return sections

    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information using regex patterns"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b(?:\+\d{1,2}\s?)?(?:\(\d{3}\)|\d{3})[\s.-]?\d{3}[\s.-]?\d{4}\b'
        
        return {
            "email": re.findall(email_pattern, text)[0] if re.findall(email_pattern, text) else None,
            "phone": re.findall(phone_pattern, text)[0] if re.findall(phone_pattern, text) else None
        }

    def _extract_summary(self, text: str) -> str:
        """Extract professional summary"""
        summary_keywords = ['professional summary', 'profile', 'about me', 'professional profile']
        for keyword in summary_keywords:
            match = re.search(f'{keyword}[:\n]*(.*?)(?:\n\n|\n[A-Z])', text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience sections"""
        work_keywords = ['work experience', 'professional experience', 'employment history']
        for keyword in work_keywords:
            match = re.search(f'{keyword}[:\n]*(.*?)(?:\n\n|\n[A-Z])', text, re.DOTALL | re.IGNORECASE)
            if match:
                # Basic parsing, can be enhanced
                return [{"description": match.group(1).strip()}]
        return []

    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education sections"""
        education_keywords = ['education', 'academic background']
        for keyword in education_keywords:
            match = re.search(f'{keyword}[:\n]*(.*?)(?:\n\n|\n[A-Z])', text, re.DOTALL | re.IGNORECASE)
            if match:
                # Basic parsing, can be enhanced
                return [{"description": match.group(1).strip()}]
        return []

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from CV"""
        skills_keywords = ['skills', 'technical skills', 'professional skills']
        for keyword in skills_keywords:
            match = re.search(f'{keyword}[:\n]*(.*?)(?:\n\n|\n[A-Z])', text, re.DOTALL | re.IGNORECASE)
            if match:
                # Split skills and clean them
                skills = [skill.strip() for skill in re.split(r'[,•\n]+', match.group(1)) if skill.strip()]
                return skills
        return []

    def analyze_cv(self, file_path: str) -> Dict[str, Any]:
        """
        Comprehensive CV analysis
        """
        parsed_data = self.parse_docx(file_path)
        
        # Additional analysis can be added here
        analysis = {
            "completeness_score": self._calculate_completeness(parsed_data),
            "recommended_improvements": self._generate_recommendations(parsed_data)
        }
        
        return {**parsed_data, **analysis}

    def _calculate_completeness(self, parsed_data: Dict) -> float:
        """Calculate CV completeness score"""
        sections = parsed_data.get('sections', {})
        total_sections = len(sections)
        filled_sections = sum(1 for section in sections.values() if section)
        return (filled_sections / total_sections) * 100 if total_sections > 0 else 0

    def _generate_recommendations(self, parsed_data: Dict) -> List[str]:
        """Generate CV improvement recommendations"""
        recommendations = []
        sections = parsed_data.get('sections', {})
        
        if not sections.get('summary'):
            recommendations.append("Add a professional summary to highlight your key strengths")
        
        if len(sections.get('work_experience', [])) < 2:
            recommendations.append("Consider adding more work experience details")
        
        if len(sections.get('skills', [])) < 5:
            recommendations.append("Expand your skills section to showcase more capabilities")
        
        return recommendations

class ProCVAnalyzer:
    def __init__(self, openai_api_key: str):
        # Load advanced NLP models
        self.nlp = spacy.load("en_core_web_lg")
        openai.api_key = openai_api_key

    def advanced_cv_score(self, cv_text: str, job_description: str = None) -> Dict[str, Any]:
        """
        Provide a comprehensive CV scoring and analysis
        
        Args:
            cv_text (str): Full text of the CV
            job_description (str, optional): Job description for targeted analysis
        
        Returns:
            Dict with detailed CV analysis and recommendations
        """
        # Basic text preprocessing
        doc = self.nlp(cv_text)
        
        # Compute advanced metrics
        metrics = {
            "readability_score": self._compute_readability(cv_text),
            "named_entities": self._extract_named_entities(doc),
            "keyword_density": self._compute_keyword_density(cv_text),
            "writing_style": self._analyze_writing_style(cv_text)
        }
        
        # AI-powered job matching (if job description provided)
        if job_description:
            metrics["job_match_score"] = self._compute_job_match(cv_text, job_description)
        
        # Generate AI-powered recommendations
        metrics["ai_recommendations"] = self._generate_ai_recommendations(cv_text)
        
        return metrics

    def _compute_readability(self, text: str) -> float:
        """
        Compute Flesch-Kincaid readability score
        
        Returns a score between 0-100, higher is more readable
        """
        words = text.split()
        sentences = text.split('.')
        
        if not sentences or not words:
            return 0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables_per_word = sum(self._count_syllables(word) for word in words) / len(words)
        
        # Flesch-Kincaid readability formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        return max(0, min(score, 100))

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count += 1
        return count

    def _extract_named_entities(self, doc) -> Dict[str, List[str]]:
        """Extract and categorize named entities"""
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "skills": []
        }
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities["persons"].append(ent.text)
            elif ent.label_ == "ORG":
                entities["organizations"].append(ent.text)
            elif ent.label_ == "GPE":
                entities["locations"].append(ent.text)
        
        # Additional skill extraction using custom logic
        entities["skills"] = self._extract_skills(doc)
        
        return entities

    def _extract_skills(self, doc) -> List[str]:
        """Extract potential skills from text"""
        skill_patterns = [
            r'\b(Python|Java|C\+\+|JavaScript|React|Angular|Vue|SQL|Machine Learning|AI|Data Science)\b',
            r'\b(Project Management|Agile|Scrum|Leadership|Communication|Problem Solving)\b'
        ]
        
        skills = []
        for pattern in skill_patterns:
            skills.extend(re.findall(pattern, doc.text, re.IGNORECASE))
        
        return list(set(skills))

    def _compute_keyword_density(self, text: str) -> Dict[str, float]:
        """Compute keyword density"""
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        
        densities = {}
        for i, score in enumerate(tfidf_matrix.toarray()[0]):
            if score > 0.1:  # Threshold to filter important keywords
                densities[feature_names[i]] = score
        
        return dict(sorted(densities.items(), key=lambda x: x[1], reverse=True)[:10])

    def _analyze_writing_style(self, text: str) -> Dict[str, Any]:
        """Analyze writing style and tone"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analyze the writing style of the following text. Provide insights on tone, professionalism, and communication effectiveness."},
                    {"role": "user", "content": text[:4000]}  # Limit text length
                ]
            )
            return {
                "style_analysis": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens
            }
        except Exception as e:
            return {"error": str(e)}

    def _compute_job_match(self, cv_text: str, job_description: str) -> float:
        """
        Compute semantic similarity between CV and job description
        
        Returns a match score between 0-1
        """
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([cv_text, job_description])
        
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity * 100  # Convert to percentage

    def _generate_ai_recommendations(self, cv_text: str) -> List[str]:
        """Generate AI-powered CV improvement recommendations"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Review this CV and provide 3-5 specific, actionable recommendations to improve its effectiveness."},
                    {"role": "user", "content": cv_text[:4000]}  # Limit text length
                ]
            )
            recommendations = response.choices[0].message.content.split('\n')
            return [rec.strip() for rec in recommendations if rec.strip()]
        except Exception as e:
            return [f"AI recommendation generation failed: {str(e)}"]

def analyze_cv_pro(file_path: str, job_description: str = None, openai_key: str = None):
    """
    Pro-tier CV analysis function
    
    Args:
        file_path (str): Path to CV document
        job_description (str, optional): Job description for targeted analysis
        openai_key (str, optional): OpenAI API key for advanced features
    
    Returns:
        Comprehensive CV analysis report
    """
    parser = CVParser()
    cv_data = parser.parse_docx(file_path)
    
    if openai_key:
        pro_analyzer = ProCVAnalyzer(openai_key)
        cv_data['pro_analysis'] = pro_analyzer.advanced_cv_score(
            cv_data['raw_text'], 
            job_description
        )
    
    return cv_data
