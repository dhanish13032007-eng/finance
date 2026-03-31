/**
 * Dashboard Intelligence Module — v2.0
 * Renders all 10 intelligent sections:
 *   1. Smart Alerts          5. Action Cards        9. Predictions
 *   2. Top Issue             6. Smart Budget       10. Trend Chart
 *   3. Monthly Summary       7. What-If Simulator
 *   4. KPI Stats             8. Behavior Analysis
 */

const API = '';
const token = localStorage.getItem('token');

if (!token) window.location.href = '/login';

// ─── Helpers ───────────────────────────────────────────────────────────
function authHeaders() {
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
}

function fmt(n) {
    return '₹' + Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtShort(n) {
    const num = Number(n || 0);
    if (num >= 100000) return '₹' + (num / 100000).toFixed(1) + 'L';
    if (num >= 1000) return '₹' + (num / 1000).toFixed(1) + 'K';
    return '₹' + num.toFixed(0);
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

function setDeltaBadge(id, pct, diff, reverseColors = false) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('skeleton');
    if (diff === 0) {
        el.className = 'delta-badge badge-neutral';
        el.innerHTML = `<span>→ 0%</span>`;
        return;
    }
    const isPositive = diff > 0;
    const icon = isPositive ? '▲' : '▼';
    let colorClass = isPositive ? 'badge-green' : 'badge-red';
    if (reverseColors) colorClass = isPositive ? 'badge-red' : 'badge-green';
    el.className = `delta-badge ${colorClass}`;
    el.innerHTML = `<span>${icon} ${Math.abs(pct)}%</span>`;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// Notifications
function toggleNotifications() {
    const d = document.getElementById('notifDropdown');
    d.classList.toggle('hidden');
    if (!d.classList.contains('hidden')) loadNotificationsList();
}

async function loadNotificationsList() {
    try {
        const res = await fetch(`${API}/api/notifications`, { headers: authHeaders() });
        const data = await res.json();
        const list = document.getElementById('notifList');
        if (!data.data.notifications.length) {
            list.innerHTML = '<div style="color:var(--text-muted);font-size:0.8rem;text-align:center;padding:1rem;">No alerts right now.</div>';
            return;
        }
        
        list.innerHTML = data.data.notifications.map(n => `
            <div style="padding:0.75rem 0; border-bottom:1px solid rgba(108,92,231,0.05); ${!n.is_read ? 'background:rgba(225,112,85,0.03);' : ''}">
                <div style="font-size:0.8rem;font-weight:700;margin-bottom:0.2rem;color:var(--primary-dark)">${n.title}</div>
                <div style="font-size:0.75rem;color:var(--text-secondary);line-height:1.4;">${n.message}</div>
            </div>
        `).join('');
    } catch {}
}

async function markAllNotificationsRead() {
    try {
        await fetch(`${API}/api/notifications/read-all`, { method: 'PUT', headers: authHeaders() });
        document.getElementById('notifBadge').style.display = 'none';
        document.getElementById('notifBadge').textContent = '0';
        loadNotificationsList();
    } catch {}
}

// Chart instances
let trendChart = null;

const CHART_COLORS = [
    '#6C5CE7', '#00CEC9', '#FD79A8', '#FDCB6E', '#00B894',
    '#74B9FF', '#E17055', '#A29BFE', '#55E6C1', '#FF6B6B'
];

// User info
const user = JSON.parse(localStorage.getItem('user') || '{}');
document.getElementById('userName').textContent = user.name || '';

// Header date
const now = new Date();
document.getElementById('headerDate').textContent = now.toLocaleDateString('en-IN', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
});


// ══════════════════════════════════════════════════════════
//  SECTION 1–4: DASHBOARD CORE DATA
// ══════════════════════════════════════════════════════════

async function loadDashboard() {
    try {
        const res = await fetch(`${API}/api/dashboard`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();
        if (data.status !== 'success') return;

        const d = data.data;

        // ── KPI Stats ──
        document.getElementById('monthIncome').innerHTML = fmt(d.current_month.income);
        document.getElementById('monthExpenses').innerHTML = fmt(d.current_month.expenses);
        document.getElementById('monthSavings').innerHTML = fmt(d.current_month.savings);
        document.getElementById('savingsPct').textContent = `${d.totals.savings_percentage}% Rate`;
        
        document.getElementById('netWorthAmount').innerHTML = fmt(d.totals.net_worth);
        setDeltaBadge('netWorthDelta', 0, 0, false); // Placeholder for delta
        
        document.getElementById('netWorthAmount').classList.remove('skeleton');

        // Notification Badge Update
        if (d.totals.unread_notifications > 0) {
            const b = document.getElementById('notifBadge');
            b.style.display = 'block';
            b.textContent = d.totals.unread_notifications;
        }

        // Burn rate badge
        if (d.current_month.daily_burn > 0) {
            document.getElementById('burnRateLabel').textContent =
                `₹${Math.round(d.current_month.daily_burn)}/day`;
        }

        // Projected spend card
        const proj = d.current_month.projected_spend;
        const inc = d.current_month.income;
        document.getElementById('projectedSpend').innerHTML = fmt(proj);
        const noteEl = document.getElementById('projectedNote');
        if (inc > 0 && proj > inc) {
            const overshoot = proj - inc;
            noteEl.innerHTML = `<span class="text-red">⚠️ ₹${Math.round(overshoot).toLocaleString()} over income</span>`;
        } else if (inc > 0) {
            const cushion = inc - proj;
            noteEl.innerHTML = `<span class="text-green">✅ ₹${Math.round(cushion).toLocaleString()} buffer left</span>`;
        } else {
            noteEl.textContent = `${d.current_month.days_remaining} days left in month`;
        }

        // Deltas
        const incD = d.current_month.income - d.current_month.prev_income;
        const expD = d.current_month.expenses - d.current_month.prev_expenses;
        const savD = d.current_month.savings - d.current_month.prev_savings;
        const incPct = d.current_month.prev_income
            ? (incD / d.current_month.prev_income * 100).toFixed(1) : 0;
        const expPct = d.current_month.prev_expenses
            ? (expD / d.current_month.prev_expenses * 100).toFixed(1) : 0;
        const savPct = d.current_month.prev_savings
            ? (savD / d.current_month.prev_savings * 100).toFixed(1) : 0;

        setDeltaBadge('incomeDelta', incPct, incD, false);
        setDeltaBadge('expenseDelta', expPct, expD, true);
        setDeltaBadge('savingsDelta', savPct, savD, false);

        // ② Top Issue
        if (d.top_issue) renderTopIssue(d.top_issue);

        // ⑤ Smart Budget
        renderSmartBudget(d.smart_budget);

        // ⑧ Behavior (lightweight from dashboard)
        renderBehaviorFromDashboard(d.behavior, d.current_month);

        // What-If category population
        const whatifSel = document.getElementById('whatifCategory');
        if (whatifSel && d.category_breakdown.length) {
            whatifSel.innerHTML = '<option value="">-- Select Category --</option>' +
                d.category_breakdown.map(c =>
                    `<option value="${c.category}">${c.category} (${fmt(c.total)})</option>`
                ).join('');
            document.getElementById('whatifSlider').disabled = false;
        }

        // ⑩ Trend Chart
        renderTrendChart(d.monthly_trends);

        // Recent Transactions
        renderRecentTransactions(d.recent_transactions);

    } catch (err) {
        console.error('Dashboard load error:', err);
        showToast('Failed to load dashboard', 'error');
    }
}


// ══════════════════════════════════════════════════════════
//  SECTION 2: TOP ISSUE CARD
// ══════════════════════════════════════════════════════════

function renderTopIssue(issue) {
    const container = document.getElementById('topIssueContainer');
    if (!issue) { container.innerHTML = ''; return; }

    container.innerHTML = `
        <div class="top-issue-card">
            <div class="top-issue-badge">⚠️ TOP ISSUE</div>
            <div class="top-issue-body">
                <div class="top-issue-category">${issue.category}</div>
                <div class="top-issue-amount">${fmt(issue.amount)}</div>
                <p class="top-issue-reason">${issue.reason}</p>
                <div class="top-issue-suggestion">
                    <span class="tip-icon">💡</span>
                    <span>${issue.suggestion}</span>
                </div>
            </div>
            <div class="top-issue-pct">${issue.pct_of_spending}%<br><small>of spending</small></div>
        </div>
    `;
}


// ══════════════════════════════════════════════════════════
//  SECTION 3: SMART SUMMARY
// ══════════════════════════════════════════════════════════

function renderSummary(narrative) {
    const card = document.getElementById('summaryCard');
    const narr = document.getElementById('summaryNarrative');
    if (!narrative || narrative.includes('No transaction')) {
        card.style.display = 'none';
        return;
    }
    narr.textContent = narrative;
    card.style.display = 'flex';
}


// ══════════════════════════════════════════════════════════
//  SECTION 5: SMART BUDGET TRACKER
// ══════════════════════════════════════════════════════════

function renderSmartBudget(budgets) {
    const section = document.getElementById('budgetSection');
    const container = document.getElementById('smartBudgetContainer');

    if (!budgets || budgets.length === 0) {
        section.style.display = 'block';
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🎯</div>
                <p>No budgets set. Click "Set Budget" to track spending limits.</p>
            </div>`;
        return;
    }

    section.style.display = 'block';
    container.innerHTML = budgets.map(b => {
        const statusClass = b.status === 'Danger' ? 'danger' :
                            b.status === 'Warning' ? 'warning' : 'safe';
        const barClass = b.status === 'Danger' ? 'danger' :
                         b.status === 'Warning' ? 'warning' : '';
        const barWidth = Math.min(b.utilization, 100);

        const exhaustInfo = b.days_to_exhaust
            ? `Exhausted by <strong>${b.exhaust_date}</strong>`
            : b.status === 'Danger'
            ? 'Budget exceeded!'
            : `Safe until month-end`;

        const speedIcon = b.speed_label === 'Very Fast' ? '🔥' :
                          b.speed_label === 'Fast' ? '⚡' :
                          b.speed_label === 'Slow' ? '🐢' : '✅';

        return `
            <div class="budget-smart-item">
                <div class="budget-smart-header">
                    <div>
                        <span class="cat-name">${b.category}</span>
                        <span class="status-pill ${statusClass}">${b.status}</span>
                    </div>
                    <div class="budget-smart-amounts">
                        <span class="text-secondary" style="font-size:0.82rem;">${fmt(b.spent)} / ${fmt(b.limit)}</span>
                    </div>
                </div>
                <div class="progress-bar" style="margin:0.75rem 0;">
                    <div class="progress-fill ${barClass}" style="width:${barWidth}%"></div>
                </div>
                <div class="budget-smart-meta">
                    <span class="burn-rate-badge">${speedIcon} ${b.speed_label} (₹${b.daily_rate}/day)</span>
                    <span class="exhaust-info">${exhaustInfo}</span>
                </div>
                ${b.will_overshoot ? `
                    <div class="budget-overshoot-warning">
                        At this rate, projected spend: <strong>${fmt(b.projected_total)}</strong>
                        vs limit <strong>${fmt(b.limit)}</strong>
                    </div>` : ''}
            </div>
        `;
    }).join('');
}


// ══════════════════════════════════════════════════════════
//  SECTION 6: ACTION CARDS
// ══════════════════════════════════════════════════════════

function renderActionCards(actions) {
    const container = document.getElementById('actionCardsContainer');
    if (!actions || actions.length === 0) {
        container.innerHTML = '';
        return;
    }

    const colorMap = {
        danger: { bg: 'rgba(225,112,85,0.08)', border: 'rgba(225,112,85,0.3)', text: '#E17055' },
        warning: { bg: 'rgba(253,203,110,0.08)', border: 'rgba(253,203,110,0.3)', text: '#FDCB6E' },
        success: { bg: 'rgba(0,184,148,0.08)', border: 'rgba(0,184,148,0.3)', text: '#00B894' },
        info: { bg: 'rgba(108,92,231,0.08)', border: 'rgba(108,92,231,0.3)', text: '#A29BFE' }
    };

    container.innerHTML = `
        <div class="action-cards-section">
            <h2 class="section-heading">⚡ Recommended Actions</h2>
            <div class="action-cards-grid">
                ${actions.map((a, idx) => {
                    const c = colorMap[a.color] || colorMap['info'];
                    return `
                        <div class="action-card" style="
                            background:${c.bg};
                            border-color:${c.border};
                        ">
                            <div class="action-card-header">
                                <span class="action-priority">#${idx + 1}</span>
                                <span class="action-icon">${a.icon}</span>
                                <h4 class="action-title" style="color:${c.text}">${a.title}</h4>
                            </div>
                            <p class="action-detail">${a.detail}</p>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}


// ══════════════════════════════════════════════════════════
//  SECTION 8: BEHAVIOR ANALYSIS
// ══════════════════════════════════════════════════════════

function renderBehaviorFromDashboard(behavior, currentMonth) {
    const section = document.getElementById('behaviorSection');
    const container = document.getElementById('behaviorContainer');
    if (!behavior) return;

    section.style.display = 'block';

    const daysRemaining = behavior.days_remaining || 0;
    const dailyBurn = behavior.daily_burn || 0;
    const projectedSavings = behavior.projected_month_savings || 0;
    const onTrack = behavior.on_track;

    container.innerHTML = `
        <div class="behavior-grid">
            <div class="behavior-stat">
                <div class="behavior-stat-icon">🔥</div>
                <div class="behavior-stat-label">Daily Burn Rate</div>
                <div class="behavior-stat-value">${fmt(dailyBurn)}<span>/day</span></div>
            </div>
            <div class="behavior-stat">
                <div class="behavior-stat-icon">${onTrack ? '✅' : '⚠️'}</div>
                <div class="behavior-stat-label">Month-End Outlook</div>
                <div class="behavior-stat-value ${onTrack ? 'text-green' : 'text-red'}">
                    ${onTrack ? 'On Track' : 'At Risk'}
                </div>
            </div>
            <div class="behavior-stat">
                <div class="behavior-stat-icon">📅</div>
                <div class="behavior-stat-label">Days Remaining</div>
                <div class="behavior-stat-value">${daysRemaining}<span> days</span></div>
            </div>
            <div class="behavior-stat">
                <div class="behavior-stat-icon">💰</div>
                <div class="behavior-stat-label">Projected Savings</div>
                <div class="behavior-stat-value ${projectedSavings >= 0 ? 'text-green' : 'text-red'}">
                    ${fmt(projectedSavings)}
                </div>
            </div>
        </div>
    `;
}

function renderFullBehavior(behavior) {
    const section = document.getElementById('behaviorSection');
    const container = document.getElementById('behaviorContainer');
    if (!behavior || Object.keys(behavior).length === 0) return;

    section.style.display = 'block';

    let html = `<div class="behavior-grid">`;

    // Busiest Day
    if (behavior.busiest_day) {
        html += `
            <div class="behavior-stat">
                <div class="behavior-stat-icon">📅</div>
                <div class="behavior-stat-label">Highest Spend Day</div>
                <div class="behavior-stat-value">${behavior.busiest_day}</div>
            </div>`;
    }

    // Weekly trend
    if (behavior.weekly_trend) {
        const wt = behavior.weekly_trend;
        const icon = wt.direction === 'up' ? '📈' : wt.direction === 'down' ? '📉' : '➡️';
        const cls = wt.direction === 'up' ? 'text-red' : wt.direction === 'down' ? 'text-green' : '';
        html += `
            <div class="behavior-stat">
                <div class="behavior-stat-icon">${icon}</div>
                <div class="behavior-stat-label">Weekly Trend</div>
                <div class="behavior-stat-value ${cls}">
                    ${wt.change_pct > 0 ? '+' : ''}${wt.change_pct}%
                </div>
            </div>`;
    }

    // Monthly direction
    if (behavior.monthly_change_pct !== undefined) {
        const icon = behavior.monthly_direction === 'up' ? '📈' : behavior.monthly_direction === 'down' ? '📉' : '➡️';
        html += `
            <div class="behavior-stat">
                <div class="behavior-stat-icon">${icon}</div>
                <div class="behavior-stat-label">Month vs Last Month</div>
                <div class="behavior-stat-value ${behavior.monthly_direction === 'up' ? 'text-red' : 'text-green'}">
                    ${behavior.monthly_change_pct > 0 ? '+' : ''}${behavior.monthly_change_pct}%
                </div>
            </div>`;
    }

    html += `</div>`;

    // Spending spikes
    if (behavior.spikes && behavior.spikes.length > 0) {
        html += `
            <div style="margin-top:1.25rem;">
                <h4 style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:0.75rem;">
                    ⚡ Spending Spikes Detected
                </h4>
                <div class="spike-list">
                    ${behavior.spikes.map(s => `
                        <div class="spike-item">
                            <span class="spike-date">${s.date}</span>
                            <span class="spike-category">${s.top_category}</span>
                            <span class="spike-amount text-red">${fmt(s.amount)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>`;
    }

    container.innerHTML = html;
}


// ══════════════════════════════════════════════════════════
//  SECTION 9: PREDICTIONS
// ══════════════════════════════════════════════════════════

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
        document.getElementById('expTrend').innerHTML =
            `<span class="trend-badge ${ep.trend}">${ep.trend.toUpperCase()} ${
                ep.trend === 'increasing' ? '↑' : ep.trend === 'decreasing' ? '↓' : '→'
            }</span>`;

        document.getElementById('predSavings').textContent = fmt(sp.predicted_next_month_savings);
        document.getElementById('predSavMsg').textContent = sp.message;
        document.getElementById('savTrend').innerHTML =
            `<span class="trend-badge ${sp.trend}">${sp.trend.toUpperCase()} ${
                sp.trend === 'improving' ? '↑' : sp.trend === 'declining' ? '↓' : '→'
            }</span>`;
    } catch (err) {
        console.error('Prediction error:', err);
    }
}


// ══════════════════════════════════════════════════════════
//  FULL INSIGHTS (from /api/insights)
// ══════════════════════════════════════════════════════════

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
                `<div class="alert-bar ${a.type}" style="animation:fadeSlideUp 0.4s ease;">
                    <span>${a.type === 'danger' ? '🚨' : '⚠️'}</span>
                    <span><strong>${a.title}:</strong> ${a.message}</span>
                    <button onclick="this.parentElement.remove()" style="margin-left:auto;background:none;border:none;cursor:pointer;font-size:1rem;color:inherit;opacity:0.7;">✕</button>
                </div>`
            ).join('');
        }

        // ③ Summary narrative
        renderSummary(d.narrative);

        // ⑥ Action cards
        if (d.actions && d.actions.length) {
            renderActionCards(d.actions);
        }

        // ② Top Issue (from insights enriches the one from dashboard)
        if (d.top_issue && !document.querySelector('.top-issue-card')) {
            renderTopIssue(d.top_issue);
        }

        // ⑧ Full Behavior
        if (d.behavior && Object.keys(d.behavior).length > 0) {
            renderFullBehavior(d.behavior);
        }

        // Financial Guide insight cards
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
            grid.innerHTML = `<div class="empty-state">
                <div class="empty-icon">💡</div>
                <h3>No insights yet</h3>
                <p>Add more transactions to unlock personalized insights.</p>
            </div>`;
        }

    } catch (err) {
        console.error('Insights error:', err);
        document.getElementById('insightsGrid').innerHTML =
            `<div class="empty-state"><p>Could not load insights.</p></div>`;
    }
}


