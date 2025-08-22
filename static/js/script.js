document.addEventListener('DOMContentLoaded', () => {
    // --- App State ---
    let isLoggedIn = false;
    let currentView = 'home';
    let currentArticleId = null;
    let currentTab = 'summary';
    const API_BASE_URL = 'http://127.0.0.1:5006';

    // --- DOM Element Cache ---
    const mainContentEl = document.getElementById('main-content');
    const navPanel = document.querySelector('nav');
    const settingsModal = document.getElementById('settings-modal');
    const searchResultsModal = document.getElementById('search-results-modal');



    // --- API Functions ---
    async function fetchApi(url, options = {}) {
        // 确保所有请求都携带凭证 (cookies)
        options.credentials = 'include';
        try {
            const response = await fetch(url, options);
            if (response.status === 401) { // 如果未授权
                updateNav(null);
                navigate('login');
                throw new Error('Unauthorized');
            }
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            // 检查响应是否为空
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                return response.json();
            } else {
                return {}; // 返回空对象而非尝试解析空响应
            }
        } catch (error) {
            if (error.message !== 'Unauthorized') {
                console.error(`Fetch error for ${url}:`, error);
                showToast(`操作失败: ${error.message}`);
            }
            throw error;
        }
    }

     // *** 修正 #1: 将所有 API 函数整合到一个物件中 ***
    const api = {
        // 核心 API
        getLatest: () => fetchApi(`${API_BASE_URL}/api/articles/latest`),
        getFavorites: () => fetchApi(`${API_BASE_URL}/api/articles/favorites`),
        getArticleDetails: (id) => fetchApi(`${API_BASE_URL}/api/articles/${id}`),
        toggleFavorite: (id) => fetchApi(`${API_BASE_URL}/api/articles/${id}/favorite`, { method: 'POST' }),
        postQuestion: (id, question) => fetchApi(`${API_BASE_URL}/api/articles/${id}/ask`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question}) }),
        deleteArticle: (id) => fetchApi(`${API_BASE_URL}/api/articles/${id}`, { method: 'DELETE' }),
        getKeywords: () => fetchApi(`${API_BASE_URL}/api/keywords`),
        addKeyword: (keyword) => fetchApi(`${API_BASE_URL}/api/keywords`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({keyword}) }),
        deleteKeyword: (keyword) => fetchApi(`${API_BASE_URL}/api/keywords/${keyword}`, { method: 'DELETE' }),
        searchArticles: (query) => fetchApi(`${API_BASE_URL}/api/articles/search?query=${encodeURIComponent(query)}`),
        batchImport: (entry_ids) => fetchApi(`${API_BASE_URL}/api/articles/batch-import`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({entry_ids}) }),
        fetchOnDemand: () => fetchApi(`${API_BASE_URL}/api/articles/fetch`, { method: 'POST' }),

        // 认证 API
        auth: {
            register: (username, password) => fetchApi(`${API_BASE_URL}/api/auth/register`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            }),
            login: (username, password) => fetchApi(`${API_BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            }),
            logout: () => fetchApi(`${API_BASE_URL}/api/auth/logout`, { method: 'POST' }),
            checkStatus: () => fetchApi(`${API_BASE_URL}/api/auth/status`),
        },

        // 使用者设定 API
        user: {
            getSettings: () => fetchApi(`${API_BASE_URL}/api/user/settings`),
            saveSettings: (settings) => fetchApi(`${API_BASE_URL}/api/user/settings`, { 
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(settings) 
            }),
        }
    };
    // --- UI Helpers ---
    function updateNav(username) {
        const mainNav = document.getElementById('main-nav');
        const authNav = document.getElementById('auth-nav');
        const userPanel = document.getElementById('user-panel');
        const usernameDisplay = document.getElementById('username-display');

        if (username) {
            isLoggedIn = true;
            mainNav.classList.remove('hidden');
            authNav.classList.add('hidden');
            userPanel.classList.remove('hidden');
            usernameDisplay.textContent = `欢迎, ${username}`;
        } else {
            isLoggedIn = false;
            mainNav.classList.add('hidden');
            authNav.classList.remove('hidden');
            userPanel.classList.add('hidden');
        }
    }


    const showToast = (message) => {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 500);
        }, 3000);
    };
    const showLoading = (message) => {
        document.getElementById('loading-text').textContent = message;
        document.getElementById('loading-overlay').classList.remove('hidden');
        document.getElementById('loading-overlay').classList.add('flex');
    };
    const hideLoading = () => {
        document.getElementById('loading-overlay').classList.add('hidden');
        document.getElementById('loading-overlay').classList.remove('flex');
    };
    const renderMathInElement = (element) => {
        if (window.renderMathInElement) {
            window.renderMathInElement(element, { delimiters: [{left: '$$', right: '$$', display: true}, {left: '$', right: '$', display: false}] });
        }
    };

    // --- Render Functions ---
    const renderers = {
        home: async () => {
            const articles = await api.getLatest();
            mainContentEl.innerHTML = `
                <header class="flex justify-between items-center mb-6">
                    <h1 class="text-3xl font-bold text-slate-100">最新论文速递</h1>
                    <button id="fetch-now-btn" title="根据预设关键词获取最新文章" class="text-slate-400 hover:text-sky-400 p-2 rounded-full">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.75 2.75L21 8"/><path d="M21 3v5h-5"/><path d="M12 21a9 9 0 0 1-9-9 9.75 9.75 0 0 1 2.75-6.75L3 8"/><path d="M3 3v5h5"/></svg>
                    </button>
                </header>
                <div id="article-list-container" class="space-y-4">
                    ${articles.map(createArticleCard).join('') || '<p class="text-slate-500">暂无最新文章。请先在“设置”中添加关键词，然后点击右上角按钮抓取。</p>'}
                </div>
            `;
        },
        favorites: async () => {
            const articles = await api.getFavorites();
            mainContentEl.innerHTML = `
                <header class="flex justify-between items-center mb-6">
                    <h1 class="text-3xl font-bold text-slate-100">我的收藏</h1>
                    <a href="${API_BASE_URL}/api/articles/favorites/export/bibtex" class="bg-sky-600 text-white font-semibold px-4 py-2 rounded-md hover:bg-sky-500 text-sm">导出全部收藏 (BibTeX)</a>
                </header>
                <div id="article-list-container" class="space-y-4">
                    ${articles.map(createArticleCard).join('') || '<p class="text-slate-500">您还没有收藏任何文章。</p>'}
                </div>
            `;
        },
        search: async () => {
            mainContentEl.innerHTML = `
                <header class="mb-6">
                    <h1 class="text-3xl font-bold text-slate-100">搜索与导入</h1>
                </header>
                <div class="relative max-w-2xl">
                    <input type="search" id="search-input" placeholder="输入关键词搜索 arXiv 上的文章..." class="w-full bg-slate-900 border border-slate-700 rounded-md p-3 pl-10 focus:outline-none focus:ring-2 focus:ring-sky-500">
                    <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                </div>
            `;
        },
        detail: async (id) => {
            currentArticleId = id;
            const article = await api.getArticleDetails(id);
            mainContentEl.innerHTML = `
                <header class="mb-6">
                    <button id="back-btn" class="text-slate-400 hover:text-white mb-4 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
                        返回
                    </button>
                    <h1 class="text-3xl font-bold text-slate-100">${article.title}</h1>
                    <p class="text-slate-400 mt-2">${article.authors.join(', ')}</p>
                </header>
                <div class="border-b border-slate-800 mb-4">
                    <nav class="flex space-x-6 -mb-px">
                        <button data-tab="summary" class="tab-item py-3 px-1 border-b-2 font-medium text-sm text-slate-400 border-transparent">智能摘要</button>
                        <button data-tab="detailed" class="tab-item py-3 px-1 border-b-2 font-medium text-sm text-slate-400 border-transparent">深度解析</button>
                        <button data-tab="images" class="tab-item py-3 px-1 border-b-2 font-medium text-sm text-slate-400 border-transparent">插图</button>
                        <button data-tab="qna" class="tab-item py-3 px-1 border-b-2 font-medium text-sm text-slate-400 border-transparent">论文问答</button>
                    </nav>
                </div>
                <div id="detail-tab-content"></div>
            `;
            renderDetailTabContent(article);
        },

        login: () => {
            mainContentEl.innerHTML = `
                <div class="max-w-md mx-auto">
                    <h1 class="text-3xl font-bold text-slate-100 mb-6">登录</h1>
                    <form id="login-form" class="space-y-4">
                        <input type="text" id="login-username" placeholder="用户名" required class="...">
                        <input type="password" id="login-password" placeholder="密码" required class="...">
                        <button type="submit" class="bg-sky-600 ...">登录</button>
                    </form>
                </div>
            `;
        },

        register: () => {
            mainContentEl.innerHTML = `
                <div class="max-w-md mx-auto">
                    <h1 class="text-3xl font-bold text-slate-100 mb-6">注册</h1>
                    <form id="register-form" class="space-y-4">
                        <input type="text" id="register-username" placeholder="用户名" required class="...">
                        <input type="password" id="register-password" placeholder="密码" required class="...">
                        <button type="submit" class="bg-sky-600 ...">注册</button>
                    </form>
                </div>
            `;
        }
    };

    function createArticleCard(article) {
        const summary = article.summary_analysis || {};
        const isFavorited = article.is_favorited;
        return `
            <div class="article-card bg-slate-900 border border-slate-800 rounded-lg p-4 flex justify-between items-start transition hover:border-slate-700 cursor-pointer" data-id="${article.id}">
                <div class="flex-grow pointer-events-none pr-4">
                    <h3 class="font-semibold text-slate-200">${article.title}</h3>
                    <p class="text-sm text-slate-400 mt-1">${article.authors.join(', ')}</p>
                </div>
                <button class="favorite-btn flex-shrink-0 ml-4 p-2 rounded-full hover:bg-slate-800" data-id="${article.id}" title="收藏">
                    <svg class="${isFavorited ? 'text-yellow-400 fill-current' : 'text-slate-500'}" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                </button>
            </div>
        `;
    }

    function renderDetailTabContent(article) {
        document.querySelectorAll('.tab-item').forEach(t => t.classList.toggle('active', t.dataset.tab === currentTab));
        const contentEl = document.getElementById('detail-tab-content');
        const summary = article.summary_analysis || {};
        const detailed = article.detailed_analysis || {};
        const qnaHistory = article.qna_history || [];
        const imagePaths = article.image_paths || [];

        const actionButtons = `
            <div class="mt-8 pt-6 border-t border-slate-800 flex items-center justify-between">
                <div class="flex items-center space-x-4">
                    <a href="${article.pdf_url}" target="_blank" class="bg-sky-600 text-white font-semibold px-4 py-2 rounded-md hover:bg-sky-500 text-sm">阅读原文</a>
                    <a href="${API_BASE_URL}/api/articles/${article.id}/export/bibtex" class="bg-slate-600 text-white font-semibold px-4 py-2 rounded-md hover:bg-slate-500 text-sm">导出 BibTeX</a>
                </div>
                <button id="delete-article-btn" data-id="${article.id}" class="bg-red-800 text-white font-semibold px-4 py-2 rounded-md hover:bg-red-700 text-sm">删除文章</button>
            </div>
        `;

        let html = '';
        if (currentTab === 'summary' || currentTab === 'detailed') {
            let contentHtml = '';
            if (currentTab === 'summary') {
                contentHtml = `<div class="bg-slate-900 p-6 rounded-lg border border-slate-800"><p class="text-slate-300 leading-relaxed">${summary.simplified_summary_zh || '无摘要'}</p></div>`;
            } else { // detailed
                contentHtml = `<div class="space-y-6 text-slate-300"><div><h3 class="font-semibold text-lg text-sky-400 mb-2">研究背景</h3><p>${detailed.background || '无'}</p></div><div><h3 class="font-semibold text-lg text-sky-400 mb-2">使用方法</h3><p>${detailed.methodology || '无'}</p></div><div><h3 class="font-semibold text-lg text-sky-400 mb-2">核心创新点</h3><ul class="list-disc list-inside space-y-1">${(detailed.key_innovations || []).map(i => `<li>${i}</li>`).join('') || '无'}</ul></div><div><h3 class="font-semibold text-lg text-sky-400 mb-2">潜在影响</h3><p>${detailed.potential_impact || '无'}</p></div></div>`;
            }
            html = `${contentHtml}${actionButtons}`;

        } else if (currentTab === 'images') {
            if (imagePaths.length > 0) {
                html = `<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${imagePaths.map(path => `
                        <div class="bg-slate-900 border border-slate-800 rounded-lg p-2">
                            <img src="${API_BASE_URL}/media/${path}" alt="Article illustration" class="w-full h-auto rounded-md">
                        </div>
                    `).join('')}
                </div>`;
            } else {
                html = '<p class="text-slate-500">本文没有提取到图片，可能原因：1) 原文不含图片；2) 未提供源码下载；3) 源码包格式特殊。</p>';
            }
        } else if (currentTab === 'qna') {
            html = `<div id="qna-history" class="mb-4 space-y-4">${qnaHistory.map(q => `<div class="text-right"><span class="bg-sky-600 text-white p-2 rounded-lg inline-block">${q.question}</span></div><div><span class="bg-slate-700 text-slate-200 p-2 rounded-lg inline-block">${q.answer}</span></div>`).join('')}</div><div class="flex"><input type="text" id="qna-input" placeholder="针对这篇文章提问..." class="flex-grow bg-slate-900 border border-slate-600 rounded-l-md p-2 focus:outline-none focus:ring-2 focus:ring-sky-500"><button id="qna-submit-btn" class="bg-sky-600 text-white font-semibold px-4 rounded-r-md hover:bg-sky-500">发送</button></div>`;
        }
        contentEl.innerHTML = html;
        renderMathInElement(contentEl);
    }
    
    function renderKeywords(keywords) {
        const keywordsListEl = document.getElementById('keywords-list');
        keywordsListEl.innerHTML = keywords.map(kw => `
            <span class="bg-slate-700 text-slate-200 text-sm px-2 py-1 rounded flex items-center">
                ${kw}
                <button data-keyword="${kw}" class="delete-keyword-btn ml-2 text-slate-400 hover:text-red-400">&times;</button>
            </span>
        `).join('') || '<p class="text-sm text-slate-400">暂无关键词</p>';
    }
    
    function renderSearchResults(results) {
        const searchResultsList = document.getElementById('search-results-list');
        if (results.length === 0) {
            searchResultsList.innerHTML = '<p class="text-slate-400 text-center">未找到相关文章。</p>';
            return;
        }
        searchResultsList.innerHTML = results.map(r => `
            <div class="p-4 border-b border-slate-700">
                <div class="flex items-start">
                    <input type="checkbox" data-id="${r.entry_id}" class="mt-1.5 mr-4 bg-slate-900 border-slate-600 text-sky-500 focus:ring-sky-500" ${r.is_imported ? 'disabled' : ''}>
                    <div class="flex-grow">
                        <h4 class="font-semibold text-slate-200">${r.title}</h4>
                        <p class="text-sm text-slate-400 mt-1">${r.authors.join(', ')}</p>
                        <p class="text-sm text-slate-400 mt-2">${r.summary.substring(0, 200)}...</p>
                        ${r.is_imported ? '<span class="text-xs text-green-400 mt-2 inline-block">已导入</span>' : ''}
                    </div>
                </div>
            </div>
        `).join('');
    }

    // --- Navigation & Event Handlers ---
    async function navigate(view) {
        if(!isLoggedIn && !['login', 'register'].includes(view)) {
            view = 'login';
        }
        currentView = view;
        document.querySelectorAll('.nav-item').forEach(item => item.classList.toggle('active', item.dataset.view === view));
        
        mainContentEl.innerHTML = '<p class="text-slate-500">加载中...</p>';
        await renderers[view]();
    }

    async function handleLogout() {
        await api.auth.logout();
        updateNav(null);
        navigate('login');
    }

    async function handleFetchNow() {
        showLoading('已开始在后台获取最新文章...');
        await api.fetchOnDemand();
        hideLoading();
        showToast('获取完成！正在刷新列表...');
        await navigate(currentView);
    }
    
    async function handleKeywordAdd() {
        const newKeywordInput = document.getElementById('new-keyword-input');
        const newKeyword = newKeywordInput.value.trim();
        if (newKeyword) {
            await api.addKeyword(newKeyword);
            newKeywordInput.value = '';
            const keywords = await api.getKeywords();
            renderKeywords(keywords);
        }
    }

    async function handleKeywordDelete(keyword) {
        await api.deleteKeyword(keyword);
        const keywords = await api.getKeywords();
        renderKeywords(keywords);
    }
    
    async function handleArticleDelete(id) {
        if (confirm('您确定要删除这篇文章吗？此操作不可恢复。')) {
            await api.deleteArticle(id);
            showToast('文章已删除。');
            navigate('home');
        }
    }

    async function handleSearch(query) {
        if (!query) return;
        searchResultsModal.querySelector('#search-results-list').innerHTML = '<p class="text-slate-400 text-center">正在搜索...</p>';
        searchResultsModal.classList.remove('hidden');
        searchResultsModal.classList.add('flex');
        const results = await api.searchArticles(query);
        renderSearchResults(results);
    }

    async function handleBatchImport() {
        const selectedIds = Array.from(searchResultsModal.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.dataset.id);
        if (selectedIds.length === 0) return;
        
        const batchImportBtn = document.getElementById('batch-import-btn');
        batchImportBtn.disabled = true;
        batchImportBtn.textContent = '正在导入...';
        
        showLoading(`正在导入 ${selectedIds.length} 篇文章...`);
        await api.batchImport(selectedIds);
        hideLoading();
        
        searchResultsModal.classList.add('hidden');
        batchImportBtn.disabled = false;
        batchImportBtn.textContent = '导入并分析';
        
        showToast('导入成功！');
        await navigate('home');
    }

    async function handleQnaSubmit() {
        const input = document.getElementById('qna-input');
        const question = input.value.trim();
        if (!question || !currentArticleId) return;
        
        const historyEl = document.getElementById('qna-history');
        historyEl.innerHTML += `<div class="text-right"><span class="bg-sky-600 text-white p-2 rounded-lg inline-block">${question}</span></div>`;
        input.value = '';
        input.disabled = true;
        
        await api.postQuestion(currentArticleId, question);
        const article = await api.getArticleDetails(currentArticleId);
        renderDetailTabContent(article);
    }
    
    async function handleSaveSettings() {
        const settings = {
            api_key: document.getElementById('setting-api-key').value,
            model_name: document.getElementById('setting-model-name').value,
            fetch_count: document.getElementById('setting-fetch-count').value,
        };
        await api.saveSettings(settings);
        showToast('设置已保存！');
        settingsModal.classList.add('hidden');
    }
    
    async function handleOpenSettings() {
        const settings = await api.getSettings();
        document.getElementById('setting-api-key').value = settings.api_key || '';
        document.getElementById('setting-model-name').value = settings.model_name || 'deepseek-chat';
        document.getElementById('setting-fetch-count').value = settings.fetch_count || 5;
        
        const keywords = await api.getKeywords();
        renderKeywords(keywords);
        settingsModal.classList.remove('hidden');
        settingsModal.classList.add('flex');
    }
    
    async function handleFavoriteToggle(button) {
        const id = button.dataset.id;
        const result = await api.toggleFavorite(id);
        const svg = button.querySelector('svg');
        svg.classList.toggle('text-yellow-400', result.is_favorited);
        svg.classList.toggle('fill-current', result.is_favorited);
        svg.classList.toggle('text-slate-500', !result.is_favorited);

        if (currentView === 'favorites' && !result.is_favorited) {
            button.closest('.article-card').remove();
        }
    }

    function setupEventListeners() {
        // Left Nav
        navPanel.addEventListener('click', (e) => {
            const navLink = e.target.closest('.nav-item');
            if (navLink) {
                e.preventDefault();
                navigate(navLink.dataset.view);
            }
            if (e.target.closest('#settings-btn')) {
                handleOpenSettings();
            }
            if (e.target.closest('#logout-btn')) {
                handleLogout();
            }
        });

        // Main Content Area
        mainContentEl.addEventListener('click', async (e) => {
            const favoriteButton = e.target.closest('.favorite-btn');
            const articleCard = e.target.closest('.article-card');
            const tabItem = e.target.closest('.tab-item');
            const backBtn = e.target.closest('#back-btn');
            const fetchNowBtn = e.target.closest('#fetch-now-btn');
            const deleteBtn = e.target.closest('#delete-article-btn'); // *** 新增 ***

            if (deleteBtn) { // *** 新增 ***
                handleArticleDelete(deleteBtn.dataset.id);
            } else if (fetchNowBtn) {
                handleFetchNow();
            } else if (favoriteButton) {
                e.stopPropagation();
                handleFavoriteToggle(favoriteButton);
            } else if (articleCard) {
                renderers.detail(articleCard.dataset.id);
            } else if (tabItem) {
                currentTab = tabItem.dataset.tab;
                const article = await api.getArticleDetails(currentArticleId);
                renderDetailTabContent(article);
            } else if (backBtn) {
                navigate(currentView);
            }
        });
        
        mainContentEl.addEventListener('keyup', (e) => {
            if (e.target.id === 'search-input' && e.key === 'Enter') {
                handleSearch(e.target.value);
            }
            if (e.target.id === 'qna-input' && e.key === 'Enter') {
                handleQnaSubmit();
            }
        });
        
        mainContentEl.addEventListener('click', (e) => {
             if (e.target.id === 'qna-submit-btn') {
                handleQnaSubmit();
            }
        });

        // Settings Modal
        settingsModal.addEventListener('click', async (e) => {
            if (e.target.id === 'close-modal-btn' || e.target.id === 'settings-modal') {
                settingsModal.classList.add('hidden');
            } else if (e.target.id === 'add-keyword-btn') {
                handleKeywordAdd();
            } else if (e.target.closest('.delete-keyword-btn')) {
                handleKeywordDelete(e.target.closest('.delete-keyword-btn').dataset.keyword);
            } else if (e.target.id === 'save-settings-btn') {
                handleSaveSettings();
            }
        });

        // Search Results Modal
        searchResultsModal.addEventListener('click', (e) => {
             if (e.target.id === 'close-search-modal-btn' || e.target.id === 'search-results-modal') {
                searchResultsModal.classList.add('hidden');
            } else if (e.target.id === 'batch-import-btn') {
                handleBatchImport();
            }
        });
        searchResultsModal.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox') {
                const count = searchResultsModal.querySelectorAll('input[type="checkbox"]:checked').length;
                searchResultsModal.querySelector('#selection-counter').textContent = `已选择 ${count} 篇`;
                searchResultsModal.querySelector('#batch-import-btn').disabled = count === 0;
            }
        });
    }
    
    // --- Initial Load ---
    async function initializeApp() {
        try {
            const status = await api.auth.checkStatus();
            if (status.isLoggedIn) {
                updateNav(status.username);
                navigate('home');
            } else {
                updateNav(null);
                navigate('login');
            }
        } catch (error) {
            updateNav(null);
            navigate('login');
        }
    }
    setupEventListeners();
    initializeApp(); // *** 修正 #3: 使用正确的初始化函数 ***
});