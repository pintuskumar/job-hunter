// Collects HTTP Basic Auth credentials for the cross-origin API and attaches
// them to every request. A cross-origin fetch() never triggers the browser's
// native login popup, so the app needs its own login form instead.
const JH_AUTH_KEY = 'jh_auth_token';

function jhGetAuthToken() {
    return sessionStorage.getItem(JH_AUTH_KEY);
}

function jhAuthHeader() {
    const token = jhGetAuthToken();
    return token ? { Authorization: `Basic ${token}` } : {};
}

function jhClearAuth() {
    sessionStorage.removeItem(JH_AUTH_KEY);
}

const JH_LOCK_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>`;
const JH_USER_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.5"/><path d="M4.5 20c1.6-3.6 4.6-5.5 7.5-5.5s5.9 1.9 7.5 5.5"/></svg>`;
const JH_KEY_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="15" r="4"/><path d="M11 12l7-7M15 5l3 3M18 8l2.5 2.5"/></svg>`;
const JH_EYE_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 12S5 5 12 5s10.5 7 10.5 7-3.5 7-10.5 7S1.5 12 1.5 12z"/><circle cx="12" cy="12" r="3"/></svg>`;
const JH_EYE_OFF_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3l18 18"/><path d="M10.6 5.2A10.6 10.6 0 0 1 12 5c7 0 10.5 7 10.5 7a13.9 13.9 0 0 1-3.2 4.1M6.5 6.6C3.7 8.4 1.5 12 1.5 12s3.5 7 10.5 7c1.4 0 2.7-.3 3.8-.7"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>`;
const JH_ALERT_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5"/><path d="M12 16.2v.1"/></svg>`;

function jhShowLogin(message) {
    return new Promise((resolve) => {
        const existing = document.getElementById('jh-login-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'jh-login-overlay';
        overlay.className = 'jh-login-overlay';
        overlay.innerHTML = `
            <form id="jh-login-form" class="jh-login-form" novalidate>
                <div class="jh-login-badge">${JH_LOCK_ICON}</div>
                <h2>Welcome back</h2>
                <p class="jh-login-sub">Sign in to Job Hunter to continue</p>

                <div class="jh-login-alert" id="jh-login-alert" hidden>
                    <span class="jh-login-alert-icon">${JH_ALERT_ICON}</span>
                    <span id="jh-login-alert-text"></span>
                </div>

                <label class="jh-field">
                    <span class="jh-field-label">Username</span>
                    <span class="jh-input-wrap">
                        <span class="jh-input-icon">${JH_USER_ICON}</span>
                        <input type="text" id="jh-login-user" autocomplete="username" placeholder="Enter your username" required>
                    </span>
                </label>

                <label class="jh-field">
                    <span class="jh-field-label">Password</span>
                    <span class="jh-input-wrap">
                        <span class="jh-input-icon">${JH_KEY_ICON}</span>
                        <input type="password" id="jh-login-pass" autocomplete="current-password" placeholder="Enter your password" required>
                        <button type="button" class="jh-eye-toggle" id="jh-eye-toggle" aria-label="Show password" tabindex="-1">${JH_EYE_ICON}</button>
                    </span>
                </label>

                <button type="submit" class="jh-login-submit" id="jh-login-submit">
                    <span class="jh-login-submit-label">Sign in</span>
                    <span class="jh-spinner" hidden></span>
                </button>
            </form>
        `;
        document.body.appendChild(overlay);

        const userInput = overlay.querySelector('#jh-login-user');
        const passInput = overlay.querySelector('#jh-login-pass');
        const form = overlay.querySelector('#jh-login-form');
        const submitBtn = overlay.querySelector('#jh-login-submit');
        const submitLabel = submitBtn.querySelector('.jh-login-submit-label');
        const spinner = submitBtn.querySelector('.jh-spinner');
        const alertBox = overlay.querySelector('#jh-login-alert');
        const alertText = overlay.querySelector('#jh-login-alert-text');
        const eyeToggle = overlay.querySelector('#jh-eye-toggle');

        function showAlert(text) {
            alertText.textContent = text;
            alertBox.hidden = false;
            overlay.querySelector('.jh-login-form').classList.add('jh-shake');
            setTimeout(() => overlay.querySelector('.jh-login-form')?.classList.remove('jh-shake'), 400);
        }

        function setBusy(busy) {
            submitBtn.disabled = busy;
            spinner.hidden = !busy;
            submitLabel.textContent = busy ? 'Signing in…' : 'Sign in';
        }

        eyeToggle.addEventListener('click', () => {
            const showing = passInput.type === 'text';
            passInput.type = showing ? 'password' : 'text';
            eyeToggle.innerHTML = showing ? JH_EYE_ICON : JH_EYE_OFF_ICON;
            eyeToggle.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
        });

        userInput.focus();
        if (message) showAlert(message);

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const user = userInput.value.trim();
            const pass = passInput.value;
            if (!user || !pass) {
                showAlert('Please enter both a username and password.');
                return;
            }
            const token = btoa(`${user}:${pass}`);
            alertBox.hidden = true;
            setBusy(true);
            try {
                const resp = await fetch(`${API_BASE_URL}/api/jobs?limit=1`, {
                    headers: { Authorization: `Basic ${token}` },
                });
                if (resp.status === 401) {
                    showAlert('Incorrect username or password.');
                    setBusy(false);
                    passInput.value = '';
                    passInput.focus();
                    return;
                }
                if (!resp.ok) {
                    showAlert(`Server error (${resp.status}). Please try again.`);
                    setBusy(false);
                    return;
                }
                sessionStorage.setItem(JH_AUTH_KEY, token);
                overlay.classList.add('jh-closing');
                setTimeout(() => overlay.remove(), 150);
                resolve();
            } catch (err) {
                showAlert('Could not reach the server. Check your connection.');
                setBusy(false);
            }
        });
    });
}

async function jhEnsureAuth() {
    if (!jhGetAuthToken()) {
        await jhShowLogin();
    }
}

async function jhHandleUnauthorized() {
    jhClearAuth();
    await jhShowLogin('Your session expired — please sign in again.');
}
