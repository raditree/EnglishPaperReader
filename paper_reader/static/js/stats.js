// 初始化图表
let charts = {};

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    // 每分钟刷新
    setInterval(loadDashboard, 60000);
});

async function loadDashboard() {
    await Promise.all([
        loadOverview(),
        loadLearningCurve(),
        loadActivityChart(),
        loadCategoryDist(),
        loadWordCloud(),
        loadMasteryDist(),
        loadReviewSuggestions(),
        loadDifficultWords(),
        loadReadingProgress()
    ]);
}

// ===== 概览数据 =====
async function loadOverview() {
    try {
        const response = await fetch('/api/daily?days=1');
        const data = await response.json();

        if (data && data.length > 0) {
            const today = data[0];
            document.getElementById('total-vocab').textContent = today.vocabulary_size || 0;
            document.getElementById('mastered-words').textContent = today.mastered_words || 0;
            document.getElementById('today-queries').textContent = today.total_words_queried || 0;
            document.getElementById('papers-read').textContent = today.total_papers_read || 0;
            document.getElementById('repeat-rate').textContent = (today.repeat_query_rate || 0).toFixed(1) + '%';

            // 格式化阅读时长
            const hours = Math.floor((today.total_reading_time || 0) / 3600);
            const minutes = Math.floor(((today.total_reading_time || 0) % 3600) / 60);
            document.getElementById('reading-time').textContent =
                hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
        } else {
            // 无数据时显示0
            ['total-vocab', 'mastered-words', 'today-queries', 'papers-read',
             'repeat-rate', 'reading-time'].forEach(id => {
                document.getElementById(id).textContent = id === 'repeat-rate' ? '0%' : '0';
            });
        }
    } catch (e) {
        console.error('加载概览失败:', e);
    }
}

// ===== 学习曲线 =====
async function loadLearningCurve() {
    try {
        const response = await fetch('/api/stats/learning_curve?days=30');
        const data = await response.json();

        const ctx = document.getElementById('learningCurve').getContext('2d');

        if (charts.learningCurve) charts.learningCurve.destroy();

        const dates = data.daily_data.map(d => d.date);
        const vocabData = data.daily_data.map(d => d.vocabulary_size);
        const newWordsData = data.daily_data.map(d => d.new_words || 0);
        const masteredData = data.daily_data.map(d => d.mastered_words || 0);

        charts.learningCurve = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: '累计词汇量',
                    data: vocabData,
                    borderColor: '#d4a373',
                    backgroundColor: 'rgba(212, 163, 115, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: '每日新词',
                    data: newWordsData,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: '已掌握词汇',
                    data: masteredData,
                    borderColor: '#17a2b8',
                    backgroundColor: 'rgba(23, 162, 184, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } catch (e) {
        console.error('加载学习曲线失败:', e);
    }
}

// ===== 每日活动图表 =====
async function loadActivityChart() {
    try {
        const response = await fetch('/api/daily?days=14');
        const data = await response.json();

        const ctx = document.getElementById('activityChart').getContext('2d');

        if (charts.activity) charts.activity.destroy();

        const dates = data.map(d => d.date);
        const queriesData = data.map(d => d.total_words_queried);
        const papersData = data.map(d => d.total_papers_read);
        const timeData = data.map(d => Math.round((d.total_reading_time || 0) / 60));

        charts.activity = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [{
                    label: '查询次数',
                    data: queriesData,
                    backgroundColor: '#d4a373',
                    yAxisID: 'y'
                }, {
                    label: '阅读论文',
                    data: papersData,
                    backgroundColor: '#28a745',
                    yAxisID: 'y'
                }, {
                    label: '阅读时长(分)',
                    data: timeData,
                    type: 'line',
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        position: 'left',
                    },
                    y1: {
                        beginAtZero: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            }
        });
    } catch (e) {
        console.error('加载活动图表失败:', e);
    }
}

// ===== 分类分布 =====
async function loadCategoryDist() {
    try {
        const response = await fetch('/api/stats/category_stats');
        const data = await response.json();

        const ctx = document.getElementById('categoryDist').getContext('2d');

        if (charts.categoryDist) charts.categoryDist.destroy();

        const categories = data.categories || [];
        const labels = categories.map(c => c.category);
        const values = categories.map(c => c.queries);
        const colors = [
            '#d4a373', '#8b7355', '#c9b896', '#e8dfca',
            '#f4ecd8', '#5c4b37', '#28a745', '#17a2b8'
        ];

        charts.categoryDist = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    } catch (e) {
        console.error('加载分类分布失败:', e);
    }
}

