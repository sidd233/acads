import express from 'express';
import cors from 'cors';
import multer from 'multer';
import { execFile } from 'node:child_process';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BINARY = path.join(__dirname, '..', 'parser', 'cflow-analyzer');
const SAMPLE = path.join(__dirname, '..', 'test-programs', 'sample1.c');
const PORT = process.env.PORT || 3001;

const app = express();
app.use(cors());
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 1024 * 1024 } });

/** Runs the compiled analyzer on a .c file on disk and returns { source, functions }. */
function analyzeFile(srcPath) {
  return new Promise((resolve, reject) => {
    const outPath = srcPath + '.out.json';
    execFile(BINARY, [srcPath, '-o', outPath], async (err, _stdout, stderr) => {
      if (err) {
        reject({ status: 400, message: stderr?.trim() || 'analysis failed' });
        return;
      }
      try {
        const [source, json] = await Promise.all([
          fs.readFile(srcPath, 'utf8'),
          fs.readFile(outPath, 'utf8'),
        ]);
        const parsed = JSON.parse(json);
        resolve({ source, functions: parsed.functions });
      } catch (e) {
        reject({ status: 500, message: 'failed to read analyzer output: ' + e.message });
      } finally {
        fs.unlink(outPath).catch(() => {});
      }
    });
  });
}

app.get('/api/sample', async (_req, res) => {
  try {
    const result = await analyzeFile(SAMPLE);
    res.json(result);
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});

app.post('/api/analyze', upload.single('file'), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'no file uploaded' });

  const tmpPath = path.join(os.tmpdir(), `cflow-${Date.now()}-${Math.random().toString(36).slice(2)}.c`);
  try {
    await fs.writeFile(tmpPath, req.file.buffer);
    const result = await analyzeFile(tmpPath);
    res.json(result);
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  } finally {
    fs.unlink(tmpPath).catch(() => {});
  }
});

app.listen(PORT, () => {
  console.log(`cflow-analyzer backend listening on http://localhost:${PORT}`);
  console.log(`using binary: ${BINARY}`);
});
