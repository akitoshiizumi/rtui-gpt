import { RealtimeAgent, RealtimeSession } from 'https://unpkg.com/@openai/agents-realtime/dist/index.mjs';

let session;

async function start() {
  const resp = await fetch('/token');
  const { token } = await resp.json();

  const agent = new RealtimeAgent({
    name: 'Assistant',
    instructions: 'You are a helpful assistant.'
  });
  session = new RealtimeSession(agent);
  await session.connect({ apiKey: token });

  const log = document.getElementById('log');

  function renderHistory(history) {
    log.innerHTML = '';
    for (const item of history) {
      if (item.type === 'message') {
        const div = document.createElement('div');
        div.className = item.role === 'user' ? 'user' : 'assistant';
        div.textContent = `${item.role}: ${item.content || item.transcript || ''}`;
        log.appendChild(div);
      }
    }
  }

  renderHistory(session.history);
  session.on('history_updated', renderHistory);
}

document.getElementById('start').addEventListener('click', start);
