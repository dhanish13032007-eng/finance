"""
Intelligent Insight Service — v2.0
Transforms raw financial data into actionable intelligence:
 1. Smart Budget System        — burn rate, exhaustion date, Safe/Warning/Danger
 2. Future Risk Prediction     — budget exhaustion forecast, savings trend
 3. Action-Based Insights      — prioritized do-this cards
 4. Problem Highlight System   — Top Issue detection
 5. What-If Connections        — suggestion amounts tied to categories
 6. Spending Behavior Analysis — weekly vs monthly, spike detection
 7. Smart Summary Generator    — monthly narrative
 8. Savings Health             — savings rate classification
"""
import pandas as pd
import numpy as np
import calendar
from datetime import date, timedelta
from collections import defaultdict


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def _pct_change(new_val, old_val):
    if old_val == 0:
        return 0
    return round((new_val - old_val) / old_val * 100, 1)


def _budget_status_label(utilization, days_passed, days_in_month):
    """Classify budget status considering both utilization and time spent."""
    time_pct = (days_passed / days_in_month) * 100 if days_in_month > 0 else 0
    if utilization >= 100:
        return 'Danger'
    if utilization >= 80:
        return 'Warning'
    # Spending faster than time elapsed
    if utilization > time_pct + 15:
        return 'Warning'
    return 'Safe'


# ─────────────────────────────────────────────
#  MAIN FUNCTION
# ─────────────────────────────────────────────

