/* Public submissions become GitHub Issues, never published articles. */
import schema from '../../data/schema.json' with { type: 'json' };

const ORIGINS = new Set(['https://uem-feiyue.github.io']);
const REPOSITORY = 'UEM-Feiyue/UEM-Feiyue-Site-Source';
const MAX_BYTES = 65536;
const CONTROL = /[\u0000-\u0008\u000b\u000c\u000e-\u001f]/;
const SIGNING_CONTEXT = 'UEM-Feiyue:submission:v2:';

function appBase64Url(bytes) {
  let value = '';
  for (const byte of bytes) value += String.fromCharCode(byte);
  return btoa(value).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function appSigningKey(env) {
  const pem = env.GITHUB_APP_PRIVATE_KEY?.replace(/\\n/g, '\n') || '';
  const match = pem.match(/-----BEGIN PRIVATE KEY-----([\s\S]+?)-----END PRIVATE KEY-----/);
  if (!match) throw Error('GitHub App PKCS#8 private key is missing');
  const raw = Uint8Array.from(atob(match[1].replace(/\s/g, '')), char => char.charCodeAt(0));
  return crypto.subtle.importKey('pkcs8', raw, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
}

async function installationToken(env, key) {
  if (!/^\d+$/.test(env.GITHUB_APP_ID || '') || !/^\d+$/.test(env.GITHUB_APP_INSTALLATION_ID || ''))
    throw Error('GitHub App identity is missing');
  const now = Math.floor(Date.now() / 1000);
  const header = appBase64Url(new TextEncoder().encode(JSON.stringify({ alg: 'RS256', typ: 'JWT' })));
  const payload = appBase64Url(new TextEncoder().encode(JSON.stringify({ iat: now - 60, exp: now + 480, iss: env.GITHUB_APP_ID })));
  const input = header + '.' + payload;
  const signature = appBase64Url(new Uint8Array(await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(input))));
  const response = await fetch('https://api.github.com/app/installations/' + env.GITHUB_APP_INSTALLATION_ID + '/access_tokens', {
    method: 'POST', headers: {
      Authorization: 'Bearer ' + input + '.' + signature,
      Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'UEM-Feiyue-Submission'
    },
    body: JSON.stringify({ repositories: ['UEM-Feiyue-Site-Source'], permissions: { issues: 'write' } }),
    signal: AbortSignal.timeout(10000)
  });
  if (!response.ok) throw Error('GitHub App token exchange failed: ' + response.status);
  const result = await response.json();
  if (!result.token) throw Error('GitHub App token missing');
  return result.token;
}

function respond(data, status = 200, origin) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
      ...(origin ? {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Vary': 'Origin'
      } : {})
    }
  });
}
const error = (message, status, origin) => respond({ ok: false, message }, status, origin);

async function readJSON(request) {
  if (!request.body) throw Error('Missing body');
  const reader = request.body.getReader();
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BYTES) throw Error('Payload too large');
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  const data = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
  if (!data || typeof data !== 'object' || Array.isArray(data)) throw Error('Invalid JSON');
  return data;
}

function validate(payload) {
  if (payload.version !== 1 || !schema.categories.some(({ id }) => id === payload.category))
    return null;
  if (typeof payload.turnstileToken !== 'string' ||
      payload.turnstileToken.length < 1 || payload.turnstileToken.length > 2048) return null;
  const record = { version: 1, category: payload.category };
  for (const field of schema.fields) {
    const value = payload[field.name] ?? '';
    if (typeof value !== 'string' || CONTROL.test(value)) return null;
    const clean = value.trim();
    if (field.required && !clean) return null;
    if (field.maxLength && clean.length > field.maxLength) return null;
    if (field.pattern && clean && !(new RegExp('^(?:' + field.pattern + ')$')).test(clean)) return null;
    record[field.name] = clean;
  }
  return record;
}

