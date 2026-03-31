/**
 * Receipt Scanning JS
 */
const API = '';
const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

function authHeaders() {
    return { 'Authorization': `Bearer ${token}` };
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || '📢'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3800);
}

// Switch UI Steps
const step1 = document.getElementById('uploadStep');
const smsStep = document.getElementById('smsStep');
const step2 = document.getElementById('processingStep');
const step3 = document.getElementById('resultStep');

let currentMode = 'receipt';

function switchTab(mode) {
    currentMode = mode;
    document.getElementById('tabReceipt').className = mode === 'receipt' ? 'btn btn-primary' : 'btn btn-secondary';
    document.getElementById('tabSMS').className = mode === 'sms' ? 'btn btn-primary' : 'btn btn-secondary';
    resetScanner();
}

function resetScanner() {
    if (currentMode === 'receipt') {
        step1.classList.remove('hidden');
        smsStep.classList.add('hidden');
    } else {
        step1.classList.add('hidden');
        smsStep.classList.remove('hidden');
    }
    step2.classList.add('hidden');
    step3.classList.add('hidden');
    document.getElementById('fileInput').value = '';
    
    const smsInput = document.getElementById('smsText');
    if (smsInput) smsInput.value = '';
}

// Drag and Drop
const dropArea = document.getElementById('dropArea');

dropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropArea.classList.add('dragover');
});
dropArea.addEventListener('dragleave', () => {
    dropArea.classList.remove('dragover');
});
dropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    dropArea.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        processFile(e.dataTransfer.files[0]);
    }
});

document.getElementById('fileInput').addEventListener('change', (e) => {
    if (e.target.files.length) {
        processFile(e.target.files[0]);
    }
});

async function processFile(file) {
    if (!file.type.match('image.*') && !file.type.match('application/pdf')) {
        return showToast('Please upload an image or PDF', 'error');
    }

    // Show processing loader
    step1.classList.add('hidden');
    step2.classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API}/api/upload/receipt`, {
            method: 'POST',
            headers: authHeaders(),
            body: formData
        });

        const data = await res.json();
        if (data.status !== 'success') {
            throw new Error(data.message || 'Scanning Failed');
        }

        // Fill form
        document.getElementById('scannedAmount').value = data.data.amount;
        document.getElementById('scannedDate').value = data.data.date;
        document.getElementById('scannedMerchant').value = data.data.merchant;
        
        const catSelect = document.getElementById('scannedCategory');
        if (Array.from(catSelect.options).some(o => o.value === data.data.suggested_category)) {
            catSelect.value = data.data.suggested_category;
        } else {
            catSelect.value = 'Other';
        }

        document.getElementById('successPill').textContent = 'OCR Success';

        // Load Accounts dropdown
        await loadAccounts();

        // Show verification form
        step2.classList.add('hidden');
        step3.classList.remove('hidden');

    } catch (err) {
        resetScanner();
        showToast(err.message, 'error');
    }
}

async function processSMS() {
    const text = document.getElementById('smsText').value.trim();
    if (!text) return showToast('Please enter SMS text', 'error');

    smsStep.classList.add('hidden');
    step2.classList.remove('hidden');

    try {
        const res = await fetch(`${API}/api/upload/sms`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ sms_text: text })
        });

        const data = await res.json();
        if (data.status !== 'success') {
            throw new Error(data.message || 'Parsing Failed');
        }

        document.getElementById('scannedAmount').value = data.data.amount;
        
        // Auto-fill today's date for SMS
        document.getElementById('scannedDate').value = new Date().toISOString().split('T')[0];
        document.getElementById('scannedMerchant').value = data.data.merchant;
        
        const catSelect = document.getElementById('scannedCategory');
        if (Array.from(catSelect.options).some(o => o.value === data.data.suggested_category)) {
            catSelect.value = data.data.suggested_category;
        } else {
            catSelect.value = 'Other';
        }

        document.getElementById('successPill').textContent = 'SMS Parsed';
        await loadAccounts();

        step2.classList.add('hidden');
        step3.classList.remove('hidden');

    } catch (err) {
        resetScanner();
        showToast(err.message, 'error');
    }
}

async function loadAccounts() {
    try {
        const res = await fetch(`${API}/api/accounts`, { headers: { 'Authorization': `Bearer ${token}` }});
        if (!res.ok) return;
        const data = await res.json();
        const sel = document.getElementById('scannedAccount');
        sel.innerHTML = data.data.accounts.map(a => `<option value="${a.id}">${a.name} (${a.type})</option>`).join('');
    } catch {}
}

document.getElementById('saveExpenseForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const account_id = document.getElementById('scannedAccount').value;
    const amount = document.getElementById('scannedAmount').value;
    const category = document.getElementById('scannedCategory').value;
    const date = document.getElementById('scannedDate').value;
    const description = document.getElementById('scannedMerchant').value;

    try {
        const res = await fetch(`${API}/api/expenses`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_id, amount, category, date, description })
        });
        
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Expense saved via OCR successfully!');
            setTimeout(() => window.location.href = '/expenses', 1200);
        } else {
            showToast(data.message, 'error');
        }
    } catch (e) {
        showToast('Network error while saving', 'error');
    }
});
