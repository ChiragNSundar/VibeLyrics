// VibeLyrics - Main JavaScript

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Close modal on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});

// API helper
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(endpoint, options);
    return response.json();
}

// Count syllables (rough client-side estimation)
function countSyllables(word) {
    word = word.toLowerCase().trim();
    if (word.length <= 3) return 1;

    word = word.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '');
    word = word.replace(/^y/, '');

    const matches = word.match(/[aeiouy]{1,2}/g);
    return matches ? matches.length : 1;
}

function countLineSyllables(text) {
    const words = text.split(/\s+/).filter(w => w);
    return words.reduce((sum, word) => sum + countSyllables(word), 0);
}

// Advanced real-time analysis for rap lyrics
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('new-line-input');
    const hint = document.getElementById('input-hint');

    if (input && hint) {
        input.addEventListener('input', () => {
            const text = input.value;
            const analysis = analyzeLine(text);
            updateAnalysisDisplay(analysis, hint);
        });
    }
});

// Analyze a line of lyrics
function analyzeLine(text) {
    if (!text.trim()) {
        return { syllables: 0, words: 0, rhymeEnding: '', features: [] };
    }

    const words = text.split(/\s+/).filter(w => w);
    const syllables = countLineSyllables(text);
    const lastWord = words[words.length - 1]?.toLowerCase().replace(/[.,!?]$/, '') || '';

    // Detect features
    const features = [];

    // Alliteration detection (same starting consonant)
    const alliteration = detectAlliteration(words);
    if (alliteration) features.push({ type: 'alliteration', label: '🔤 Alliteration' });

    // Internal rhyme detection
    const internalRhymes = detectInternalRhymes(words);
    if (internalRhymes > 0) features.push({ type: 'internal-rhyme', label: `🔗 ${internalRhymes} internal rhyme${internalRhymes > 1 ? 's' : ''}` });

    // Multisyllabic words (complexity indicator)
    const multiSyllabicCount = words.filter(w => countSyllables(w) >= 3).length;
    if (multiSyllabicCount > 0) features.push({ type: 'complex', label: `💎 ${multiSyllabicCount} complex word${multiSyllabicCount > 1 ? 's' : ''}` });

    // Assonance detection (repeated vowel sounds)
    const assonance = detectAssonance(text);
    if (assonance) features.push({ type: 'assonance', label: '🎵 Assonance' });

    // SIMILE detection (using "like" or "as...as" comparisons)
    const simile = detectSimile(text);
    if (simile) features.push({ type: 'simile', label: '🎭 Simile' });

    // Metaphor hint (contains "is" without "like/as")
    const metaphor = detectMetaphor(text, simile);
    if (metaphor) features.push({ type: 'metaphor', label: '🌟 Metaphor' });

    // Word count indicator
    const wordDensity = words.length >= 6 ? 'dense' : words.length >= 4 ? 'medium' : 'light';

    return {
        syllables,
        words: words.length,
        rhymeEnding: lastWord.slice(-2),
        features,
        wordDensity
    };
}

// Update the analysis display
function updateAnalysisDisplay(analysis, container) {
    const syllableCounter = container.querySelector('.syllable-counter');
    if (syllableCounter) {
        syllableCounter.innerHTML = `<strong>${analysis.syllables}</strong> syllables · ${analysis.words} words`;
    }

    // Show features if any detected
    let featuresContainer = container.querySelector('.line-features');
    if (!featuresContainer) {
        featuresContainer = document.createElement('div');
        featuresContainer.className = 'line-features';
        container.appendChild(featuresContainer);
    }

    if (analysis.features.length > 0) {
        featuresContainer.innerHTML = analysis.features.map(f =>
            `<span class="feature-badge ${f.type}">${f.label}</span>`
        ).join('');
        featuresContainer.style.display = 'flex';
    } else {
        featuresContainer.style.display = 'none';
    }
}

// Detect alliteration (repeated starting sounds)
function detectAlliteration(words) {
    if (words.length < 2) return false;
    const firstLetters = words.map(w => w[0]?.toLowerCase()).filter(l => l && l.match(/[a-z]/));
    const letterCounts = {};
    firstLetters.forEach(l => letterCounts[l] = (letterCounts[l] || 0) + 1);
    return Object.values(letterCounts).some(count => count >= 2);
}

// Detect internal rhymes (words that rhyme within the line)
function detectInternalRhymes(words) {
    if (words.length < 2) return 0;
    const endings = words.map(w => w.toLowerCase().replace(/[.,!?]$/, '').slice(-2));
    const endingCounts = {};
    endings.forEach(e => endingCounts[e] = (endingCounts[e] || 0) + 1);
    return Object.values(endingCounts).filter(count => count >= 2).length;
}

// Detect assonance (repeated vowel sounds)
function detectAssonance(text) {
    const vowelGroups = text.toLowerCase().match(/[aeiou]+/g) || [];
    if (vowelGroups.length < 3) return false;
    const vowelCounts = {};
    vowelGroups.forEach(v => vowelCounts[v] = (vowelCounts[v] || 0) + 1);
    return Object.values(vowelCounts).some(count => count >= 3);
}

// Detect simile (comparisons using "like" or "as...as")
function detectSimile(text) {
    const lower = text.toLowerCase();
    // Pattern: "like a/the" or "as X as"
    const likePattern = /\blike\s+(a|an|the|my|your|his|her|their|some)\b/i;
    const asPattern = /\bas\s+\w+\s+as\b/i;

    return likePattern.test(lower) || asPattern.test(lower);
}

// Detect potential metaphor (X is Y pattern without simile)
function detectMetaphor(text, hasSimile) {
    if (hasSimile) return false;
    const lower = text.toLowerCase();
    // Look for "is/am/are" patterns that suggest metaphor
    const metaphorPatterns = [
        /\bi('m| am)\s+(a|an|the)\s+\w+/i,  // "I'm a lion"
        /\bis\s+(a|an|the)\s+\w+/i,          // "life is a game"
        /\bare\s+(the|my|your)\s+\w+/i       // "we are the future"
    ];
    return metaphorPatterns.some(p => p.test(lower));
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        color: var(--text-primary);
        z-index: 2000;
        animation: fadeIn 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}