// ===== 词云 =====
async function loadWordCloud() {
    try {
        const response = await fetch('/api/stats/word_frequency?days=7&limit=30');
        const data = await response.json();

        const container = document.getElementById('wordCloud');
        container.innerHTML = '';

        if (!data.words || data.words.length === 0) {
            container.innerHTML = '<p style="color: #8b7355; text-align: center;">暂无数据</p>';
            return;
        }

        data.words.forEach((item, index) => {
            const tag = document.createElement('span');
            tag.className = 'word-tag';
            tag.textContent = item.word;
            tag.style.fontSize = Math.max(12, 26 - index * 0.5) + 'px';
            tag.style.opacity = Math.max(0.5, 1 - index * 0.03);
            tag.title = `查询 ${item.total} 次`;
            tag.onclick = () => showWordHistory(item.word);
            container.appendChild(tag);
        });
    } catch (e) {
        console.error('加载词云失败:', e);
    }
}

// ===== 掌握度分布 =====
async function loadMasteryDist() {
    try {
        const response = await fetch('/api/stats/mastery_distribution');
        const data = await response.json();

        const ctx = document.getElementById('masteryChart').getContext('2d');

        if (charts.mastery) charts.mastery.destroy();

        const labels = ['陌生', '初识', '了解', '熟悉', '掌握', '精通'];
        const counts = new Array(6).fill(0);

        (data.distribution || []).forEach(d => {
            const level = Math.min(5, Math.max(0, d.mastery_level || 0));
            counts[level] = d.count;
        });

        charts.mastery = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '单词数量',
                    data: counts,
                    backgroundColor: [
                        '#dc3545', '#ffc107', '#17a2b8',
                        '#28a745', '#6f42c1', '#d4a373'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } catch (e) {
        console.error('加载掌握度分布失败:', e);
    }
}

// ===== 难词分析 =====
async function loadDifficultWords() {
    try {
        const response = await fetch('/api/stats/difficult_words?limit=20');
        const data = await response.json();

        const container = document.getElementById('difficult-words');
        container.innerHTML = '';

        if (!data.difficult_words || data.difficult_words.length === 0) {
            container.innerHTML = '<p style="color: #8b7355; text-align: center; grid-column: 1/-1;">暂无难词数据</p>';
            return;
        }

        data.difficult_words.forEach(item => {
            const div = document.createElement('div');
            div.className = 'word-item';
            div.innerHTML = `
                <span class="word">${item.word}</span>
                <span class="count">${item.query_count}次</span>
            `;
            div.onclick = () => showWordHistory(item.word);
            container.appendChild(div);
        });
    } catch (e) {
        console.error('加载难词失败:', e);
    }
}

// ===== 复习建议 =====
async function loadReviewSuggestions() {
    try {
        const response = await fetch('/api/stats/review_suggestions?limit=15');
        const data = await response.json();

        const container = document.getElementById('review-list');
        container.innerHTML = '';

        if (!data.suggestions || data.suggestions.length === 0) {
            container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #8b7355;">暂无需要复习的单词，继续保持！</p>';
            return;
        }

        data.suggestions.forEach(item => {
            const div = document.createElement('div');
            div.className = 'review-item';
            div.innerHTML = `
                <div class="word">${item.word}</div>
                <div class="info">
                    查询${item.query_count}次 |
                    ${item.days_since.toFixed(0)}天前
                </div>
            `;
            div.onclick = () => showWordHistory(item.word);
            container.appendChild(div);
        });
    } catch (e) {
        console.error('加载复习建议失败:', e);
    }
}

// ===== 阅读进度 =====
async function loadReadingProgress() {
    try {
        const response = await fetch('/api/stats/reading_progress?days=30');
        const data = await response.json();

        if (data.progress) {
            document.getElementById('total-papers').textContent = data.progress.total_papers || 0;

            const hours = ((data.progress.total_hours || 0)).toFixed(1);
            document.getElementById('total-hours').textContent = hours + 'h';

            const avgMinutes = Math.round((data.progress.avg_session_time || 0) / 60);
            document.getElementById('avg-session').textContent = avgMinutes + 'min';

            document.getElementById('total-pages').textContent = data.progress.total_pages || 0;
        }
    } catch (e) {
        console.error('加载阅读进度失败:', e);
    }
}

// ===== 高级查询 =====
async function executeQuery() {
    const type = document.getElementById('query-type').value;
    const param = document.getElementById('query-param').value;

    const resultDiv = document.getElementById('query-result');
    resultDiv.textContent = '加载中...';

    try {
        let url = `/api/stats/${type}`;

        const params = new URLSearchParams();
        if (param) {
            if (type === 'word_history') {
                params.append('word', param);
            } else {
                params.append(type.includes('days') ? 'days' : 'limit', param);
            }
        }

        if (params.toString()) url += '?' + params.toString();

        const response = await fetch(url);
        const data = await response.json();

        resultDiv.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        resultDiv.textContent = '查询失败: ' + e.message;
    }
}

function showWordHistory(word) {
    document.getElementById('query-type').value = 'word_history';
    document.getElementById('query-param').value = word;
    executeQuery();
    document.getElementById('query-result').scrollIntoView({ behavior: 'smooth' });
}

// ===== 数据管理功能 =====

// 重置数据
function confirmResetData() {
    document.getElementById('reset-modal').classList.add('active');
}

function closeResetModal() {
    document.getElementById('reset-modal').classList.remove('active');
}

async function executeReset() {
    const resetType = document.querySelector('input[name="reset-type"]:checked').value;

    if (!confirm('确定要重置数据吗？此操作不可恢复！')) {
        return;
    }

    try {
        const response = await fetch('/api/user/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: resetType })
        });

        const data = await response.json();

        if (data.success) {
            alert('数据已重置');
            closeResetModal();
            loadDashboard(); // 刷新数据
        } else {
            alert('重置失败: ' + (data.error || '未知错误'));
        }
    } catch (e) {
        alert('重置失败: ' + e.message);
    }
}

