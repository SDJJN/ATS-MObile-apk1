/* ═══════════════════════════════════════════════════════════════════════════
   ATS Resume Analyzer — Frontend Logic
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    // ─── DOM Elements ─────────────────────────────────────────────────────
    const form = document.getElementById('analyzeForm');
    const dropzone = document.getElementById('dropzone');
    const resumeInput = document.getElementById('resumeInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const fileRemove = document.getElementById('fileRemove');
    const jobDescription = document.getElementById('jobDescription');
    const charCount = document.getElementById('charCount');
    const btnAnalyze = document.getElementById('btnAnalyze');
    const btnText = btnAnalyze.querySelector('.btn-text');
    const btnLoader = btnAnalyze.querySelector('.btn-loader');
    const errorBanner = document.getElementById('errorBanner');
    const errorText = document.getElementById('errorText');
    const resultsSection = document.getElementById('resultsSection');

    let selectedFile = null;

    // ─── Dropzone: Click to browse ────────────────────────────────────────
    dropzone.addEventListener('click', (e) => {
        if (e.target === fileRemove || e.target.closest('.file-remove')) return;
        resumeInput.click();
    });

    resumeInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // ─── Dropzone: Drag & Drop ────────────────────────────────────────────
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('drag-over');
    });

    dropzone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    function handleFile(file) {
        const validTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ];
        const ext = file.name.split('.').pop().toLowerCase();
        const validExts = ['pdf', 'docx', 'txt'];

        if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
            showError('Please upload a PDF, DOCX, or TXT file.');
            return;
        }

        selectedFile = file;
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);

        // Hide the upload prompt, show file info
        dropzone.querySelector('.dropzone-content').style.display = 'none';
        fileInfo.style.display = 'block';
    }

    // ─── Remove file ──────────────────────────────────────────────────────
    fileRemove.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedFile = null;
        resumeInput.value = '';
        dropzone.querySelector('.dropzone-content').style.display = 'block';
        fileInfo.style.display = 'none';
    });

    // ─── Character count ──────────────────────────────────────────────────
    jobDescription.addEventListener('input', () => {
        const len = jobDescription.value.length;
        charCount.textContent = len.toLocaleString() + ' character' + (len !== 1 ? 's' : '');
    });

    // ─── Format file size ─────────────────────────────────────────────────
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }

    // ─── Show / hide error ────────────────────────────────────────────────
    function showError(msg) {
        errorText.textContent = msg;
        errorBanner.style.display = 'flex';
        errorBanner.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(() => { errorBanner.style.display = 'none'; }, 6000);
    }

    function hideError() {
        errorBanner.style.display = 'none';
    }

    // ─── Form submission ──────────────────────────────────────────────────
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        // Validate
        if (!selectedFile) {
            showError('Please upload a resume file.');
            return;
        }
        if (!jobDescription.value.trim()) {
            showError('Please enter a job description.');
            return;
        }

        // Show loading state
        setLoading(true);

        try {
            const formData = new FormData();
            formData.append('resume', selectedFile);
            formData.append('job_description', jobDescription.value);

            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                showError(data.error || 'Something went wrong.');
                setLoading(false);
                return;
            }

            renderResults(data);
        } catch (err) {
            showError('Failed to connect to server. Make sure Flask is running.');
        } finally {
            setLoading(false);
        }
    });

    function setLoading(loading) {
        btnAnalyze.disabled = loading;
        btnText.style.display = loading ? 'none' : 'inline-flex';
        btnLoader.style.display = loading ? 'inline-flex' : 'none';
    }

    // ─── Render results ───────────────────────────────────────────────────
    function renderResults(data) {
        resultsSection.style.display = 'block';

        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

        // ── Main Score ring animation ──
        const score = Math.min(data.score, 100);
        const circumference = 2 * Math.PI * 85; 
        const offset = circumference - (score / 100) * circumference;

        const scoreFill = document.getElementById('scoreFill');
        const scoreNumber = document.getElementById('scoreNumber');
        const scoreLabel = document.getElementById('scoreLabel');
        const scoreMessage = document.getElementById('scoreMessage');

        let strokeColor, labelClass;
        if (score <= 40) {
            strokeColor = '#ef4444';
            labelClass = 'low';
        } else if (score <= 65) {
            strokeColor = '#f59e0b';
            labelClass = 'average';
        } else {
            strokeColor = '#10b981';
            labelClass = 'good';
        }

        scoreFill.style.stroke = strokeColor;
        requestAnimationFrame(() => {
            scoreFill.style.strokeDashoffset = offset;
        });

        animateCounter(scoreNumber, 0, score, 1500);
        scoreLabel.textContent = data.score_label;
        scoreLabel.className = 'score-label ' + labelClass;
        scoreMessage.textContent = data.message;

        // ── Professional Badges ──
        const badgeDegree = document.getElementById('badgeDegree');
        const badgeExp = document.getElementById('badgeExp');
        badgeDegree.style.display = data.has_degree ? 'flex' : 'none';
        badgeExp.style.display = data.has_exp ? 'flex' : 'none';

        // ── Skills Fit and TF-IDF Bars ──
        document.getElementById('skillsFitValue').textContent = data.skills_fit + '%';
        document.getElementById('skillsFitBar').style.width = data.skills_fit + '%';
        document.getElementById('tfidfValue').textContent = data.tfidf_similarity + '%';
        document.getElementById('tfidfBar').style.width = data.tfidf_similarity + '%';

        // ── Stats Row ──
        document.getElementById('statMatchedSkills').textContent = data.matched_skills.length;
        document.getElementById('statMissingSkills').textContent = data.missing_skills.length;
        document.getElementById('statMatchedKw').textContent = data.matched_keywords.length;

        // ── Keyword & Skills Pills ──
        renderKeywordPills('matchedSkillsPills', data.matched_skills, 'matched-pill');
        renderKeywordPills('missingSkillsPills', data.missing_skills, 'missing-pill');
        renderKeywordPills('matchedPills', data.matched_keywords, 'matched-pill');
        renderKeywordPills('missingPills', data.missing_keywords, 'missing-pill');

        // ── Suggestions ──
        const suggestionsCard = document.getElementById('suggestionsCard');
        const suggestionsList = document.getElementById('suggestionsList');
        suggestionsList.innerHTML = '';

        if (data.suggestions && data.suggestions.length > 0) {
            suggestionsCard.style.display = 'block';
            data.suggestions.forEach((s, i) => {
                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.style.animationDelay = (i * 0.08) + 's';
                item.innerHTML = `
                    <span class="suggestion-badge">${escapeHtml(s.keyword)}</span>
                    <span class="suggestion-text">${escapeHtml(s.suggestion)}</span>
                `;
                suggestionsList.appendChild(item);
            });
        } else {
            suggestionsCard.style.display = 'none';
        }

        // ── Entity tables ──
        populateTable('resumeTable', data.resume_entities);
        populateTable('jobTable', data.job_entities);
    }

    function renderKeywordPills(containerId, keywords, className) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        if (!keywords || keywords.length === 0) {
            container.innerHTML = '<span style="color: var(--text-muted); font-size: 0.8rem;">None detected</span>';
            return;
        }
        keywords.forEach(kw => {
            const span = document.createElement('span');
            span.className = 'pill ' + className;
            span.textContent = kw;
            container.appendChild(span);
        });
    }

    // ─── Entity toggle logic ──────────────────────────────────────────────
    const toggleBtn = document.getElementById('toggleEntities');
    const entitiesContent = document.getElementById('entitiesContent');
    const entitiesCard = document.getElementById('entitiesCard');

    toggleBtn.addEventListener('click', () => {
        const isHidden = entitiesContent.style.display === 'none';
        entitiesContent.style.display = isHidden ? 'block' : 'none';
        toggleBtn.textContent = isHidden ? 'Hide Details' : 'Show Details';
        if (isHidden) {
            entitiesCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });

    // We make sure the card is visible if there are entities
    window.addEventListener('analyze-done', () => {
        entitiesCard.style.display = 'block';
    });

    // ─── Populate entity table ────────────────────────────────────────────
    function populateTable(tableId, entities) {
        const tbody = document.getElementById(tableId).querySelector('tbody');
        tbody.innerHTML = '';

        if (!entities || entities.length === 0) {
            const tr = document.createElement('tr');
            tr.innerHTML = '<td colspan="2" style="text-align:center; color: var(--text-muted); padding: 20px;">No entities detected</td>';
            tbody.appendChild(tr);
            return;
        }

        entities.forEach(e => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${escapeHtml(e.label)}</td><td>${escapeHtml(e.text)}</td>`;
            tbody.appendChild(tr);
        });

        // Trigger visible card
        document.getElementById('entitiesCard').style.display = 'block';
    }

    // ─── Animate counter ──────────────────────────────────────────────────
    function animateCounter(el, start, end, duration) {
        const startTime = performance.now();
        const isFloat = end % 1 !== 0;

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            const eased = 1 - Math.pow(1 - progress, 3);
            const current = start + (end - start) * eased;

            el.textContent = isFloat ? current.toFixed(1) : Math.round(current);

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = isFloat ? end.toFixed(1) : Math.round(end);
            }
        }

        requestAnimationFrame(update);
    }

    // ─── HTML escape ──────────────────────────────────────────────────────
    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
});