def generate_insights(expenses_list, incomes_list, budgets_list):
    """
    Analyze user's financial data and return a rich intelligence payload.

    Returns dict with:
        insights        — enriched insight cards
        alerts          — urgent alerts
        suggestions     — raw text suggestions (legacy compat)
        actions         — prioritized action cards (NEW)
        top_issue       — the single biggest problem (NEW)
        smart_budget    — per-budget burn/exhaustion data (NEW)
        behavior        — weekly/monthly patterns (NEW)
        narrative       — smart monthly summary string (NEW)
        risk            — forward-looking risk signals (NEW)
        summary         — quick stats block
    """
    today = date.today()
    insights = []
    alerts = []
    suggestions = []
    actions = []

    # ── Guard: no data ──
    if not expenses_list:
        return {
            'insights': [{'type': 'info', 'title': 'No Data Yet',
                          'message': 'Start adding expenses to unlock your financial intelligence.',
                          'icon': '🚀'}],
            'alerts': [],
            'suggestions': ['Add your first expense to begin personalized insights.'],
            'actions': [],
            'top_issue': None,
            'smart_budget': [],
            'behavior': {},
            'narrative': 'No spending data yet. Add some expenses to get started.',
            'risk': {},
            'summary': {'total_expenses': 0, 'num_categories': 0,
                        'num_transactions': 0, 'top_category': None}
        }

    # ── Build DataFrames ──
    exp_data = [{
        'amount': e.amount,
        'category': e.category,
        'date': e.date,
        'description': e.description
    } for e in expenses_list]

    df = pd.DataFrame(exp_data)
    df['date'] = pd.to_datetime(df['date'])
    df['month_str'] = df['date'].dt.strftime('%Y-%m')
    df['week'] = df['date'].dt.isocalendar().week.astype(int)
    df['day_of_week'] = df['date'].dt.day_name()
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

    # Current month filter
    cur_df = df[(df['year'] == today.year) & (df['month'] == today.month)]
    cur_exp_total = float(cur_df['amount'].sum())

    # All-time totals
    cat_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    total_exp = float(cat_totals.sum())

    # Income totals
    total_income = sum(i.amount for i in incomes_list) if incomes_list else 0
    cur_income = sum(
        i.amount for i in incomes_list
        if i.date.month == today.month and i.date.year == today.year
    ) if incomes_list else 0

    days_in_month = _days_in_month(today.year, today.month)
    days_passed = today.day
    days_remaining = days_in_month - days_passed

    # ════════════════════════════════════════════
    #  MODULE 1 — SMART BUDGET SYSTEM
    # ════════════════════════════════════════════
    smart_budget = []
    for b in budgets_list:
        if b.month != today.month or b.year != today.year:
            continue

        cat_spent = float(sum(
            e.amount for e in expenses_list
            if e.category == b.category
            and e.date.month == today.month
            and e.date.year == today.year
        ))
        limit = float(b.limit_amount)
        utilization = (cat_spent / limit * 100) if limit > 0 else 0
        remaining = limit - cat_spent

        # Daily burn rate
        daily_rate = cat_spent / days_passed if days_passed > 0 else 0

        # Days until budget exhausted at current rate
        if daily_rate > 0 and remaining > 0:
            days_to_exhaust = remaining / daily_rate
            exhaust_date = today + timedelta(days=int(days_to_exhaust))
            exhaust_str = exhaust_date.strftime('%b %d')
            exhaust_within_month = days_to_exhaust <= days_remaining
        else:
            days_to_exhaust = None
            exhaust_str = 'Not at risk'
            exhaust_within_month = False

        # Projected end-of-month spend
        projected_total = cat_spent + (daily_rate * days_remaining)

        status = _budget_status_label(utilization, days_passed, days_in_month)

        # Spending-speed label
        time_pct = (days_passed / days_in_month) * 100
        if utilization > 0 and time_pct > 0:
            speed_ratio = utilization / time_pct
            if speed_ratio >= 1.5:
                speed_label = 'Very Fast'
            elif speed_ratio >= 1.15:
                speed_label = 'Fast'
            elif speed_ratio >= 0.85:
                speed_label = 'Normal'
            else:
                speed_label = 'Slow'
        else:
            speed_label = 'No data'

        smart_budget.append({
            'category': b.category,
            'limit': limit,
            'spent': round(cat_spent, 2),
            'remaining': round(remaining, 2),
            'utilization': round(utilization, 1),
            'daily_rate': round(daily_rate, 2),
            'days_to_exhaust': round(days_to_exhaust, 1) if days_to_exhaust else None,
            'exhaust_date': exhaust_str,
            'exhaust_within_month': exhaust_within_month,
            'projected_total': round(projected_total, 2),
            'will_overshoot': projected_total > limit,
            'status': status,           # Safe / Warning / Danger
            'speed_label': speed_label, # Very Fast / Fast / Normal / Slow
            'suggestion': _budget_suggestion(b.category, status, remaining, daily_rate, days_remaining)
        })

        # Feed into alerts
        if status == 'Danger':
            alerts.append({
                'type': 'danger',
                'title': f'Budget Exceeded: {b.category}',
                'message': f'Spent ₹{cat_spent:,.0f} of ₹{limit:,.0f} ({utilization:.0f}%). '
                           f'₹{abs(remaining):,.0f} over limit.'
            })
        elif status == 'Warning' and exhaust_within_month:
            alerts.append({
                'type': 'warning',
                'title': f'Budget Risk: {b.category}',
                'message': f'At this rate, budget exhausted by {exhaust_str}. '
                           f'Daily spend: ₹{daily_rate:,.0f}/day.'
            })
        elif status == 'Warning':
            alerts.append({
                'type': 'warning',
                'title': f'Budget Alert: {b.category}',
                'message': f'{utilization:.0f}% used with {days_remaining} days left. '
                           f'Slow down to stay within ₹{limit:,.0f}.'
            })

    # ════════════════════════════════════════════
    #  MODULE 2 — FUTURE RISK PREDICTION
    # ════════════════════════════════════════════
    risk = {}
    if cur_exp_total > 0 and days_passed > 0:
        daily_burn = cur_exp_total / days_passed
        projected_month_end = cur_exp_total + daily_burn * days_remaining
        monthly_savings_projected = cur_income - projected_month_end
        yearly_savings_projected = monthly_savings_projected * 12

        risk = {
            'daily_burn_rate': round(daily_burn, 2),
            'projected_month_spend': round(projected_month_end, 2),
            'projected_month_savings': round(monthly_savings_projected, 2),
            'projected_yearly_savings': round(yearly_savings_projected, 2),
            'days_remaining': days_remaining,
            'on_track': projected_month_end <= cur_income,
        }

        if projected_month_end > cur_income and cur_income > 0:
            overshoot = projected_month_end - cur_income
            alerts.append({
                'type': 'danger',
                'title': '⚠️ Projected Overspend',
                'message': f'At ₹{daily_burn:,.0f}/day, you\'ll spend ₹{projected_month_end:,.0f} '
                           f'against income ₹{cur_income:,.0f}. Potential deficit: ₹{overshoot:,.0f}.'
            })

    # ════════════════════════════════════════════
    #  MODULE 3 — SPENDING BEHAVIOR ANALYSIS
    # ════════════════════════════════════════════
    behavior = {}
    if len(df) > 0:
        # Weekly spending pattern (last 4 weeks)
        week_totals = cur_df.groupby('week')['amount'].sum()
        if len(week_totals) >= 2:
            weeks_sorted = week_totals.sort_index()
            last_week_total = float(weeks_sorted.iloc[-1])
            prev_week_total = float(weeks_sorted.iloc[-2])
            weekly_change_pct = _pct_change(last_week_total, prev_week_total)

            behavior['weekly_trend'] = {
                'last_week': round(last_week_total, 2),
                'prev_week': round(prev_week_total, 2),
                'change_pct': weekly_change_pct,
                'direction': 'up' if weekly_change_pct > 10 else
                             'down' if weekly_change_pct < -10 else 'stable'
            }
        else:
            behavior['weekly_trend'] = None

        # Spike detection: days with > 2x average daily spend
        if len(cur_df) > 0:
            cur_df_grouped = cur_df.copy()
            cur_df_grouped['date_only'] = cur_df_grouped['date'].dt.date
            daily_totals = cur_df_grouped.groupby('date_only')['amount'].sum()
            avg_daily = float(daily_totals.mean()) if len(daily_totals) > 0 else 0
            spikes = daily_totals[daily_totals > avg_daily * 2.0]

            spike_list = []
            for spike_date, spike_amount in spikes.items():
                top_cat = cur_df_grouped[
                    cur_df_grouped['date_only'] == spike_date
                ].groupby('category')['amount'].sum().idxmax()
                spike_list.append({
                    'date': spike_date.strftime('%b %d'),
                    'amount': round(float(spike_amount), 2),
                    'top_category': top_cat
                })
            behavior['spikes'] = spike_list[:3]  # Show top 3
        else:
            behavior['spikes'] = []

        # Day-of-week pattern (all time)
        dow_totals = df.groupby('day_of_week')['amount'].mean().sort_values(ascending=False)
        if len(dow_totals) > 0:
            highest_dow = dow_totals.index[0]
            behavior['busiest_day'] = highest_dow
        else:
            behavior['busiest_day'] = None

        # Monthly trend analysis
        monthly_totals = df.groupby('month_str')['amount'].sum().sort_index()
        if len(monthly_totals) >= 2:
            last_m = float(monthly_totals.iloc[-1])
            prev_m = float(monthly_totals.iloc[-2])
            m_change = _pct_change(last_m, prev_m)
            behavior['monthly_change_pct'] = m_change
            behavior['monthly_direction'] = (
                'up' if m_change > 10 else
                'down' if m_change < -10 else 'stable'
            )

            if m_change > 20:
                insights.append({
                    'type': 'trend',
                    'title': 'Spending Spike Detected',
                    'message': f'Your spending jumped {m_change:.1f}% vs last month '
                               f'(₹{prev_m:,.0f} → ₹{last_m:,.0f}).',
                    'icon': '📈'
                })
                actions.append({
                    'priority': 1,
                    'type': 'reduce',
                    'title': 'Investigate Spending Spike',
                    'detail': f'Expenses rose {m_change:.1f}% this month. Review your top categories '
                              f'and cut back discretionary spend this week.',
                    'icon': '🔍',
                    'color': 'danger'
                })
            elif m_change < -10:
                insights.append({
                    'type': 'trend',
                    'title': 'Great Progress!',
                    'message': f'Spending fell {abs(m_change):.1f}% vs last month. Keep it up!',
                    'icon': '📉'
                })

    # ════════════════════════════════════════════
    #  MODULE 4 — PROBLEM HIGHLIGHT (Top Issue)
    # ════════════════════════════════════════════
    top_issue = None
    if len(cur_df) > 0:
        cur_cat_totals = cur_df.groupby('category')['amount'].sum().sort_values(ascending=False)
        if len(cur_cat_totals) > 0:
            worst_cat = cur_cat_totals.index[0]
            worst_amt = float(cur_cat_totals.iloc[0])
            worst_pct = (worst_amt / cur_exp_total * 100) if cur_exp_total > 0 else 0

            # Determine root cause
            if worst_pct > 50:
                reason = f'consuming over {worst_pct:.0f}% of your monthly budget'
            elif worst_pct > 35:
                reason = f'taking up {worst_pct:.0f}% of all spending — too concentrated'
            else:
                reason = f'your heaviest expense category at ₹{worst_amt:,.0f} this month'

            top_issue = {
                'category': worst_cat,
                'amount': round(worst_amt, 2),
                'pct_of_spending': round(worst_pct, 1),
                'reason': reason,
                'suggestion': f'Try reducing {worst_cat} by 20% to save ₹{worst_amt * 0.2:,.0f} this month.'
            }

            # Top-issue action card
            actions.append({
                'priority': 1,
                'type': 'reduce_category',
                'title': f'Cut {worst_cat} Spending',
                'detail': f'{worst_cat} is {reason}. Reducing it by 20% saves '
                          f'₹{worst_amt * 0.2:,.0f}/month (₹{worst_amt * 0.2 * 12:,.0f}/year).',
                'icon': '✂️',
                'color': 'warning',
                'category': worst_cat,
                'suggested_reduction_pct': 20
            })

    # ════════════════════════════════════════════
    #  MODULE 5 — HIGH SPENDING CATEGORY INSIGHT
    # ════════════════════════════════════════════
    if len(cat_totals) > 0:
        top_cat = cat_totals.index[0]
        top_pct = (float(cat_totals.iloc[0]) / total_exp * 100) if total_exp > 0 else 0
        insights.append({
            'type': 'spending',
            'title': 'Highest Spending Category',
            'message': f'"{top_cat}" accounts for {top_pct:.1f}% of total expenses '
                       f'(₹{cat_totals.iloc[0]:,.0f}).',
            'icon': '💸'
        })
        if top_pct > 40:
            suggestions.append(
                f'"{top_cat}" is over 40% of your total spend. Consider setting a strict budget limit.'
            )

    # ════════════════════════════════════════════
    #  MODULE 6 — SAVINGS HEALTH
    # ════════════════════════════════════════════
    savings_insight = {}
    if total_income > 0:
        savings_amount = total_income - total_exp
        savings_rate = (savings_amount / total_income) * 100

        if savings_rate < 0:
            savings_label = 'Critical'
            color = 'danger'
        elif savings_rate < 10:
            savings_label = 'Low'
            color = 'warning'
        elif savings_rate < 20:
            savings_label = 'Fair'
            color = 'info'
        elif savings_rate < 30:
            savings_label = 'Good'
            color = 'success'
        else:
            savings_label = 'Excellent'
            color = 'success'

        savings_insight = {
            'rate': round(savings_rate, 1),
            'label': savings_label,
            'color': color
        }

        insights.append({
            'type': 'savings',
            'title': f'Savings Rate: {savings_label}',
            'message': f'You save {savings_rate:.1f}% of income overall.',
            'icon': '💰'
        })

        if savings_rate < 10:
            actions.append({
                'priority': 2,
                'type': 'improve_savings',
                'title': 'Boost Your Savings Rate',
                'detail': f'Savings rate is only {savings_rate:.1f}%. '
                          f'Target 20% — that\'s ₹{total_income * 0.2:,.0f}/month.',
                'icon': '💰',
                'color': 'info'
            })
            suggestions.append(
                f'Your savings rate is {savings_rate:.1f}%. Aim for 20% by cutting discretionary spending.'
            )
        elif savings_rate > 30:
            actions.append({
                'priority': 3,
                'type': 'invest',
                'title': 'Invest Your Surplus',
                'detail': f'Great! You save {savings_rate:.1f}%. Consider moving surplus into '
                          f'an SIP, FD, or emergency fund.',
                'icon': '📈',
                'color': 'success'
            })
            suggestions.append(
                f'Excellent {savings_rate:.1f}% savings rate! Consider investing the surplus.'
            )

    # ════════════════════════════════════════════
    #  MODULE 7 — CATEGORY TREND (rising categories)
    # ════════════════════════════════════════════
    monthly_totals_check = df.groupby('month_str')['amount'].sum().sort_index()
    if len(monthly_totals_check) >= 2:
        recent_months = sorted(df['month_str'].unique())[-2:]
        if len(recent_months) == 2:
            prev_m_df = df[df['month_str'] == recent_months[0]]
            curr_m_df = df[df['month_str'] == recent_months[1]]
            prev_m_cats = prev_m_df.groupby('category')['amount'].sum()
            curr_m_cats = curr_m_df.groupby('category')['amount'].sum()

            for cat in curr_m_cats.index:
                curr_val = float(curr_m_cats.get(cat, 0))
                prev_val = float(prev_m_cats.get(cat, 0)) if cat in prev_m_cats else 0
                if prev_val > 0 and ((curr_val - prev_val) / prev_val) > 0.3:
                    pct_rise = ((curr_val - prev_val) / prev_val) * 100
                    suggestions.append(
                        f'"{cat}" up {pct_rise:.0f}% this month (₹{prev_val:,.0f}→₹{curr_val:,.0f}). Review recent purchases.'
                    )

    # ════════════════════════════════════════════
    #  MODULE 8 — SMART SUMMARY NARRATIVE
    # ════════════════════════════════════════════
    narrative = _build_narrative(
        today, cur_income, cur_exp_total, total_income,
        cat_totals, risk, behavior, savings_insight
    )

    # Average daily spend (all-time)
    if len(df) > 0:
        date_range = (df['date'].max() - df['date'].min()).days + 1
        if date_range > 0:
            avg_daily = total_exp / date_range
            insights.append({
                'type': 'daily',
                'title': 'Average Daily Spend',
                'message': f'You spend ₹{avg_daily:,.0f}/day on average.',
                'icon': '📅'
            })

    # Sort actions by priority
    actions = sorted(actions, key=lambda x: x.get('priority', 99))[:3]

    return {
        'insights': insights,
        'alerts': alerts,
        'suggestions': suggestions[:5],
        'actions': actions,
        'top_issue': top_issue,
        'smart_budget': smart_budget,
        'behavior': behavior,
        'narrative': narrative,
        'risk': risk,
        'savings_health': savings_insight,
        'summary': {
            'total_expenses': round(total_exp, 2),
            'num_categories': int(len(cat_totals)),
            'num_transactions': len(df),
            'top_category': str(cat_totals.index[0]) if len(cat_totals) > 0 else None
        }
    }


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _budget_suggestion(category, status, remaining, daily_rate, days_remaining):
    """Generate a short, specific action for this budget item."""
    if status == 'Danger':
        return f'Stop {category} spending — budget already exceeded.'
    if status == 'Warning':
        if daily_rate > 0 and days_remaining > 0:
            safe_daily = remaining / days_remaining if days_remaining > 0 else 0
            return f'Limit {category} to ₹{safe_daily:,.0f}/day for the rest of the month.'
        return f'Slow down {category} spending immediately.'
    return f'{category} budget is on track. Maintain current pace.'


