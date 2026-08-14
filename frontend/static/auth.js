// Collects HTTP Basic Auth credentials for the cross-origin API and attaches
// them to every request. A cross-origin fetch() never triggers the browser's
// native login popup, so the app needs its own tiny login form instead.
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

function jhShowLogin(message) {
    return new Promise((resolve) => {
        const existing = document.getElementById('jh-login-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'jh-login-overlay';
        overlay.className = 'jh-login-overlay';
        overlay.innerHTML = `
            <form id="jh-login-form" class="jh-login-form">
                <h2>Job Hunter Login</h2>
                ${message ? `<p class="jh-login-error">${message}</p>` : ''}
                <label>Username<input type="text" id="jh-login-user" autocomplete="username" required></label>
                <label>Password<input type="password" id="jh-login-pass" autocomplete="current-password" required></label>
                <button type="submit" class="btn btn-primary">Sign in</button>
            </form>
        `;
        document.body.appendChild(overlay);
        overlay.querySelector('#jh-login-user').focus();
        overlay.querySelector('#jh-login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const user = overlay.querySelector('#jh-login-user').value;
            const pass = overlay.querySelector('#jh-login-pass').value;
            sessionStorage.setItem(JH_AUTH_KEY, btoa(`${user}:${pass}`));
            overlay.remove();
            resolve();
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
    await jhShowLogin('Invalid credentials — please try again.');
}
