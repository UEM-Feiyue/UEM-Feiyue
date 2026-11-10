import test from 'node:test';
import assert from 'node:assert/strict';
import { generateKeyPairSync, webcrypto } from 'node:crypto';
import worker, { validate, issueFor } from '../worker/src/index.js';

const { privateKey } = generateKeyPairSync('rsa', { modulusLength: 2048 });
const privatePem = privateKey.export({ type: 'pkcs8', format: 'pem' });
const signingKey = await webcrypto.subtle.importKey('pkcs8', privateKey.export({ type: 'pkcs8', format: 'der' }),
  { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
const appEnv = { GITHUB_APP_ID: '5666636', GITHUB_APP_INSTALLATION_ID: '1234', GITHUB_APP_PRIVATE_KEY: privatePem };

const valid = {
  version: 2, category: 'career', author: '张同学', year: '2026',
  college: '某学院', major: '软件工程',
  destination: '某科技公司', program: '软件工程师',
  body: '我准备了项目经历和面试。', contact: '', turnstileToken: 'sample-token'
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
test('renders a signed, reviewable Issue', async () => {
  const issue = await issueFor(validate(valid), signingKey);
  assert.match(issue.title, /^\[飞跃手册投稿\]/);
  assert.deepEqual(issue.labels, ['submission:pending']);
  assert.match(issue.body, /uem-submission-v2:/);
  assert.match(issue.body, /^\*\*方向：\*\* 就业/m);
  assert.match(issue.body, /\n---\n\n\*\*已分配至：\*\* @UEM-Feiyue\/career-reviewers\n\n<!-- uem-submission-v2:/);
  assert.doesNotMatch(issue.body, /飞跃手册经历投稿（待审核）|公开投稿，内容尚未经核实|\*\*审核组：\*\*/);
  assert.doesNotMatch(issue.body, /sample-token/);
});
test('requires program everywhere and admission details only for postgraduate submissions', async () => {
  for (const category of ['kaoyan', 'overseas', 'career', 'public']) {
    assert.equal(validate({ ...valid, category, program: '' }), null);
  }
  assert.equal(validate({ ...valid, category: 'kaoyan' }), null);
  const admission = { ...valid, category: 'kaoyan', destination: '北京理工大学', institution_id: 'bit', admission_year: '2026', degree_type: 'academic', admission_method: 'exam' };
  assert.equal(validate(admission).institution_id, 'bit');
  assert.match((await issueFor(validate(admission), signingKey)).body, /录取年份/);
  assert.equal(validate({ ...admission, institution_id: 'missing' }), null);
  assert.equal(validate({ ...admission, destination: '其他单位' }), null);
  assert.equal(validate({ ...admission, destination: '未收录单位', institution_id: '' }).institution_id, '');
  for (const key of ['admission_year', 'degree_type', 'admission_method']) assert.equal(validate({ ...admission, [key]: '' }), null);
  assert.equal(validate({ ...valid, institution_type: '985' }), null);
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
      ...appEnv, TURNSTILE_SECRET: 'dummy',
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
    if (String(url).includes('access_tokens')) return Response.json({ token: 'installation-token' });
    return Response.json({
      html_url: 'https://github.com/UEM-Feiyue/UEM-Feiyue/issues/57'
    }, { status: 201 });
  };
  try {
    const env = {
      SUBMISSIONS_DISABLED: 'false', SUBMISSION_MODE: 'public',
      ...appEnv, TURNSTILE_SECRET: 'test-only',
      SUBMISSION_LIMITER: { limit: async () => ({ success: true }) }
    };
    const response = await worker.fetch(request(), env);
    assert.equal(response.status, 201);
    assert.equal((await response.json()).ok, true);
    assert.equal(calls.length, 3);
    assert.deepEqual(JSON.parse(calls[1].options.body).permissions, { issues: 'write' });
    assert.equal(calls[2].options.headers.Authorization, 'Bearer installation-token');
    const body = JSON.parse(calls[2].options.body);
    assert.deepEqual(body.labels, ['submission:pending']);
    assert.match(body.body, /uem-submission-v2:/);
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
      ...appEnv, TURNSTILE_SECRET: 'test-only',
      SUBMISSION_LIMITER: { limit: async () => ({ success: true }) }
    };
    const response = await worker.fetch(request(), env);
    assert.equal(response.status, 403);
    assert.equal(calls, 1);
  } finally { globalThis.fetch = originalFetch; }
});