// 导入熟词
function showImportModal() {
    document.getElementById('import-modal').classList.add('active');
}

function closeImportModal() {
    document.getElementById('import-modal').classList.remove('active');
    document.getElementById('import-text').value = '';
    document.getElementById('import-file').value = '';
}

function toggleFileUpload() {
    const useFile = document.getElementById('import-from-file').checked;
    document.getElementById('import-text').disabled = useFile;
    document.getElementById('import-file').style.display = useFile ? 'block' : 'none';
}

function handleFileUpload(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('import-text').value = e.target.result;
        };
        reader.readAsText(input.files[0]);
    }
}

async function executeImport() {
    const text = document.getElementById('import-text').value.trim();

    if (!text) {
        alert('请输入文本或选择文件');
        return;
    }

    try {
        const response = await fetch('/api/user/import-familiar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                source: 'manual_import'
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(`成功导入 ${data.added} 个熟词（共提取 ${data.total_extracted} 个单词）`);
            closeImportModal();
            loadDashboard(); // 刷新数据
        } else {
            alert('导入失败: ' + (data.error || '未知错误'));
        }
    } catch (e) {
        alert('导入失败: ' + e.message);
    }
}

// 导出数据
async function exportData() {
    try {
        // 获取所有统计数据
        const [daily, words, sessions] = await Promise.all([
            fetch('/api/daily?days=365').then(r => r.json()),
            fetch('/api/stats/word_frequency?days=365&limit=1000').then(r => r.json()),
            fetch('/api/stats/reading_progress?days=365').then(r => r.json())
        ]);

        const exportData = {
            export_date: new Date().toISOString(),
            daily_stats: daily,
            top_words: words,
            reading_progress: sessions
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `learning_stats_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (e) {
        alert('导出失败: ' + e.message);
    }
}

// ===== 词库查看功能 =====
let vocabPage = 0;
const vocabPageSize = 50;
let vocabSearch = '';
let vocabTotal = 0;

function showVocabularyModal() {
    document.getElementById('vocabulary-modal').classList.add('active');
    vocabPage = 0;
    vocabSearch = '';
    document.getElementById('vocab-search').value = '';
    loadVocabulary();
}

function closeVocabularyModal() {
    document.getElementById('vocabulary-modal').classList.remove('active');
}

async function loadVocabulary(retryCount = 0) {
    const listContainer = document.getElementById('vocabulary-list');
    const maxRetries = 3;
    const retryDelay = 1000;
    const timeoutMs = 8000;
    
    if (retryCount === 0) {
        listContainer.innerHTML = '<p class="loading-text">加载中...</p>';
    }
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        
        const response = await fetch(
            `/api/user/familiar-words/details?limit=${vocabPageSize}&offset=${vocabPage * vocabPageSize}&search=${encodeURIComponent(vocabSearch)}`,
            { signal: controller.signal }
        );
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        vocabTotal = data.total;
        
        if (data.words.length === 0) {
            listContainer.innerHTML = '<p style="text-align: center; color: #8b7355;">暂无单词</p>';
        } else {
            let html = '<div class="vocabulary-grid">';
            data.words.forEach(word => {
                html += `
                    <div class="vocabulary-item">
                        <span class="word">${word.word}</span>
                        <span class="info">查询 ${word.query_count} 次 | ${word.added_date}</span>
                    </div>
                `;
            });
            html += '</div>';
            listContainer.innerHTML = html;
        }
        
        // 更新计数和分页信息
        document.getElementById('vocab-count').textContent = `共 ${vocabTotal} 个单词`;
        const totalPages = Math.ceil(vocabTotal / vocabPageSize) || 1;
        document.getElementById('vocab-page-info').textContent = `第 ${vocabPage + 1} / ${totalPages} 页`;
        
        // 更新分页按钮状态
        const prevBtn = document.querySelector('#vocab-pagination button:first-child');
        const nextBtn = document.querySelector('#vocab-pagination button:last-child');
        prevBtn.disabled = vocabPage === 0;
        nextBtn.disabled = vocabPage >= totalPages - 1;
    } catch (e) {
        console.error(`加载词库失败 (重试 ${retryCount}/${maxRetries}):`, e);
        
        if (retryCount < maxRetries) {
            listContainer.innerHTML = `<p class="loading-text">加载失败，${retryDelay/1000}秒后重试... (${retryCount + 1}/${maxRetries})</p>`;
            setTimeout(() => loadVocabulary(retryCount + 1), retryDelay);
        } else {
            listContainer.innerHTML = `
                <div style="text-align: center; color: #dc3545; padding: 20px;">
                    <p>加载失败: ${e.message}</p>
                    <button class="btn btn-secondary" onclick="loadVocabulary(0)" style="margin-top: 10px;">
                        重新加载
                    </button>
                </div>
            `;
        }
    }
}

function searchVocabulary() {
    vocabSearch = document.getElementById('vocab-search').value.trim();
    vocabPage = 0;
    loadVocabulary();
}

function changeVocabPage(delta) {
    vocabPage += delta;
    if (vocabPage < 0) vocabPage = 0;
    loadVocabulary();
}

// ===== 导入历史和撤销功能 =====
function showImportHistoryModal() {
    document.getElementById('import-history-modal').classList.add('active');
    loadImportHistory();
}

function closeImportHistoryModal() {
    document.getElementById('import-history-modal').classList.remove('active');
}

async function loadImportHistory(retryCount = 0) {
    const listContainer = document.getElementById('import-history-list');
    const maxRetries = 3;
    const retryDelay = 1000;
    const timeoutMs = 8000;
    
    if (retryCount === 0) {
        listContainer.innerHTML = '<p class="loading-text">加载中...</p>';
    }
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        
        const response = await fetch('/api/user/import-batches', { signal: controller.signal });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.batches.length === 0) {
            listContainer.innerHTML = '<p style="text-align: center; color: #8b7355;">暂无导入记录</p>';
        } else {
            let html = '<div class="import-history-list">';
            data.batches.forEach(batch => {
                html += `
                    <div class="import-batch-item">
                        <div class="batch-info">
                            <span class="batch-id">批次: ${batch.import_batch}</span>
                            <span class="batch-date">${batch.added_date}</span>
                            <span class="batch-count">${batch.word_count} 个单词</span>
                            <span class="batch-source">来源: ${batch.source || '导入'}</span>
                        </div>
                        <button class="btn btn-sm btn-danger" onclick="undoImport('${batch.import_batch}', ${batch.word_count})">撤销</button>
                    </div>
                `;
            });
            html += '</div>';
            listContainer.innerHTML = html;
        }
    } catch (e) {
        console.error(`加载导入历史失败 (重试 ${retryCount}/${maxRetries}):`, e);
        
        if (retryCount < maxRetries) {
            listContainer.innerHTML = `<p class="loading-text">加载失败，${retryDelay/1000}秒后重试... (${retryCount + 1}/${maxRetries})</p>`;
            setTimeout(() => loadImportHistory(retryCount + 1), retryDelay);
        } else {
            listContainer.innerHTML = `
                <div style="text-align: center; color: #dc3545; padding: 20px;">
                    <p>加载失败: ${e.message}</p>
                    <button class="btn btn-secondary" onclick="loadImportHistory(0)" style="margin-top: 10px;">
                        重新加载
                    </button>
                </div>
            `;
        }
    }
}

async function undoImport(batchId, wordCount) {
    if (!confirm(`确定要撤销这次导入吗？这将从熟词中移除 ${wordCount} 个单词。`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/user/undo-import/${batchId}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert(`成功撤销导入，移除了 ${data.deleted} 个单词`);
            loadImportHistory();
            loadDashboard();
        } else {
            alert('撤销失败: ' + (data.error || '未知错误'));
        }
    } catch (e) {
        alert('撤销失败: ' + e.message);
    }
}