// ══════════════════════════════════════════════════════════
//  SECTION 10: TREND CHART
// ══════════════════════════════════════════════════════════

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
                    backgroundColor: 'rgba(0,184,148,0.75)',
                    borderColor: '#00B894',
                    borderWidth: 1,
                    borderRadius: 6,
                    barPercentage: 0.55
                },
                {
                    label: 'Expenses',
                    data: trends.map(t => t.expenses),
                    backgroundColor: 'rgba(225,112,85,0.75)',
                    borderColor: '#E17055',
                    borderWidth: 1,
                    borderRadius: 6,
                    barPercentage: 0.55
                },
                {
                    label: 'Savings',
                    type: 'line',
                    data: trends.map(t => t.savings),
                    borderColor: '#A29BFE',
                    backgroundColor: 'rgba(162,155,254,0.1)',
                    borderWidth: 2,
                    pointBackgroundColor: '#A29BFE',
                    pointRadius: 4,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    labels: { color: '#A7A5C6', font: { family: 'Inter' }, usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.dataset.label}: ₹${Number(ctx.raw).toLocaleString('en-IN')}`
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#6B6990', font: { family: 'Inter', size: 11 } },
                    grid: { color: 'rgba(108,92,231,0.05)' }
                },
                y: {
                    ticks: {
                        color: '#6B6990',
                        font: { family: 'Inter', size: 11 },
                        callback: v => '₹' + v.toLocaleString('en-IN')
                    },
                    grid: { color: 'rgba(108,92,231,0.05)' }
                }
            }
        }
    });
}


// ══════════════════════════════════════════════════════════
//  RECENT TRANSACTIONS
// ══════════════════════════════════════════════════════════

function renderRecentTransactions(transactions) {
    const body = document.getElementById('recentBody');
    if (!transactions.length) {
        body.innerHTML = `<tr><td colspan="5"><div class="empty-state">
            <div class="empty-icon">📭</div>
            <h3>No transactions yet</h3>
            <p>Start adding income and expenses.</p>
        </div></td></tr>`;
        return;
    }

    body.innerHTML = transactions.map(t => {
        const isExpense = t.type === 'expense';
        const badgeClass = isExpense ? 'badge-red' : 'badge-green';
        const amtClass = isExpense ? 'text-red' : 'text-green';
        const prefix = isExpense ? '-' : '+';
        const label = isExpense ? t.category : t.source;

        return `<tr>
            <td><span class="badge ${badgeClass}">${t.type.toUpperCase()}</span></td>
            <td>${label}</td>
            <td class="amount ${amtClass}">${prefix}${fmt(t.amount)}</td>
            <td>${t.date}</td>
            <td>${t.description || '—'}</td>
        </tr>`;
    }).join('');
}


// ══════════════════════════════════════════════════════════
//  BUDGET MODAL
// ══════════════════════════════════════════════════════════

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
            loadInsights();
        } else {
            showToast(data.message || 'Failed to save budget', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
});


// ══════════════════════════════════════════════════════════
//  WHAT-IF SIMULATOR (v2)
// ══════════════════════════════════════════════════════════

const whatifSlider = document.getElementById('whatifSlider');
const whatifCategory = document.getElementById('whatifCategory');

if (whatifSlider) {
    whatifSlider.addEventListener('input', (e) => {
        document.getElementById('whatifPercentLabel').textContent = `${e.target.value}%`;
        calculateWhatIf();
    });
}

if (whatifCategory) {
    whatifCategory.addEventListener('change', calculateWhatIf);
}

async function calculateWhatIf() {
    const category = whatifCategory?.value;
    const pct = parseInt(whatifSlider?.value || 0);
    const resultsDiv = document.getElementById('whatifResults');

    if (!category || pct === 0) {
        resultsDiv.style.display = 'none';
        return;
    }

    try {
        const res = await fetch(`${API}/api/whatif`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ category, reduce_by_percent: pct })
        });
        const data = await res.json();
        if (data.status !== 'success') return;

        const r = data.data;
        const rateDir = r.rate_improvement > 0 ? '▲' : '▼';
        const rateColor = r.rate_improvement >= 0 ? 'text-green' : 'text-red';

        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = `
            <div class="whatif-grid">
                <div class="whatif-metric">
                    <div class="whatif-metric-label">Monthly Savings</div>
                    <div class="whatif-metric-old">${fmt(r.current_savings)}</div>
                    <div class="whatif-metric-arrow">→</div>
                    <div class="whatif-metric-new text-green">${fmt(r.projected_savings)}</div>
                    <div class="whatif-metric-gain">+${fmt(r.difference)}/mo</div>
                </div>
                <div class="whatif-metric">
                    <div class="whatif-metric-label">Savings Rate</div>
                    <div class="whatif-metric-old">${r.current_savings_rate}%</div>
                    <div class="whatif-metric-arrow">→</div>
                    <div class="whatif-metric-new ${rateColor}">${r.projected_savings_rate}%</div>
                    <div class="whatif-metric-gain ${rateColor}">${rateDir} ${Math.abs(r.rate_improvement).toFixed(1)}%</div>
                </div>
                <div class="whatif-metric yearly-impact">
                    <div class="whatif-metric-label">🎯 Annual Impact</div>
                    <div class="yearly-gain">${fmt(r.yearly_gain)}</div>
                    <div class="yearly-label">extra this year</div>
                </div>
            </div>
            <div class="whatif-narrative">
                <span class="tip-icon">💬</span>
                <em>${r.narrative}</em>
            </div>
        `;
    } catch (e) {
        console.error('WhatIf error:', e);
    }
}


// ══════════════════════════════════════════════════════════
//  CSV EXPORT
// ══════════════════════════════════════════════════════════

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
            showToast('CSV exported!');
        })
        .catch(() => showToast('Export failed', 'error'));
}


// ══════════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    loadPredictions();
    loadInsights();
});
