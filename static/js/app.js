document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchInput = document.getElementById('searchInput');
    const btnSearch = document.getElementById('btnSearch');
    const btnClearSearch = document.getElementById('btnClearSearch');
    const autocompleteDropdown = document.getElementById('autocompleteDropdown');
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsHeader = document.getElementById('resultsHeader');
    const resultsCount = document.getElementById('resultsCount');
    const resultsTime = document.getElementById('resultsTime');
    const heroSection = document.getElementById('heroSection');
    const suggestionBanner = document.getElementById('suggestionBanner');
    const suggestionLink = document.getElementById('suggestionLink');

    // Stats
    const statDocs = document.getElementById('statDocs');
    const statTerms = document.getElementById('statTerms');
    const statAvgLen = document.getElementById('statAvgLen');

    // Modal
    const addDocModal = document.getElementById('addDocModal');
    const btnOpenModal = document.getElementById('btnOpenModal');
    const btnCloseModal = document.getElementById('btnCloseModal');
    const btnCancelModal = document.getElementById('btnCancelModal');
    const addDocForm = document.getElementById('addDocForm');

    // Debounce timer for autocomplete
    let debounceTimer = null;
    let currentPage = 1;

    // Load Initial Stats
    fetchStats();

    // Event Listeners
    btnSearch.addEventListener('click', () => performSearch());
    
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            hideAutocomplete();
            performSearch();
        }
    });

    searchInput.addEventListener('input', (e) => {
        const value = e.target.value;
        btnClearSearch.style.display = value.length > 0 ? 'block' : 'none';

        clearTimeout(debounceTimer);
        if (value.trim().length >= 2) {
            debounceTimer = setTimeout(() => fetchAutocomplete(value), 200);
        } else {
            hideAutocomplete();
        }
    });

    btnClearSearch.addEventListener('click', () => {
        searchInput.value = '';
        btnClearSearch.style.display = 'none';
        hideAutocomplete();
        resultsContainer.innerHTML = '';
        resultsHeader.style.display = 'none';
        suggestionBanner.style.display = 'none';
        heroSection.style.display = 'block';
    });

    // Quick Chips
    document.querySelectorAll('.quick-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            searchInput.value = chip.textContent;
            btnClearSearch.style.display = 'block';
            performSearch();
        });
    });

    // Suggestion Link Click
    suggestionLink.addEventListener('click', (e) => {
        e.preventDefault();
        searchInput.value = suggestionLink.textContent;
        performSearch();
    });

    // Radio algorithm change triggers search if active query
    document.querySelectorAll('input[name="algorithm"]').forEach(radio => {
        radio.addEventListener('change', () => {
            if (searchInput.value.trim().length > 0) {
                performSearch();
            }
        });
    });

    // Modal Events
    btnOpenModal.addEventListener('click', () => addDocModal.style.display = 'flex');
    btnCloseModal.addEventListener('click', () => addDocModal.style.display = 'none');
    btnCancelModal.addEventListener('click', () => addDocModal.style.display = 'none');

    addDocForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            title: document.getElementById('docTitle').value,
            category: document.getElementById('docCategory').value,
            url: document.getElementById('docUrl').value,
            content: document.getElementById('docContent').value
        };

        try {
            const res = await fetch('/api/documents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok) {
                alert('✨ Document indexed successfully!');
                addDocForm.reset();
                addDocModal.style.display = 'none';
                fetchStats();
            } else {
                alert('Error: ' + data.error);
            }
        } catch (err) {
            console.error(err);
            alert('Failed to index document.');
        }
    });

    // Helper Functions
    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            const data = await res.json();
            statDocs.textContent = data.total_documents;
            statTerms.textContent = data.vocabulary_size;
            statAvgLen.textContent = data.avg_doc_length;
        } catch (err) {
            console.error('Stats error:', err);
        }
    }

    async function fetchAutocomplete(prefix) {
        try {
            const res = await fetch(`/api/suggest?q=${encodeURIComponent(prefix)}`);
            const data = await res.json();
            renderAutocomplete(data.suggestions);
        } catch (err) {
            console.error('Autocomplete error:', err);
        }
    }

    function renderAutocomplete(suggestions) {
        if (!suggestions || suggestions.length === 0) {
            hideAutocomplete();
            return;
        }

        autocompleteDropdown.innerHTML = suggestions.map(item => `
            <div class="suggestion-item">
                <i class="fa-solid fa-magnifying-glass"></i>
                <span>${escapeHtml(item)}</span>
            </div>
        `).join('');

        autocompleteDropdown.style.display = 'block';

        document.querySelectorAll('.suggestion-item').forEach(el => {
            el.addEventListener('click', () => {
                searchInput.value = el.querySelector('span').textContent;
                hideAutocomplete();
                performSearch();
            });
        });
    }

    function hideAutocomplete() {
        autocompleteDropdown.style.display = 'none';
    }

    async function performSearch(page = 1) {
        const query = searchInput.value.trim();
        if (!query) return;
        currentPage = page;

        hideAutocomplete();
        const selectedAlgo = document.querySelector('input[name="algorithm"]:checked').value;

        resultsContainer.innerHTML = '<div class="results-loading"><i class="fa-solid fa-circle-notch fa-spin"></i> Searching index...</div>';
        resultsHeader.style.display = 'none';
        suggestionBanner.style.display = 'none';

        try {
            const res = await fetch(
                `/api/search?q=${encodeURIComponent(query)}&algo=${selectedAlgo}&page=${page}&per_page=10`
            );
            const data = await res.json();

            heroSection.style.display = 'none';
            renderResults(data);
        } catch (err) {
            console.error(err);
            resultsContainer.innerHTML = '<div class="results-error">An error occurred while communicating with search backend.</div>';
        }
    }

    function renderResults(data) {
        resultsCount.textContent = `Found ${data.total_results} matching document${data.total_results === 1 ? '' : 's'}`;
        resultsTime.textContent = `(${data.execution_time_ms} ms using ${data.algorithm})`;
        resultsHeader.style.display = 'flex';

        if (data.suggestion) {
            suggestionLink.textContent = data.suggestion;
            suggestionBanner.style.display = 'block';
        }

        if (data.results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="result-card" style="text-align: center; padding: 40px;">
                    <i class="fa-solid fa-ghost" style="font-size: 2.5rem; color: var(--text-dim); margin-bottom: 12px;"></i>
                    <h3>No results found for "${escapeHtml(data.query)}"</h3>
                    <p style="color: var(--text-muted); margin-top: 6px;">Try adjusting your search terms or algorithm choice.</p>
                </div>
            `;
            return;
        }

        // Calculate maximum score for relative percentage bars
        const maxScore = Math.max(...data.results.map(r => r.score)) || 1.0;

        const resultsHTML = data.results.map(item => {
            const pct = Math.min(100, Math.round((item.score / maxScore) * 100));
            const highlightedSnippet = highlightText(item.snippet, data.query);
            
            const termBreakdownHtml = Object.entries(item.term_scores || {}).map(([term, sc]) => {
                const formattedScore = typeof sc === 'number' ? sc.toFixed(3) : sc;
                return `<span class="term-chip">${escapeHtml(term)}: ${escapeHtml(formattedScore)}</span>`;
            }).join('');
            const resultUrl = safeHref(item.url);

            let breakdownLabel = 'TF-IDF Contributions:';
            if (data.algorithm === 'BM25') {
                breakdownLabel = 'BM25 Contributions:';
            } else if (data.algorithm === 'SEMANTIC') {
                breakdownLabel = 'Semantic Similarity:';
            }

            return `
                <div class="result-card">
                    <div class="card-top">
                        <span class="category-tag">${escapeHtml(item.category)}</span>
                        <div class="score-badge">
                            <div class="score-bar-bg" title="Relevance Score">
                                <div class="score-bar-fill" style="width: ${pct}%;"></div>
                            </div>
                            <span>${item.score.toFixed(3)}</span>
                        </div>
                    </div>
                    <h3 class="card-title">
                        <a href="${escapeHtml(resultUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a>
                    </h3>
                    <span class="card-url"><i class="fa-solid fa-link"></i> ${escapeHtml(item.url)}</span>
                    <p class="card-snippet">${highlightedSnippet}</p>
                    <div class="card-footer">
                        <span style="color: var(--text-dim);">${breakdownLabel}</span>
                        <div class="term-breakdown">${termBreakdownHtml}</div>
                    </div>
                </div>
            `;
        }).join('');
        const totalPages = data.total_pages || 1;

        const paginationHTML = totalPages > 1 ? `
            <div class="pagination-controls">
                <button
                    class="btn-secondary"
                    data-page="${data.page - 1}"
                    ${data.page <= 1 ? 'disabled' : ''}>
                    ← Previous
                </button>

                <span>
                    Page ${data.page} of ${totalPages}
                    · ${data.total_results.toLocaleString()} matches
                </span>

                <button
                    class="btn-secondary"
                    data-page="${data.page + 1}"
                    ${data.page >= totalPages ? 'disabled' : ''}>
                    Next →
                </button>
            </div>
        ` : '';

        resultsContainer.innerHTML = paginationHTML + resultsHTML + paginationHTML;

        
    }
   resultsContainer.addEventListener('click', async (event) => {
        const button = event.target.closest('button[data-page]');
        if (!button || button.disabled) return;

        await performSearch(Number(button.dataset.page));

        resultsHeader.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    });

    function highlightText(text, query) {
        if (!query || !text) return escapeHtml(text || '');
        const terms = query.split(/\s+/).filter(t => t.length > 0);
        let result = escapeHtml(text);

        terms.forEach(term => {
            const safeTerm = escapeHtml(term);
            const regex = new RegExp(`(${escapeRegExp(safeTerm)})`, 'gi');
            result = result.replace(regex, '<mark class="matched-highlight">$1</mark>');
        });

        return result;
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, char => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[char]);
    }

    function safeHref(value) {
        try {
            const parsed = new URL(String(value || '#'), window.location.origin);
            return ['http:', 'https:'].includes(parsed.protocol) ? parsed.href : '#';
        } catch (_) {
            return '#';
        }
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
});
