// ====================================================================
        // STATE
        // ====================================================================
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        let timerInterval = null;
        let startTime = null;
        
        // Text storage
        let rawTranscription = '';
        let textVariants = {
            original: '',
            english: '',
            enhanced: ''
        };
        let generatedVariants = {
            prompt: '',
            ticket: '',
            spec: ''
        };
        let currentOriginalTab = 'original';
        let currentGeneratedTab = 'prompt';
        let currentSearchText = '';  // For search by generated
        let contextData = [];  // Store full context for checkboxes
        
        // Elements
        const recordBtn = document.getElementById('recordBtn');
        const recordStatus = document.getElementById('recordStatus');
        const recordTimer = document.getElementById('recordTimer');
        const editableText = document.getElementById('editableText');
        const loading = document.getElementById('loading');
        const loadingText = document.getElementById('loadingText');
        const outputCard = document.getElementById('outputCard');
        const generatedCard = document.getElementById('generatedCard');
        const contextCard = document.getElementById('contextCard');
        const actionBtns = document.querySelectorAll('.action-btn[data-format]');
        
        // ====================================================================
        // RECORDING
        // ====================================================================
        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    await transcribeAudio(audioBlob);
                };
                
                mediaRecorder.start(1000);
                isRecording = true;
                recordBtn.classList.add('recording');
                recordBtn.textContent = '⏹️';
                recordStatus.textContent = 'Recording... Click to stop';
                
                startTime = Date.now();
                timerInterval = setInterval(updateTimer, 100);
            } catch (err) {
                recordStatus.textContent = 'Error: ' + err.message;
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(t => t.stop());
                isRecording = false;
                recordBtn.classList.remove('recording');
                recordBtn.textContent = '🎙️';
                clearInterval(timerInterval);
            }
        }
        
        function updateTimer() {
            const elapsed = Date.now() - startTime;
            const seconds = Math.floor(elapsed / 1000);
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            recordTimer.textContent = String(minutes).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
        }
        
        recordBtn.addEventListener('click', () => {
            if (isRecording) stopRecording();
            else startRecording();
        });
        
        // Sync editable text with rawTranscription AND enable buttons
        editableText.addEventListener('input', () => {
            rawTranscription = editableText.value;
            textVariants.original = rawTranscription;
            currentSearchText = rawTranscription;  // Update search text
            
            // Enable all buttons when user types
            if (rawTranscription.trim().length > 0) {
                actionBtns.forEach(btn => btn.disabled = false);
                document.getElementById('searchBtn').disabled = false;
                document.getElementById('totalRecallBtn').disabled = false;
            }
        });
        
        // ====================================================================
        // TRANSCRIPTION
        // ====================================================================
        async function transcribeAudio(audioBlob) {
            showLoading('Transcribing audio...');
            
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            
            try {
                const response = await fetch('/transcribe', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    recordStatus.textContent = 'Transcription complete!';
                    rawTranscription = data.text;
                    textVariants.original = data.text;
                    editableText.value = data.text;
                    currentSearchText = data.text;
                    
                    // Enable buttons
                    actionBtns.forEach(btn => btn.disabled = false);
                    document.getElementById('searchBtn').disabled = false;
                    document.getElementById('totalRecallBtn').disabled = false;
                    
                    // Auto-enhance
                    await processText('enhanced');
                } else {
                    recordStatus.textContent = 'Error: ' + data.error;
                }
            } catch (err) {
                recordStatus.textContent = 'Network error: ' + err.message;
            }
            
            hideLoading();
        }
        
        // ====================================================================
        // PROCESSING
        // ====================================================================
        async function processText(formatType) {
            if (!rawTranscription && !editableText.value) return;
            
            const textToProcess = editableText.value || rawTranscription;
            showLoading(`Processing (${formatType})...`);
            
            // Get selected context files from Related Content panel
            const selectedContext = getSelectedContext();
            
            // Include Tree Viewer scope data for enhanced context
            const scopeData = {
                centralFiles: searchScope.centralFiles,  // User-marked as important (Human-in-the-Loop)
                externalFiles: searchScope.externalFiles.map(f => ({
                    name: f.name,
                    content: f.content,
                    source: 'external'
                })),
                excludedDirs: searchScope.excludedDirs
            };
            
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: textToProcess,
                        format: formatType,
                        search_context: true,
                        context_files: selectedContext,
                        scope: scopeData  // New: Tree Viewer scope with source attribution
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Store in appropriate variant
                    if (['original', 'english', 'enhanced'].includes(formatType)) {
                        textVariants.original = rawTranscription;
                        textVariants.english = data.original_en || '';
                        textVariants.enhanced = data.enhanced || '';
                        outputCard.style.display = 'block';
                        updateOriginalDisplay();
                    }
                    
                    if (['prompt', 'ticket', 'spec'].includes(formatType)) {
                        generatedVariants[formatType] = data.formatted || '';
                        currentSearchText = data.formatted || textToProcess;
                        generatedCard.style.display = 'block';
                        currentGeneratedTab = formatType;
                        updateGeneratedDisplay();
                        markTabHasContent(formatType);
                    } else {
                        // Enhanced also updates original panel
                        outputCard.style.display = 'block';
                        updateOriginalDisplay();
                    }
                    
                    // Update context
                    if (data.context && data.context.length > 0) {
                        displayContext(data.context);
                    }
                    
                    document.getElementById('processTime').textContent = 
                        `Processed in ${data.processing_time_sec.toFixed(2)}s`;
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (err) {
                alert('Network error: ' + err.message);
            }
            
            hideLoading();
        }
        
        // ====================================================================
        // DISPLAY FUNCTIONS
        // ====================================================================
        function updateOriginalDisplay() {
            const text = textVariants[currentOriginalTab] || '';
            document.getElementById('originalText').textContent = text;
            
            // Update tab active state
            document.querySelectorAll('#originalTabs .tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tab === currentOriginalTab);
            });
        }
        
        function updateGeneratedDisplay() {
            const text = generatedVariants[currentGeneratedTab] || '';
            document.getElementById('generatedText').textContent = text || '(Not generated yet)';
            
            // Update tab active state
            document.querySelectorAll('#generatedTabs .tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tab === currentGeneratedTab);
            });
        }
        
        function markTabHasContent(tabName) {
            const tab = document.querySelector(`#generatedTabs .tab-btn[data-tab="${tabName}"]`);
            if (tab) tab.classList.add('has-content');
        }
        
        function escapeHtml(text) {
            if (!text) return '';
            return text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }
        
        let lastSearchSource = 'embedding';  // 'total_recall' or 'embedding'
        
        function displayContext(results, source = 'embedding') {
            contextData = results;
            lastSearchSource = source;
            contextCard.style.display = 'block';
            document.getElementById('contextCount').textContent = `${results.length} docs`;
            
            // Source label styling
            const sourceLabel = source === 'total_recall' 
                ? '<span style="color: #22c55e; font-size: 0.7rem; margin-left: 0.5rem;">🧠 Total Recall</span>'
                : '<span style="color: #60a5fa; font-size: 0.7rem; margin-left: 0.5rem;">📊 Embeddings</span>';
            
            document.getElementById('contextResults').innerHTML = results.map((r, i) => {
                // After Total Recall, embedding results are unchecked by default
                const isChecked = source === 'total_recall' || r.source === 'total_recall' ? 'checked' : '';
                const itemSource = r.source || source;
                const sourceStyle = itemSource === 'total_recall' 
                    ? 'border-left-color: #22c55e;' 
                    : 'border-left-color: #60a5fa;';
                
                return `
                <div class="context-item" data-index="${i}" data-source="${itemSource}" style="${sourceStyle}">
                    <div class="context-item-header">
                        <input type="checkbox" class="context-checkbox" ${isChecked} data-path="${escapeHtml(r.file_path)}">
                        <span class="context-file" onclick="openFile('${escapeHtml(r.file_path)}')">${escapeHtml(r.file_path)}</span>
                        <span class="context-score">${(r.score * 100).toFixed(0)}%</span>
                        <button class="expand-btn" onclick="toggleExpand(${i})">▼</button>
                    </div>
                    <div class="context-excerpt">${escapeHtml(r.excerpt || '')}</div>
                    <div class="context-full" id="full-${i}">${escapeHtml(r.full_content || r.excerpt || '')}</div>
                </div>
            `}).join('');
        }
        
        function toggleExpand(index) {
            const fullEl = document.getElementById(`full-${index}`);
            fullEl.classList.toggle('expanded');
        }
        
        function openFile(path) {
            // Try to open file in new tab
            window.open(`file://${path}`, '_blank');
        }
        
        function getSelectedContext() {
            const checkboxes = document.querySelectorAll('.context-checkbox:checked');
            return Array.from(checkboxes).map(cb => cb.dataset.path);
        }
        
        function selectAllContext(checked) {
            document.querySelectorAll('.context-checkbox').forEach(cb => cb.checked = checked);
        }
        
        function selectTopN(n) {
            // Select only first N checkboxes, uncheck rest
            const checkboxes = document.querySelectorAll('.context-checkbox');
            checkboxes.forEach((cb, i) => {
                cb.checked = i < n;
            });
        }
        
        // Fetch summaries for search results
        async function fetchSummaries(filePaths) {
            try {
                const response = await fetch('/api/get_summaries', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_paths: filePaths })
                });
                
                const data = await response.json();
                if (data.success && data.summaries) {
                    // Update context items with summaries
                    Object.entries(data.summaries).forEach(([path, info]) => {
                        const item = document.querySelector(`[data-path="${path}"] .context-summary`);
                        if (item && info.summary) {
                            item.textContent = info.summary;
                            item.style.fontStyle = 'italic';
                            item.style.color = 'var(--text-secondary)';
                        }
                    });
                    console.log(`[DEBUG] Loaded ${Object.keys(data.summaries).length} summaries`);
                }
            } catch (err) {
                console.error('Summary fetch error:', err);
            }
        }
        
        function copyText(elementId) {
            const text = document.getElementById(elementId).textContent;
            navigator.clipboard.writeText(text).then(() => {
                // Visual feedback handled by button
            });
        }
        
        // ====================================================================
        // HYPOTHESIS FUNCTIONS
        // ====================================================================
        let hypothesesData = [];
        let hypothesisMapping = {};
        
        async function generateHypotheses() {
            const query = currentSearchText || editableText.value || rawTranscription;
            if (!query) {
                alert('Enter text first');
                return;
            }
            
            // Build context from available sources (not just Total Recall)
            let files = [];
            
            // 1. Use Total Recall results if available
            if (contextData && contextData.length > 0) {
                files = contextData.map(f => ({
                    file_path: f.file_path,
                    excerpt: f.excerpt || ''
                }));
            }
            // 2. Otherwise use centralFiles from Tree
            else if (searchScope.centralFiles.length > 0) {
                files = searchScope.centralFiles.map(f => ({
                    file_path: f,
                    excerpt: '[User selected]'
                }));
            }
            // 3. Otherwise use external files
            else if (searchScope.externalFiles.length > 0) {
                files = searchScope.externalFiles.map(f => ({
                    file_path: f.name,
                    excerpt: f.content?.substring(0, 200) || ''
                }));
            }
            // 4. Can work with no context too
            
            showLoading('💡 Generating hypotheses...');
            
            try {
                const response = await fetch('/hypotheses', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: query,
                        files: files
                    })
                });
                
                const data = await response.json();
                console.log('Hypotheses response:', data);
                
                if (data.success && data.hypotheses) {
                    hypothesesData = data.hypotheses;
                    displayHypotheses(data.hypotheses);
                } else {
                    alert('Error: ' + (data.error || 'Failed to generate hypotheses'));
                    if (data.raw_response) console.log('Raw:', data.raw_response);
                }
            } catch (err) {
                console.error('Hypotheses error:', err);
                alert('Network error: ' + err.message);
            }
            
            hideLoading();
        }
        
        function displayHypotheses(hypotheses) {
            const card = document.getElementById('hypothesesCard');
            card.style.display = 'block';
            document.getElementById('hypothesesCount').textContent = `${hypotheses.length} hypotheses`;
            
            document.getElementById('hypothesesResults').innerHTML = hypotheses.map((h, i) => `
                <div class="hypothesis-item" data-index="${i}" onclick="selectHypothesis(${i})">
                    <div class="hypothesis-header">
                        <input type="checkbox" class="hypothesis-checkbox" data-id="${h.id}" onchange="onHypothesisChange(${i})" onclick="event.stopPropagation()">
                        <span class="hypothesis-title">H${h.id}: ${escapeHtml(h.title)}</span>
                        <span class="hypothesis-confidence">${(h.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div class="hypothesis-description">${escapeHtml(h.description)}</div>
                    <div class="hypothesis-files">Files: ${h.file_indices ? h.file_indices.join(', ') : 'none'}</div>
                </div>
            `).join('');
        }
        
        function selectHypothesis(index) {
            const item = document.querySelectorAll('.hypothesis-item')[index];
            const checkbox = item.querySelector('.hypothesis-checkbox');
            checkbox.checked = !checkbox.checked;
            onHypothesisChange(index);
        }
        
        function onHypothesisChange(index) {
            const item = document.querySelectorAll('.hypothesis-item')[index];
            const checkbox = item.querySelector('.hypothesis-checkbox');
            item.classList.toggle('selected', checkbox.checked);
            
            // Update file checkboxes based on selected hypotheses
            updateFileCheckboxes();
        }
        
        function updateFileCheckboxes() {
            // Get all selected hypothesis file indices
            const selectedIndices = new Set();
            
            document.querySelectorAll('.hypothesis-checkbox:checked').forEach(cb => {
                const hIndex = parseInt(cb.closest('.hypothesis-item').dataset.index);
                const hypothesis = hypothesesData[hIndex];
                if (hypothesis && hypothesis.file_indices) {
                    hypothesis.file_indices.forEach(fi => {
                        selectedIndices.add(fi - 1);  // Convert 1-indexed to 0-indexed
                    });
                }
            });
            
            // Update file checkboxes
            document.querySelectorAll('.context-checkbox').forEach((cb, i) => {
                if (selectedIndices.size > 0) {
                    cb.checked = selectedIndices.has(i);
                }
            });
        }
        
        // Generate Hypotheses button handler
        document.getElementById('generateHypothesesBtn').addEventListener('click', generateHypotheses);
        
        // Apply Hypotheses button handler
        document.getElementById('applyHypothesesBtn').addEventListener('click', () => {
            const selected = Array.from(document.querySelectorAll('.hypothesis-checkbox:checked'))
                .map(cb => hypothesesData[parseInt(cb.closest('.hypothesis-item').dataset.index)]);
            
            if (selected.length === 0) {
                alert('Select at least one hypothesis');
                return;
            }
            
            console.log('Applied hypotheses:', selected);
            
            // Show selected file count
            const checkedFiles = document.querySelectorAll('.context-checkbox:checked').length;
            document.getElementById('processTime').textContent = 
                `${selected.length} hypotheses → ${checkedFiles} files selected`;
        });
        
        // ====================================================================
        // EVENT HANDLERS
        // ====================================================================
        
        // Original tabs
        document.querySelectorAll('#originalTabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                currentOriginalTab = btn.dataset.tab;
                updateOriginalDisplay();
            });
        });
        
        // Generated tabs
        document.querySelectorAll('#generatedTabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                currentGeneratedTab = btn.dataset.tab;
                updateGeneratedDisplay();
                // Update search text to this generated content
                if (generatedVariants[currentGeneratedTab]) {
                    currentSearchText = generatedVariants[currentGeneratedTab];
                }
            });
        });
        
        // Action buttons
        actionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const format = btn.dataset.format;
                if (format) processText(format);
            });
        });
        
        // Search button - uses integrated multi-channel search
        document.getElementById('searchBtn').addEventListener('click', async () => {
            // Determine query based on active context:
            // If editing spec/ticket/prompt, search around that content
            let query = '';
            let activeContext = '';
            
            // Check if generated content exists and use it
            if (currentGeneratedTab && generatedVariants[currentGeneratedTab]) {
                query = generatedVariants[currentGeneratedTab];
                activeContext = currentGeneratedTab;
                console.log('[DEBUG] Search using active tab:', activeContext);
            } else {
                query = currentSearchText || editableText.value || rawTranscription;
            }
            
            if (!query) return;
            
            showLoading(`🔍 Integrated search ${activeContext ? '(around ' + activeContext + ')' : ''}...`);
            
            // Get selected files from Tree Viewer for Human-in-the-Loop context
            const selectedFiles = searchScope.centralFiles;
            
            try {
                const response = await fetch('/api/search_integrated', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        query: query, 
                        top_k: 100,
                        selected_files: selectedFiles,
                        active_context: activeContext  // Tell backend what we're editing
                    })
                });
                
                const data = await response.json();
                if (data.results) {
                    displayContext(data.results, 'integrated');
                    // Show Total Recall Lite button for LLM filtering
                    document.getElementById('totalRecallLiteBtn').style.display = 'inline-flex';
                    console.log('[DEBUG] Search used channels:', data.channels_used);
                    
                    // Auto-fetch summaries for top results
                    const topPaths = data.results.slice(0, 10).map(r => r.file_path);
                    if (topPaths.length > 0) {
                        fetchSummaries(topPaths);
                    }
                }
            } catch (err) {
                console.error('Search error:', err);
            }
            
            hideLoading();
        });
        
        // Re-index button - rebuild embeddings
        document.getElementById('reindexBtn').addEventListener('click', async () => {
            if (!confirm('Rebuild embeddings index? This may take 1-2 minutes.')) return;
            
            showLoading('🔄 Re-indexing project documentation...');
            
            try {
                const response = await fetch('/api/reindex', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ incremental: true })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('✅ Index rebuilt successfully!');
                } else {
                    alert('❌ Re-index error: ' + data.error);
                }
            } catch (err) {
                console.error('Re-index error:', err);
                alert('❌ Re-index failed: ' + err.message);
            }
            
            hideLoading();
        });
        
        // Total Recall button
        document.getElementById('totalRecallBtn').addEventListener('click', async () => {
            const query = currentSearchText || editableText.value || rawTranscription;
            if (!query) {
                alert('Please enter or record text first');
                return;
            }
            
            showLoading('🧠 Total Recall: Scanning files with scope...');
            console.log('Total Recall started with query:', query.substring(0, 100));
            console.log('Search scope:', searchScope);
            
            try {
                const response = await fetch('/total_recall', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        query: query,
                        excluded_dirs: searchScope.excludedDirs,
                        central_files: searchScope.centralFiles,
                        external_files: searchScope.externalFiles.map(f => f.path)
                    })
                });
                
                const data = await response.json();
                console.log('Total Recall response:', data);
                
                if (data.success && data.results) {
                    console.log('Total Recall found', data.results.length, 'relevant files');
                    
                    // Ensure central files are checked and never auto-unchecked
                    displayContext(data.results, 'total_recall');
                    
                    // Mark central files as checked after display
                    setTimeout(() => {
                        searchScope.centralFiles.forEach(cf => {
                            const checkbox = document.querySelector(`.context-checkbox[data-path="${cf}"]`);
                            if (checkbox) checkbox.checked = true;
                        });
                    }, 100);
                    
                    // Show Generate Hypotheses button
                    document.getElementById('generateHypothesesBtn').style.display = 'block';
                    document.getElementById('processTime').textContent = 
                        `Total Recall: ${data.files_relevant}/${data.files_scanned} files in ${data.duration_sec.toFixed(1)}s`;
                } else if (data.error) {
                    alert('Total Recall error: ' + data.error);
                } else {
                    console.log('No results found');
                    displayContext([]);
                }
            } catch (err) {
                console.error('Total Recall error:', err);
                alert('Network error: ' + err.message);
            }
            
            hideLoading();
        });
        
        // Total Recall Lite button - LLM filters the 200 embedding results
        document.getElementById('totalRecallLiteBtn').addEventListener('click', async () => {
            if (!contextData || contextData.length === 0) {
                alert('First run Search to get embedding results');
                return;
            }
            
            const query = currentSearchText || editableText.value || rawTranscription;
            if (!query) {
                alert('Please enter or record text first');
                return;
            }
            
            showLoading(`🧠 Total Recall Lite: Checking ${contextData.length} files with LLM...`);
            console.log('Total Recall Lite started for', contextData.length, 'files');
            
            try {
                // Send current context files for LLM relevance check
                const filesToCheck = contextData.map(r => ({
                    file_path: r.file_path,
                    excerpt: r.excerpt,
                    score: r.score
                }));
                
                const response = await fetch('/total_recall_lite', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        query: query, 
                        files: filesToCheck  // Send files to filter
                    })
                });
                
                const data = await response.json();
                console.log('Total Recall Lite response:', data);
                
                if (data.success && data.results) {
                    console.log('Total Recall Lite found', data.relevant_count, 'relevant files');
                    
                    // Update checkboxes based on LLM relevance
                    const relevantPaths = new Set(data.results.map(r => r.file_path));
                    document.querySelectorAll('.context-checkbox').forEach(cb => {
                        const path = cb.dataset.path;
                        cb.checked = relevantPaths.has(path);
                        // Update border color
                        const item = cb.closest('.context-item');
                        item.style.borderLeftColor = relevantPaths.has(path) ? '#22c55e' : '#60a5fa';
                    });
                    
                    document.getElementById('generateHypothesesBtn').style.display = 'inline-flex';
                    document.getElementById('processTime').textContent = 
                        `Total Recall Lite: ${data.relevant_count}/${data.files_checked} relevant in ${data.duration_sec.toFixed(1)}s`;
                } else if (data.error) {
                    alert('Total Recall Lite error: ' + data.error);
                }
            } catch (err) {
                console.error('Total Recall Lite error:', err);
                alert('Network error: ' + err.message);
            }
            
            hideLoading();
        });
        
        // Display context with selective pre-selection (for Memory Lite)
        function displayContextWithSelection(results, selectTopN) {
            contextData = results;
            lastSearchSource = 'memory_lite';
            contextCard.style.display = 'block';
            document.getElementById('contextCount').textContent = `${results.length} docs`;
            
            document.getElementById('contextResults').innerHTML = results.map((r, i) => {
                // Only first selectTopN are checked by default
                const isChecked = i < selectTopN ? 'checked' : '';
                const borderColor = i < selectTopN ? '#22c55e' : '#60a5fa';  // Green for selected, blue for others
                
                return `
                <div class="context-item" data-index="${i}" style="border-left-color: ${borderColor};">
                    <div class="context-item-header">
                        <input type="checkbox" class="context-checkbox" ${isChecked} data-path="${escapeHtml(r.file_path)}">
                        <span class="context-file" onclick="openFile('${escapeHtml(r.file_path)}')">${escapeHtml(r.file_path)}</span>
                        <span class="context-score">${(r.score * 100).toFixed(0)}%</span>
                        <button class="expand-btn" onclick="toggleExpand(${i})">▼</button>
                    </div>
                    <div class="context-excerpt">${escapeHtml(r.excerpt || '')}</div>
                    <div class="context-full" id="full-${i}">${escapeHtml(r.full_content || r.excerpt || '')}</div>
                </div>
            `}).join('');
        }
        // ====================================================================
        // TREE VIEWER FUNCTIONS
        // ====================================================================
        let projectTree = null;
        let expandedDirs = new Set();
        let searchScope = {
            includedDirs: [],
            excludedDirs: ['.'],  // By default ALL unchecked (exclude root = exclude all)
            centralFiles: [],     // Never auto-uncheck!
            externalFiles: []
        };
        
        // Fetch and display project tree on load
        async function fetchProjectTree() {
            try {
                const response = await fetch('/api/project_tree');
                const data = await response.json();
                if (data.success && data.tree) {
                    projectTree = data.tree;
                    document.getElementById('treeContainer').innerHTML = renderTree(projectTree);
                } else {
                    document.getElementById('treeContainer').innerHTML = 
                        '<div style="color: var(--warning);">No tree data</div>';
                }
            } catch (err) {
                console.error('Tree fetch error:', err);
                document.getElementById('treeContainer').innerHTML = 
                    '<div style="color: var(--error);">Error loading tree</div>';
            }
        }
        
        function renderTree(node, depth = 0) {
            if (!node || depth > 5) return '';
            
            const isDir = node.type === 'dir';
            const isExpanded = expandedDirs.has(node.path);
            const isCentral = searchScope.centralFiles.includes(node.path);
            const isIncluded = searchScope.excludedDirs.length === 0 || 
                              !searchScope.excludedDirs.some(d => node.path.startsWith(d));
            
            let html = `
            <div class="tree-node depth-${depth}" data-path="${escapeHtml(node.path)}" data-type="${node.type}">
                ${isDir ? `<span class="tree-toggle" onclick="toggleDirExpand('${escapeHtml(node.path)}')">${isExpanded ? '▼' : '▶'}</span>` : '<span class="tree-toggle"></span>'}
                <input type="checkbox" class="tree-checkbox" ${isIncluded ? 'checked' : ''} 
                       onchange="toggleTreeInclude('${escapeHtml(node.path)}', '${node.type}', this.checked)">
                <span class="tree-star ${isCentral ? 'central' : ''}" onclick="toggleCentralFile('${escapeHtml(node.path)}')">⭐</span>
                <span class="tree-icon">${isDir ? '📁' : '📄'}</span>
                <span class="tree-name ${isDir ? 'tree-dir' : 'tree-file'}">${escapeHtml(node.name)}</span>
                ${isDir && node.file_count ? `<span style="font-size:0.7rem;color:var(--text-secondary)">(${node.file_count})</span>` : ''}
            </div>`;
            
            // Render children if expanded
            if (isDir && isExpanded && node.children) {
                for (const child of node.children) {
                    html += renderTree(child, depth + 1);
                }
            }
            
            return html;
        }
        
        function refreshTreeUI() {
            if (projectTree) {
                document.getElementById('treeContainer').innerHTML = renderTree(projectTree);
            }
        }
        
        function toggleDirExpand(path) {
            if (expandedDirs.has(path)) {
                expandedDirs.delete(path);
            } else {
                expandedDirs.add(path);
            }
            refreshTreeUI();
        }
        
        function toggleTreeInclude(path, type, isChecked) {
            console.log('[DEBUG] toggleTreeInclude:', path, type, isChecked);
            
            // Helper: collect all descendant paths from tree
            function collectAllPaths(node, paths = []) {
                paths.push(node.path);
                if (node.children) {
                    node.children.forEach(child => collectAllPaths(child, paths));
                }
                return paths;
            }
            
            // Find the node in tree by path
            function findNode(node, targetPath) {
                if (node.path === targetPath) return node;
                if (node.children) {
                    for (const child of node.children) {
                        const found = findNode(child, targetPath);
                        if (found) return found;
                    }
                }
                return null;
            }
            
            // Get all paths to affect (this node + all descendants)
            const node = findNode(projectTree, path);
            const pathsToAffect = node ? collectAllPaths(node) : [path];
            console.log('[DEBUG] Paths to affect:', pathsToAffect.length);
            
            if (!isChecked) {
                // Add all paths to excluded
                pathsToAffect.forEach(p => {
                    if (!searchScope.excludedDirs.includes(p)) {
                        searchScope.excludedDirs.push(p);
                    }
                });
            } else {
                // Remove all paths from excluded
                searchScope.excludedDirs = searchScope.excludedDirs.filter(
                    d => !pathsToAffect.includes(d)
                );
            }
            
            refreshTreeUI();
        }
        
        function toggleCentralFile(path) {
            const idx = searchScope.centralFiles.indexOf(path);
            if (idx >= 0) {
                searchScope.centralFiles.splice(idx, 1);
            } else {
                searchScope.centralFiles.push(path);
            }
            refreshTreeUI();
        }
        
        function selectAllTree(checked) {
            console.log('[DEBUG] selectAllTree:', checked);
            if (checked) {
                // Clear all exclusions = everything included
                searchScope.excludedDirs = [];
            } else {
                // Collect ALL paths from tree and exclude them
                function collectAllPaths(node, paths = []) {
                    paths.push(node.path);
                    if (node.children) {
                        node.children.forEach(child => collectAllPaths(child, paths));
                    }
                    return paths;
                }
                if (projectTree) {
                    searchScope.excludedDirs = collectAllPaths(projectTree);
                }
            }
            refreshTreeUI();
        }
        
        function toggleTreeCollapse() {
            if (expandedDirs.size > 0) {
                expandedDirs.clear();
            } else {
                // Expand first 2 levels
                function expandNode(node, depth) {
                    if (depth > 1 || node.type !== 'dir') return;
                    expandedDirs.add(node.path);
                    if (node.children) {
                        node.children.forEach(c => expandNode(c, depth + 1));
                    }
                }
                if (projectTree) expandNode(projectTree, 0);
            }
            refreshTreeUI();
        }
        
        async function smartPreselect() {
            const query = editableText.value || rawTranscription;
            if (!query) {
                alert('Enter a query first for smart selection');
                return;
            }
            
            showLoading('🤖 Smart preselect...');
            try {
                const response = await fetch('/api/smart_preselect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                const data = await response.json();
                
                if (data.success && data.suggestions) {
                    const suggestions = data.suggestions;
                    // Clear current selections (but NOT central files!)
                    searchScope.excludedDirs = [];
                    
                    // Add suggested files as central
                    suggestions.suggested_files?.forEach(f => {
                        if (!searchScope.centralFiles.includes(f)) {
                            searchScope.centralFiles.push(f);
                        }
                    });
                    
                    refreshTreeUI();
                    document.getElementById('processTime').textContent = 
                        `Smart: ${suggestions.suggested_dirs?.length || 0} dirs, ${suggestions.suggested_files?.length || 0} files`;
                }
            } catch (err) {
                console.error('Smart preselect error:', err);
            }
            hideLoading();
        }
        
        // Tree Total Recall - scan only selected files/directories
        async function treeTotalRecall() {
            const query = editableText.value || rawTranscription;
            if (!query) {
                alert('Enter a query first for Total Recall');
                return;
            }
            
            // Helper to check if path is excluded
            function isExcluded(path) {
                // '.' means all excluded
                if (searchScope.excludedDirs.includes('.')) return true;
                // Check if path or any parent is excluded
                return searchScope.excludedDirs.some(excl => 
                    path === excl || path.startsWith(excl + '/')
                );
            }
            
            // Get only non-excluded paths (checked items)
            const includedPaths = [];
            function collectIncluded(node) {
                if (!isExcluded(node.path)) {
                    if (node.type === 'file') {
                        includedPaths.push(node.path);
                    }
                    if (node.children) {
                        node.children.forEach(c => collectIncluded(c));
                    }
                }
            }
            if (projectTree) collectIncluded(projectTree);
            
            if (includedPaths.length === 0) {
                alert('No files selected. Check some items in the tree first.');
                return;
            }
            
            showLoading(`🧠 Tree Total Recall: Scanning ${includedPaths.length} selected files...`);
            
            try {
                const response = await fetch('/total_recall', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: query,
                        excluded_dirs: searchScope.excludedDirs,
                        central_files: searchScope.centralFiles,
                        external_files: searchScope.externalFiles.map(f => ({
                            name: f.name,
                            content: f.content
                        })),
                        mode: 'tree_only'  // Special mode for tree-only scan
                    })
                });
                
                const data = await response.json();
                if (data.results) {
                    // Mark found files as central
                    data.results.forEach(r => {
                        if (!searchScope.centralFiles.includes(r.file_path)) {
                            searchScope.centralFiles.push(r.file_path);
                        }
                    });
                    refreshTreeUI();
                    displayContext(data.results, 'total_recall');
                    
                    console.log(`[DEBUG] Tree Total Recall found ${data.results.length} relevant files`);
                }
            } catch (err) {
                console.error('Tree Total Recall error:', err);
            }
            
            hideLoading();
        }
        
        // ====================================================================
        // EXTERNAL FILES FUNCTIONS (File Picker via FileReader API)
        // ====================================================================
        
        // Setup file picker event handler
        document.getElementById('externalFileInput').addEventListener('change', handleExternalFiles);
        document.getElementById('externalFolderInput').addEventListener('change', handleExternalFiles);
        
        async function handleExternalFiles(e) {
            console.log('[DEBUG] File/folder picker changed, files:', e.target.files.length);
            const files = Array.from(e.target.files);
            const maxSize = 500 * 1024; // 500KB
            const allowedExt = ['.md', '.txt', '.py', '.json'];
            
            showLoading('Loading external files...');
            let addedCount = 0;
            let skippedCount = 0;
            
            for (const file of files) {
                // Check extension
                const ext = '.' + file.name.split('.').pop().toLowerCase();
                if (!allowedExt.includes(ext)) {
                    skippedCount++;
                    continue;  // Skip silently for folders with many files
                }
                
                // Check size
                if (file.size > maxSize) {
                    console.log('[DEBUG] File too large:', file.name, file.size);
                    skippedCount++;
                    continue;
                }
                
                // Read file content
                try {
                    const content = await readFileAsText(file);
                    
                    // Use webkitRelativePath if available (for folders)
                    const displayPath = file.webkitRelativePath || file.name;
                    
                    // Add to external files (if not already added)
                    if (!searchScope.externalFiles.find(f => f.name === displayPath)) {
                        searchScope.externalFiles.push({
                            path: displayPath,
                            name: displayPath,
                            content: content,
                            size_kb: Math.round(file.size / 1024 * 10) / 10,
                            extension: ext
                        });
                        addedCount++;
                    }
                } catch (err) {
                    console.error('[DEBUG] Error reading file:', file.name, err);
                }
            }
            
            refreshExternalFilesList();
            hideLoading();
            
            if (addedCount > 0 || skippedCount > 0) {
                console.log(`[DEBUG] External files: ${addedCount} added, ${skippedCount} skipped`);
            }
            
            // Reset input so same selection can be made again
            e.target.value = '';
        }
        
        // Helper function to read file as text
        function readFileAsText(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = () => reject(reader.error);
                reader.readAsText(file);
            });
        }
        
        function removeExternalFile(path) {
            searchScope.externalFiles = searchScope.externalFiles.filter(f => f.path !== path);
            refreshExternalFilesList();
        }
        
        function refreshExternalFilesList() {
            const list = document.getElementById('externalFilesList');
            if (searchScope.externalFiles.length === 0) {
                list.innerHTML = '<div style="color: var(--text-secondary); font-size: 0.8rem;">No external files added</div>';
                return;
            }
            
            list.innerHTML = searchScope.externalFiles.map(f => `
                <div class="external-file-item">
                    <span class="path">${escapeHtml(f.name)}</span>
                    <span style="font-size: 0.7rem; color: var(--text-secondary);">${f.size_kb}KB</span>
                    <span class="remove-btn" onclick="removeExternalFile('${escapeHtml(f.path)}')">✕</span>
                </div>
            `).join('');
        }
        
        // Initialize on load
        fetchProjectTree();
        refreshExternalFilesList();
        
        // ====================================================================
        // HELPERS
        // ====================================================================
        function showLoading(text) {
            loading.classList.add('active');
            loadingText.textContent = text;
        }
        
        function hideLoading() {
            loading.classList.remove('active');
        }
        
        async function checkHealth() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                document.getElementById('whisperStatus').classList.toggle('error', data.whisper !== 'OK');
                document.getElementById('llmStatus').classList.toggle('error', data.llm !== 'OK');
            } catch (err) {}
        }
        
        checkHealth();
        setInterval(checkHealth, 30000);