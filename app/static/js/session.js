// VibeLyrics - Session Page JavaScript

// Initialize Socket.IO
const socket = io();

socket.on('connect', () => {
    console.log('Connected to socket server');
    socket.emit('join', { session_id: SESSION_ID });
});

// Listener: Real-time line updates from ONE WRITER to OTHERS
socket.on('line_updated', (data) => {
    // Find the line row
    const lineRow = document.querySelector(`[data-line-id="${data.line_id}"]`);
    if (lineRow) {
        // Update text if not currently being edited by THIS user
        const input = lineRow.querySelector('.line-edit-input');
        if (!input) {
            const lineText = lineRow.querySelector('.line-text');
            if (lineText) {
                lineText.textContent = data.content;
                // Highlight update effect
                lineText.style.color = 'var(--accent-primary)';
                setTimeout(() => lineText.style.color = '', 500);
            }
        }

        // Update syllable count
        const sylCount = lineRow.querySelector('.syllable-count');
        if (sylCount) {
            sylCount.textContent = `${data.syllable_count} syl`;
        }

        // Update stress visualization
        let stressViz = lineRow.querySelector('.stress-viz');
        if (!stressViz) {
            // Create if missing
            const meta = lineRow.querySelector('.line-meta');
            if (meta) {
                stressViz = document.createElement('div');
                stressViz.className = 'stress-viz';
                stressViz.title = "Stressed(●)/Unstressed(○) pattern";
                meta.appendChild(stressViz);
            }
        }
        if (stressViz) {
            stressViz.innerHTML = renderStressPattern(data.stress_pattern);
        }

        // Update data attributes for buttons
        lineRow.querySelectorAll('[data-line-text]').forEach(btn => {
            btn.dataset.lineText = data.content;
        });
    }
});

// Listener: New line added by collaborator
socket.on('line_added', (data) => {
    // Check if we have a pending line for this content
    // We look for a line with data-pending="true" and matching text
    const pendingLines = document.querySelectorAll('.line-row[data-pending="true"]');
    let match = null;

    // Find the first pending line that matches content
    for (const row of pendingLines) {
        const text = row.querySelector('.line-text').textContent;
        if (text === data.content) {
            match = row;
            break;
        }
    }

    if (match) {
        // Reconcile / Upgrade the pending line
        match.dataset.lineId = data.id;
        match.dataset.lineNumber = data.line_number;
        delete match.dataset.pending;
        match.style.opacity = '1';

        // Update stats from server (authoritative)
        match.querySelector('.syllable-count').textContent = `${data.syllable_count} syl`;
        match.querySelector('.line-number').textContent = data.line_number;

        // Update content with highlighted HTML from server if available
        if (data.highlighted_html) {
            match.querySelector('.line-text').innerHTML = data.highlighted_html;
        }

        // Update edit buttons data-attributes
        match.querySelectorAll('[data-line-id]').forEach(btn => {
            btn.dataset.lineId = data.id;
        });

        // Add stress viz if needed
        if (data.stress_pattern) {
            const meta = match.querySelector('.line-meta');
            let stressViz = meta.querySelector('.stress-viz');
            if (!stressViz) {
                stressViz = document.createElement('div');
                stressViz.className = 'stress-viz';
                meta.appendChild(stressViz);
            }
            stressViz.innerHTML = renderStressPattern(data.stress_pattern);
        }

        // Refresh flow visualization
        refreshFlowViz();
    } else {
        // If no pending match found (e.g. from another user), append normally
        if (document.querySelector(`[data-line-id="${data.id}"]`)) return;

        const mappedData = {
            line_id: data.id,
            line_number: data.line_number,
            syllable_count: data.syllable_count || 0,
            has_internal_rhyme: data.has_internal_rhyme || false,
            stress_pattern: data.stress_pattern,
            highlighted_html: data.highlighted_html
        };

        const container = document.getElementById('lines-container');
        const lineRow = createLineElement(mappedData, data.content);
        container.appendChild(lineRow);
        container.scrollTop = container.scrollHeight;
        updateLineNumber();

        // Refresh flow visualization
        refreshFlowViz();
    }
});


