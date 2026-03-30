/**
 * Dashboard Module
 * Loads stats, charts, predictions, insights, budgets, and recent transactions.
 */

const API = '';
const token = localStorage.getItem('token');

// ── Auth guard ──
if (!token) window.location.href = '/login';

// ── Helpers ──
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

// ── Chart instances ──
let trendChart = null;
let categoryChart = null;

// ── Category colors ──
const CHART_COLORS = [
    '#6C5CE7', '#00CEC9', '#FD79A8', '#FDCB6E', '#00B894',
    '#74B9FF', '#E17055', '#A29BFE', '#55E6C1', '#FF6B6B',
    '#48DBFB', '#FF9FF3', '#54A0FF', '#5F27CD', '#01A3A4'
];

// ── Load user info ──
const user = JSON.parse(localStorage.getItem('user') || '{}');
document.getElementById('userName').textContent = user.name || '';

// ══════════════════════════════════
//  LOAD DASHBOARD DATA
// ══════════════════════════════════

async function loadDashboard() {
    try {
        const res = await fetch(`${API}/api/dashboard`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();
        if (data.status !== 'success') return;

        const d = data.data;

        // Stats cards
        document.getElementById('totalIncome').textContent = fmt(d.totals.total_income);
        document.getElementById('totalExpenses').textContent = fmt(d.totals.total_expenses);
        document.getElementById('netSavings').textContent = fmt(d.totals.net_savings);
        document.getElementById('savingsPct').textContent = `Savings: ${d.totals.savings_percentage}%`;
        document.getElementById('monthIncome').textContent = `This month: ${fmt(d.current_month.income)}`;
        document.getElementById('monthExpenses').textContent = `This month: ${fmt(d.current_month.expenses)}`;
        document.getElementById('monthSavings').textContent = fmt(d.current_month.savings);

        // Trend chart
        renderTrendChart(d.monthly_trends);

        // Category chart
        renderCategoryChart(d.category_breakdown);

        // Budget status
        renderBudgetStatus(d.budget_status);

        // Recent transactions
        renderRecentTransactions(d.recent_transactions);

    } catch (err) {
        console.error('Dashboard load error:', err);
        showToast('Failed to load dashboard data', 'error');
    }
}

// ── Trend Chart (Bar) ──
function renderTrendChart(trends) {
    const ctx = document.getElementById('trendChart');
    if (!ctx) return;

    if (trendChart) trendChart.destroy();

    trendChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: trends.map(t => t.month),
            datasets: [
                {
                    label: 'Income',
                    data: trends.map(t => t.income),
                    backgroundColor: 'rgba(0, 184, 148, 0.7)',
                    borderColor: '#00B894',
                    borderWidth: 1,
                    borderRadius: 6,
                    barPercentage: 0.6
                },
                {
                    label: 'Expenses',
                    data: trends.map(t => t.expenses),
                    backgroundColor: 'rgba(225, 112, 85, 0.7)',
                    borderColor: '#E17055',
                    borderWidth: 1,
                    borderRadius: 6,
                    barPercentage: 0.6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#A7A5C6', font: { family: 'Inter' } } }
            },
            scales: {
                x: { ticks: { color: '#6B6990' }, grid: { color: 'rgba(108,92,231,0.06)' } },
                y: { ticks: { color: '#6B6990', callback: v => '₹' + v.toLocaleString() }, grid: { color: 'rgba(108,92,231,0.06)' } }
            }
        }
    });
}

// ── Category Doughnut Chart ──
function renderCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;

    if (categoryChart) categoryChart.destroy();

    if (!categories.length) {
        ctx.parentElement.innerHTML = '<div class="empty-state"><div class="empty-icon">📭</div><h3>No expenses this month</h3></div>';
        return;
    }

    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                data: categories.map(c => c.total),
                backgroundColor: CHART_COLORS.slice(0, categories.length),
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#A7A5C6', font: { family: 'Inter', size: 11 }, padding: 12, usePointStyle: true }
                }
            }
        }
    });
}

