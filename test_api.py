import requests
import os
import json

# Create a test TXT resume with more detailed info
resume_text = """John Smith
Software Engineer
john.smith@example.com | New York, NY

PROFESSIONAL SUMMARY:
Experienced Software Engineer with 5 years of experience in Python, Java, and Cloud technologies. 
Specialized in building scalable microservices and deploying machine learning models.

EDUCATION:
Bachelor of Science in Computer Science
Massachusetts Institute of Technology (MIT), 2018

TECHNICAL SKILLS:
Languages: Python, Java, JavaScript, SQL, C++, Go
Frameworks/Tools: Flask, Django, React, Node.js, Docker, Kubernetes, Git
Cloud: AWS, Azure, Google Cloud
Data Science: Machine Learning, NLP, Pandas, Scikit-learn

WORK EXPERIENCE:
Senior Software Engineer @ Google (2020 - Present)
- Developed REST APIs using Python and Flask for high-traffic microservices.
- Implemented CI/CD pipelines using Jenkins and GitHub Actions.

Software Developer @ Microsoft (2018 - 2020)
- Built enterprise applications using Java Spring Boot.
- Managed PostgreSQL databases and optimized queries.
"""

with open("test_resume.txt", "w") as f:
    f.write(resume_text)

# Detailed Job Description
job_desc = """We are seeking a Senior Software Engineer with strong expertise in Python and Java. 
You will be responsible for designing and developing scalable microservices using Flask or Django. 
Requirements:
- 3+ years of professional experience in Backend development.
- Deep knowledge of Cloud platforms (AWS, Azure, or GCP).
- Experience with Docker, Kubernetes, and container orchestration.
- Familiarity with Machine Learning and NLP is a plus.
- Bachelor's degree in Computer Science or related field.
- Proficiency in SQL and PostgreSQL.
"""

print("🚀 Sending analysis request to http://localhost:5000/analyze...")

with open("test_resume.txt", "rb") as f:
    response = requests.post(
        "http://localhost:5000/analyze",
        files={"resume": ("test_resume.txt", f, "text/plain")},
        data={"job_description": job_desc},
    )

print("Status:", response.status_code)

if response.status_code != 200:
    print("Error Output:", response.text)
    exit()

data = response.json()

print("\n--- Summary Results ---")
print(f"Overall Score: {data.get('score')}/100 ({data.get('score_label')})")
print(f"Skills Fit:    {data.get('skills_fit')}%")
print(f"TF-IDF Match:  {data.get('tfidf_similarity')}%")
print(f"Keyword Match: {data.get('keyword_match')}%")

print("\n--- Professional Indicators ---")
print(f"Education Match: {'✅' if data.get('has_degree') else '❌'}")
print(f"Experience Match: {'✅' if data.get('has_exp') else '❌'}")

print("\n--- Matched Skills ---")
matched_skills = data.get('matched_skills', [])
print(", ".join(matched_skills) if matched_skills else "None")

print("\n--- Missing Skills ---")
missing_skills = data.get('missing_skills', [])
print(", ".join(missing_skills) if missing_skills else "None")

print("\n--- NER Entities (Top 5) ---")
for e in data.get("resume_entities", [])[:5]:
    print(f"[{e['label']}] {e['text']}")

os.remove("test_resume.txt")
print("\n✅ Test complete.")