// Toggle AI Panel
function toggleAIPanel() {
    const panel = document.getElementById('ai-panel');
    panel.classList.toggle('active');
}

// Add line to session (Socket Version)
async function addLine() {
    const input = document.getElementById('new-line-input');
    const lineContent = input.value.trim();

    if (!lineContent) return;

    const section = document.getElementById('section-select')?.value || 'Verse';

    // Optimistic: Create temporary line immediately
    const tempId = 'temp-' + Date.now(); // Unique temp ID
    const currentLines = document.querySelectorAll('.line-row');
    const nextNum = currentLines.length + 1;

    // Client-side syllable guess
    let sylCount = 0;
    if (typeof countSyllablesClient === 'function') {
        sylCount = countSyllablesClient(lineContent);
    }

    const tempData = {
        line_id: tempId,
        line_number: nextNum,
        syllable_count: sylCount,
        has_internal_rhyme: false,
        stress_pattern: ''
    };

    const container = document.getElementById('lines-container');
    const lineRow = createLineElement(tempData, lineContent);

    // Add visual indicator that it's syncing? (Optional, maybe opacity)
    lineRow.style.opacity = '0.7';
    lineRow.dataset.pending = 'true';

    container.appendChild(lineRow);
    container.scrollTop = container.scrollHeight;
    updateLineNumber();

    // Clear input immediately
    input.value = '';
    document.querySelector('.syllable-counter').textContent = '0 syllables';

    // Emit to server
    socket.emit('new_line', {
        session_id: SESSION_ID,
        content: lineContent,
        section: section
    });
}

// Create line element
function createLineElement(data, text) {
    const div = document.createElement('div');
    div.className = 'line-row';
    div.dataset.lineId = data.line_id;
    div.dataset.lineNumber = data.line_number;

    // Use highlighted HTML if available, otherwise escape text
    const contentHtml = data.highlighted_html || escapeHtml(text);

    div.innerHTML = `
        <span class="line-number">${data.line_number}</span>
        <div class="line-content">
            <span class="line-text" oncontextmenu="handleWordRightClick(event)">${contentHtml}</span>
            <div class="line-meta">
                <span class="syllable-count" title="Syllable count">${data.syllable_count} syl</span>
                ${data.has_internal_rhyme ? '<span class="rhyme-badge" title="Has internal rhyme">🔗</span>' : ''}
                <div class="stress-viz" title="Stressed(●)/Unstressed(○) pattern">${renderStressPattern(data.stress_pattern)}</div>
            </div>
        </div>
        <div class="line-actions">
            <button class="btn-icon edit-btn" data-line-id="${data.line_id}" data-line-text="${escapeHtml(text)}" onclick="editLine(this.dataset.lineId, this.dataset.lineText)" title="Edit">✏️</button>
            <button class="btn-icon improve-btn" data-line-id="${data.line_id}" data-line-text="${escapeHtml(text)}" onclick="improveLine(this.dataset.lineId, this.dataset.lineText)" title="Improve">✨</button>
            <button class="btn-icon delete-btn" data-line-id="${data.line_id}" onclick="deleteLine(this.dataset.lineId)" title="Delete">🗑️</button>
        </div>
    `;

    return div;
}

// Render 1010 pattern as dots
function renderStressPattern(pattern) {
    if (!pattern) return '';
    // 1=Primary(●), 2=Secondary(◎), 0=Unstressed(○)
    return pattern.split('').map(char => {
        if (char === '1') return '<span class="stress-dot primary">●</span>';
        if (char === '2') return '<span class="stress-dot secondary">◎</span>';
        return '<span class="stress-dot unstressed">○</span>';
    }).join('');
}

// Update line number in input
function updateLineNumber() {
    const lines = document.querySelectorAll('.line-row');
    const lineNumberSpan = document.querySelector('.input-row .line-number');
    if (lineNumberSpan) {
        lineNumberSpan.textContent = lines.length + 1;
    }
}

// IDE-Style Ghost Text Autocomplete
let currentSuggestionText = '';
let isLoadingSuggestion = false;

