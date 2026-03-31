/**
 * Expenses Module
 * Full CRUD with advanced filtering (date, category, amount range, keyword).
 */

const API = '';
const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

function authHeaders() {
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}

function fmt(n) {
    return '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✅', error: '❌', warning: '⚠️' };
    toast.innerHTML = `<span>${icons[type] || '📢'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3500);
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// ── Categories ──
const CATEGORIES = [
    'Food & Dining', 'Transportation', 'Housing', 'Utilities',
    'Healthcare', 'Entertainment', 'Shopping', 'Education',
    'Insurance', 'Savings & Investments', 'Personal Care',
    'Travel', 'Gifts & Donations', 'Subscriptions', 'Other'
];

function populateCategories() {
    // Modal category select
    const modalSel = document.getElementById('category');
    modalSel.innerHTML = CATEGORIES.map(c => `<option value="${c}">${c}</option>`).join('');

    // Filter category select
    const filterSel = document.getElementById('filterCategory');
    filterSel.innerHTML = '<option value="">All Categories</option>' +
        CATEGORIES.map(c => `<option value="${c}">${c}</option>`).join('');
}

// ── Accounts ──
async function loadAccounts() {
    try {
        const res = await fetch(`${API}/api/accounts`, { headers: authHeaders() });
        const data = await res.json();
        const sel = document.getElementById('account_id');
        sel.innerHTML = data.data.accounts.map(a => `<option value="${a.id}">${a.name} (${a.type})</option>`).join('');
    } catch {}
}

// ══════════════════════════════════
//  LOAD EXPENSES
// ══════════════════════════════════

async function loadExpenses(params = {}) {
    try {
        const query = new URLSearchParams();
        if (params.start_date) query.set('start_date', params.start_date);
        if (params.end_date) query.set('end_date', params.end_date);
        if (params.category) query.set('category', params.category);
        if (params.min_amount) query.set('min_amount', params.min_amount);
        if (params.max_amount) query.set('max_amount', params.max_amount);
        if (params.keyword) query.set('keyword', params.keyword);

        const url = `${API}/api/expenses${query.toString() ? '?' + query.toString() : ''}`;
        const res = await fetch(url, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();

        if (data.status !== 'success') return;

        const expenses = data.data;
        const total = expenses.reduce((sum, e) => sum + e.amount, 0);

        document.getElementById('totalExpenses').textContent = fmt(total);
        document.getElementById('totalRecords').textContent = expenses.length;

        const filterInfo = document.getElementById('filterInfo');
        if (Object.values(params).some(v => v)) {
            filterInfo.textContent = `Showing ${expenses.length} filtered results`;
        } else {
            filterInfo.textContent = '';
        }

        renderTable(expenses);
    } catch (err) {
        console.error('Load expenses error:', err);
        showToast('Failed to load expenses', 'error');
    }
}

function renderTable(expenses) {
    const body = document.getElementById('expenseBody');

    if (!expenses.length) {
        body.innerHTML = `<tr><td colspan="5">
            <div class="empty-state">
                <div class="empty-icon">💸</div>
                <h3>No expenses found</h3>
                <p>Add an expense or adjust your filters.</p>
            </div>
        </td></tr>`;
        return;
    }

    body.innerHTML = expenses.map(e => `
        <tr>
            <td><span class="badge">${escapeHtml(e.category)}</span></td>
            <td class="amount text-red">-${fmt(e.amount)}</td>
            <td>${e.date}</td>
            <td>${escapeHtml(e.description || '—')}</td>
            <td class="actions">
                <button class="edit-btn" onclick="openEditModal(${e.id}, '${escapeAttr(e.category)}', ${e.amount}, '${e.date}', '${escapeAttr(e.description || '')}')" title="Edit">✏️</button>
                <button class="delete-btn" onclick="deleteExpense(${e.id})" title="Delete">🗑️</button>
            </td>
        </tr>
    `).join('');
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ══════════════════════════════════
//  FILTERS
// ══════════════════════════════════

function applyFilters() {
    const params = {
        start_date: document.getElementById('filterStartDate').value,
        end_date: document.getElementById('filterEndDate').value,
        category: document.getElementById('filterCategory').value,
        min_amount: document.getElementById('filterMinAmount').value,
        max_amount: document.getElementById('filterMaxAmount').value,
        keyword: document.getElementById('filterKeyword').value.trim()
    };
    loadExpenses(params);
}

function clearFilters() {
    document.getElementById('filterStartDate').value = '';
    document.getElementById('filterEndDate').value = '';
    document.getElementById('filterCategory').value = '';
    document.getElementById('filterMinAmount').value = '';
    document.getElementById('filterMaxAmount').value = '';
    document.getElementById('filterKeyword').value = '';
    loadExpenses();
}

// ══════════════════════════════════
//  MODAL OPERATIONS
// ══════════════════════════════════

function openAddModal() {
    document.getElementById('modalTitle').textContent = 'Add Expense';
    document.getElementById('submitBtn').textContent = 'Add Expense';
    document.getElementById('editId').value = '';
    document.getElementById('category').value = CATEGORIES[0];
    document.getElementById('amount').value = '';
    document.getElementById('date').value = new Date().toISOString().split('T')[0];
    document.getElementById('description').value = '';
    document.getElementById('expenseModal').classList.add('active');
}

function openEditModal(id, category, amount, date, description) {
    document.getElementById('modalTitle').textContent = 'Edit Expense';
    document.getElementById('submitBtn').textContent = 'Update Expense';
    document.getElementById('editId').value = id;
    document.getElementById('category').value = category;
    document.getElementById('amount').value = amount;
    document.getElementById('date').value = date;
    document.getElementById('description').value = description;
    document.getElementById('expenseModal').classList.add('active');
}

function closeModal() {
    document.getElementById('expenseModal').classList.remove('active');
}

document.getElementById('expenseModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
});

// ══════════════════════════════════
//  ADD / UPDATE EXPENSE
// ══════════════════════════════════

document.getElementById('expenseForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const editId = document.getElementById('editId').value;
    const payload = {
        category: document.getElementById('category').value,
        amount: parseFloat(document.getElementById('amount').value),
        date: document.getElementById('date').value,
        description: document.getElementById('description').value.trim()
    };
    
    // account_id only needed for creations right now (as per backend logic)
    const accSelect = document.getElementById('account_id');
    if (accSelect && accSelect.value && !editId) {
        payload.account_id = accSelect.value;
    }

    if (!payload.category || !payload.amount || !payload.date) {
        showToast('Please fill all required fields', 'error');
        return;
    }

    if (payload.amount <= 0) {
        showToast('Amount must be positive', 'error');
        return;
    }

    try {
        const isEdit = !!editId;
        const url = isEdit ? `${API}/api/expenses/${editId}` : `${API}/api/expenses`;
        const method = isEdit ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method,
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast(isEdit ? 'Expense updated!' : 'Expense added!');
            closeModal();
            loadExpenses();
        } else {
            showToast(data.message || 'Operation failed', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
});

// ══════════════════════════════════
//  DELETE EXPENSE
// ══════════════════════════════════

async function deleteExpense(id) {
    if (!confirm('Are you sure you want to delete this expense?')) return;

    try {
        const res = await fetch(`${API}/api/expenses/${id}`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast('Expense deleted');
            loadExpenses();
        } else {
            showToast(data.message || 'Delete failed', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
}

// ── CSV Export ──
function exportExpensesCSV() {
    fetch(`${API}/api/reports/export/expenses`, { headers: authHeaders() })
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'expenses.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast('Expenses CSV downloaded!');
        })
        .catch(() => showToast('Export failed', 'error'));
}

async function uploadCSV(inputEl, type) {
    const file = inputEl.files[0];
    if (!file) return;
    
    const account_id = prompt('Enter the internal Account ID to import to (default is 1 for Main Bank):', '1');
    if (!account_id) { inputEl.value = ''; return; }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('account_id', account_id);

    try {
        const res = await fetch(`${API}/api/upload/csv`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }, // Form data, don't set Content-Type
            body: formData
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast(data.message, 'success');
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showToast(data.message, 'error');
        }
    } catch {
        showToast('CSV Upload Failed', 'error');
    }
    inputEl.value = '';
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
    populateCategories();
    loadAccounts();
    loadExpenses();
});
