import { createLocalAudio } from './local-audio.mjs';

export const COMPOSER_EMOJIS = Object.freeze([
  ['😀','Sorriso'], ['😊','Sorriso com olhos sorridentes'], ['👍','Polegar para cima'], ['🙏','Mãos juntas'],
  ['👋','Aceno'], ['🤝','Aperto de mãos'], ['✅','Marca de confirmação'], ['❤️','Coração'],
  ['🎉','Celebração'], ['🙂','Rosto sorridente'], ['😉','Piscadela'], ['💬','Balão de conversa']
]);
export function insertDraftEmoji(text, start, end, emoji, limit = 500) {
  if (typeof text !== 'string' || !COMPOSER_EMOJIS.some(([value]) => value === emoji)) return null;
  const a = Math.max(0, Math.min(text.length, Number.isInteger(start) ? start : text.length));
  const b = Math.max(a, Math.min(text.length, Number.isInteger(end) ? end : a));
  const value = text.slice(0,a) + emoji + text.slice(b);
  return value.length <= limit ? { value, cursor: a + emoji.length } : null;
}
export function audioDuration(seconds) {
  const value = Math.max(0, Math.floor(seconds));
  return `${Math.floor(value / 60)}:${String(value % 60).padStart(2,'0')}`;
}

/** Instala somente UI local. getContext revalida a elegibilidade a cada ação. */
export function installCommunicationComposer({ getContext, onAttach, onNotice }) {
  const byId = id => document.getElementById(id);
  const input = byId('message-input'), toggle = byId('emoji-toggle'), picker = byId('emoji-picker');
  const record = byId('audio-record'), panel = byId('audio-draft'), player = byId('audio-preview');
  let selection = { start: 0, end: 0 }, playerURL = null;
  const buttons = [];
  function closeEmoji(restore = false) {
    picker.hidden = true; toggle.setAttribute('aria-expanded','false');
    if (restore && getContext().allowed) {
      input.focus(); input.setSelectionRange?.(selection.start, selection.end);
    }
  }
  function rememberCursor() {
    selection = { start: input.selectionStart ?? input.value.length, end: input.selectionEnd ?? input.value.length };
  }
  for (const event of ['input','select','keyup','click']) input.addEventListener(event, rememberCursor);
  COMPOSER_EMOJIS.forEach(([emoji,label], index) => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'emoji-option'; button.textContent = emoji;
    button.setAttribute('aria-label',label);
    button.addEventListener('click', () => {
      if (!getContext().allowed) { closeEmoji(); return; }
      const candidate = insertDraftEmoji(input.value,selection.start,selection.end,emoji,input.maxLength > 0 ? input.maxLength : 500);
      if (!candidate) { onNotice('Limite de 500 caracteres. Remova parte do texto para inserir o emoji.'); closeEmoji(true); return; }
      input.value = candidate.value; selection = { start: candidate.cursor, end: candidate.cursor };
      closeEmoji(true);
    });
    button.addEventListener('keydown', event => {
      const delta = { ArrowRight:1, ArrowLeft:-1, ArrowDown:4, ArrowUp:-4 }[event.key];
      if (delta !== undefined || ['Home','End'].includes(event.key)) {
        event.preventDefault();
        buttons[event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length-1 : (index+delta+buttons.length)%buttons.length].focus();
      }
    });
    buttons.push(button); picker.append(button);
  });
  toggle.addEventListener('click', () => {
    if (!getContext().allowed) return;
    if (!picker.hidden) { closeEmoji(true); return; }
    rememberCursor(); picker.hidden = false; toggle.setAttribute('aria-expanded','true'); buttons[0].focus();
  });
  picker.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation?.(); closeEmoji(true); }
  });
  document.addEventListener('click', event => {
    if (!picker.hidden && !picker.contains(event.target) && !toggle.contains(event.target)) closeEmoji();
  });
  picker.addEventListener('focusout', event => {
    if (event.relatedTarget && !picker.contains(event.relatedTarget) && event.relatedTarget !== toggle) closeEmoji();
  });
  function clearPlayer() {
    if (playerURL) {
      player.pause(); player.removeAttribute('src'); player.load(); playerURL = null;
    }
  }
  function audioView(value) {
    const thread = byId('thread-body');
    const followLatest = thread.scrollHeight - thread.scrollTop - thread.clientHeight <= 80;
    const { phase, error, duration, draft } = value;
    panel.hidden = phase === 'idle'; panel.dataset.phase = phase;
    const labels = { requesting:'Aguardando permissão do microfone…', recording:'Gravando áudio',
      stopping:'Preparando prévia…', ready:'Áudio pronto para ouvir', error };
    // Atualizações do cronômetro não inundam a região live.
    if (byId('audio-status').textContent !== (labels[phase] || ''))
      byId('audio-status').textContent = labels[phase] || '';
    byId('audio-duration').textContent = audioDuration(duration);
    byId('audio-duration').hidden = ['idle','requesting','error'].includes(phase);
    byId('audio-stop').hidden = phase !== 'recording';
    byId('audio-attach').hidden = phase !== 'ready';
    byId('audio-delete').hidden = phase === 'idle';
    byId('audio-delete').setAttribute('aria-label',phase === 'requesting' ? 'Cancelar pedido de microfone' : 'Excluir rascunho de áudio');
    record.disabled = !getContext().allowed || ['requesting','recording','stopping','ready'].includes(phase);
    record.setAttribute('aria-pressed',String(phase === 'recording'));
    player.hidden = phase !== 'ready';
    if (draft && playerURL !== draft.url) { clearPlayer(); player.src = draft.url; playerURL = draft.url; }
    if (!draft) clearPlayer();
    document.querySelectorAll('.local-audio-message').forEach(node => {
      if (!audio.getClip(node.dataset.localAudioId) && node.getAttribute('src')) {
        node.pause(); node.removeAttribute('src'); node.load();
      }
    });
    if (followLatest) thread.scrollTop = thread.scrollHeight;
  }
  const audio = createLocalAudio({ getContext, onChange: audioView });
  record.addEventListener('click', async () => {
    closeEmoji();
    const pending = audio.start();
    if (audio.snapshot().phase === 'requesting') byId('audio-delete').focus();
    await pending;
    const phase = audio.snapshot().phase;
    if (phase === 'recording') byId('audio-stop').focus();
    else if (phase === 'error') byId('audio-delete').focus();
  });
  byId('audio-stop').addEventListener('click', () => {
    audio.stop(); byId('audio-delete').focus();
  });
  byId('audio-delete').addEventListener('click', () => {
    audio.discard(); if (getContext().allowed) record.focus();
  });
  byId('audio-attach').addEventListener('click', () => {
    clearPlayer();
    const clip = audio.attach();
    if (!clip) return;
    onAttach(clip);
    if (getContext().allowed) input.focus();
  });
  player.addEventListener('error', () => {
    if (audio.snapshot().phase === 'ready') onNotice('Este navegador não conseguiu reproduzir o áudio. Exclua o rascunho e tente novamente.');
  });
  function reset() { closeEmoji(); clearPlayer(); audio.reset(); }
  function sync() {
    const allowed = getContext().allowed;
    toggle.disabled = !allowed;
    if (!allowed) closeEmoji();
    audio.sync(); audioView(audio.snapshot());
  }
  window.addEventListener('pagehide', reset);
  document.addEventListener('visibilitychange', () => { if (document.hidden) reset(); });
  return { reset, sync, getClip: audio.getClip };
}