// ── Budget Status ──
function renderBudgetStatus(budgets) {
    const section = document.getElementById('budgetSection');
    const container = document.getElementById('budgetStatusContainer');

    if (!budgets || budgets.length === 0) {
        section.style.display = 'block';
        container.innerHTML = '<div class="empty-state"><div class="empty-icon">🎯</div><p>No budgets set. Click "Set Budget" to get started.</p></div>';
        return;
    }

    section.style.display = 'block';
    container.innerHTML = budgets.map(b => {
        let barClass = '';
        if (b.utilization >= 100) barClass = 'danger';
        else if (b.utilization >= 80) barClass = 'warning';

        return `
            <div class="budget-item">
                <div class="budget-info">
                    <span class="cat-name">${b.category}</span>
                    <span style="color:var(--text-muted);font-size:0.8rem;">
                        ${fmt(b.spent)} / ${fmt(b.limit)}
                        ${b.exceeded ? '<span class="badge badge-red" style="margin-left:0.5rem;">EXCEEDED</span>' : ''}
                    </span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${barClass}" style="width:${Math.min(b.utilization, 100)}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

// ── Recent Transactions ──
function renderRecentTransactions(transactions) {
    const body = document.getElementById('recentBody');

    if (!transactions.length) {
        body.innerHTML = '<tr><td colspan="5"><div class="empty-state"><div class="empty-icon">📭</div><h3>No transactions yet</h3><p>Start adding income and expenses.</p></div></td></tr>';
        return;
    }

    body.innerHTML = transactions.map(t => {
        const isExpense = t.type === 'expense';
        const badgeClass = isExpense ? 'badge-red' : 'badge-green';
        const label = isExpense ? t.category : t.source;
        const amtClass = isExpense ? 'text-red' : 'text-green';
        const prefix = isExpense ? '-' : '+';

        return `<tr>
            <td><span class="badge ${badgeClass}">${t.type.toUpperCase()}</span></td>
            <td>${label}</td>
            <td class="amount ${amtClass}">${prefix}${fmt(t.amount)}</td>
            <td>${t.date}</td>
            <td>${t.description || '—'}</td>
        </tr>`;
    }).join('');
}

// ══════════════════════════════════
//  PREDICTIONS
// ══════════════════════════════════

async function loadPredictions() {
    try {
        const res = await fetch(`${API}/api/prediction`, { headers: authHeaders() });
        if (!res.ok) return;
        const data = await res.json();
        if (data.status !== 'success') return;

        const ep = data.data.expense_prediction;
        const sp = data.data.savings_prediction;

        document.getElementById('predExpense').textContent = fmt(ep.predicted_next_month_expense);
        document.getElementById('predExpMsg').textContent = ep.message;
        document.getElementById('expTrend').innerHTML = `<span class="trend-badge ${ep.trend}">${ep.trend.toUpperCase()} ${ep.trend === 'increasing' ? '↑' : ep.trend === 'decreasing' ? '↓' : '→'}</span>`;

        document.getElementById('predSavings').textContent = fmt(sp.predicted_next_month_savings);
        document.getElementById('predSavMsg').textContent = sp.message;
        document.getElementById('savTrend').innerHTML = `<span class="trend-badge ${sp.trend}">${sp.trend.toUpperCase()} ${sp.trend === 'improving' ? '↑' : sp.trend === 'declining' ? '↓' : '→'}</span>`;
    } catch (err) {
        console.error('Prediction error:', err);
    }
}

// ══════════════════════════════════
//  INSIGHTS
// ══════════════════════════════════

async function loadInsights() {
    try {
        const res = await fetch(`${API}/api/insights`, { headers: authHeaders() });
        if (!res.ok) return;
        const data = await res.json();
        if (data.status !== 'success') return;

        const d = data.data;

        // Alerts
        const alertsContainer = document.getElementById('alertsContainer');
        if (d.alerts && d.alerts.length) {
            alertsContainer.innerHTML = d.alerts.map(a =>
                `<div class="alert-bar ${a.type}"><span>${a.type === 'danger' ? '🚨' : '⚠️'}</span><strong>${a.title}:</strong> ${a.message}</div>`
            ).join('');
        }

        // Insight cards
        const grid = document.getElementById('insightsGrid');
        if (d.insights && d.insights.length) {
            grid.innerHTML = d.insights.map(i =>
                `<div class="insight-card">
                    <span class="insight-icon">${i.icon || '📊'}</span>
                    <div class="insight-content">
                        <h4>${i.title}</h4>
                        <p>${i.message}</p>
                    </div>
                </div>`
            ).join('');
        } else {
            grid.innerHTML = '<div class="empty-state"><div class="empty-icon">💡</div><h3>No insights yet</h3><p>Add more transactions to get insights.</p></div>';
        }

        // Suggestions
        if (d.suggestions && d.suggestions.length) {
            const card = document.getElementById('suggestionsCard');
            card.style.display = 'block';
            document.getElementById('suggestionsList').innerHTML = d.suggestions.map(s => `<li>${s}</li>`).join('');
        }

    } catch (err) {
        console.error('Insights error:', err);
        document.getElementById('insightsGrid').innerHTML = '<div class="empty-state"><p>Could not load insights.</p></div>';
    }
}

// ══════════════════════════════════
//  BUDGET MODAL
// ══════════════════════════════════

const CATEGORIES = [
    'Food & Dining', 'Transportation', 'Housing', 'Utilities',
    'Healthcare', 'Entertainment', 'Shopping', 'Education',
    'Insurance', 'Savings & Investments', 'Personal Care',
    'Travel', 'Gifts & Donations', 'Subscriptions', 'Other'
];

function populateBudgetCategories() {
    const sel = document.getElementById('budgetCategory');
    sel.innerHTML = CATEGORIES.map(c => `<option value="${c}">${c}</option>`).join('');
}

function openBudgetModal() {
    populateBudgetCategories();
    document.getElementById('budgetModal').classList.add('active');
}

function closeBudgetModal() {
    document.getElementById('budgetModal').classList.remove('active');
}

document.getElementById('budgetForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const category = document.getElementById('budgetCategory').value;
    const limit_amount = parseFloat(document.getElementById('budgetLimit').value);

    if (!category || !limit_amount || limit_amount <= 0) {
        showToast('Please fill all fields correctly', 'error');
        return;
    }

    try {
        const res = await fetch(`${API}/api/budgets`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ category, limit_amount })
        });
        const data = await res.json();
        if (data.status === 'success') {
            showToast('Budget saved!');
            closeBudgetModal();
            loadDashboard();
        } else {
            showToast(data.message || 'Failed to save budget', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
});

// ── CSV Export ──
function exportExpensesCSV() {
    window.open(`${API}/api/reports/export/expenses?token=${token}`, '_blank');
    // Fallback: fetch with auth
    fetch(`${API}/api/reports/export/expenses`, { headers: authHeaders() })
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'expenses.csv';
            a.click();
            URL.revokeObjectURL(url);
        })
        .catch(() => showToast('Export failed', 'error'));
}

// ── Initialize ──
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadPredictions();
    loadInsights();
});
