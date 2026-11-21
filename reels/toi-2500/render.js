// Deterministic frame renderer: node render.js <outDir> <fps> [startFrame endFrame] | --stills t1,t2,...
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const args = process.argv.slice(2);
  const out = args[0];
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('PAGEERROR', e.message));
  await page.goto('file://' + path.resolve(__dirname, 'reel.html'));
  await page.waitForFunction(() => window.READY === true);
  if (args[1] === '--stills') {
    for (const t of args[2].split(',').map(Number)) {
      await page.evaluate(tt => window.renderAt(tt), t);
      await page.screenshot({ path: path.join(out, `still_${t.toFixed(2)}.png`) });
    }
  } else {
    const fps = Number(args[1]);
    const dur = await page.evaluate(() => window.DUR);
    const total = Math.round(dur * fps);
    const a = args[2] ? Number(args[2]) : 0;
    const b = args[3] ? Number(args[3]) : total;
    for (let i = a; i < b; i++) {
      await page.evaluate(tt => window.renderAt(tt), i / fps);
      await page.screenshot({ path: path.join(out, `f${String(i).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 93 });
      if (i % 200 === 0) console.log('frame', i, '/', b);
    }
  }
  await browser.close();
})();
