const assert = require('node:assert/strict');
const test = require('node:test');

global.document = { addEventListener() {} };

const { api } = require('../static/app.js');

test('api throws a redacted backend detail for non-2xx responses', async () => {
    global.fetch = async () => ({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable',
        json: async () => ({ detail: 'Google Sheets is not configured' }),
    });

    await assert.rejects(
        () => api('/export/sheets'),
        /503: Google Sheets is not configured/,
    );
});

test('api returns JSON for successful responses', async () => {
    global.fetch = async () => ({
        ok: true,
        headers: { get: () => 'application/json' },
        json: async () => ({ exported: 3 }),
        text: async () => '',
    });

    assert.deepEqual(await api('/export/sheets'), { exported: 3 });
});
