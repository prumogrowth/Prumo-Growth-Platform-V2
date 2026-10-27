/** FV-UX-01: captura efêmera. Blob/URL nunca saem da memória desta página.
 * Não é mídia Meta, autenticação, upload ou confirmação de transporte.
 */
export function createLocalAudio({ getContext, onChange = () => {},
  mediaDevices = globalThis.navigator?.mediaDevices, Recorder = globalThis.MediaRecorder,
  permissions = globalThis.navigator?.permissions,
  makeURL = blob => URL.createObjectURL(blob), dropURL = url => URL.revokeObjectURL(url),
  now = () => performance.now(), schedule = fn => setInterval(fn, 250),
  unschedule = id => clearInterval(id) } = {}) {
  let phase = 'idle', error = '', duration = 0, generation = 0, context = null;
  let stream = null, recorder = null, timer = null, started = 0, chunks = [], bytes = 0;
  let draft = null, permission = null, clipSequence = 0;
  const clips = new Map();
  const snapshot = () => ({ phase, error, duration, draft });
  const emit = () => onChange(snapshot());
  const valid = () => {
    const current = getContext();
    return current.allowed && context === current.key;
  };
  function stopTracks() {
    if (stream) for (const track of stream.getTracks()) {
      track.onended = null;
      track.stop();
    }
    stream = null;
  }
  function releaseCapture() {
    if (timer !== null) unschedule(timer);
    timer = null;
    if (recorder) {
      recorder.ondataavailable = recorder.onstop = recorder.onerror = null;
      if (recorder.state !== 'inactive') { try { recorder.stop(); } catch {} }
    }
    recorder = null;
    stopTracks();
    chunks = []; bytes = 0;
  }
  function discard() {
    generation++;
    releaseCapture();
    if (permission) permission.onchange = null;
    permission = null;
    if (draft) dropURL(draft.url);
    draft = null; phase = 'idle'; error = ''; duration = 0;
    emit();
  }
  function reset() {
    for (const clip of clips.values()) dropURL(clip.url);
    clips.clear(); context = null;
    discard();
  }
  function fail(message) {
    discard(); phase = 'error'; error = message; emit();
  }
  function sync() {
    if (context !== null && !valid()) reset();
  }
  function stop() {
    if (phase !== 'recording') return;
    if (!valid()) { reset(); return; }
    duration = Math.max(0, (now() - started) / 1000);
    phase = 'stopping';
    if (timer !== null) unschedule(timer);
    timer = null;
    emit();
    try { recorder.stop(); stopTracks(); }
    catch { fail('Não foi possível finalizar o áudio. Tente gravar novamente.'); }
  }
  async function start() {
    if (!getContext().allowed || ['requesting','recording','stopping','ready'].includes(phase)) return;
    discard(); context = getContext().key;
    if (!mediaDevices?.getUserMedia || !Recorder) {
      fail('Gravação indisponível neste navegador. Use um navegador compatível em HTTPS ou localhost.'); return;
    }
    const ticket = generation;
    phase = 'requesting'; emit();
    try {
      const acquired = await mediaDevices.getUserMedia({ audio: true });
      if (ticket !== generation || !valid()) {
        for (const track of acquired.getTracks()) track.stop();
        if (ticket === generation) reset();
        return;
      }
      stream = acquired;
      for (const track of stream.getTracks()) track.onended = () => {
        if (ticket !== generation) return;
        if (!valid()) { reset(); return; }
        if (['recording','requesting'].includes(phase)) fail('Acesso ao microfone interrompido. O rascunho foi descartado.');
      };
      const mimeType = ['audio/webm;codecs=opus','audio/ogg;codecs=opus','audio/mp4']
        .find(type => Recorder.isTypeSupported?.(type));
      recorder = mimeType ? new Recorder(stream, { mimeType }) : new Recorder(stream);
      recorder.ondataavailable = event => {
        if (ticket !== generation || !valid() || !event.data?.size) return;
        bytes += event.data.size;
        if (bytes > 10 * 1024 * 1024) { fail('O áudio excedeu o limite desta prévia local. Grave um trecho menor.'); return; }
        chunks.push(event.data);
      };
      recorder.onerror = () => {
        if (ticket !== generation) return;
        if (!valid()) { reset(); return; }
        fail('Falha na gravação. O rascunho foi descartado; tente novamente.');
      };
      recorder.onstop = () => {
        if (ticket !== generation) return;
        if (!valid()) { reset(); return; }
        const type = recorder.mimeType || chunks[0]?.type || '';
        const blob = new Blob(chunks, { type });
        releaseCapture();
        if (!blob.size) { fail('Nenhum áudio foi capturado. Verifique o microfone e tente novamente.'); return; }
        try { draft = { url: makeURL(blob), duration, type }; }
        catch { fail('Não foi possível preparar a prévia de áudio. Tente novamente.'); return; }
        phase = 'ready'; emit();
      };
      recorder.start(250); started = now(); phase = 'recording'; emit();
      timer = schedule(() => {
        if (!valid()) { reset(); return; }
        duration = Math.max(0, (now() - started) / 1000);
        emit();
        if (duration >= 120) stop(); // Limite da demo, não contrato produtivo.
      });
      // Suporte opcional. Safari e outros navegadores podem negar esta consulta.
      if (permissions?.query) {
        try {
          const observed = await permissions.query({ name: 'microphone' });
          if (ticket === generation && ['recording','stopping','ready'].includes(phase)) {
            permission = observed;
            permission.onchange = () => {
              if (permission?.state === 'denied') reset();
            };
            if (permission.state === 'denied') reset();
          }
        } catch { /* Tracks e revalidação de contexto continuam obrigatórios. */ }
      }
    } catch (cause) {
      if (ticket !== generation) return;
      if (!valid()) { reset(); return; }
      fail(cause?.name === 'NotAllowedError' || cause?.name === 'SecurityError'
        ? 'Permissão de microfone negada. Libere o acesso nas configurações do navegador e tente novamente.'
        : cause?.name === 'NotFoundError'
          ? 'Nenhum microfone disponível neste dispositivo.'
          : 'Não foi possível acessar o microfone. Verifique se ele está disponível e tente novamente.');
    }
  }
  function attach() {
    if (!valid()) { reset(); return null; }
    if (phase !== 'ready' || !draft) return null;
    const id = `local-audio-${++clipSequence}`;
    clips.set(id, draft);
    const result = { id, duration: draft.duration };
    draft = null; phase = 'idle'; duration = 0; error = ''; emit();
    return result;
  }
  return { start, stop, discard, reset, sync, attach, snapshot,
    getClip: id => clips.get(id) ?? null };
}
