/**
 * Income Module
 * Full CRUD operations for income records with modal form.
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

// ══════════════════════════════════
//  LOAD INCOME DATA
// ══════════════════════════════════

async function loadIncome() {
    try {
        const res = await fetch(`${API}/api/income`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();

        if (data.status !== 'success') return;

        const incomes = data.data;
        const total = incomes.reduce((sum, i) => sum + i.amount, 0);

        document.getElementById('totalIncome').textContent = fmt(total);
        document.getElementById('totalRecords').textContent = incomes.length;

        renderTable(incomes);
    } catch (err) {
        console.error('Load income error:', err);
        showToast('Failed to load income data', 'error');
    }
}

function renderTable(incomes) {
    const body = document.getElementById('incomeBody');

    if (!incomes.length) {
        body.innerHTML = `<tr><td colspan="5">
            <div class="empty-state">
                <div class="empty-icon">💰</div>
                <h3>No income records yet</h3>
                <p>Click "+ Add Income" to add your first entry.</p>
            </div>
        </td></tr>`;
        return;
    }

    body.innerHTML = incomes.map(i => `
        <tr>
            <td><strong>${escapeHtml(i.source)}</strong></td>
            <td class="amount text-green">${fmt(i.amount)}</td>
            <td>${i.date}</td>
            <td>${escapeHtml(i.description || '—')}</td>
            <td class="actions">
                <button class="edit-btn" onclick="openEditModal(${i.id}, '${escapeAttr(i.source)}', ${i.amount}, '${i.date}', '${escapeAttr(i.description || '')}')" title="Edit">✏️</button>
                <button class="delete-btn" onclick="deleteIncome(${i.id})" title="Delete">🗑️</button>
            </td>
        </tr>
    `).join('');
}

// ── HTML escaping ──
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ══════════════════════════════════
//  MODAL OPERATIONS
// ══════════════════════════════════

function openAddModal() {
    document.getElementById('modalTitle').textContent = 'Add Income';
    document.getElementById('submitBtn').textContent = 'Add Income';
    document.getElementById('editId').value = '';
    document.getElementById('source').value = '';
    document.getElementById('amount').value = '';
    document.getElementById('date').value = new Date().toISOString().split('T')[0];
    document.getElementById('description').value = '';
    document.getElementById('incomeModal').classList.add('active');
}

function openEditModal(id, source, amount, date, description) {
    document.getElementById('modalTitle').textContent = 'Edit Income';
    document.getElementById('submitBtn').textContent = 'Update Income';
    document.getElementById('editId').value = id;
    document.getElementById('source').value = source;
    document.getElementById('amount').value = amount;
    document.getElementById('date').value = date;
    document.getElementById('description').value = description;
    document.getElementById('incomeModal').classList.add('active');
}

function closeModal() {
    document.getElementById('incomeModal').classList.remove('active');
}

// Close modal on outside click
document.getElementById('incomeModal').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeModal();
});

// ══════════════════════════════════
//  ADD / UPDATE INCOME
// ══════════════════════════════════

document.getElementById('incomeForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const editId = document.getElementById('editId').value;
    const payload = {
        source: document.getElementById('source').value.trim(),
        amount: parseFloat(document.getElementById('amount').value),
        date: document.getElementById('date').value,
        description: document.getElementById('description').value.trim()
    };

    if (!payload.source || !payload.amount || !payload.date) {
        showToast('Please fill all required fields', 'error');
        return;
    }

    if (payload.amount <= 0) {
        showToast('Amount must be positive', 'error');
        return;
    }

    try {
        const isEdit = !!editId;
        const url = isEdit ? `${API}/api/income/${editId}` : `${API}/api/income`;
        const method = isEdit ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method,
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast(isEdit ? 'Income updated!' : 'Income added!');
            closeModal();
            loadIncome();
        } else {
            showToast(data.message || 'Operation failed', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
});

// ══════════════════════════════════
//  DELETE INCOME
// ══════════════════════════════════

async function deleteIncome(id) {
    if (!confirm('Are you sure you want to delete this income record?')) return;

    try {
        const res = await fetch(`${API}/api/income/${id}`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast('Income deleted');
            loadIncome();
        } else {
            showToast(data.message || 'Delete failed', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
}

// ── CSV Export ──
function exportIncomeCSV() {
    fetch(`${API}/api/reports/export/income`, { headers: authHeaders() })
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'income.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showToast('Income CSV downloaded!');
        })
        .catch(() => showToast('Export failed', 'error'));
}

// ── Init ──
document.addEventListener('DOMContentLoaded', loadIncome);
