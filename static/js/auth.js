/**
 * Auth Module — Handles login and registration
 * Stores JWT token in localStorage for authenticated API calls.
 */

const API = '';

// ── Toast Notifications ──
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = { success: '✅', error: '❌', warning: '⚠️' };
    toast.innerHTML = `<span>${icons[type] || '📢'}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// ── Redirect if already logged in ──
(function checkAuth() {
    const token = localStorage.getItem('token');
    if (token && (window.location.pathname === '/login' || window.location.pathname === '/' || window.location.pathname === '/register')) {
        // Verify token is still valid
        fetch(`${API}/api/auth/profile`, {
            headers: { 'Authorization': `Bearer ${token}` }
        }).then(res => {
            if (res.ok) window.location.href = '/dashboard';
        }).catch(() => {});
    }
})();

// ── Login Form ──
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('loginBtn');
        btn.disabled = true;
        btn.textContent = 'Signing in...';

        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        if (!email || !password) {
            showToast('Please fill all fields', 'error');
            btn.disabled = false;
            btn.textContent = 'Sign In';
            return;
        }

        try {
            const res = await fetch(`${API}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();

            if (res.ok && data.status === 'success') {
                localStorage.setItem('token', data.data.token);
                localStorage.setItem('user', JSON.stringify(data.data.user));
                showToast('Login successful!');
                setTimeout(() => window.location.href = '/dashboard', 500);
            } else {
                showToast(data.message || 'Login failed', 'error');
                btn.disabled = false;
                btn.textContent = 'Sign In';
            }
        } catch (err) {
            showToast('Network error. Is the server running?', 'error');
            btn.disabled = false;
            btn.textContent = 'Sign In';
        }
    });
}

// ── Register Form ──
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('registerBtn');
        btn.disabled = true;
        btn.textContent = 'Creating account...';

        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (!name || !email || !password) {
            showToast('Please fill all fields', 'error');
            btn.disabled = false;
            btn.textContent = 'Create Account';
            return;
        }

        if (password !== confirmPassword) {
            showToast('Passwords do not match', 'error');
            btn.disabled = false;
            btn.textContent = 'Create Account';
            return;
        }

        if (password.length < 6) {
            showToast('Password must be at least 6 characters', 'error');
            btn.disabled = false;
            btn.textContent = 'Create Account';
            return;
        }

        try {
            const res = await fetch(`${API}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            const data = await res.json();

            if (res.ok && data.status === 'success') {
                showToast('Account created! Redirecting to login...');
                setTimeout(() => window.location.href = '/login', 1200);
            } else {
                showToast(data.message || 'Registration failed', 'error');
                btn.disabled = false;
                btn.textContent = 'Create Account';
            }
        } catch (err) {
            showToast('Network error. Is the server running?', 'error');
            btn.disabled = false;
            btn.textContent = 'Create Account';
        }
    });
}
