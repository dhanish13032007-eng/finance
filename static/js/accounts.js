/**
 * Accounts JS
 */
const API = '';
const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

function fmt(n) { return '₹' + Number(n||0).toLocaleString('en-IN', {minimumFractionDigits:2}); }

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || '📢'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3800);
}

const modal = document.getElementById('accountModal');
function openModal() { modal.classList.add('active'); }
function closeModal() { modal.classList.remove('active'); document.getElementById('accountForm').reset(); }

async function loadAccounts() {
    try {
        const res = await fetch(`${API}/api/accounts`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.status === 401) return window.location.href = '/login';
        
        const data = await res.json();
        if (data.status !== 'success') throw new Error(data.message);
        
        document.getElementById('netWorthDisplay').textContent = `Total Net Worth: ${fmt(data.data.net_worth)}`;
        
        const grid = document.getElementById('accountsGrid');
        if (!data.data.accounts.length) {
            grid.innerHTML = `<div class="empty-state" style="grid-column: 1/-1">
                <div class="empty-icon">🏦</div>
                <h3>No Accounts Added</h3>
                <p>Click '+ Add Account' to link your bank, cash, or wallet.</p>
            </div>`;
            return;
        }
        
        grid.innerHTML = data.data.accounts.map(a => `
            <div class="account-card">
                <div class="account-header">
                    <span class="account-type">${a.type}</span>
                    <button class="account-actions delete-btn" onclick="deleteAccount(${a.id})">Delete</button>
                </div>
                <div class="account-name">${a.name}</div>
                <div class="account-balance ${a.current_balance < 0 ? 'text-red' : ''}">${fmt(a.current_balance)}</div>
            </div>
        `).join('');
    } catch (e) {
        showToast('Error loading accounts', 'error');
    }
}

document.getElementById('accountForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('accName').value;
    const type = document.getElementById('accType').value;
    const balance = document.getElementById('accBalance').value || 0;
    
    try {
        const res = await fetch(`${API}/api/accounts`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type, balance })
        });
        
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Account added successfully');
            closeModal();
            loadAccounts();
        } else {
            showToast(data.message, 'error');
        }
    } catch {
        showToast('Network error', 'error');
    }
});

async function deleteAccount(id) {
    if (!confirm('Are you sure? This will delete all transactions linked to this account.')) return;
    try {
        const res = await fetch(`${API}/api/accounts/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Account deleted');
            loadAccounts();
        } else {
            showToast(data.message || 'Failed to delete account', 'error');
            console.error(data);
        }
    } catch (e) {
        showToast('Network error', 'error');
        console.error(e);
    }
}

document.addEventListener('DOMContentLoaded', loadAccounts);
