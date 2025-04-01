const newsListElement = document.getElementById('news-list');
const statusMessageElement = document.getElementById('status-message');
const paramsForm = document.getElementById('news-params-form'); // 獲取表單

// --- 函數：顯示狀態消息 ---
function showStatus(message, type = 'loading') {
    statusMessageElement.textContent = message;
    statusMessageElement.className = `status ${type}`;
    if (type === 'success') {
        setTimeout(() => {
            statusMessageElement.className = `status success`;
        }, 2000);
    } else {
         statusMessageElement.style.display = 'block';
    }
}

// --- 函數：顯示新聞 ---
function displayNews(articles) {
    newsListElement.innerHTML = '';
    if (!articles || articles.length === 0) {
        showStatus('目前沒有新聞可顯示。', 'success');
        return;
    }
    articles.forEach(article => {
        const listItem = document.createElement('li');
        const titleLink = document.createElement('a');
        titleLink.href = article.url;
        titleLink.textContent = article.title || '無標題';
        titleLink.target = '_blank';
        titleLink.rel = 'noopener noreferrer';
        const description = document.createElement('p');
        description.textContent = article.description || '';
        const source = document.createElement('div');
        source.className = 'source';
        source.textContent = `來源: ${article.source?.name || '未知來源'}`;
        listItem.appendChild(titleLink);
        if (article.description) {
            listItem.appendChild(description);
        }
        listItem.appendChild(source);
        newsListElement.appendChild(listItem);
    });
    showStatus('新聞已更新！', 'success');
}

// --- 函數：從後端獲取新聞 ---
async function fetchNews(event) { // <--- 確保接收 event 參數

    // --- 關鍵：阻止表單默認提交行為 ---
    if (event) { // 只有在事件觸發時 (而不是初始加載時) 才執行
        event.preventDefault(); // <--- 這一行至關重要！
        console.log("Form submit event prevented."); // 添加調試信息
    }
    // -------------------------------------

    console.log("正在獲取新聞...");
    showStatus('正在更新新聞...', 'loading');

    const country = paramsForm.country.value;
    const category = paramsForm.category.value;
    const pageSize = paramsForm.pageSize.value;
    const sortBy = paramsForm.sortBy.value;

    const queryString = `country=${country}&category=${category}&pageSize=${pageSize}&sortBy=${sortBy}`;
    const apiUrl = `/get_news?${queryString}`;
    console.log("Requesting API:", apiUrl); // 打印請求的 API URL

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            let errorMsg = `伺服器錯誤: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                if (errorData && errorData.message) {
                    errorMsg = errorData.message;
                }
            } catch (e) { /* ignore json parsing error */ }
            throw new Error(errorMsg);
        }
        const data = await response.json();
        if (data.status === 'ok') {
            displayNews(data.articles);
        } else {
            throw new Error(data.message || '獲取新聞時發生未知錯誤。');
        }
    } catch (error) {
        console.error('獲取新聞失敗:', error);
        showStatus(`錯誤: ${error.message}`, 'error');
    }
}

// --- 初始化和事件監聽 ---
// 頁面載入後立即獲取一次新聞 (使用表單中的初始值)
fetchNews();

// 將 fetchNews 函數綁定到表單的 submit 事件
paramsForm.addEventListener('submit', fetchNews); // <--- 確保這一行存在且正確

// (如果你有定時器，確保它也被移除或註釋掉了，除非你確實需要)
// const UPDATE_INTERVAL = 10000;
// setInterval(fetchNews, UPDATE_INTERVAL);