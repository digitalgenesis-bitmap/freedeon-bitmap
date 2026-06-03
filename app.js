'use strict';

(function () {

  // ── DOM refs ────────────────────────────────────────────────────────────────
  const output   = document.getElementById('console-output');
  const inputEl  = document.getElementById('console-input');
  const form     = document.getElementById('console-form');

  // ── History ─────────────────────────────────────────────────────────────────
  const history  = [];
  let   histIdx  = -1;

  // ── Helpers ──────────────────────────────────────────────────────────────────
  function print(text, cls) {
    const line = document.createElement('div');
    line.className = 'console-line' + (cls ? ' ' + cls : '');
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
  }

  function printPrompt(cmd) {
    print('> ' + cmd, 'input-echo');
  }

  function printResponse(text) {
    print(text, 'response');
  }

  function printError(text) {
    print('ERROR: ' + text, 'error');
  }

  // ── Network ──────────────────────────────────────────────────────────────────
  async function sendCommand(cmd) {
    try {
      const res = await fetch('http://localhost:8000/signal', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ command: cmd })
      });

      if (!res.ok) {
        printError('Server returned ' + res.status);
        return;
      }

      const data = await res.json();
      printResponse(data.response || '(empty response)');
    } catch (err) {
      printError('Could not reach server. Is server.py running on port 8000?');
    }
  }

  // ── Submit ───────────────────────────────────────────────────────────────────
  function handleSubmit() {
    const raw = inputEl.value;
    const cmd = raw.trim().toLowerCase();

    inputEl.value = '';
    histIdx = -1;

    if (!cmd) return;

    history.unshift(cmd);
    if (history.length > 50) history.pop();

    printPrompt(cmd);
    sendCommand(cmd);
  }

  // ── Keyboard ─────────────────────────────────────────────────────────────────
  inputEl.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
      return;
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (history.length === 0) return;
      histIdx = Math.min(histIdx + 1, history.length - 1);
      inputEl.value = history[histIdx];
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      histIdx = Math.max(histIdx - 1, -1);
      inputEl.value = histIdx === -1 ? '' : history[histIdx];
      return;
    }
  });

  // ── Form fallback ────────────────────────────────────────────────────────────
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      handleSubmit();
    });
  }

  // ── Boot message ─────────────────────────────────────────────────────────────
  print('System online. Type a command: help, status, memory, territory, signal', 'info');
  inputEl.focus();

}());
