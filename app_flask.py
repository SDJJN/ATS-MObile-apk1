import os
import re
import tempfile
import traceback

import pdfplumber
import spacy
from docx import Document
from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

# ─── Load spaCy NER model once at startup ────────────────────────────────────
NER_MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ner_model')
try:
    nlp = spacy.load(NER_MODEL_PATH)
    print("[OK] NER model loaded")
except Exception as e:
    print(f"[WARN] NER model failed to load: {e}")
    nlp = None

# Also load a general spaCy model for better tokenization
try:
    nlp_general = spacy.load("en_core_web_sm")
    print("[OK] en_core_web_sm loaded")
except Exception:
    nlp_general = None
    print("[INFO] en_core_web_sm not available, using basic tokenizer")


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs)


def extract_text_from_txt(file_obj):
    return file_obj.read().decode('utf-8', errors='ignore')


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT PREPROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def preprocess_text(text):
    if not text:
        return ""
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_keywords(text):
    """Extract meaningful keywords from text using basic NLP."""
    text_lower = text.lower()
    # Remove common stop words and get meaningful tokens
    stop_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'dare', 'ought', 'used', 'this', 'that', 'these', 'those', 'i', 'me',
        'my', 'we', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her',
        'it', 'its', 'they', 'them', 'their', 'what', 'which', 'who', 'whom',
        'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'just', 'because', 'as', 'until',
        'while', 'about', 'between', 'through', 'during', 'before', 'after',
        'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again',
        'further', 'then', 'once', 'here', 'there', 'also', 'etc', 'like',
        'well', 'back', 'even', 'still', 'way', 'take', 'come', 'make', 'go',
        'get', 'give', 'us', 'able', 'work', 'working', 'looking', 'using',
        'including', 'e', 'g', 'ie', 'eg', 'new', 'use', 'one', 'two',
    }
    # Split into words and filter
    words = re.findall(r'[a-zA-Z+#.]+', text_lower)
    keywords = [w for w in words if w not in stop_words and len(w) > 1]
    return keywords


# ═══════════════════════════════════════════════════════════════════════════════
# NER ENTITY EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_entities(text):
    """Extract named entities using the custom NER model."""
    if not nlp or not text:
        return []
    try:
        doc = nlp(text)
        return [[ent.label_, ent.text] for ent in doc.ents]
    except Exception as e:
        print(f"[WARN] NER extraction failed: {e}")
        return []


# ─── Comprehensive Tech Skills Dictionary ─────────────────────────────────────
SKILLS_DICTIONARY = {
    'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'php', 'ruby', 'swift', 'kotlin', 'go', 'rust', 'scala',
    'react', 'angular', 'vue', 'next.js', 'node.js', 'express', 'django', 'flask', 'spring boot', 'laravel', 'asp.net',
    'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'git', 'github',
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'cassandra', 'elasticsearch', 'dynamodb', 'oracle',
    'machine learning', 'deep learning', 'nlp', 'pytorch', 'tensorflow', 'scikit-learn', 'pandas', 'numpy', 'opencv',
    'data science', 'big data', 'hadoop', 'spark', 'tableau', 'power bi', 'excel', 'r', 'matlab',
    'devops', 'ci/cd', 'agile', 'scrum', 'rest api', 'graphql', 'microservices', 'serverless', 'blockchain',
    'ios', 'android', 'flutter', 'react native', 'swiftui', 'unity', 'unreal engine',
    'cybersecurity', 'penetration testing', 'firewalls', 'networking', 'linux', 'unix', 'shell scripting',
    'html', 'css', 'sass', 'tailwind', 'bootstrap', 'material ui', 'webpack', 'vite', 'npm', 'yarn',
    'jira', 'confluence', 'trello', 'slack', 'notion', 'figma', 'adobe xd', 'photoshop', 'illustrator',
}


