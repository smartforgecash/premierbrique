const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('js/google-tag.js', 'utf8');

test('public templates use the shared consent loader without the legacy container', () => {
  for (const name of fs.readdirSync('.').filter(name => name.endsWith('.html'))) {
    const html = fs.readFileSync(name, 'utf8');
    assert.doesNotMatch(html, /GTM-M7FSFSM|AW-16805492716|G-13B51XTD31/, name);
    if (/<head[\s>]/i.test(html)) {
      assert.equal((html.match(/include "analytics.html"/g) || []).length, 1, name);
    }
  }
});

function browser(saved, blockedStorage = false, pageViewDestination = '') {
  const head = [], body = [], stored = {};
  function element(tag) {
    return { tag, hidden: false, handlers: {}, setAttribute() {}, focus() {},
      addEventListener(event, callback) { this.handlers[event] = callback; },
      querySelector() { return { focus() {} }; } };
  }
  const context = {
    document: {
      currentScript: { dataset: { googleAdsId: 'AW-18397712539', googleAnalyticsId: 'G-TEST123', googleAdsPageView: pageViewDestination } },
      head: { appendChild(node) { head.push(node); } },
      body: { appendChild(node) { body.push(node); } },
      createElement: element, cookie: ''
    },
    localStorage: {
      getItem() { if (blockedStorage) throw Error('blocked'); return saved; },
      setItem(key, value) { if (blockedStorage) throw Error('blocked'); stored[key] = value; }
    },
    location: { hostname: 'la-premiere-brique.com', reload() { context.reloaded = true; } }
  };
  context.window = context;
  vm.runInNewContext(source, context);
  return { context, head, body, stored,
    scripts: () => head.filter(node => node.tag === 'script'),
    choose: value => body[0].handlers.click({ target: { getAttribute: () => value } }) };
}

test('no Google request before consent; accept loads once and configures both destinations', () => {
  const b = browser(null);
  assert.equal(b.scripts().length, 0);
  assert.equal(b.body[0].hidden, false);
  b.choose('accepted');
  b.choose('accepted');
  assert.equal(b.scripts().length, 1);
  assert.match(b.scripts()[0].src, /AW-18397712539$/);
  const commands = b.context.dataLayer.map(args => Array.from(args));
  assert.equal(commands.filter(c => c[0] === 'config').length, 2);
  assert.equal(commands.some(c => c[0] === 'event'), false);
  assert.equal(commands[0][2].ad_storage, 'denied');
  assert.equal(commands[1][2].ad_personalization, 'denied');
  vm.runInNewContext(source, b.context);
  assert.equal(b.scripts().length, 1);
});

const pageViewDestination = 'AW-18397712539/pDnVCKOztpgdEJuh28RE';
const conversions = b => b.context.dataLayer.map(args => Array.from(args))
  .filter(c => c[0] === 'event' && c[1] === 'conversion');

test('conversion waits for acceptance and is sent once despite repeated initialization or clicks', () => {
  const b = browser(null, false, pageViewDestination);
  assert.equal(conversions(b).length, 0);
  b.choose('refused');
  assert.equal(conversions(b).length, 0);
  b.choose('accepted');
  b.choose('accepted');
  vm.runInNewContext(source, b.context);
  assert.equal(conversions(b).length, 1);
  const event = conversions(b)[0];
  assert.equal(event[2].send_to, pageViewDestination);
  assert.equal(event[2].value, 1);
  assert.equal(event[2].currency, 'EUR');
  const commands = b.context.dataLayer.map(args => Array.from(args));
  assert.ok(commands.indexOf(commands.find(c => c[0] === 'config')) <
    commands.indexOf(commands.find(c => c[0] === 'event')));
});

test('conversion respects saved consent and does not fire for invalid or different destinations', () => {
  const accepted = JSON.stringify({value:'accepted',time:Date.now()});
  assert.equal(conversions(browser(accepted, false, pageViewDestination)).length, 1);
  assert.equal(conversions(browser(JSON.stringify({value:'refused',time:Date.now()}), false, pageViewDestination)).length, 0);
  for (const destination of ['', 'AW-999999/someLabel', 'invalid']) {
    assert.equal(conversions(browser(accepted, false, destination)).length, 0);
  }
  const blockedStorage = browser(null, true, pageViewDestination);
  blockedStorage.choose('accepted');
  assert.equal(conversions(blockedStorage).length, 1);
});

test('refusal blocks loading and can later be changed to acceptance', () => {
  const b = browser(null);
  b.choose('refused');
  assert.equal(b.scripts().length, 0);
  b.choose('accepted');
  assert.equal(b.scripts().length, 1);
  assert.equal(b.context['ga-disable-AW-18397712539'], false);
  b.choose('refused');
  assert.equal(b.context['ga-disable-AW-18397712539'], true);
  assert.equal(b.context.reloaded, true);
});

test('remembered choices expire, and unavailable storage does not block the page', () => {
  assert.equal(browser(JSON.stringify({value:'accepted',time:Date.now()})).scripts().length, 1);
  assert.equal(browser(JSON.stringify({value:'refused',time:Date.now()})).scripts().length, 0);
  assert.equal(browser(JSON.stringify({value:'accepted',time:0})).scripts().length, 0);
  const b = browser(null, true);
  assert.equal(b.scripts().length, 0);
  b.choose('accepted');
  assert.equal(b.scripts().length, 1);
});