def _build_narrative(today, cur_income, cur_exp_total, total_income,
                     cat_totals, risk, behavior, savings_insight):
    """Build a smart, human-readable monthly summary."""
    month_name = today.strftime('%B %Y')
    parts = []

    if cur_income > 0 or cur_exp_total > 0:
        cur_savings = cur_income - cur_exp_total
        sav_rate = (cur_savings / cur_income * 100) if cur_income > 0 else 0

        parts.append(
            f'In {month_name}, you earned ₹{cur_income:,.0f} and spent ₹{cur_exp_total:,.0f}, '
            f'saving ₹{cur_savings:,.0f} ({sav_rate:.0f}%).'
        )

        if len(cat_totals) > 0:
            top = cat_totals.index[0]
            parts.append(f'Your biggest expense was {top} at ₹{float(cat_totals.iloc[0]):,.0f}.')

        if risk:
            proj = risk.get('projected_month_spend', 0)
            daily = risk.get('daily_burn_rate', 0)
            parts.append(
                f'At ₹{daily:,.0f}/day, you are projected to spend ₹{proj:,.0f} by month-end.'
            )

        if behavior.get('monthly_direction') == 'up':
            pct = behavior.get('monthly_change_pct', 0)
            parts.append(f'Spending increased {pct:.1f}% vs last month — review discretionary categories.')
        elif behavior.get('monthly_direction') == 'down':
            pct = abs(behavior.get('monthly_change_pct', 0))
            parts.append(f'Great job! Spending fell {pct:.1f}% vs last month.')

        if savings_insight:
            label = savings_insight.get('label', '')
            rate = savings_insight.get('rate', 0)
            if label in ('Critical', 'Low'):
                parts.append(f'Savings rate is {label.lower()} at {rate:.1f}% — aim for 20%.')
            elif label in ('Excellent', 'Good'):
                parts.append(f'Savings health is {label.lower()} at {rate:.1f}%. Keep it up!')
    else:
        parts.append(f'No transactions recorded for {month_name} yet.')

    return ' '.join(parts)
