import Busboy from 'busboy';
import fs from 'fs';
import path from 'path';
import os from 'os';
import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';

// Ukuran maksimal file icon (10MB)
const MAX_FILE_SIZE = 10 * 1024 * 1024;

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Parse multipart form-data
  const { fields, files } = await parseMultipart(req);

  const websiteUrl = fields.url;
  const appName = fields.appName;
  const email = fields.email;
  const iconFile = files.icon;

  if (!websiteUrl || !appName || !email || !iconFile) {
    return res.status(400).json({ error: 'Missing required fields: url, appName, email, icon' });
  }

  // Validasi tipe file (harus gambar)
  if (!iconFile.mimeType.startsWith('image/')) {
    return res.status(400).json({ error: 'Icon must be an image' });
  }

  // Simpan file sementara di /tmp
  const tempPath = path.join(os.tmpdir(), `icon-${Date.now()}.png`);
  fs.writeFileSync(tempPath, iconFile.buffer);

  try {
    // Konfigurasi argumen untuk Puppeteer
    const browser = await puppeteer.launch({
      args: [
        ...chromium.args,
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--disable-extensions',
        '--disable-features=HttpsFirstBalancedModeAutoEnable', // hindari error ERR_BLOCKED_BY_CLIENT
      ],
      executablePath: await chromium.executablePath(),
      headless: chromium.headless,
      defaultViewport: { width: 1280, height: 800 },
    });

    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');

    // ---------- Langkah 1: Halaman awal median.co ----------
    await page.goto('https://median.co/', { waitUntil: 'networkidle2' });

    // Isi URL
    const urlInput = await page.$('input[placeholder*="URL"], input[type="url"]');
    if (!urlInput) throw new Error('URL input tidak ditemukan');
    await urlInput.type(websiteUrl);

    // Klik tombol "Build your app" / "Enter any URL to try it out"
    const buildButton = await page.$('button:contains("Build"), a:contains("Build")');
    if (!buildButton) throw new Error('Tombol Build tidak ditemukan');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle2' }),
      buildButton.click(),
    ]);

    // ---------- Langkah 2: Halaman Create New App ----------
    // Isi App Name
    const nameInput = await page.$('input[placeholder*="App Name"], input[name="appName"]');
    if (!nameInput) throw new Error('Input App Name tidak ditemukan');
    await nameInput.type(appName);

    // Isi Email
    const emailInput = await page.$('input[type="email"], input[placeholder*="Email"]');
    if (!emailInput) throw new Error('Input Email tidak ditemukan');
    await emailInput.type(email);

    // Klik "Start Building my App!"
    const startButton = await page.$('button:contains("Start Building")');
    if (!startButton) throw new Error('Tombol Start Building tidak ditemukan');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle2' }),
      startButton.click(),
    ]);

    // ---------- Langkah 3: Halaman Branding ----------
    // Tunggu hingga halaman branding muncul (URL mengandung /branding)
    await page.waitForFunction(() => window.location.href.includes('/branding'), { timeout: 30000 });

    // Centang semua checkbox (iOS & Android) – opsional, untuk amannya
    const checkboxes = await page.$$('input[type="checkbox"]');
    for (const cb of checkboxes) {
      await cb.evaluate(c => c.checked = true);
    }

    // Upload file icon
    const fileInput = await page.$('input[type="file"]');
    if (!fileInput) throw new Error('Input file icon tidak ditemukan');
    await fileInput.uploadFile(tempPath);

    // Tunggu beberapa saat untuk upload & proses (bisa memicu redirect)
    await new Promise(r => setTimeout(r, 3000));

    // Coba klik tombol "Continue" / "Next" / "Generate" jika ada
    const possibleButtons = [
      'button:contains("Continue")',
      'button:contains("Next")',
      'button:contains("Generate")',
      'button:contains("Upload")',
      'button:contains("Save")',
    ];
    for (const sel of possibleButtons) {
      const btn = await page.$(sel);
      if (btn) {
        await Promise.all([
          page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 10000 }).catch(() => {}),
          btn.click(),
        ]);
        break;
      }
    }

    // Tunggu hingga URL berubah menjadi /build (maks 60 detik)
    await page.waitForFunction(() => window.location.href.includes('/build'), { timeout: 60000 });

    const buildUrl = page.url();

    await browser.close();
    fs.unlinkSync(tempPath); // hapus file sementara

    return res.status(200).json({ 
      success: true, 
      buildUrl,
      message: 'Aplikasi berhasil dibuat. Silakan buka link tersebut untuk memantau progress build dan mengunduh file.'
    });

  } catch (error) {
    console.error('Error during automation:', error);
    // Bersihkan file sementara jika gagal
    if (fs.existsSync(tempPath)) fs.unlinkSync(tempPath);
    return res.status(500).json({ error: error.message });
  }
}

// Helper untuk parse multipart/form-data
function parseMultipart(req) {
  return new Promise((resolve, reject) => {
    const busboy = Busboy({ headers: req.headers, limits: { fileSize: MAX_FILE_SIZE } });
    const fields = {};
    const files = {};

    busboy.on('file', (fieldname, file, info) => {
      const { filename, mimeType } = info;
      const chunks = [];
      file.on('data', chunk => chunks.push(chunk));
      file.on('end', () => {
        files[fieldname] = {
          filename,
          mimeType,
          buffer: Buffer.concat(chunks),
        };
      });
    });

    busboy.on('field', (fieldname, val) => {
      fields[fieldname] = val;
    });

    busboy.on('finish', () => resolve({ fields, files }));
    busboy.on('error', reject);

    req.pipe(busboy);
  });
}

// Agar bisa dijalankan di Vercel, kita perlu menonaktifkan bodyParser default
export const config = {
  api: {
    bodyParser: false,
  },
};
