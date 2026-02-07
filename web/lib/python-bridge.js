/**
 * Python Bridge — calls H3lPeR Python modules via child_process.
 *
 * Currently used only for rendering briefing JSON → HTML via the
 * Python emailer module. Weather and stocks are now client-side.
 */

const { execFile, spawn } = require('child_process');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const PYTHON = process.env.PYTHON_PATH || 'python3';
const ENV_FILE = path.join(PROJECT_ROOT, '.env');

/**
 * Run a Python snippet in the project root, with .env loaded.
 * Returns stdout as a string.
 */
function runPython(script, { timeout = 30000 } = {}) {
  return new Promise((resolve, reject) => {
    const wrappedScript = `
import sys, os
sys.path.insert(0, ${JSON.stringify(PROJECT_ROOT)})
os.chdir(${JSON.stringify(PROJECT_ROOT)})
from dotenv import load_dotenv
load_dotenv(${JSON.stringify(ENV_FILE)})
${script}
`;
    execFile(PYTHON, ['-c', wrappedScript], {
      cwd: PROJECT_ROOT,
      timeout,
      maxBuffer: 1024 * 1024 * 5,
      env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' }
    }, (err, stdout, stderr) => {
      if (err) {
        reject(new Error(stderr || err.message));
      } else {
        resolve(stdout);
      }
    });
  });
}

/**
 * High-level call dispatcher. Supported commands:
 *   - render_briefing  (pass JSON string as arg)
 */
async function pythonCall(command, arg = null) {
  switch (command) {
    case 'render_briefing':
      if (!arg) throw new Error('render_briefing requires a JSON argument');
      return new Promise((resolve, reject) => {
        const wrappedScript = `
import sys, os
sys.path.insert(0, ${JSON.stringify(PROJECT_ROOT)})
os.chdir(${JSON.stringify(PROJECT_ROOT)})
from dotenv import load_dotenv
load_dotenv(${JSON.stringify(ENV_FILE)})
import json
from emailer import render_briefing_html, validate_briefing_json
doc = json.loads(sys.stdin.read())
validate_briefing_json(doc)
print(render_briefing_html(doc))
`;
        const child = spawn(PYTHON, ['-c', wrappedScript], {
          cwd: PROJECT_ROOT,
          env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' }
        });

        let stdout = '';
        let stderr = '';
        child.stdout.on('data', d => stdout += d);
        child.stderr.on('data', d => stderr += d);
        child.on('close', code => {
          if (code !== 0) reject(new Error(stderr || `Python exited with code ${code}`));
          else resolve(stdout);
        });

        child.stdin.write(arg);
        child.stdin.end();
      });

    default:
      throw new Error(`Unknown python-bridge command: ${command}`);
  }
}

module.exports = { pythonCall, runPython };
