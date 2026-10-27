import test from 'node:test';
import assert from 'node:assert/strict';
import { createLocalAudio } from '../local-audio.mjs';

function audioFixture(options = {}) {
  let context = { key:'rafael:aurora:A-102', allowed:true }, clock = 0, tick;
  const tracks = [], revoked = [], states = [], made = [];
  const permission = { state:'granted', onchange:null };
  const mediaDevices = { getUserMedia: async () => {
    const track = { stopped:false, stop(){this.stopped=true;}, onended:null };
    tracks.push(track);
    return { getTracks: () => [track] };
  } };
  class Recorder {
    static isTypeSupported(type) { return type === 'audio/webm;codecs=opus'; }
    constructor(stream, config) { this.stream=stream; this.mimeType=config?.mimeType; this.state='inactive'; }
    start(){ this.state='recording'; }
    stop(){ this.state='inactive'; this.ondataavailable?.({data:new Blob(['synthetic audio'],{type:this.mimeType})}); this.onstop?.(); }
  }
  const audio = createLocalAudio({getContext:()=>context, onChange:s=>states.push(s), mediaDevices, Recorder,
    permissions:{query:async()=>permission}, now:()=>clock,
    schedule:fn=>{tick=fn;return 1;}, unschedule:()=>{tick=null;},
    makeURL:blob=>{made.push(blob);return `blob:synthetic-${made.length}`;}, dropURL:url=>revoked.push(url),
    ...options });
  return { audio, tracks, revoked, made, states, permission,
    setContext:value=>{context=value;}, advance:seconds=>{clock+=seconds*1000; tick?.();} };
}