async function suggestNext() {
    if (isLoadingSuggestion) return;
    isLoadingSuggestion = true;

    const ghostText = document.getElementById('ghost-text');
    const tabHint = document.getElementById('tab-hint');
    const input = document.getElementById('new-line-input');

    ghostText.textContent = 'thinking...';
    ghostText.classList.add('loading');
    currentSuggestionText = '';

    try {
        const result = await apiCall('/api/line/suggest', 'POST', {
            session_id: SESSION_ID,
            action: 'next'
        });

        if (result.success && result.result && result.result.suggestion) {
            currentSuggestionText = result.result.suggestion;

            // Show ghost text (what user has typed + suggestion continuation)
            updateGhostText();
            tabHint.style.display = 'inline';
        } else {
            ghostText.textContent = '';
            currentSuggestionText = '';
        }
    } catch (e) {
        ghostText.textContent = '';
        console.error('Suggestion error:', e);
    } finally {
        ghostText.classList.remove('loading');
        isLoadingSuggestion = false;
    }
}

// Update ghost text based on input value
function updateGhostText() {
    const input = document.getElementById('new-line-input');
    const ghostText = document.getElementById('ghost-text');

    if (!currentSuggestionText) {
        ghostText.textContent = '';
        return;
    }

    const userText = input.value;

    // Show full suggestion as ghost text
    if (userText.length === 0) {
        ghostText.textContent = currentSuggestionText;
    } else if (currentSuggestionText.toLowerCase().startsWith(userText.toLowerCase())) {
        // User is typing matching the suggestion - show remaining part
        ghostText.textContent = userText + currentSuggestionText.slice(userText.length);
    } else {
        // User typed something different - clear ghost
        ghostText.textContent = '';
        currentSuggestionText = '';
        document.getElementById('tab-hint').style.display = 'none';
    }
}

// Accept the ghost text suggestion
function acceptSuggestion() {
    if (currentSuggestionText) {
        const input = document.getElementById('new-line-input');
        input.value = currentSuggestionText;
        input.focus();
        clearGhostText();
    }
}

// Clear ghost text
function clearGhostText() {
    const ghostText = document.getElementById('ghost-text');
    const tabHint = document.getElementById('tab-hint');
    ghostText.textContent = '';
    tabHint.style.display = 'none';
    currentSuggestionText = '';
}

// Keyboard event handlers
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('new-line-input');

    if (input) {
        // Tab to accept suggestion
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Tab' && currentSuggestionText) {
                e.preventDefault();
                acceptSuggestion();
            } else if (e.key === 'Escape') {
                clearGhostText();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                addLine();
            }
        });

        // Update ghost text as user types
        input.addEventListener('input', () => {
            updateGhostText();
        });
    }

    // Set default improvement type
    document.querySelector('[data-type="rhyme"]')?.classList.add('active');
});

// Use a suggestion
function useSuggestion(text) {
    const input = document.getElementById('new-line-input');
    input.value = text;
    input.focus();

    // Update syllable count (client-side guess)
    // const syllables = countLineSyllables(text);
    // document.querySelector('.syllable-counter').textContent = `${syllables} syllables`;
}

