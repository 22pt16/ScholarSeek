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
    const expansionBanner = document.getElementById('expansionBanner');
    const expansionTerms = document.getElementById('expansionTerms');
    const chkExpand = document.getElementById('chkExpand');

    // Stats
    const statDocs = document.getElementById('statDocs');
    const statTerms = document.getElementById('statTerms');
    const statAvgLen = document.getElementById('statAvgLen');

    // Add Document Modal
    const addDocModal = document.getElementById('addDocModal');
    const btnOpenModal = document.getElementById('btnOpenModal');
    const btnCloseModal = document.getElementById('btnCloseModal');
    const btnCancelModal = document.getElementById('btnCancelModal');
    const addDocForm = document.getElementById('addDocForm');

    // Evaluation Modal
    const evalModal = document.getElementById('evalModal');
    const btnOpenEval = document.getElementById('btnOpenEval');
    const btnCloseEval = document.getElementById('btnCloseEval');
    const btnCloseEval2 = document.getElementById('btnCloseEval2');
    const btnRunEval = document.getElementById('btnRunEval');
    const evalResults = document.getElementById('evalResults');

    // Debounce timer for autocomplete
    let debounceTimer = null;

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
        expansionBanner.style.display = 'none';
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

    // Evaluation Modal Events
    if (btnOpenEval) btnOpenEval.addEventListener('click', () => evalModal.style.display = 'flex');
    if (btnCloseEval) btnCloseEval.addEventListener('click', () => evalModal.style.display = 'none');
    if (btnCloseEval2) btnCloseEval2.addEventListener('click', () => evalModal.style.display = 'none');
    if (btnRunEval) btnRunEval.addEventListener('click', runEvaluation);

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
                <span>${item}</span>
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

    async function performSearch() {
        const query = searchInput.value.trim();
        if (!query) return;

        hideAutocomplete();
        const selectedAlgo = document.querySelector('input[name="algorithm"]:checked').value;
        const expand = chkExpand && chkExpand.checked ? 'true' : 'false';

        resultsContainer.innerHTML = '<div class="results-loading"><i class="fa-solid fa-circle-notch fa-spin"></i> Searching index...</div>';
        resultsHeader.style.display = 'none';
        suggestionBanner.style.display = 'none';
        if (expansionBanner) expansionBanner.style.display = 'none';

        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&algo=${selectedAlgo}&expand=${expand}`);
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

        // Show query expansion terms if any.
        if (expansionBanner && data.expanded_terms && data.expanded_terms.length > 0) {
            expansionTerms.innerHTML = data.expanded_terms.map(t =>
                `<span class="term-chip" style="background:rgba(139,92,246,0.15);color:#a78bfa;">${t}</span>`
            ).join(' ');
            expansionBanner.style.display = 'block';
        } else if (expansionBanner) {
            expansionBanner.style.display = 'none';
        }

        if (data.results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="result-card" style="text-align: center; padding: 40px;">
                    <i class="fa-solid fa-ghost" style="font-size: 2.5rem; color: var(--text-dim); margin-bottom: 12px;"></i>
                    <h3>No results found for "${data.query}"</h3>
                    <p style="color: var(--text-muted); margin-top: 6px;">Try adjusting your search terms or algorithm choice.</p>
                </div>
            `;
            return;
        }

        // Calculate maximum score for relative percentage bars
        const maxScore = Math.max(...data.results.map(r => r.score)) || 1.0;

        resultsContainer.innerHTML = data.results.map(item => {
            const pct = Math.min(100, Math.round((item.score / maxScore) * 100));
            const highlightedSnippet = highlightText(item.snippet, data.query);
            
            const breakdownLabel = data.algorithm === 'SEMANTIC'
                ? 'Semantic Match:'
                : (data.algorithm === 'BM25' ? 'BM25 Score:'
                : (data.algorithm === 'FIELD_AWARE' ? 'Field-Aware BM25:'
                : (data.algorithm === 'HYBRID' ? 'Hybrid RRF Score:' : 'TF-IDF Score:')));

            const termBreakdownHtml = Object.entries(item.term_scores).map(([term, sc]) => 
                `<span class="term-chip">${term === 'semantic' ? 'cosine_sim' : term}: ${typeof sc === 'number' ? sc.toFixed(3) : sc}</span>`
            ).join('');

            return `
                <div class="result-card">
                    <div class="card-top">
                        <span class="category-tag">${item.category}</span>
                        <div class="score-badge">
                            <div class="score-bar-bg" title="Relevance Score">
                                <div class="score-bar-fill" style="width: ${pct}%;"></div>
                            </div>
                            <span>${item.score.toFixed(3)}</span>
                        </div>
                    </div>
                    <h3 class="card-title">
                        <a href="${item.url}" target="_blank">${item.title}</a>
                    </h3>
                    <span class="card-url"><i class="fa-solid fa-link"></i> ${item.url}</span>
                    <p class="card-snippet">${highlightedSnippet}</p>
                    <div class="card-footer">
                        <span style="color: var(--text-dim);">${breakdownLabel}</span>
                        <div class="term-breakdown">${termBreakdownHtml}</div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function highlightText(text, query) {
        if (!query || !text) return text;
        const terms = query.split(/\s+/).filter(t => t.length > 0);
        let result = text;

        terms.forEach(term => {
            const regex = new RegExp(`(${escapeRegExp(term)})`, 'gi');
            result = result.replace(regex, '<mark class="matched-highlight">$1</mark>');
        });

        return result;
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // -----------------------------------------------------------------------
    // Evaluation Panel
    // -----------------------------------------------------------------------
    async function runEvaluation() {
        const query = document.getElementById('evalQuery').value.trim();
        const relevantRaw = document.getElementById('evalRelevant').value.trim();
        const k = parseInt(document.getElementById('evalK').value) || 10;
        const checkedAlgos = Array.from(document.querySelectorAll('.eval-algo-cb:checked')).map(cb => cb.value);

        if (!query || !relevantRaw) {
            evalResults.innerHTML = '<p style="color:var(--text-muted)">Please fill in both Query and Relevant IDs.</p>';
            return;
        }

        const relevant_ids = relevantRaw.split(',').map(s => s.trim()).filter(Boolean);

        btnRunEval.disabled = true;
        btnRunEval.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Running...';
        evalResults.innerHTML = '<p style="color:var(--text-muted)">Running evaluation across algorithms...</p>';

        try {
            const res = await fetch('/api/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, relevant_ids, algorithms: checkedAlgos, k })
            });
            const data = await res.json();

            if (!res.ok) {
                evalResults.innerHTML = `<p style="color:#f87171">Error: ${data.error}</p>`;
                return;
            }

            renderEvalResults(data);
        } catch (err) {
            evalResults.innerHTML = `<p style="color:#f87171">Request failed: ${err.message}</p>`;
        } finally {
            btnRunEval.disabled = false;
            btnRunEval.innerHTML = '<i class="fa-solid fa-play"></i> Run Evaluation';
        }
    }

    function renderEvalResults(data) {
        const metrics = data.metrics;
        const algos = Object.keys(metrics);
        const k = data.k;
        const metricKeys = [`precision@${k}`, `recall@${k}`, `f1@${k}`, `ndcg@${k}`, 'mrr', `map@${k}`];
        const metricLabels = [`P@${k}`, `R@${k}`, `F1@${k}`, `NDCG@${k}`, 'MRR', `MAP@${k}`];

        // Find best value per metric for highlighting.
        const bestPerMetric = {};
        metricKeys.forEach(mk => {
            bestPerMetric[mk] = Math.max(...algos.map(a => metrics[a][mk] || 0));
        });

        const algoLabels = { tfidf: 'TF-IDF', bm25: 'BM25', field_aware: 'Field-Aware', semantic: 'Semantic', hybrid: 'Hybrid' };

        let html = `<div class="eval-summary">`;
        html += `<p><strong>Query:</strong> "${data.query}" &nbsp;|&nbsp; <strong>Relevant docs:</strong> ${data.relevant_count} &nbsp;|&nbsp; <strong>K:</strong> ${k}</p>`;
        html += `</div>`;
        html += `<div class="eval-table-wrap"><table class="eval-table">`;
        html += `<thead><tr><th>Algorithm</th>${metricLabels.map(m => `<th>${m}</th>`).join('')}<th>Time (ms)</th><th>Hits</th></tr></thead>`;
        html += `<tbody>`;

        algos.forEach(algo => {
            const m = metrics[algo];
            if (m.error) {
                html += `<tr><td>${algoLabels[algo] || algo}</td><td colspan="${metricLabels.length + 2}" style="color:#f87171">${m.error}</td></tr>`;
                return;
            }
            html += `<tr>`;
            html += `<td class="algo-cell">${algoLabels[algo] || algo}</td>`;
            metricKeys.forEach(mk => {
                const val = (m[mk] || 0);
                const isBest = val > 0 && val === bestPerMetric[mk];
                html += `<td class="${isBest ? 'best-cell' : ''}">${val.toFixed(4)}</td>`;
            });
            html += `<td>${m.execution_time_ms || '-'}</td>`;
            html += `<td>${m.hits || 0} / ${k}</td>`;
            html += `</tr>`;
        });

        html += `</tbody></table></div>`;
        html += `<p style="color:var(--text-dim);font-size:0.78rem;margin-top:0.5rem;">&#9733; Green cells = best score for that metric across algorithms.</p>`;
        evalResults.innerHTML = html;
    }
});