test('grava apenas após gesto, finaliza, ouve por URL efêmera e anexa sem transporte', async()=>{
  const f=audioFixture(); assert.equal(f.tracks.length,0);
  await f.audio.start(); assert.equal(f.audio.snapshot().phase,'recording');
  f.advance(3.2); f.audio.stop();
  assert.equal(f.audio.snapshot().phase,'ready'); assert.equal(f.audio.snapshot().duration,3.2);
  assert.ok(f.tracks.every(t=>t.stopped)); assert.equal(f.made[0].type,'audio/webm;codecs=opus');
  const clip=f.audio.attach(); assert.equal(clip.duration,3.2); assert.ok(f.audio.getClip(clip.id));
  assert.equal(f.audio.attach(),null); assert.equal(f.audio.snapshot().phase,'idle');
  f.audio.reset(); assert.equal(f.audio.getClip(clip.id),null); assert.equal(f.revoked.length,1);
});
test('excluir libera URL de rascunho sem afetar texto ou anexar',async()=>{
  const f=audioFixture(); await f.audio.start(); f.audio.stop(); f.audio.discard();
  assert.equal(f.audio.snapshot().draft,null); assert.equal(f.revoked.length,1);
  assert.equal(f.audio.attach(),null);
});
test('permissão negada e navegador sem gravador não simulam sucesso',async()=>{
  for(const options of [
    {mediaDevices:{getUserMedia:async()=>{throw Object.assign(new Error(),{name:'NotAllowedError'});}}},
    {Recorder:null},
    {mediaDevices:{getUserMedia:async()=>{throw Object.assign(new Error(),{name:'NotFoundError'});}}}
  ]) {
    const f=audioFixture(options); await f.audio.start();
    assert.equal(f.audio.snapshot().phase,'error'); assert.ok(f.audio.snapshot().error);
    assert.equal(f.audio.attach(),null); assert.equal(f.made.length,0);
  }
});
test('cancelamento ou troca de contexto durante permissão encerra stream que chega tarde',async()=>{
  for(const cancel of [true,false]) {
    let resolve; const track={stopped:false,stop(){this.stopped=true;}};
    const f=audioFixture({mediaDevices:{getUserMedia:()=>new Promise(r=>{resolve=r;})}});
    const pending=f.audio.start(); assert.equal(f.audio.snapshot().phase,'requesting');
    if(cancel)f.audio.discard(); else {f.setContext({key:'lia:aurora:A-117',allowed:true});f.audio.sync();}
    resolve({getTracks:()=>[track]}); await pending;
    assert.equal(track.stopped,true); assert.equal(f.audio.snapshot().phase,'idle'); assert.equal(f.made.length,0);
  }
});
test('contexto invalidado antes do stop e revogação da capacidade descartam rascunho',async()=>{
  for(const phase of ['recording','ready','attached']) {
    const f=audioFixture(); await f.audio.start();
    if(phase!=='recording')f.audio.stop();
    const clip=phase==='attached'?f.audio.attach():null;
    f.setContext({key:'rafael:aurora:A-102',allowed:false}); f.audio.sync();
    assert.equal(f.audio.snapshot().phase,'idle'); assert.ok(f.tracks.every(t=>t.stopped));
    assert.equal(f.audio.snapshot().draft,null);
    if(clip)assert.equal(f.audio.getClip(clip.id),null);
    assert.equal(f.revoked.length,phase==='recording'?0:1);
  }
});
test('revogação do microfone e interrupção de track encerram captura',async()=>{
  const f=audioFixture(); await f.audio.start(); f.permission.state='denied'; f.permission.onchange();
  assert.ok(f.tracks.every(t=>t.stopped)); assert.equal(f.audio.snapshot().phase,'idle');
  const g=audioFixture(); await g.audio.start(); g.tracks[0].onended();
  assert.equal(g.audio.snapshot().phase,'error'); assert.ok(g.tracks[0].stopped);
});
test('revogação depois da prévia também libera URL',async()=>{
  const f=audioFixture(); await f.audio.start();f.audio.stop();
  assert.equal(typeof f.permission.onchange,'function');
  f.permission.state='denied';f.permission.onchange();
  assert.equal(f.audio.snapshot().draft,null); assert.equal(f.revoked.length,1);
});
test('limite de demonstração encerra gravação e erro do gravador encerra recursos',async()=>{
  const f=audioFixture();await f.audio.start();f.advance(120);
  assert.equal(f.audio.snapshot().phase,'ready');assert.ok(f.tracks[0].stopped);f.audio.reset();
  let active;
  class BrokenRecorder {constructor(){active=this;this.state='inactive';}start(){this.state='recording';}stop(){this.state='inactive';}}
  const g=audioFixture({Recorder:BrokenRecorder});await g.audio.start();active.onerror();
  assert.equal(g.audio.snapshot().phase,'error');assert.ok(g.tracks[0].stopped);
});
test('supervisão ou janela não autorizada não solicita microfone',async()=>{
  const f=audioFixture();f.setContext({key:'marina:aurora:A-102',allowed:false});
  await f.audio.start();assert.equal(f.tracks.length,0);assert.equal(f.audio.snapshot().phase,'idle');
});
test('recorder vazio e falha ao preparar URL não deixam streams ativos',async()=>{
  class EmptyRecorder {constructor(){this.state='inactive';}start(){this.state='recording';}stop(){this.state='inactive';this.onstop?.();}}
  for(const options of [{Recorder:EmptyRecorder},{makeURL:()=>{throw Error('unavailable');}}]){
    const f=audioFixture(options);await f.audio.start();f.audio.stop();
    assert.equal(f.audio.snapshot().phase,'error');assert.ok(f.tracks[0].stopped);assert.equal(f.audio.attach(),null);
  }
});
test('callback antigo de erro não descarta uma gravação nova',async()=>{
  const all=[];
  class DelayedRecorder {
    constructor(){all.push(this);this.state='inactive';}
    start(){this.state='recording';}
    stop(){this.state='inactive';}
  }
  const f=audioFixture({Recorder:DelayedRecorder});await f.audio.start();
  const lateError=all[0].onerror,lateEnded=f.tracks[0].onended;
  f.audio.reset();await f.audio.start();lateError();lateEnded();
  assert.equal(f.audio.snapshot().phase,'recording');assert.equal(f.tracks[1].stopped,false);
  f.audio.reset();assert.equal(f.tracks[1].stopped,true);
});
