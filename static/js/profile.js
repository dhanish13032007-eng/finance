/**
 * Profile Module
 * Handles profile update and password change.
 */

const API = '';
const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';

function authHeaders() {
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
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
//  LOAD PROFILE
// ══════════════════════════════════

async function loadProfile() {
    try {
        const res = await fetch(`${API}/api/auth/profile`, { headers: authHeaders() });
        if (res.status === 401) return logout();
        const data = await res.json();

        if (data.status === 'success') {
            const user = data.data;
            document.getElementById('name').value = user.name;
            document.getElementById('email').value = user.email;
            document.getElementById('memberSince').value = user.created_at
                ? new Date(user.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
                : 'N/A';
        }
    } catch (err) {
        showToast('Failed to load profile', 'error');
    }
}

// ══════════════════════════════════
//  UPDATE PROFILE
// ══════════════════════════════════

document.getElementById('profileForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();

    if (!name || !email) {
        showToast('Name and email are required', 'error');
        return;
    }

    try {
        const res = await fetch(`${API}/api/auth/profile`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({ name, email })
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast('Profile updated successfully!');
            // Update stored user info
            const user = JSON.parse(localStorage.getItem('user') || '{}');
            user.name = name;
            user.email = email;
            localStorage.setItem('user', JSON.stringify(user));
        } else {
            showToast(data.message || 'Update failed', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
});

// ══════════════════════════════════
//  CHANGE PASSWORD
// ══════════════════════════════════

document.getElementById('passwordForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (!oldPassword || !newPassword || !confirmPassword) {
        showToast('Please fill all password fields', 'error');
        return;
    }

    if (newPassword !== confirmPassword) {
        showToast('New passwords do not match', 'error');
        return;
    }

    if (newPassword.length < 6) {
        showToast('New password must be at least 6 characters', 'error');
        return;
    }

    try {
        const res = await fetch(`${API}/api/auth/change-password`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast('Password changed successfully!');
            document.getElementById('passwordForm').reset();
        } else {
            showToast(data.message || 'Password change failed', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
});

// ── Init ──
document.addEventListener('DOMContentLoaded', loadProfile);
