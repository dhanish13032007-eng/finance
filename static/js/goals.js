/**
 * Goals JS
 */
const API = '';
const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

function fmt(n) { return '₹' + Number(n||0).toLocaleString('en-IN', {maximumFractionDigits:0}); }

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || '📢'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3800);
}

const gModal = document.getElementById('goalModal');
function openGoalModal() { gModal.classList.add('active'); }
function closeGoalModal() { gModal.classList.remove('active'); document.getElementById('goalForm').reset(); }

const fModal = document.getElementById('fundModal');
function openFundModal(id) { document.getElementById('fundGoalId').value = id; fModal.classList.add('active'); }
function closeFundModal() { fModal.classList.remove('active'); document.getElementById('fundForm').reset(); }

async function loadGoals() {
    try {
        const res = await fetch(`${API}/api/goals`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.status === 401) return window.location.href = '/login';
        
        const data = await res.json();
        if (data.status !== 'success') throw new Error(data.message);
        
        const grid = document.getElementById('goalsGrid');
        if (!data.data.length) {
            grid.innerHTML = `<div class="empty-state" style="grid-column: 1/-1">
                <div class="empty-icon">🎯</div>
                <h3>No Goals Set</h3>
                <p>Click '+ New Goal' to start saving for your next milestone.</p>
            </div>`;
            return;
        }
        
        grid.innerHTML = data.data.map(g => {
            const isComplete = g.progress_percent >= 100;
            const barColor = isComplete ? '#00B894' : g.color || '#6C5CE7';
            return `
            <div class="goal-card">
                <div class="goal-header">
                    <div>
                        <div class="goal-title">${g.name} ${isComplete ? '🎉' : ''}</div>
                        ${g.deadline ? `<div class="goal-deadline">Target: ${new Date(g.deadline).toLocaleDateString()}</div>` : ''}
                    </div>
                    <span class="status-pill ${isComplete ? 'safe' : 'primary'}" style="margin:0">${g.progress_percent}%</span>
                </div>
                
                <div class="goal-amounts">
                    <span>Saved: <strong>${fmt(g.current_amount)}</strong></span>
                    <span style="color:var(--text-muted)">of ${fmt(g.target_amount)}</span>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${g.progress_percent}%; background: ${barColor}"></div>
                </div>
                
                <div class="goal-actions">
                    <button class="btn-add" onclick="openFundModal(${g.id})" ${isComplete ? 'disabled style="opacity:0.5"' : ''}>+ Add Funds</button>
                    <button class="btn-del" onclick="deleteGoal(${g.id})">Delete</button>
                </div>
            </div>`;
        }).join('');
    } catch {
        showToast('Error loading goals', 'error');
    }
}

document.getElementById('goalForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('gName').value;
    const target = document.getElementById('gTarget').value;
    const deadline = document.getElementById('gDeadline').value;
    
    try {
        const res = await fetch(`${API}/api/goals`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, target_amount: target, deadline })
        });
        
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Goal created!');
            closeGoalModal();
            loadGoals();
        } else showToast(data.message, 'error');
    } catch { showToast('Network error', 'error'); }
});

document.getElementById('fundForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('fundGoalId').value;
    const add_amount = document.getElementById('fAmount').value;
    
    try {
        const res = await fetch(`${API}/api/goals/${id}`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ add_amount })
        });
        
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Funds added successfully!');
            closeFundModal();
            loadGoals();
        } else showToast(data.message, 'error');
    } catch { showToast('Network error', 'error'); }
});

async function deleteGoal(id) {
    if (!confirm('Are you sure you want to delete this goal?')) return;
    try {
        const res = await fetch(`${API}/api/goals/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Goal deleted');
            loadGoals();
        }
    } catch { showToast('Network error', 'error'); }
}

document.addEventListener('DOMContentLoaded', loadGoals);