// Improve a line
async function improveLine(lineId, lineText) {
    currentLineToImprove = { id: lineId, text: lineText };

    const resultDiv = document.getElementById('improvement-result');
    resultDiv.innerHTML = '<p>Improving...</p>';

    // Open AI panel and scroll to improvement section
    document.getElementById('ai-panel').classList.add('active');
    document.getElementById('improvement-section').scrollIntoView();

    try {
        const result = await apiCall('/api/line/suggest', 'POST', {
            session_id: SESSION_ID,
            action: 'improve',
            current_line: lineText,
            improvement_type: currentImprovementType
        });

        if (result.success && result.result) {
            const data = result.result;

            let html = `
                <div class="original-line">
                    <strong>Original:</strong> ${escapeHtml(lineText)}
                </div>
                <div class="improved-line suggestion-item" onclick="applyImprovement(${lineId}, '${escapeHtml(data.improved)}')">
                    <strong>Improved:</strong> ${escapeHtml(data.improved)}
                </div>
            `;

            if (data.explanation) {
                html += `<p class="help-text">${escapeHtml(data.explanation)}</p>`;
            }

            if (data.changes_made && data.changes_made.length > 0) {
                html += '<ul class="changes-list">';
                data.changes_made.forEach(change => {
                    html += `<li>${escapeHtml(change)}</li>`;
                });
                html += '</ul>';
            }

            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<p class="error">${result.error || 'Error improving line'}</p>`;
        }
    } catch (e) {
        resultDiv.innerHTML = `<p class="error">Error: ${e.message}</p>`;
    }
}

// Apply improvement
async function applyImprovement(lineId, newText) {
    // THIS function calls handle_update_line manually? 
    // Or we rely on editLine?

    // Let's use socket update
    socket.emit('update_line', {
        session_id: SESSION_ID,
        line_id: lineId,
        content: newText
    });

    const lineRow = document.querySelector(`[data-line-id="${lineId}"]`);
    if (lineRow) {
        // Optimistic update
        const txt = lineRow.querySelector('.line-text');
        if (txt) txt.textContent = newText;
    }
    showToast('Line improved! ✨');
}

// Set improvement type
function setImprovementType(type) {
    currentImprovementType = type;

    // Update UI
    document.querySelectorAll('.improvement-types .chip').forEach(chip => {
        chip.classList.remove('active');
    });
    document.querySelector(`[data-type="${type}"]`)?.classList.add('active');

    // Re-run improvement if we have a line selected
    if (currentLineToImprove) {
        improveLine(currentLineToImprove.id, currentLineToImprove.text);
    }
}

// Ask AI
async function askAI() {
    const input = document.getElementById('ask-input');
    const responseDiv = document.getElementById('ask-response');
    const question = input.value.trim();

    if (!question) return;

    responseDiv.innerHTML = '<p>Thinking...</p>';

    try {
        const result = await apiCall('/api/ask', 'POST', {
            question: question,
            session_id: SESSION_ID
        });

        if (result.success) {
            responseDiv.innerHTML = `<div class="ai-answer">${escapeHtml(result.answer)}</div>`;
            input.value = '';
        } else {
            responseDiv.innerHTML = `<p class="error">${result.error}</p>`;
        }
    } catch (e) {
        responseDiv.innerHTML = `<p class="error">Error: ${e.message}</p>`;
    }
}

// Analyze session
async function analyzeSession() {
    openModal('analysis-modal');
    const content = document.getElementById('analysis-content');
    content.innerHTML = '<div class="spinner"></div>';

    try {
        const result = await apiCall(`/api/session/${SESSION_ID}/analyze`);
        if (result.complexity) {
            const dims = result.complexity.dimensions;
            content.innerHTML = `
                <div class="analysis-results">
                    <div class="analysis-header">
                        <div class="overall-score">${result.complexity.overall}</div>
                        <div class="complexity-label">Level: ${getComplexityLabel(result.complexity.overall)}</div>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-label">Internal Rhymes</div>
                            <div class="stat-bar"><div class="fill" style="width:${dims.internal_rhyme * 100}%"></div></div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Vocab Complexity</div>
                            <div class="stat-bar"><div class="fill" style="width:${dims.vocabulary * 100}%"></div></div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Vocab Diversity</div>
                            <div class="stat-bar"><div class="fill" style="width:${(dims.diversity_score || 0) * 100}%"></div></div>
                            <small class="stat-subtext">${Math.round((dims.vocabulary_diversity || 0) * 100)}% unique words</small>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Rhyme Connectivity</div>
                            <div class="stat-bar"><div class="fill" style="width:${dims.rhyme_scheme * 100}%"></div></div>
                        </div>
                    </div>

                    <div class="analysis-section">
                        <h4>Rhyme Scheme DNA</h4>
                        <div class="dna-sequence">${result.rhyme_scheme || 'N/A'}</div>
                    </div>

                    <div class="analysis-section">
                        <h4>Expert Suggestions</h4>
                        <ul class="suggestions-list">
                            ${(result.improvement_suggestions || []).map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
    } catch (e) {
        content.innerHTML = `<p class="error">Error: ${e.message}</p>`;
        console.error(e);
    }
}

function getComplexityLabel(score) {
    if (score < 0.3) return "Simple";
    if (score < 0.5) return "Moderate";
    if (score < 0.7) return "Complex";
    if (score < 0.85) return "Advanced";
    return "Expert";
}

// Handle word click/context menu
function handleWordRightClick(event) {
    event.preventDefault();
    const word = getWordAtClick(event);
    if (word) {
        showWordTools(word, event.pageX, event.pageY);
    }
}

// Get word at click position
function getWordAtClick(event) {
    let range;
    let textNode;
    let offset;

    if (document.caretRangeFromPoint) {
        range = document.caretRangeFromPoint(event.clientX, event.clientY);
        textNode = range.startContainer;
        offset = range.startOffset;
    } else if (document.caretPositionFromPoint) {
        range = document.caretPositionFromPoint(event.clientX, event.clientY);
        textNode = range.offsetNode;
        offset = range.offset;
    }

    if (textNode && textNode.nodeType === 3) {
        const text = textNode.nodeValue;
        // Find word boundaries
        let start = offset;
        while (start > 0 && /\w/.test(text[start - 1])) start--;
        let end = offset;
        while (end < text.length && /\w/.test(text[end])) end++;

        const word = text.substring(start, end).trim();
        if (word && /\w+/.test(word)) return word;
    }
    return null;
}

// Show Word Tools Popup
async function showWordTools(word, x, y) {
    // Remove existing
    const existing = document.getElementById('word-tools-popup');
    if (existing) existing.remove();

    const popup = document.createElement('div');
    popup.id = 'word-tools-popup';
    popup.className = 'word-tools-popup';
    popup.style.left = `${x}px`;
    popup.style.top = `${y}px`;
    popup.innerHTML = `
        <div class="wt-header">
            <strong>${word}</strong>
            <button onclick="this.closest('.word-tools-popup').remove()">×</button>
        </div>
        <div class="wt-tabs">
            <button class="active" onclick="switchWtTab(this, 'rhymes')">Rhymes</button>
            <button onclick="switchWtTab(this, 'pocket')">Pocket</button>
            <button onclick="switchWtTab(this, 'synonyms')">Synonyms</button>
            <button onclick="switchWtTab(this, 'antonyms')">Antonyms</button>
        </div>
        <div class="wt-filters">
            <input type="text" id="wt-topic-input" class="wt-topic-input" placeholder="Topic? (e.g. food)" 
                   onkeydown="if(event.key==='Enter') searchTopicRhymes(this)">
            <div class="syl-filters">
                <button class="active" onclick="filterWt(this, 'all')">All</button>
                <button onclick="filterWt(this, 1)">1</button>
                <button onclick="filterWt(this, 2)">2</button>
                <button onclick="filterWt(this, 3)">3+</button>
            </div>
        </div>
        <div class="wt-content loading">Loading...</div>
    `;

    document.body.appendChild(popup);

    setTimeout(() => {
        document.addEventListener('click', function close(e) {
            if (!popup.contains(e.target)) {
                popup.remove();
                document.removeEventListener('click', close);
            }
        });
    }, 100);

    // Fetch Rhymes (Default)
    await loadWtContent(word, 'rhyme', popup);
}

// Global cache for current popup data to support filtering
let currentWtData = [];

// Search Topic
async function searchTopicRhymes(input) {
    const popup = input.closest('.word-tools-popup');
    const word = popup.querySelector('.wt-header strong').textContent;
    const topic = input.value.trim();
    if (!topic) return;

    // Switch to rhymes tab if not active
    // ...
    await loadWtContent(word, 'rhyme', popup, 'rhymes', topic);
}

// Switch Tab
async function switchWtTab(btn, type) {
    const popup = btn.closest('.word-tools-popup');
    popup.querySelectorAll('.wt-tabs button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Reset filters
    popup.querySelectorAll('.syl-filters button').forEach(b => b.classList.remove('active'));
    popup.querySelector('.syl-filters button:first-of-type').classList.add('active');

    const word = popup.querySelector('.wt-header strong').textContent;
    let apiType = 'rhyme';
    if (type === 'synonyms' || type === 'antonyms') apiType = 'synonym';
    if (type === 'pocket') apiType = 'rhyme';

    await loadWtContent(word, apiType, popup, type);
}

function filterWt(btn, sylCount) {
    const popup = btn.closest('.word-tools-popup');
    popup.querySelectorAll('.syl-filters button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    renderWtGrid(currentWtData, popup, sylCount);
}

// Load Content
async function loadWtContent(word, apiType, popup, tabContext = 'rhymes', topic = '') {
    const content = popup.querySelector('.wt-content');
    content.innerHTML = '<div class="spinner small"></div>';

    let url = `/api/tools/lookup?word=${word}&type=${apiType}`;
    if (topic) url += `&topic=${topic}`;

    try {
        const result = await apiCall(url);
        let items = [];
        let sectionTitle = '';

        if (result.results) {
            if (apiType === 'rhyme') {
                if (tabContext === 'pocket') {
                    items = (result.results.pocket || []).map(w => ({ word: w, syllables: countSyllables(w) }));
                    sectionTitle = "Fit your pocket (Rhymes with same rhythm)";
                } else if (topic && result.results.topic_rhymes && result.results.topic_rhymes.length > 0) {
                    items = result.results.topic_rhymes.map(w => ({ word: w, syllables: countSyllables(w), isTopic: true }));
                    sectionTitle = `Rhymes related to "${topic}"`;
                } else {
                    if (result.results.perfect) {
                        items = result.results.perfect.map(w => ({ word: w, syllables: countSyllables(w) }));
                    } else if (Array.isArray(result.results)) {
                        items = result.results.map(w => ({ word: w, syllables: countSyllables(w) }));
                    }
                }
            } else {
                if (tabContext === 'synonyms') items = result.results.synonyms || [];
                else if (tabContext === 'antonyms') items = result.results.antonyms || [];
            }
        }

        currentWtData = items;
        renderWtGrid(items, popup, 'all', sectionTitle);

    } catch (e) {
        content.innerHTML = '<div class="wt-error">Error loading</div>';
        console.error(e);
    }
}

function renderWtGrid(items, popup, filterSyl, title = '') {
    const content = popup.querySelector('.wt-content');

    let filtered = items;
    if (filterSyl !== 'all') {
        if (filterSyl === 3) {
            filtered = items.filter(i => i.syllables >= 3);
        } else {
            filtered = items.filter(i => i.syllables === filterSyl);
        }
    }

    if (filtered.length === 0) {
        content.innerHTML = '<div class="wt-empty">No results found</div>';
        return;
    }

    content.innerHTML = `
        ${title ? `<div class="wt-section-title" style="font-size:0.8em; opacity:0.7; grid-column:1/-1; margin-bottom:5px;">${title}</div>` : ''}
        <div class="wt-grid">
            ${filtered.map(item => `
                <span class="wt-chip ${item.isTopic ? 'topic-match' : ''}" onclick="useSuggestion('${item.word.replace(/'/g, "\\'")}')" style="${item.isTopic ? 'border-color:var(--accent-primary);' : ''}">
                    ${item.word} 
                    <small style="opacity:0.5; font-size:0.7em; margin-left:4px;">${item.syllables || '?'}</small>
                </span>
            `).join('')}
        </div>
    `;
}

// Simple Client-side syllable guess for rhymes since RhymeDictionary returns plain strings
function countSyllablesClient(word) {
    word = word.toLowerCase();
    if (word.length <= 3) return 1;
    word = word.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '');
    word = word.replace(/^y/, '');
    const vowels = word.match(/[aeiouy]{1,2}/g);
    return vowels ? vowels.length : 1;
}

// Handle Input context menu (for textboxes)
function handleInputRightClick(event) {
    // Only if it's a text input
    if (event.target.tagName !== 'INPUT' && event.target.tagName !== 'TEXTAREA') return;

    // Check if we typically allow default (e.g. for paste). 
    // If text is selected or cursor is on a word, we might prioritize our tool
    // BUT user needs Paste. 
    // Compromise: Ctrl+RightClick? Or just override and provide Paste button?
    // User asked for it to "work", usually implies overriding default or augmenting.
    // Let's override for now, usually Ctrl+V is used for paste by pros.
    // Or check if a word is actually clicked.

    const word = getWordFromInput(event.target);
    if (word) {
        event.preventDefault();
        showWordTools(word, event.pageX, event.pageY);
    }
}

// Get word from input at cursor
function getWordFromInput(input) {
    const text = input.value;
    const cursor = input.selectionStart;

    // Find word boundaries around cursor
    let start = cursor;
    while (start > 0 && /\w/.test(text[start - 1])) start--;
    let end = cursor;
    while (end < text.length && /\w/.test(text[end])) end++;

    const word = text.substring(start, end).trim();
    if (word && /\w+/.test(word)) return word;
    return null;
}

// Initialize listeners
document.addEventListener('DOMContentLoaded', () => {
    // ... (existing listeners)

    // Add context menu to main input
    const mainInput = document.getElementById('new-line-input');
    if (mainInput) {
        mainInput.addEventListener('contextmenu', handleInputRightClick);
    }
});

// Update editLine to attach to new inputs
function editLine(lineId, currentText) {
    // ... (existing find row)
    const lineRow = document.querySelector(`[data-line-id="${lineId}"]`);
    if (!lineRow) return;

    const lineTextSpan = lineRow.querySelector('.line-text');
    const originalText = currentText;

    // Create an input field for editing
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'line-edit-input';
    input.value = currentText;

    // ATTACH RIGHT CLICK HANDLER
    input.addEventListener('contextmenu', handleInputRightClick);

    // Replace text with input
    lineTextSpan.replaceWith(input);
    input.focus();
    input.select();

    // ... (rest of saveEdit logic)
    const saveEdit = async () => {
        // ...
        // (Copied existing logic from previous view to ensure integrity)
        const newText = input.value.trim();
        if (newText && newText !== originalText) {
            socket.emit('update_line', {
                session_id: SESSION_ID,
                line_id: lineId,
                content: newText
            });
            const newSpan = document.createElement('span');
            newSpan.className = 'line-text';
            newSpan.textContent = newText;
            newSpan.setAttribute('oncontextmenu', 'handleWordRightClick(event)');
            input.replaceWith(newSpan);
            // ... update btns ...
            lineRow.querySelectorAll('[data-line-text]').forEach(btn => btn.dataset.lineText = newText);
            showToast('Line updated!');
        } else {
            const revertSpan = document.createElement('span');
            revertSpan.className = 'line-text';
            revertSpan.textContent = originalText;
            revertSpan.setAttribute('oncontextmenu', 'handleWordRightClick(event)');
            input.replaceWith(revertSpan);
        }
    };

    input.addEventListener('blur', saveEdit);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
        } else if (e.key === 'Escape') {
            input.value = originalText;
            input.blur();
        }
    });
}

