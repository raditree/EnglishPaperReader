class PaperReader {
    constructor() {
        this.currentPaper = null;
        this.sessionId = this.generateSessionId();
        this.queryCount = 0;
        this.wordCount = new Set();
        this.lastSelection = '';
        this.currentPaperInfo = null;

        this.renderConfig = {
            baseScale: 1.5,
            devicePixelRatio: window.devicePixelRatio || 1,
            textLayerOpacity: 0.15,
            enableHiDPI: true
        };

        this.arxivCategories = {};

        // ===== 翻译缓存相关 =====
        this.translationCache = new Map(); // 预加载的翻译缓存
        this.isPreloading = false;         // 是否正在预加载
        this.preloadedWords = new Set();   // 已预加载的单词集合

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadCategories();
        this.setupColorTemp();
        this.setupResizer();
        this.setupModal();
        this.startSession();

        setInterval(() => this.saveSession(), 60000);
        window.addEventListener('beforeunload', () => this.endSession());
    }

    generateSessionId() {
        return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // ===== 事件绑定 =====
    bindEvents() {
        // 论文选择按钮
        document.getElementById('select-paper-btn').addEventListener('click', () => {
            this.openModal();
        });

        // 主题切换
        document.getElementById('theme-toggle').addEventListener('click', () => {
            this.toggleTheme();
        });

        // 面板折叠
        document.querySelector('.panel-header').addEventListener('click', (e) => {
            if (e.target.closest('.panel-controls')) return;
            document.getElementById('translation-panel').classList.toggle('collapsed');
        });

        document.getElementById('close-panel').addEventListener('click', () => {
            document.getElementById('translation-panel').classList.add('collapsed');
        });

        // 快捷键 - Ctrl+M
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
                e.preventDefault();
                this.translateSelection();
            }
        });

        // 标签切换
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
            });
        });

        // 关闭模态窗口
        document.getElementById('close-paper-modal').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('paper-modal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('paper-modal')) {
                this.closeModal();
            }
        });

        // 搜索输入框回车事件
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchPapers();
            }
        });

        // 筛选器变化
        document.getElementById('local-filter-category').addEventListener('change', () => this.loadLocalPapers());
        document.getElementById('local-filter-read').addEventListener('change', () => this.loadLocalPapers());
        document.getElementById('latest-filter-category').addEventListener('change', () => this.loadLatestPapers());
    }

    // ===== 模态窗口设置 =====
    setupModal() {
        const modal = document.getElementById('paper-modal-content');
        const header = document.getElementById('paper-modal-header');

        let isDragging = false;
        let startX, startY, initialLeft, initialTop;

        header.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            const rect = modal.getBoundingClientRect();
            initialLeft = rect.left;
            initialTop = rect.top;
            modal.style.position = 'fixed';
            modal.style.left = initialLeft + 'px';
            modal.style.top = initialTop + 'px';
            modal.style.margin = '0';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            modal.style.left = Math.max(0, initialLeft + dx) + 'px';
            modal.style.top = Math.max(0, initialTop + dy) + 'px';
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
        });
    }

    openModal() {
        document.getElementById('paper-modal').classList.add('active');
        this.loadLocalPapers();
    }

    closeModal() {
        document.getElementById('paper-modal').classList.remove('active');
    }

    // ===== 分类加载 =====
    async loadCategories() {
        try {
            const response = await fetch('/api/categories');
            const categories = await response.json();
            this.arxivCategories = categories;

            // 填充分类下拉框
            const selects = [
                document.getElementById('local-filter-category'),
                document.getElementById('latest-filter-category'),
                document.getElementById('search-filter-category')
            ];

            selects.forEach(select => {
                if (!select) return;
                select.innerHTML = '<option value="">全部分类</option>';
                Object.entries(categories).forEach(([code, name]) => {
                    const option = document.createElement('option');
                    option.value = code;
                    option.textContent = `${code} - ${name}`;
                    select.appendChild(option);
                });
            });
        } catch (e) {
            console.error('加载分类失败:', e);
        }
    }

    // ===== 本地论文加载 =====
    async loadLocalPapers() {
        const container = document.getElementById('local-paper-list');
        container.innerHTML = '<div class="empty-papers"><div class="spinner"></div><p>加载中...</p></div>';

        try {
            const response = await fetch('/api/papers');
            let papers = await response.json();

            // 应用筛选
            const categoryFilter = document.getElementById('local-filter-category').value;
            const readFilter = document.getElementById('local-filter-read').value;

            if (categoryFilter) {
                papers = papers.filter(p => p.category === categoryFilter);
            }
            if (readFilter !== '') {
                papers = papers.filter(p => p.is_read === parseInt(readFilter));
            }

            this.renderPaperList(papers, container, 'local');
        } catch (e) {
            container.innerHTML = `<div class="empty-papers"><p>加载失败: ${e.message}</p></div>`;
        }
    }

    // ===== 最新论文加载 =====
    async loadLatestPapers() {
        const container = document.getElementById('latest-paper-list');
        container.innerHTML = '<div class="empty-papers"><div class="spinner"></div><p>获取最新论文...</p></div>';

        try {
            const category = document.getElementById('latest-filter-category').value;
            const url = category
                ? `/api/papers/latest?categories=${category}&max_results=10`
                : '/api/papers/latest?max_results=10';

            const response = await fetch(url);
            const data = await response.json();
            this.renderPaperList(data.papers || [], container, 'latest');
        } catch (e) {
            container.innerHTML = `<div class="empty-papers"><p>获取失败: ${e.message}</p></div>`;
        }
    }

    // ===== 搜索论文 =====
    async searchPapers() {
        const query = document.getElementById('search-input').value.trim();
        if (!query) {
            alert('请输入搜索关键词');
            return;
        }

        const container = document.getElementById('search-paper-list');
        container.innerHTML = '<div class="empty-papers"><div class="spinner"></div><p>搜索中...</p></div>';

        try {
            // 如果是纯数字格式，当作arXiv ID直接获取
            const arxivIdPattern = /^\d{4}\.\d{4,5}(v\d+)?$/;
            if (arxivIdPattern.test(query)) {
                const response = await fetch(`/api/papers/${query}`);
                const paper = await response.json();
                if (paper.error) {
                    container.innerHTML = `<div class="empty-papers"><p>未找到论文: ${query}</p></div>`;
                } else {
                    // 检查本地状态
                    const localInfo = await fetch(`/api/papers/${query}`).then(r => r.json()).catch(() => null);
                    if (localInfo && !localInfo.error) {
                        paper.is_downloaded = localInfo.local_path != null;
                        paper.is_read = localInfo.is_read;
                    }
                    this.renderPaperList([paper], container, 'search');
                }
            } else {
                // 关键词搜索
                const category = document.getElementById('search-filter-category').value;
                const response = await fetch('/api/papers/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query, category, max_results: 20 })
                });
                const data = await response.json();
                this.renderPaperList(data.papers || [], container, 'search');
            }
        } catch (e) {
            container.innerHTML = `<div class="empty-papers"><p>搜索失败: ${e.message}</p></div>`;
        }
    }

    // ===== 渲染论文列表 =====
    renderPaperList(papers, container, type) {
        if (!papers || papers.length === 0) {
            container.innerHTML = `
                <div class="empty-papers">
                    <div class="empty-papers-icon">📭</div>
                    <p>没有找到论文</p>
                </div>`;
            return;
        }

        container.innerHTML = '';
        papers.forEach(paper => {
            const item = document.createElement('div');
            item.className = 'paper-item';
            if (paper.is_read) item.classList.add('read');
            if (paper.is_downloaded || paper.local_path) item.classList.add('downloaded');

            const categoryName = this.arxivCategories[paper.primary_category || paper.category] || '';
            const isDownloaded = paper.is_downloaded || paper.local_path;

            item.innerHTML = `
                <div class="paper-item-header">
                    <div class="paper-title">${paper.title || paper.id || paper.arxiv_id}</div>
                    <div class="paper-badges">
                        <span class="badge badge-category">${paper.primary_category || paper.category || 'misc'}</span>
                        ${paper.is_read ? '<span class="badge badge-read">已读</span>' : ''}
                        ${isDownloaded ? '<span class="badge badge-downloaded">已下载</span>' : ''}
                    </div>
                </div>
                <div class="paper-meta">
                    <span>📝 ${paper.arxiv_id || paper.id}</span>
                    <span>📅 ${this.formatDate(paper.published || paper.published_date)}</span>
                    ${categoryName ? `<span>🏷️ ${categoryName}</span>` : ''}
                </div>
                ${paper.authors ? `
                <div class="paper-authors">
                    👤 ${Array.isArray(paper.authors) ? paper.authors.slice(0, 3).join(', ') : paper.authors}
                    ${Array.isArray(paper.authors) && paper.authors.length > 3 ? ' 等' : ''}
                </div>` : ''}
                ${paper.abstract ? `
                <div class="paper-abstract">${paper.abstract.substring(0, 300)}${paper.abstract.length > 300 ? '...' : ''}</div>
                ` : ''}
                <div class="paper-actions">
                    ${isDownloaded
                        ? `<button class="paper-action-btn primary" onclick="reader.loadPaper('${paper.local_path || paper.path}')">📖 阅读</button>`
                        : `<button class="paper-action-btn primary" onclick="reader.downloadAndLoadPaper('${paper.arxiv_id || paper.id}', '${paper.primary_category || paper.category || 'misc'}')">⬇️ 下载并阅读</button>`
                    }
                    <button class="paper-action-btn" onclick="window.open('https://arxiv.org/abs/${paper.arxiv_id || paper.id}', '_blank')">🔗 arXiv</button>
                </div>
            `;

            container.appendChild(item);
        });
    }

    formatDate(dateStr) {
        if (!dateStr) return '未知';
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-CN');
    }

    // ===== 下载并阅读 =====
    async downloadAndLoadPaper(arxivId, category) {
        this.showLoading(true, '下载论文中...');
        try {
            const response = await fetch('/api/papers/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ arxiv_id: arxivId, category: category })
            });
            const data = await response.json();

            if (data.success) {
                this.closeModal();
                await this.loadPaper(data.path);
            } else {
                alert('下载失败: ' + (data.error || '未知错误'));
            }
        } catch (e) {
            alert('下载失败: ' + e.message);
        } finally {
            this.showLoading(false);
        }
    }

    // ===== PDF加载和渲染 =====
    async loadPaper(path) {
        if (!path) return;

        this.showLoading(true, '加载论文中...');
        const container = document.getElementById('pdf-container');
        container.innerHTML = '';

        const pdfWrapper = document.createElement('div');
        pdfWrapper.className = 'pdf-wrapper';
        container.appendChild(pdfWrapper);

        // 重置翻译缓存
        this.translationCache.clear();
        this.preloadedWords.clear();

        try {
            const url = `/api/paper/${path}`;
            const loadingTask = pdfjsLib.getDocument({
                url: url,
                useSystemFonts: true,
                cMapUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
                cMapPacked: true,
            });

            const pdf = await loadingTask.promise;

            this.currentPaper = path;
            const parts = path.split('/');
            this.currentCategory = parts[0];
            this.currentPaperId = parts[1].replace('.pdf', '');

            // 更新当前论文信息显示
            document.getElementById('current-paper-info').textContent = this.currentPaperId;

            // 重置会话
            this.endSession();
            this.startSession();
            this.queryCount = 0;
            this.wordCount.clear();
            this.updateStats();

            // 收集所有页面的文本内容用于预加载
            let allTextContent = [];

            // 渲染所有页面
            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
                const pageText = await this.renderPage(pdf, pageNum, pdfWrapper);
                if (pageText) {
                    allTextContent.push(pageText);
                }
            }

            // 开始后台预加载翻译
            this.preloadTranslations(allTextContent.join(' '));

            // 标记为已读
            fetch('/api/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    paper_id: this.currentPaperId,
                    category: this.currentCategory
                })
            });

        } catch (e) {
            container.innerHTML = `<div class="empty-state"><p>加载失败: ${e.message}</p></div>`;
        }

        this.showLoading(false);
    }

    async renderPage(pdf, pageNum, container) {
        console.log(`开始渲染页面 ${pageNum}`);
        const page = await pdf.getPage(pageNum);
        const containerWidth = container.clientWidth || window.innerWidth;
        const unscaledViewport = page.getViewport({ scale: 1 });
        const scale = this.calculateOptimalScale(unscaledViewport.width, containerWidth);
        const viewport = page.getViewport({ scale: scale });

        // 创建页面容器
        const pageDiv = document.createElement('div');
        pageDiv.className = 'pdf-page';
        pageDiv.style.width = `${Math.floor(viewport.width)}px`;
        pageDiv.style.height = `${Math.floor(viewport.height)}px`;
        pageDiv.style.setProperty('--scale-factor', scale.toFixed(5));

        // Canvas层
        const canvas = document.createElement('canvas');
        canvas.style.display = 'block';
        canvas.style.width = `${Math.floor(viewport.width)}px`;
        canvas.style.height = `${Math.floor(viewport.height)}px`;

        const context = canvas.getContext('2d', { alpha: false });
        const outputScale = this.renderConfig.enableHiDPI ? (window.devicePixelRatio || 1) : 1;

        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);

        // 设置缩放变换以匹配devicePixelRatio
        if (outputScale !== 1) {
            context.setTransform(outputScale, 0, 0, outputScale, 0, 0);
        }

        pageDiv.appendChild(canvas);

        // 文本层 - 放在Canvas之上
        const textLayerDiv = document.createElement('div');
        textLayerDiv.className = 'textLayer';
        textLayerDiv.style.width = `${Math.floor(viewport.width)}px`;
        textLayerDiv.style.height = `${Math.floor(viewport.height)}px`;
        pageDiv.appendChild(textLayerDiv);

        container.appendChild(pageDiv);

        // 渲染Canvas
        const renderContext = {
            canvasContext: context,
            viewport: viewport,
            enableWebGL: false,
            intent: 'display'
        };

        try {
            await page.render(renderContext).promise;
            console.log(`页面 ${pageNum} Canvas渲染完成`);
        } catch (e) {
            console.error('Canvas渲染失败:', e);
        }

        // 渲染文本层并收集文本
        let pageText = '';
        try {
            const textContent = await page.getTextContent();
            console.log(`页面 ${pageNum} 获取到 ${textContent.items.length} 个文本项`);

            // 收集页面文本用于预加载
            pageText = textContent.items.map(item => item.str).join(' ');

            // 使用PDF.js的renderTextLayer函数
            const textLayerRenderTask = pdfjsLib.renderTextLayer({
                textContent: textContent,
                container: textLayerDiv,
                viewport: viewport,
                textDivs: []
            });

            // 等待渲染完成 - 处理不同版本的PDF.js
            if (textLayerRenderTask && typeof textLayerRenderTask.promise !== 'undefined') {
                await textLayerRenderTask.promise;
            } else if (textLayerRenderTask && typeof textLayerRenderTask.then === 'function') {
                await textLayerRenderTask;
            }

            // 检查是否有文本
            const spans = textLayerDiv.querySelectorAll('span');
            console.log(`页面 ${pageNum} 文本层渲染完成，包含 ${spans.length} 个span元素`);

            if (spans.length > 0) {
                // 设置点击事件
                this.setupTextLayerClick(textLayerDiv);
                console.log(`页面 ${pageNum} 点击事件已设置`);
            } else {
                console.warn(`页面 ${pageNum} 没有可选择的文本`);
            }
        } catch (e) {
            console.error('文本层渲染失败:', e);
        }

        return pageText;
    }

    calculateOptimalScale(pageWidth, containerWidth) {
        const margin = 40;
        const availableWidth = containerWidth - margin;
        const scaleToFit = availableWidth / pageWidth;
        const minScale = 0.8;
        const maxScale = 2.5;
        return Math.min(Math.max(scaleToFit, minScale), maxScale);
    }

    // ===== 点击单词翻译 =====
    setupTextLayerClick(textLayerDiv) {
        console.log('设置文本层点击事件');

        // 单击翻译单词
        textLayerDiv.addEventListener('click', (e) => {
            // 获取点击位置的选中文本（通过caret position）
            const selection = window.getSelection();
            let range;
            if (document.caretRangeFromPoint) {
                range = document.caretRangeFromPoint(e.clientX, e.clientY);
            } else if (document.caretPositionFromPoint) {
                const position = document.caretPositionFromPoint(e.clientX, e.clientY);
                range = position.offsetNode ? document.createRange() : null;
                if (range && position.offsetNode) {
                    range.setStart(position.offsetNode, position.offset);
                    range.setEnd(position.offsetNode, position.offset);
                }
            }

            if (!range) {
                console.log('无法获取caret position');
                return;
            }

            // 获取点击的文本节点
            const textNode = range.startContainer;
            if (!textNode || textNode.nodeType !== Node.TEXT_NODE) {
                console.log('点击的不是文本节点');
                return;
            }

            // 获取完整文本和点击位置
            const fullText = textNode.textContent;
            const clickOffset = range.startOffset;

            console.log('点击位置:', clickOffset, '完整文本:', fullText);

            // 提取点击位置的单词
            const word = this.extractWordAtPosition(fullText, clickOffset);
            console.log('提取的单词:', word);

            if (!word || word.length < 2) {
                console.log('单词太短');
                return;
            }

            // 清理单词
            const cleanWord = word.replace(/[^a-zA-Z]/g, '').toLowerCase();
            if (cleanWord.length < 2) {
                console.log('清理后单词太短');
                return;
            }

            // 高亮效果
            const parentSpan = textNode.parentElement;
            if (parentSpan) {
                textLayerDiv.querySelectorAll('span').forEach(s => s.classList.remove('clicked'));
                parentSpan.classList.add('clicked');
            }

            // 翻译
            this.translateWord(cleanWord);
        });
    }

    // 从文本中提取指定位置的单词
    extractWordAtPosition(text, position) {
        if (!text || position < 0 || position >= text.length) {
            return '';
        }

        // 找到单词开始位置
        let start = position;
        while (start > 0 && /[a-zA-Z]/.test(text[start - 1])) {
            start--;
        }

        // 找到单词结束位置
        let end = position;
        while (end < text.length && /[a-zA-Z]/.test(text[end])) {
            end++;
        }

        return text.substring(start, end);
    }

    // ===== 预加载翻译 =====
    async preloadTranslations(textContent) {
        if (!textContent || this.isPreloading) return;

        this.isPreloading = true;
        console.log('开始预加载论文单词翻译...');

        try {
            // 调用批量预加载API
            const response = await fetch('/api/translate/preload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: textContent,
                    paper_id: this.currentPaperId
                })
            });

            if (!response.ok) {
                throw new Error(`预加载失败: ${response.status}`);
            }

            const data = await response.json();

            // 将翻译结果存入缓存
            if (data.translations) {
                Object.entries(data.translations).forEach(([word, translation]) => {
                    this.translationCache.set(word, translation);
                    this.preloadedWords.add(word);
                });

                console.log(`✓ 预加载完成: ${data.total_words} 个单词`);
                console.log(`  - 已缓存: ${this.translationCache.size} 个`);
            }
        } catch (e) {
            console.warn('预加载翻译失败:', e);
            // 预加载失败不影响正常使用，继续即可
        } finally {
            this.isPreloading = false;
        }
    }

    // ===== 翻译功能 =====
    async translateWord(word) {
        if (!word || word.length < 2) {
            this.showTranslation('请选中有效的英文单词');
            return;
        }

        word = word.toLowerCase().trim();

        // 首先检查预加载缓存
        if (this.translationCache.has(word)) {
            console.log(`[缓存命中] ${word}`);
            const cached = this.translationCache.get(word);

            // 更新统计
            this.queryCount++;
            this.wordCount.add(word);
            this.updateStats();

            // 记录查询到后端
            fetch('/api/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    word: word,
                    context: '',
                    session_id: this.sessionId,
                    paper_id: this.currentPaperId,
                    category: this.currentCategory
                })
            }).catch(e => console.warn('记录查询失败:', e));

            this.showTranslationResult(word, cached.translation);
            return;
        }

        // 缓存未命中，调用API翻译
        this.showLoading(true, '翻译中...');

        try {
            const response = await fetch('/api/translate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    word: word,
                    context: '',
                    session_id: this.sessionId,
                    paper_id: this.currentPaperId,
                    category: this.currentCategory
                })
            });

            const data = await response.json();

            // 更新统计
            this.queryCount++;
            this.wordCount.add(word);
            this.updateStats();

            // 存入缓存
            this.translationCache.set(word, {
                translation: data.translation,
                is_cached: false
            });

            this.showTranslationResult(word, data.translation);
        } catch (e) {
            this.showTranslation('翻译失败: ' + e.message);
        } finally {
            this.showLoading(false);
        }
    }

    async translateSelection() {
        const selection = window.getSelection().toString().trim();

        if (!selection) {
            this.showTranslation('请先选中单词');
            return;
        }

        const word = selection.split(/\s+/)[0].replace(/[^a-zA-Z]/g, '').toLowerCase();

        if (!word || word.length < 2) {
            this.showTranslation('请选中有效的英文单词');
            return;
        }

        await this.translateWord(word);
    }

    showTranslationResult(word, translation) {
        const panel = document.getElementById('translation-content');

        // 解析翻译结果
        let phonetic = '';
        let meaning = translation;

        if (translation.includes('音标：') && translation.includes('。释义：')) {
            const match = translation.match(/音标：\/(.*?)\/。释义：(.*)/);
            if (match) {
                phonetic = match[1];
                meaning = match[2];
            }
        }

        panel.innerHTML = `
            <div class="translation-result">
                <div class="word">${word}</div>
                ${phonetic ? `<div class="phonetic">/${phonetic}/</div>` : ''}
                <div class="meaning">${meaning}</div>
            </div>
        `;

        document.getElementById('translation-panel').classList.remove('collapsed');
    }

    showTranslation(text) {
        document.getElementById('translation-content').innerHTML =
            `<div class="empty-state">${text}</div>`;
    }

    // ===== 显示设置 =====
    setupColorTemp() {
        const slider = document.getElementById('color-temp');
        const body = document.body;

        slider.addEventListener('input', (e) => {
            const value = e.target.value;
            let hue, saturation;

            if (value < 50) {
                hue = 220 + (value / 50) * 40;
                saturation = 20;
            } else {
                hue = 30 + ((value - 50) / 50) * 20;
                saturation = 40 + ((value - 50) / 50) * 20;
            }

            body.style.filter = `sepia(${value/200}) hue-rotate(${hue-40}deg)`;
            localStorage.setItem('colorTemp', value);
        });

        const saved = localStorage.getItem('colorTemp');
        if (saved) {
            slider.value = saved;
            slider.dispatchEvent(new Event('input'));
        }
    }

    setupBrightness() {
        const slider = document.getElementById('brightness');
        if (!slider) return;

        this.bgOverlay = document.createElement('div');
        this.bgOverlay.id = 'reader-bg-overlay';
        this.bgOverlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:-1;';
        document.body.appendChild(this.bgOverlay);

        slider.addEventListener('input', (e) => {
            const value = e.target.value;
            const tempVal = document.getElementById('color-temp')?.value || 0;
            let hue;
            if (tempVal < 50) {
                hue = 220 + (tempVal / 50) * 40;
            } else {
                hue = 30 + ((tempVal - 50) / 50) * 20;
            }
            if (this.bgOverlay) {
                this.bgOverlay.style.filter = `brightness(${value}%) sepia(${tempVal/200}) hue-rotate(${hue-40}deg)`;
            }
            localStorage.setItem('brightness', value);
        });

        const saved = localStorage.getItem('brightness');
        if (saved) {
            slider.value = saved;
            slider.dispatchEvent(new Event('input'));
        }
    }

    toggleTheme() {
        const body = document.body;
        const themes = ['sepia-mode', 'light-mode', 'night-mode'];
        const current = themes.find(t => body.classList.contains(t)) || 'sepia-mode';
        const next = themes[(themes.indexOf(current) + 1) % themes.length];

        body.classList.remove(...themes);
        body.classList.add(next);
        localStorage.setItem('theme', next);

        const btn = document.getElementById('theme-toggle');
        btn.textContent = next === 'night-mode' ? '☀️' : next === 'light-mode' ? '📄' : '🌙';
    }

    setupResizer() {
        const resizer = document.getElementById('resizer');
        const translationPanel = document.getElementById('translation-panel');
        if (!resizer || !translationPanel) return;

        let startY = 0;
        let startHeight = 0;

        const onMouseDown = (e) => {
            startY = e.clientY;
            const rect = translationPanel.getBoundingClientRect();
            startHeight = rect.height;
            resizer.classList.add('dragging');
            document.body.style.userSelect = 'none';
            document.body.style.cursor = 'row-resize';
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        };

        const onMouseMove = (e) => {
            const dy = e.clientY - startY;
            const newHeight = startHeight - dy;
            const minHeight = 80;
            const maxHeight = window.innerHeight * 0.4;
            if (newHeight > minHeight && newHeight < maxHeight) {
                translationPanel.style.height = `${newHeight}px`;
            }
        };

        const onMouseUp = () => {
            resizer.classList.remove('dragging');
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            localStorage.setItem('panelHeight', translationPanel.style.height);
        };

        resizer.addEventListener('mousedown', onMouseDown);

        const savedHeight = localStorage.getItem('panelHeight');
        if (savedHeight) {
            translationPanel.style.height = savedHeight;
        }
    }

    // ===== 统计和会话 =====
    updateStats() {
        document.getElementById('reading-stats').textContent =
            `词汇: ${this.wordCount.size} | 查询: ${this.queryCount}`;
    }

    showLoading(show, text = '加载中...') {
        document.getElementById('loading-text').textContent = text;
        document.getElementById('loading').classList.toggle('hidden', !show);
    }

    async startSession() {
        if (!this.currentPaperId) return;
        await fetch('/api/session/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                paper_id: this.currentPaperId,
                category: this.currentCategory
            })
        });
    }

    async saveSession() {}

    async endSession() {
        if (!this.sessionId || !this.currentPaperId) return;
        const duration = Math.floor((Date.now() - parseInt(this.sessionId.split('_')[1])) / 1000);
        await fetch('/api/session/end', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: this.sessionId,
                duration_seconds: duration
            })
        });
    }
}

// 初始化
const reader = new PaperReader();

// 恢复主题设置
const savedTheme = localStorage.getItem('theme') || 'sepia-mode';
document.body.classList.add(savedTheme);

// 更新主题按钮图标
const themeBtn = document.getElementById('theme-toggle');
if (themeBtn) {
    themeBtn.textContent = savedTheme === 'night-mode' ? '☀️' :
                           savedTheme === 'light-mode' ? '📄' : '🌙';
}
