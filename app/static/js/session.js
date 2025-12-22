// VibeLyrics - Session Page JavaScript

// Toggle AI Panel
function toggleAIPanel() {
    const panel = document.getElementById('ai-panel');
    panel.classList.toggle('active');
}

// Add line to session
async function addLine() {
    const input = document.getElementById('new-line-input');
    const line = input.value.trim();

    if (!line) return;

    try {
        const result = await apiCall('/api/line/add', 'POST', {
            session_id: SESSION_ID,
            line: line
        });

        if (result.success) {
            // Add line to UI
            const container = document.getElementById('lines-container');
            const lineRow = createLineElement(result, line);
            container.appendChild(lineRow);

            // Clear input and update line number
            input.value = '';
            updateLineNumber();

            // Update syllable counter
            document.querySelector('.syllable-counter').textContent = '0 syllables';

            // Scroll to bottom
            container.scrollTop = container.scrollHeight;

            // Auto-suggest next line (vibe writing mode!)
            suggestNext();
        }
    } catch (e) {
        showToast('Error adding line: ' + e.message, 'error');
    }
}

// Create line element
function createLineElement(data, text) {
    const div = document.createElement('div');
    div.className = 'line-row';
    div.dataset.lineId = data.line_id;
    div.dataset.lineNumber = data.line_number;

    div.innerHTML = `
        <span class="line-number">${data.line_number}</span>
        <div class="line-content">
            <span class="line-text">${escapeHtml(text)}</span>
            <div class="line-meta">
                <span class="syllable-count" title="Syllable count">${data.syllable_count} syl</span>
                ${data.has_internal_rhyme ? '<span class="rhyme-badge" title="Has internal rhyme">🔗</span>' : ''}
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

    // Update syllable count
    const syllables = countLineSyllables(text);
    document.querySelector('.syllable-counter').textContent = `${syllables} syllables`;
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
    const lineRow = document.querySelector(`[data-line-id="${lineId}"]`);
    if (!lineRow) return;

    const originalText = currentLineToImprove.text;

    // Update UI immediately
    lineRow.querySelector('.line-text').textContent = newText;

    // Track the correction
    try {
        await apiCall('/api/line/accept', 'POST', {
            line_id: lineId,
            original_suggestion: newText,
            accepted_version: newText
        });

        showToast('Line improved! ✨');
    } catch (e) {
        showToast('Error saving improvement', 'error');
    }
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
    const modal = document.getElementById('analysis-modal');
    const content = document.getElementById('analysis-content');

    modal.classList.add('active');
    content.innerHTML = '<div class="analyzing"><div class="spinner"></div><p>Analyzing your bars...</p></div>';

    try {
        const result = await apiCall(`/api/session/${SESSION_ID}/analyze`);

        if (result.error) {
            content.innerHTML = `<p class="error">${result.error}</p>`;
            return;
        }

        // Calculate additional metrics
        const avgSyllables = result.complexity.avg_syllables || 11;
        const rhymeDensity = (result.complexity.rhyme_density || 0.5) * 100;
        const vocabularyRichness = (result.complexity.vocabulary_richness || 0.6) * 100;
        const flowConsistency = (result.complexity.flow_score || 0.7) * 100;

        let html = `
            <div class="analysis-grid">
                <!-- Stats Row -->
                <div class="stats-row">
                    <div class="stat-card">
                        <div class="stat-value">${result.line_count}</div>
                        <div class="stat-label">Lines</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${avgSyllables.toFixed(1)}</div>
                        <div class="stat-label">Avg Syllables</div>
                    </div>
                    <div class="stat-card accent">
                        <div class="stat-value">${(result.complexity.overall * 100).toFixed(0)}%</div>
                        <div class="stat-label">Complexity</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${BPM}</div>
                        <div class="stat-label">BPM</div>
                    </div>
                </div>

                <!-- Rhyme Scheme -->
                <div class="analysis-card">
                    <h3>🎯 Rhyme Scheme</h3>
                    <div class="rhyme-scheme-visual">
                        ${result.rhyme_scheme.split('').map((letter, i) =>
            `<span class="rhyme-letter" style="--hue: ${(letter.charCodeAt(0) - 65) * 30}">${letter}</span>`
        ).join('')}
                    </div>
                    <p class="scheme-type">${getRhymeSchemeType(result.rhyme_scheme)}</p>
                </div>

                <!-- Skill Breakdown -->
                <div class="analysis-card">
                    <h3>📊 Skill Breakdown</h3>
                    <div class="skill-bars">
                        <div class="skill-row">
                            <span class="skill-name">Rhyme Density</span>
                            <div class="skill-bar"><div class="skill-fill rhyme" style="width: ${rhymeDensity}%"></div></div>
                            <span class="skill-value">${rhymeDensity.toFixed(0)}%</span>
                        </div>
                        <div class="skill-row">
                            <span class="skill-name">Vocabulary</span>
                            <div class="skill-bar"><div class="skill-fill vocab" style="width: ${vocabularyRichness}%"></div></div>
                            <span class="skill-value">${vocabularyRichness.toFixed(0)}%</span>
                        </div>
                        <div class="skill-row">
                            <span class="skill-name">Flow</span>
                            <div class="skill-bar"><div class="skill-fill flow" style="width: ${flowConsistency}%"></div></div>
                            <span class="skill-value">${flowConsistency.toFixed(0)}%</span>
                        </div>
                        <div class="skill-row">
                            <span class="skill-name">Complexity</span>
                            <div class="skill-bar"><div class="skill-fill complexity" style="width: ${result.complexity.overall * 100}%"></div></div>
                            <span class="skill-value">${(result.complexity.overall * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                </div>

                <!-- Techniques Detected -->
                <div class="analysis-card">
                    <h3>✨ Techniques Detected</h3>
                    <div class="techniques-grid">
                        ${getTechniquesBadges(result.complexity)}
                    </div>
                </div>
        `;

        if (result.improvement_suggestions && result.improvement_suggestions.length > 0) {
            html += `
                <div class="analysis-card suggestions">
                    <h3>💡 Level Up Tips</h3>
                    <ul class="tips-list">
                        ${result.improvement_suggestions.map(s => `<li><span class="tip-icon">→</span> ${escapeHtml(s)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (result.flow_suggestions && result.flow_suggestions.recommended_styles) {
            html += `
                <div class="analysis-card flow-styles">
                    <h3>🎵 Recommended Flows for ${BPM} BPM</h3>
                    <div class="flow-cards">
                        ${result.flow_suggestions.recommended_styles.map(style => `
                            <div class="flow-card">
                                <div class="flow-name">${style.style}</div>
                                <div class="flow-desc">${style.description}</div>
                                <div class="flow-artists">${style.example_artists.join(', ')}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        html += `</div>`;
        content.innerHTML = html;


    } catch (e) {
        content.innerHTML = `<p class="error">Error: ${e.message}</p>`;
    }
}

// Switch AI provider
async function switchProvider(provider) {
    try {
        await apiCall('/api/provider/switch', 'POST', { provider });
        showToast(`Switched to ${provider}`);
    } catch (e) {
        showToast('Error switching provider', 'error');
    }
}

// Helper: Get complexity label
function getComplexityLabel(score) {
    if (score < 0.3) return 'Simple';
    if (score < 0.5) return 'Moderate';
    if (score < 0.7) return 'Complex';
    if (score < 0.85) return 'Advanced';
    return 'Expert';
}

// Helper: Get rhyme scheme type description
function getRhymeSchemeType(scheme) {
    if (!scheme) return 'No rhymes detected yet';
    const unique = [...new Set(scheme.split(''))].length;
    const total = scheme.length;

    if (scheme === 'AABB' || scheme.includes('AABB')) return 'Couplet Pattern - Classic hip-hop structure';
    if (scheme === 'ABAB' || scheme.includes('ABAB')) return 'Alternate Pattern - Storytelling flow';
    if (scheme === 'ABBA' || scheme.includes('ABBA')) return 'Envelope Pattern - Poetic structure';
    if (scheme === 'AAAA') return 'Monorhyme - Intense, driving delivery';
    if (unique === 1) return 'Monorhyme - All lines rhyme together';
    if (unique === total) return 'Free Verse - No repeat rhymes';
    if (unique <= total / 2) return 'Dense Rhymes - Multiple rhyme groups';
    return `${unique} distinct rhyme sounds across ${total} lines`;
}

// Helper: Get techniques badges
function getTechniquesBadges(complexity) {
    const techniques = [];

    // Based on complexity data, generate technique badges
    if (complexity.overall > 0.6) techniques.push({ name: 'Complex Bars', icon: '💎' });
    if (complexity.rhyme_density > 0.5) techniques.push({ name: 'Rhyme Heavy', icon: '🎯' });
    if (complexity.vocabulary_richness > 0.6) techniques.push({ name: 'Rich Vocab', icon: '📚' });
    if (complexity.flow_score > 0.7) techniques.push({ name: 'Smooth Flow', icon: '🌊' });
    if (complexity.multisyllabic > 0.3) techniques.push({ name: 'Multisyllabic', icon: '🔥' });

    // Add some default techniques if we don't have enough
    if (techniques.length < 2) {
        techniques.push({ name: 'Wordplay', icon: '🧠' });
    }

    return techniques.map(t =>
        `<span class="technique-badge">${t.icon} ${t.name}</span>`
    ).join('');
}

// Helper: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, "\\'").replace(/"/g, '\\"');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set default improvement type
    document.querySelector('[data-type="rhyme"]')?.classList.add('active');
});

// Edit a line
function editLine(lineId, currentText) {
    const lineRow = document.querySelector(`[data-line-id="${lineId}"]`);
    if (!lineRow) return;

    const lineTextSpan = lineRow.querySelector('.line-text');
    const originalText = currentText;

    // Create an input field for editing
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'line-edit-input';
    input.value = currentText;

    // Replace text with input
    lineTextSpan.replaceWith(input);
    input.focus();
    input.select();

    // Save on blur or Enter
    const saveEdit = async () => {
        const newText = input.value.trim();
        if (newText && newText !== originalText) {
            try {
                await apiCall('/api/line/update', 'POST', {
                    line_id: lineId,
                    text: newText
                });

                // Create new span with updated text
                const newSpan = document.createElement('span');
                newSpan.className = 'line-text';
                newSpan.textContent = newText;
                input.replaceWith(newSpan);

                // Update data attributes on buttons
                lineRow.querySelectorAll('[data-line-text]').forEach(btn => {
                    btn.dataset.lineText = newText;
                });

                showToast('Line updated!');
            } catch (e) {
                showToast('Error updating line', 'error');
                // Revert on error
                const revertSpan = document.createElement('span');
                revertSpan.className = 'line-text';
                revertSpan.textContent = originalText;
                input.replaceWith(revertSpan);
            }
        } else {
            // Revert if empty or unchanged
            const revertSpan = document.createElement('span');
            revertSpan.className = 'line-text';
            revertSpan.textContent = originalText;
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