function base64url(value) {
  const bytes = new TextEncoder().encode(JSON.stringify(value));
  let raw = '';
  for (const byte of bytes) raw += String.fromCharCode(byte);
  return btoa(raw).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
const quote = value => value.split(/\r?\n/).map(line => '> ' + line.replace(/</g, '&lt;')).join('\n');

async function issueFor(record, key) {
  const category = schema.categories.find(item => item.id === record.category);
  const title = '[飞跃手册投稿] [' + category.label + '] ' +
    (record.author + ' — ' + record.destination + (record.program ? ' · ' + record.program : ''))
      .replace(/\s+/g, ' ').slice(0, 95);
  const lines = [
    '**方向：** ' + category.label,
    '**作者：** ' + record.author,
    '**毕业届次：** ' + record.year,
    '**学院：** ' + record.college,
    '**专业：** ' + record.major,
    '**去向单位：** ' + record.destination,
    '**专业 / 项目 / 岗位：** ' + (record.program || '未填写'), '',
    '### 经历正文', quote(record.body), '',
    '### 联系方式', record.contact ? quote(record.contact) : '> 未填写', '',
    '---', '',
    '**已分配至：** @UEM-Feiyue/' + category.reviewTeam
  ];
  const encoded = base64url(record);
  const signature = appBase64Url(new Uint8Array(await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key,
    new TextEncoder().encode(SIGNING_CONTEXT + encoded))));
  lines.push('', '<!-- uem-submission-v2:' + encoded + ':' + signature + ' -->');
  return { title, body: lines.join('\n'), labels: ['submission:pending'] };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/health' && request.method === 'GET')
      return respond({ ok: true, service: 'uem-feiyue-submissions' });
    if (url.pathname !== '/submit') return error('Not found', 404);
    const origin = request.headers.get('Origin');
    if (!ORIGINS.has(origin)) return error('Forbidden', 403);
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '600',
        'Vary': 'Origin'
      } });
    }
    const reject = (message, status = 400) => error(message, status, origin);
    if (request.method !== 'POST') return reject('Method not allowed', 405);
    if (env.SUBMISSIONS_DISABLED !== 'false' || env.SUBMISSION_MODE !== 'public')
      return reject('投稿服务尚未开放。', 503);
    if (!env.GITHUB_APP_ID || !env.GITHUB_APP_INSTALLATION_ID || !env.GITHUB_APP_PRIVATE_KEY || !env.TURNSTILE_SECRET || !env.SUBMISSION_LIMITER)
      return reject('投稿服务尚未配置完成。', 503);
    if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get('Content-Type') || ''))
      return reject('仅支持 JSON 格式。', 415);
    if (Number(request.headers.get('Content-Length') || 0) > MAX_BYTES)
      return reject('投稿内容过长。', 413);
    try {
      const key = request.headers.get('CF-Connecting-IP');
      if (!key || !(await env.SUBMISSION_LIMITER.limit({ key })).success)
        return reject('提交过于频繁，请稍后重试。', 429);
    } catch {
      return reject('限流服务暂不可用。', 503);
    }

    let payload;
    try { payload = await readJSON(request); }
    catch { return reject('投稿数据无效或过长。'); }
    const record = validate(payload);
    if (!record) return reject('请检查投稿字段及内容长度。');

    let verification;
    try {
      const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({
          secret: env.TURNSTILE_SECRET,
          response: payload.turnstileToken,
          remoteip: request.headers.get('CF-Connecting-IP') || ''
        }),
        signal: AbortSignal.timeout(10000)
      });
      if (!response.ok) throw Error('Turnstile unavailable');
      verification = await response.json();
    } catch { return reject('人机验证服务暂不可用。', 503); }
    if (verification?.success !== true ||
        verification.hostname !== new URL(origin).hostname ||
        verification.action !== 'uem_feiyue_submit')
      return reject('人机验证失败或已过期。', 403);

    let issue;
    try {
      const key = await appSigningKey(env);
      const token = await installationToken(env, key);
      const response = await fetch('https://api.github.com/repos/' + REPOSITORY + '/issues', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + token,
          'Accept': 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': 'UEM-Feiyue-Submission'
        },
        body: JSON.stringify(await issueFor(record, key)),
        signal: AbortSignal.timeout(10000)
      });
      if (!response.ok) throw Error('GitHub issue creation failed: ' + response.status);
      issue = await response.json();
      if (typeof issue.html_url !== 'string' ||
          !issue.html_url.startsWith('https://github.com/' + REPOSITORY + '/issues/'))
        throw Error('Invalid GitHub response');
    } catch (cause) {
      console.error('Submission failed', String(cause));
      return reject('投稿暂未能保存，请稍后重试。', 503);
    }
    return respond({ ok: true, issueUrl: issue.html_url }, 201, origin);
  }
};

export { validate, issueFor };
