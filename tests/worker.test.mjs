import test from 'node:test';
import assert from 'node:assert/strict';
import worker, { validate, issueFor } from '../worker/src/index.js';

const valid = {
  version: 1, category: 'career', author: '张同学', year: '2026',
  college: '某学院', major: '软件工程',
  destination: '某科技公司', program: '软件工程师',
  body: '我准备了项目经历和面试。', contact: 'test@example.com', turnstileToken: 'sample-token'
};
const request = (body = valid, origin = 'https://uem-feiyue.github.io') =>
  new Request('https://worker.example/submit', {
    method: 'POST',
    headers: { Origin: origin, 'Content-Type': 'application/json', 'CF-Connecting-IP': '203.0.113.1' },
    body: JSON.stringify(body)
  });
test('validates with the canonical schema', () => {
  assert.equal(validate(valid)?.category, 'career');
  assert.equal(validate({ ...valid, category: 'made-up' }), null);
  assert.equal(validate({ ...valid, year: '20xx' }), null);
  assert.equal(validate({ ...valid, author: '' }), null);
  assert.equal(validate({ ...valid, college: '' }), null);
  assert.equal(validate({ ...valid, major: '' }), null);
  assert.equal(validate({ ...valid, body: 'x'.repeat(8000) })?.category, 'career');
  assert.equal(validate({ ...valid, body: 'x'.repeat(8001) }), null);
  assert.equal(validate({ ...valid, contact: 'x'.repeat(501) }), null);
  assert.equal(validate({ ...valid, author: 123 }), null);
});
test('renders a public, reviewable Issue', () => {
  const issue = issueFor(validate(valid));
  assert.match(issue.title, /^\[飞跃手册投稿\]/);
  assert.deepEqual(issue.labels, ['submission:pending']);
  assert.match(issue.body, /uem-submission-v1:/);
  assert.match(issue.body, /待审核/);
  assert.doesNotMatch(issue.body, /sample-token/);
});
test('school type is required only for postgraduate submissions', () => {
  assert.equal(validate(valid).institution_type, '');
  for (const institution_type of ['985', '211', 'other']) {
    assert.equal(validate({ ...valid, category: 'kaoyan', institution_type }).institution_type, institution_type);
  }
  assert.equal(validate({ ...valid, category: 'kaoyan', institution_type: '' }), null);
  for (const payload of [{ ...valid, institution_type: '985' }, { ...valid, category: 'kaoyan', institution_type: 'fake' }]) {
    assert.equal(validate(payload), null);
  }
  assert.match(issueFor(validate({ ...valid, category: 'kaoyan', institution_type: '211' })).body, /211 院校（非985）/);
});
test('all applicable content fields are required and contact remains public in Issues', () => {
  for (const name of ['author', 'year', 'college', 'major', 'destination', 'program', 'body']) {
    assert.equal(validate({ ...valid, [name]: '' }), null, name);
  }
  assert.equal(validate({ ...valid, contact: '' }).contact, '');
  assert.equal(validate({ ...valid, contact: Array(4).fill('QQ：123456').join('\n') }).category, 'career');
  assert.equal(validate({ ...valid, contact: Array(5).fill('QQ：123456').join('\n') }), null);
  const { contact, ...withoutContact } = valid;
  assert.equal(validate(withoutContact).contact, '');
  assert.equal(validate(valid).show_contact, 'no');
  assert.equal(validate({ ...valid, show_contact: '' }).show_contact, 'no');
  assert.equal(validate({ ...valid, show_contact: 'invalid' }), null);
  for (const show_contact of ['yes', 'no']) {
    const record = validate({ ...valid, show_contact });
    assert.equal(record.show_contact, show_contact);
    assert.match(issueFor(record).body, /test@example.com/);
  }
});
test('fails closed before contacting external services', async () => {
  let contacted = false;
  const oldFetch = globalThis.fetch;
  globalThis.fetch = async () => { contacted = true; throw Error('Unexpected call'); };
  try {
    const env = { SUBMISSION_MODE: 'closed', SUBMISSIONS_DISABLED: 'true' };
    const response = await worker.fetch(request(), env);
    assert.equal(response.status, 503);
    assert.equal(contacted, false);
    assert.equal((await worker.fetch(request(valid, 'https://evil.example'), env)).status, 403);
  } finally { globalThis.fetch = oldFetch; }
});
test('rejects malformed submissions before Turnstile or GitHub', async () => {
  let contacted = false;
  const oldFetch = globalThis.fetch;
  globalThis.fetch = async () => { contacted = true; throw Error('Unexpected call'); };
  try {
    const env = {
      SUBMISSION_MODE: 'public', SUBMISSIONS_DISABLED: 'false',
      GITHUB_TOKEN: 'dummy', TURNSTILE_SECRET: 'dummy',
      SUBMISSION_LIMITER: { limit: async () => ({ success: true }) }
    };
    const response = await worker.fetch(request({ ...valid, category: 'fake' }), env);
    assert.equal(response.status, 400);
    assert.equal(contacted, false);
  } finally { globalThis.fetch = oldFetch; }
});

test('valid verified submission creates one pending Issue', async () => {
  const calls = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    calls.push({ url: String(url), options });
    if (String(url).includes('turnstile')) return Response.json({
      success: true, hostname: 'uem-feiyue.github.io', action: 'uem_feiyue_submit'
    });
    return Response.json({
      html_url: 'https://github.com/UEM-Feiyue/UEM-Feiyue-Site-Source/issues/57'
    }, { status: 201 });
  };
  try {
    const env = {
      SUBMISSIONS_DISABLED: 'false', SUBMISSION_MODE: 'public',
      GITHUB_TOKEN: 'test-only', TURNSTILE_SECRET: 'test-only',
      SUBMISSION_LIMITER: { limit: async () => ({ success: true }) }
    };
    const response = await worker.fetch(request(), env);
    assert.equal(response.status, 201);
    assert.equal((await response.json()).ok, true);
    assert.equal(calls.length, 2);
    const body = JSON.parse(calls[1].options.body);
    assert.deepEqual(body.labels, ['submission:pending']);
    assert.match(body.body, /uem-submission-v1:/);
    assert.doesNotMatch(body.body, /sample-token/);
  } finally { globalThis.fetch = originalFetch; }
});
test('rejects verification for another origin or action', async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return Response.json({ success: true, hostname: 'other.example', action: 'wrong_action' });
  };
  try {
    const env = {
      SUBMISSIONS_DISABLED: 'false', SUBMISSION_MODE: 'public',
      GITHUB_TOKEN: 'test-only', TURNSTILE_SECRET: 'test-only',
      SUBMISSION_LIMITER: { limit: async () => ({ success: true }) }
    };
    const response = await worker.fetch(request(), env);
    assert.equal(response.status, 403);
    assert.equal(calls, 1);
  } finally { globalThis.fetch = originalFetch; }
});