def get_all_skills(text, ner_entities=[]):
    """Hybrid skill extraction: NER + Dictionary matching."""
    found_skills = set()
    text_lower = text.lower()

    # 1. From NER model
    for label, ent_text in ner_entities:
        if label == 'SKILLS':
            found_skills.add(ent_text.lower())

    # 2. From Dictionary matching (to ensure accuracy)
    # Using regex word boundaries to avoid partial matches
    for skill in SKILLS_DICTIONARY:
        if re.search(rf'\b{re.escape(skill)}\b', text_lower):
            found_skills.add(skill)

    return found_skills


# ═══════════════════════════════════════════════════════════════════════════════
# TF-IDF SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def compute_tfidf_score(resume_text, job_text):
    """Compute ATS score using TF-IDF, Keywords, and Specific Skills Matching."""

    # --- 1) NER entities (for display and logic) ---
    resume_entities = extract_entities(resume_text)
    job_entities = extract_entities(job_text)

    # --- 2) TF-IDF Cosine Similarity ---
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
    )
    try:
        tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except Exception:
        similarity = 0.0

    # --- 3) Dedicated Skills Fit Analysis ---
    skills_resume = get_all_skills(resume_text, resume_entities)
    skills_job = get_all_skills(job_text, job_entities)

    if len(skills_job) > 0:
        matched_skills = skills_resume & skills_job
        missing_skills = skills_job - skills_resume
        skills_fit_pct = len(matched_skills) / len(skills_job)
    else:
        matched_skills = set()
        missing_skills = set()
        skills_fit_pct = 0.0

    # --- 4) Keyword overlap analysis (General Keywords) ---
    resume_kw = set(extract_keywords(resume_text))
    job_kw = set(extract_keywords(job_text))

    if len(job_kw) > 0:
        matched_kw = resume_kw & job_kw
        kw_match_pct = len(matched_kw) / len(job_kw)
    else:
        matched_kw = set()
        kw_match_pct = 0.0

    # --- 5) Combined Final Score ---
    # Weighting: 40% TF-IDF, 30% NER Skills Match, 30% Keyword Matching
    final_score = (similarity * 0.4 + skills_fit_pct * 0.3 + kw_match_pct * 0.3) * 100
    score = round(min(final_score, 100), 1)

    # --- 6) Professional Indicators (Experience, Degree) ---
    has_degree = any(e[0] == 'DEGREE' for e in resume_entities) or re.search(r'\b(bachelor|master|degree|phd|university)\b', resume_text.lower())
    has_exp = any(e[0] == 'YEARS_OF_EXPERIENCE' or e[0] == 'DESIGNATION' for e in resume_entities)

    return {
        'score': score,
        'score_label': 'Low' if score <= 40 else ('Average' if score <= 65 else 'Good'),
        'tfidf_similarity': round(similarity * 100, 1),
        'keyword_match': round(kw_match_pct * 100, 1),
        'skills_fit': round(skills_fit_pct * 100, 1),
        'matched_skills': sorted(list(matched_skills)),
        'missing_skills': sorted(list(missing_skills)),
        'matched_keywords': sorted(list(matched_kw))[:30],
        'missing_keywords': sorted(list(job_kw - resume_kw))[:20],
        'resume_entities': resume_entities,
        'job_entities': job_entities,
        'has_degree': bool(has_degree),
        'has_exp': bool(has_exp),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SUGGESTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

SECTION_PATTERNS = {
    'contact_info': r'(email|phone|mobile|address|linkedin|github)',
    'education': r'(bachelor|master|degree|university|college|school|gpa|diploma)',
    'experience': r'(experience|worked|employed|position|role|responsibility|years)',
    'skills': r'(skills?|proficien|expertise|technologies|tools|frameworks|languages)',
    'projects': r'(projects?|built|developed|created|implemented|designed)',
    'certifications': r'(certif|licensed|accredited|credential)',
    'summary': r'(summary|objective|profile|overview|about)',
}


def generate_suggestions(resume_text, missing_keywords, score):
    """Generate improvement suggestions based on analysis."""
    suggestions = []
    resume_lower = resume_text.lower()

    # Check which standard resume sections are present
    for section, pattern in SECTION_PATTERNS.items():
        if not re.search(pattern, resume_lower):
            labels = {
                'contact_info': ('Contact Info', 'Add email, phone number, and LinkedIn profile for easy recruiter contact.'),
                'education': ('Education', 'Include your educational background — degree, university, and graduation year.'),
                'experience': ('Work Experience', 'Detail your professional experience with roles, companies, and achievements.'),
                'skills': ('Skills Section', 'Add a dedicated skills section highlighting your technical and soft skills.'),
                'projects': ('Projects', 'Showcase relevant projects that demonstrate your hands-on abilities.'),
                'certifications': ('Certifications', 'Include industry certifications to stand out from other candidates.'),
                'summary': ('Professional Summary', 'Add a brief summary at the top to quickly convey your value proposition.'),
            }
            label, text = labels[section]
            suggestions.append({'keyword': label, 'suggestion': text})

    # Add suggestions for top missing keywords
    if missing_keywords:
        top_missing = missing_keywords[:8]
        suggestions.append({
            'keyword': 'Missing Keywords',
            'suggestion': f'Your resume is missing these keywords from the job description: {", ".join(top_missing)}. Try to naturally incorporate them.'
        })

    # Score-based tips
    if score < 40:
        suggestions.append({
            'keyword': 'Low Match',
            'suggestion': 'Your resume has a low match with this job. Consider tailoring it specifically for this role.'
        })
    elif score < 65:
        suggestions.append({
            'keyword': 'Improve Match',
            'suggestion': 'Your resume partially matches. Focus on adding missing technical skills and using similar terminology as the job description.'
        })

    return suggestions


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file uploaded'}), 400

        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        job_description = request.form.get('job_description', '').strip()
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400

        print(f"\n[ANALYZE] File: {file.filename}")

        # Extract text based on file type
        text = ""
        filename = file.filename.lower()

        if filename.endswith('.pdf'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            text = extract_text_from_pdf(tmp_path)
            os.unlink(tmp_path)

        elif filename.endswith('.docx'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            text = extract_text_from_docx(tmp_path)
            os.unlink(tmp_path)

        elif filename.endswith('.txt'):
            text = extract_text_from_txt(file)

        else:
            return jsonify({'error': 'Unsupported format. Use PDF, DOCX, or TXT.'}), 400

        if not text or not text.strip():
            return jsonify({'error': 'Could not extract text from the file.'}), 400

        # Preprocess
        text = preprocess_text(text)
        job_description = preprocess_text(job_description)

        print(f"[ANALYZE] Resume text: {len(text)} chars | JD: {len(job_description)} chars")

        # Compute TF-IDF score
        result = compute_tfidf_score(text, job_description)

        print(f"[ANALYZE] Score: {result['score']} | TF-IDF: {result['tfidf_similarity']}% | Keywords: {result['keyword_match']}%")

        # Generate suggestions
        suggestions = generate_suggestions(text, result['missing_keywords'], result['score'])

        return jsonify({
            'score': result['score'],
            'score_label': result['score_label'],
            'message': f"Your ATS Score is {result['score']} out of 100",
            'tfidf_similarity': result['tfidf_similarity'],
            'keyword_match': result['keyword_match'],
            'skills_fit': result['skills_fit'],
            'matched_skills': result['matched_skills'],
            'missing_skills': result['missing_skills'],
            'matched_keywords': result['matched_keywords'],
            'missing_keywords': result['missing_keywords'],
            'resume_entities': [{'label': e[0], 'text': e[1]} for e in result['resume_entities']],
            'job_entities': [{'label': e[0], 'text': e[1]} for e in result['job_entities']],
            'has_degree': result['has_degree'],
            'has_exp': result['has_exp'],
            'suggestions': suggestions,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500


if __name__ == '__main__':
    print("  🚀 ATS Scoring System running at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