// Delete a line
async function deleteLine(lineId) {
    if (!confirm('Delete this line?')) return;

    try {
        await apiCall('/api/line/delete', 'POST', { line_id: lineId });
        // NOTE: we should probably emit 'delete_line' socket event too for robustness, 
        // but user didn't explicitly ask for delete sync, just writing. 
        // I'll stick to basic writing sync for now.

        // Remove from UI
        const lineRow = document.querySelector(`[data-line-id="${lineId}"]`);
        if (lineRow) {
            lineRow.remove();
            updateLineNumber();
            showToast('Line deleted');
        }
    } catch (e) {
        showToast('Error deleting line', 'error');
    }
}


// Utility to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    return text.toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Refresh Flow Visualization with current line data
function refreshFlowViz() {
    // Check if viz exists (defined in session.html)
    if (typeof viz === 'undefined' || !viz) return;

    // Collect syllable data from all lines in DOM
    const lineRows = document.querySelectorAll('.line-row');
    const linesData = [];

    lineRows.forEach(row => {
        const sylSpan = row.querySelector('.syllable-count');
        if (sylSpan) {
            const sylText = sylSpan.textContent;
            const match = sylText.match(/(\d+)/);
            const syllable_count = match ? parseInt(match[1]) : 0;
            linesData.push({ syllable_count });
        }
    });

    viz.update(linesData);
}

