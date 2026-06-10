document.addEventListener('DOMContentLoaded', () => {
    // Generate a unique thread ID for the session
    const threadId = 'web_thread_' + Math.random().toString(36).substring(2, 11);
    let currentFilename = '';
    
    // UI Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileInfo = document.getElementById('file-info');
    const fileNameSpan = document.getElementById('file-name');
    const statRowsSpan = document.getElementById('stat-rows');
    const statColsSpan = document.getElementById('stat-cols');
    const changeFileBtn = document.getElementById('change-file-btn');
    const tableContainer = document.getElementById('table-container');
    
    const queryForm = document.getElementById('query-form');
    const queryInput = document.getElementById('query-input');
    const submitQueryBtn = document.getElementById('submit-query-btn');
    
    const agentStatusCard = document.getElementById('agent-status-card');
    const hitlPanel = document.getElementById('hitl-panel');
    const finalResponseCard = document.getElementById('final-response-card');
    
    const hitlQuery = document.getElementById('hitl-query');
    const hitlExtracted = document.getElementById('hitl-extracted');
    const hitlResponse = document.getElementById('hitl-response');
    const hitlErrorBlock = document.getElementById('hitl-error-block');
    const hitlError = document.getElementById('hitl-error');
    
    const approveBtn = document.getElementById('approve-btn');
    const rejectBtn = document.getElementById('reject-btn');
    
    const feedbackContainer = document.getElementById('feedback-container');
    const feedbackInput = document.getElementById('feedback-input');
    const submitFeedbackBtn = document.getElementById('submit-feedback-btn');
    const cancelFeedbackBtn = document.getElementById('cancel-feedback-btn');
    
    const finalResponseText = document.getElementById('final-response-text');
    const copyBtn = document.getElementById('copy-btn');

    // Drag and Drop Logic
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            handleFileUpload(files[0]);
        }
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });

    changeFileBtn.addEventListener('click', () => {
        resetApp();
    });

    // File Upload Handler
    async function handleFileUpload(file) {
        if (!file.name.endsWith('.csv')) {
            alert('Por favor, carregue um arquivo CSV válido.');
            return;
        }

        dropZone.innerHTML = `<div class="placeholder-text">Uploading and parsing dataset...</div>`;
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Upload failed');
            }

            const data = await response.json();
            
            // Set current file info
            currentFilename = data.filename;
            fileNameSpan.textContent = data.filename;
            statRowsSpan.textContent = data.num_rows.toLocaleString();
            statColsSpan.textContent = data.num_columns.toLocaleString();
            
            // Toggle visibility
            dropZone.classList.add('hidden');
            fileInfo.classList.remove('hidden');
            
            // Enable Query Form
            queryForm.classList.remove('disabled');
            queryInput.disabled = false;
            submitQueryBtn.disabled = false;

            // Render Preview Table
            renderPreviewTable(data.preview, data.columns);

        } catch (error) {
            alert(`Error loading CSV: ${error.message}`);
            resetApp();
        }
    }

    function renderPreviewTable(records, columns) {
        if (!records || !records.length) {
            tableContainer.innerHTML = '<p class="placeholder-text">No records found in CSV.</p>';
            return;
        }

        let html = '<table><thead><tr>';
        columns.forEach(col => {
            html += `<th>${escapeHtml(col)}</th>`;
        });
        html += '</tr></thead><tbody>';

        records.forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                html += `<td>${escapeHtml(row[col] !== undefined ? row[col] : '')}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        tableContainer.innerHTML = html;
    }

    // Reset Application State
    function resetApp() {
        currentFilename = '';
        dropZone.classList.remove('hidden');
        dropZone.innerHTML = `
            <svg class="upload-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="drop-text">Drag and drop your CSV file here, or <span class="highlight">browse</span></p>
            <input type="file" id="file-input" accept=".csv" class="file-input">
        `;
        
        // Re-bind file input change event
        document.getElementById('file-input').addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFileUpload(e.target.files[0]);
            }
        });

        fileInfo.classList.add('hidden');
        tableContainer.innerHTML = '<p class="placeholder-text">Upload a CSV dataset to preview records here</p>';
        
        queryForm.classList.add('disabled');
        queryInput.value = '';
        queryInput.disabled = true;
        submitQueryBtn.disabled = true;
        
        agentStatusCard.classList.add('hidden');
        hitlPanel.classList.add('hidden');
        if (hitlErrorBlock) hitlErrorBlock.classList.add('hidden');
        finalResponseCard.classList.add('hidden');
        
        resetTimeline();
    }

    // Submit Query Handler
    queryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;

        // Reset UI Panels
        hitlPanel.classList.add('hidden');
        finalResponseCard.classList.add('hidden');
        feedbackContainer.classList.add('hidden');
        feedbackInput.value = '';
        
        agentStatusCard.classList.remove('hidden');
        resetTimeline();

        // Run execution timeline steps
        updateTimelineStep('step-parse', 'active');
        
        try {
            submitQueryBtn.disabled = true;
            submitQueryBtn.textContent = 'Analisando...';
            
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    csv_filename: currentFilename,
                    thread_id: threadId
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Query run failed');
            }

            const result = await response.json();
            handleWorkflowResponse(result);

        } catch (error) {
            alert(`Query Execution Failed: ${error.message}`);
            updateTimelineStep('step-parse', 'error');
        } finally {
            submitQueryBtn.disabled = false;
            submitQueryBtn.textContent = 'Analisar Dados com IA';
        }
    });

    // Handle Workflow state results
    function handleWorkflowResponse(result) {
        const state = result.state;
        
        // Parse CSV
        updateTimelineStep('step-parse', 'completed');

        // Understand Node
        if (state.pandas_query) {
            updateTimelineStep('step-understand', 'completed');
        } else if (state.error) {
            updateTimelineStep('step-understand', 'error');
        }

        // Extract Node
        if (state.extracted_data) {
            updateTimelineStep('step-extract', 'completed');
        } else if (state.error) {
            updateTimelineStep('step-extract', 'error');
        }

        // Draft Response Node
        if (state.response) {
            updateTimelineStep('step-draft', 'completed');
        } else if (state.error) {
            updateTimelineStep('step-draft', 'error');
        }

        // Human Validation Node
        if (result.is_paused) {
            updateTimelineStep('step-validation', 'active');
            
            // Show HITL card with code or errors
            hitlQuery.textContent = state.pandas_query || '// Nenhuma query foi gerada';
            hitlExtracted.textContent = state.extracted_data || 'Nenhum dado retornado.';
            
            if (state.error) {
                hitlError.textContent = state.error;
                hitlErrorBlock.classList.remove('hidden');
                hitlResponse.innerHTML = renderMarkdown('Não foi possível gerar um rascunho de resposta porque ocorreu um erro na execução do código.');
            } else {
                hitlErrorBlock.classList.add('hidden');
                hitlResponse.innerHTML = renderMarkdown(state.response || 'Nenhum rascunho de resposta gerado.');
            }
            
            hitlPanel.classList.remove('hidden');
            hitlPanel.scrollIntoView({ behavior: 'smooth' });
        } else {
            updateTimelineStep('step-validation', 'completed');
            showFinalResponse(state.response || state.error);
        }
    }

    // HITL: Approve
    approveBtn.addEventListener('click', async () => {
        try {
            toggleHitlButtons(true);
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    thread_id: threadId,
                    approved: true
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Approval failed');
            }

            const result = await response.json();
            updateTimelineStep('step-validation', 'completed');
            hitlPanel.classList.add('hidden');
            showFinalResponse(result.state.response);

        } catch (error) {
            alert(`Approval Failed: ${error.message}`);
        } finally {
            toggleHitlButtons(false);
        }
    });

    // HITL: Reject - Expose feedback inputs
    rejectBtn.addEventListener('click', () => {
        feedbackContainer.classList.remove('hidden');
        feedbackContainer.scrollIntoView({ behavior: 'smooth' });
    });

    cancelFeedbackBtn.addEventListener('click', () => {
        feedbackContainer.classList.add('hidden');
        feedbackInput.value = '';
    });

    // HITL: Submit Rejection Feedback
    submitFeedbackBtn.addEventListener('click', async () => {
        const feedback = feedbackInput.value.trim();
        if (!feedback) {
            alert('Please enter refinement details or feedback before submitting.');
            return;
        }

        try {
            toggleHitlButtons(true);
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    thread_id: threadId,
                    approved: false,
                    feedback: feedback
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Rejection failed');
            }

            // Clean up and restart timeline
            feedbackContainer.classList.add('hidden');
            feedbackInput.value = '';
            hitlPanel.classList.add('hidden');
            
            resetTimeline();
            updateTimelineStep('step-parse', 'completed');
            updateTimelineStep('step-understand', 'active');
            
            const result = await response.json();
            handleWorkflowResponse(result);

        } catch (error) {
            alert(`Feedback Submission Failed: ${error.message}`);
        } finally {
            toggleHitlButtons(false);
        }
    });

    // Markdown parser helper using marked library
    function renderMarkdown(text) {
        if (!text) return '';
        if (typeof marked !== 'undefined') {
            return marked.parse(text);
        }
        // Fallback: simple newline replacement
        return escapeHtml(text).replace(/\n/g, '<br>');
    }

    let lastResponseText = '';

    // Display Final Answer Card
    function showFinalResponse(responseText) {
        lastResponseText = responseText;
        finalResponseText.innerHTML = renderMarkdown(responseText);
        finalResponseCard.classList.remove('hidden');
        finalResponseCard.scrollIntoView({ behavior: 'smooth' });
    }

    // Copy Response text
    copyBtn.addEventListener('click', () => {
        const textToCopy = lastResponseText || finalResponseText.textContent;
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                copyBtn.textContent = 'Copiado!';
                setTimeout(() => {
                    copyBtn.textContent = 'Copiar para área de transferência';
                }, 2000);
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);
            });
    });

    // Timeline helpers
    function resetTimeline() {
        ['step-parse', 'step-understand', 'step-extract', 'step-draft', 'step-validation'].forEach(id => {
            const el = document.getElementById(id);
            el.className = 'timeline-step';
        });
    }

    function updateTimelineStep(stepId, statusClass) {
        const el = document.getElementById(stepId);
        if (el) {
            el.className = `timeline-step ${statusClass}`;
        }
    }

    function toggleHitlButtons(disabled) {
        approveBtn.disabled = disabled;
        rejectBtn.disabled = disabled;
        submitFeedbackBtn.disabled = disabled;
        cancelFeedbackBtn.disabled = disabled;
    }

    // HTML sanitizer helper
    function escapeHtml(unsafe) {
        if (unsafe === null || unsafe === undefined) return '';
        return String(unsafe)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
