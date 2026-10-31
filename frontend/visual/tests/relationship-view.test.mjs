import test from 'node:test';
import assert from 'node:assert/strict';
import { postmarkViewFor, postmarkCopy } from '../postmark-view.mjs';
import { copyCFDemoFixtures } from '../cf-op-02.mjs';
import { projectMockClarificationScene } from '../human-cycle-view.mjs';
import { withRevisionScenes } from '../revision-fixtures.mjs';
import { aiCommunicationsFor, operationalHistoryFor, bankReadinessFor } from '../relationship-view.mjs';
const scene=()=>withRevisionScenes(copyCFDemoFixtures());
const row=(rows,id)=>rows.find(r=>r.id===id);

test('AT-03: F01/F02/F03 acumulam publicações sem substituir resultados anteriores',()=>{
 const rows=scene(),record=row(rows,'A-108');
 const entries=aiCommunicationsFor(record,rows,'rafael','aurora');
 assert.deepEqual(entries.map(e=>e.source),['F01','F02','F02','F03','F03']);
 assert.equal(new Set(entries.map(e=>e.id)).size,5);
 assert.ok(entries.every(e=>e.synthetic && e.time));
 assert.match(entries.at(-1).content,/v1-ficticia/);
 assert.equal(record.messages.some(m=>m.side==='ai'),false);
});
test('AT-03: registro não publicado, origem desconhecida, duplicata e F03 bruto não aparecem',()=>{
 const rows=scene(),record=row(rows,'A-108');
 const entries=record.aiCommunicationsProjection.entries;
 entries.push({...entries[0]}, {...entries[0],id:'draft',published:false},
   {...entries[0],id:'raw-f03',source:'F03',content:'DADO BRUTO PROTEGIDO'});
 assert.equal(aiCommunicationsFor(record,rows,'rafael','aurora').length,5);
 record.aiCommunicationsProjection.shopId='horizonte';
 assert.deepEqual(aiCommunicationsFor(record,rows,'rafael','aurora').map(e=>e.source),['F03','F03']);
});
test('AT-03/04: supervisor consulta comunicações D2 sem obter recortes/versões F03 protegidos',()=>{
 const rows=scene(),record=row(rows,'A-108');
 const entries=aiCommunicationsFor(record,rows,'marina','aurora');
 assert.deepEqual(entries.map(e=>e.source),['F01','F02','F02']);
 assert.doesNotMatch(JSON.stringify(entries),/a108-1|v1-ficticia|Valor fictício confirmado/);
 assert.deepEqual(aiCommunicationsFor(record,rows,'daniel','aurora'),[]);
 assert.deepEqual(aiCommunicationsFor(record,rows,'rafael','horizonte'),[]);
});
test('AT-04: histórico operacional não transforma mensagens em acontecimentos',()=>{
 const rows=scene(),record=row(rows,'A-102');
 const before=operationalHistoryFor(record,rows,'rafael','aurora');
 record.messages.push({id:'local',side:'out',body:'Rascunho sem envio',deliveryState:'local_demo_not_sent'});
 assert.deepEqual(operationalHistoryFor(record,rows,'rafael','aurora'),before);
 assert.deepEqual(before.events.map(e=>e.kind),['lead','f01_started','handoff','assignment']);
 assert.ok(before.events.every(e=>e.state==='confirmed'));
});
test('AT-04: transferência por caso é evento próprio e não revela carteira ou outra loja',()=>{
 const rows=scene(),record=row(rows,'A-117');
 const history=operationalHistoryFor(record,rows,'lia','aurora');
 assert.match(history.events.at(-1).label,/Transferência confirmada para Lia/);
 assert.deepEqual(operationalHistoryFor(row(rows,'A-102'),rows,'lia','aurora').events,[]);
 assert.deepEqual(operationalHistoryFor(record,rows,'lia','horizonte').events,[]);
});
test('AT-04: evento sem confirmação, versão ou vínculo de loja é descartado',()=>{
 const rows=scene(),record=row(rows,'A-102');
 record.relationshipProjection.events.push({...record.relationshipProjection.events[0],id:'pending',confirmed:false});
 assert.equal(operationalHistoryFor(record,rows,'rafael','aurora').events.length,4);
 record.relationshipProjection.shopId='horizonte';
 assert.equal(operationalHistoryFor(record,rows,'rafael','aurora').events.length,0);
});
test('AT-04: resultado terminal exige acontecimento confirmado além do status',()=>{
 const rows=scene(),record=row(rows,'A-115');
 assert.ok(operationalHistoryFor(record,rows,'rafael','aurora').events.some(e=>e.kind==='sold'));
 record.relationshipProjection.events.at(-1).resultConfirmed=false;
 assert.equal(operationalHistoryFor(record,rows,'rafael','aurora').events.some(e=>e.kind==='sold'),false);
});
test('AT-05: planejamento, execução, falha, incerteza e cancelamento não se confundem',()=>{
 const rows=scene(),record=row(rows,'A-110');
 const history=operationalHistoryFor(record,rows,'rafael','aurora');
 assert.equal(history.future.length,3);
 for(const state of ['sent_confirmed','executing','failed','uncertain','cancelled'])
   assert.ok(history.events.some(e=>e.state===state),state);
 assert.equal(history.future.some(e=>e.state==='cancelled'),false);
 assert.match(history.events.find(e=>e.state==='cancelled').statusLabel,/Cancelada/);
});
test('AT-05: cancelamento confirmado sai do futuro e preserva o registro',()=>{
 const rows=scene(),record=row(rows,'A-110');
 record.followupProjection.attempts[0].state='cancelled';
 const history=operationalHistoryFor(record,rows,'rafael','aurora');
 assert.equal(history.future.length,2);
 assert.equal(history.events.filter(e=>e.state==='cancelled').length,2);
 assert.ok(history.events.some(e=>e.label.startsWith('Tentativa 1')));
});
test('AT-05: novo pedido local preserva acontecimentos anteriores e não vira agendamento',()=>{
 const rows=scene(),record=row(rows,'A-110');
 const history=operationalHistoryFor(record,rows,'rafael','aurora',{kind:'uncertain'},{kind:'request_chain'});
 assert.equal(history.future.length,3);
 assert.ok(history.events.some(e=>e.state==='sent_confirmed'));
 assert.ok(history.events.some(e=>e.statusLabel.includes('nunca ENVIADO')));
 assert.equal(history.events.at(-1).state,'uncertain');
});
test('AT-04: continuidade exige vínculo recíproco e acesso aos dois casos',()=>{
 const rows=scene(),record=row(rows,'A-114');
 assert.equal(operationalHistoryFor(record,rows,'rafael','aurora').related.relatedCaseId,'A-105');
 row(rows,'A-105').assignedTo='bianca';
 const view=operationalHistoryFor(record,rows,'rafael','aurora');
 assert.equal(view.related.linked,false);assert.equal(view.related.relatedCaseId,null);
 assert.ok(view.events.some(e=>e.kind==='human_cycle'));
 row(rows,'A-105').name=record.name;row(rows,'A-105').shopId='horizonte';
 assert.equal(operationalHistoryFor(record,rows,'rafael','aurora').related.linked,false);
});
test('fixtures adicionais são cópias isoladas e não modificam grants ou estados canônicos',()=>{
 const original=copyCFDemoFixtures(),snapshot=structuredClone(original),copies=withRevisionScenes(original);
 copies.find(r=>r.id==='A-110').followupProjection.attempts[0].state='cancelled';
 assert.deepEqual(original,snapshot);
 for(const copy of copies){const source=row(original,copy.id);
   assert.equal(copy.status,source.status);assert.equal(copy.assignedTo,source.assignedTo);
   assert.deepEqual(copy.allowedActionsProjection,source.allowedActionsProjection);
 }
});

test('AT-03/04: cenário alternativo preserva publicações e acontecimentos anteriores autorizados',()=>{
 const rows=scene(),base=row(rows,'A-108'),alternative=projectMockClarificationScene(base,'rafael','aurora');
 assert.equal(aiCommunicationsFor(alternative,rows,'rafael','aurora').length,5);
 assert.equal(operationalHistoryFor(alternative,rows,'rafael','aurora').events.length,6);
 assert.deepEqual(aiCommunicationsFor(alternative,rows,'marina','aurora'),[]);
});
test('AT-05: cancelamento do plano tira pendências futuras sem apagar tentativas já enviadas',()=>{
 const rows=scene(),record=row(rows,'A-110');record.followupProjection.state='cancelled';
 const result=operationalHistoryFor(record,rows,'rafael','aurora');
 assert.equal(result.future.length,0);
 assert.equal(result.events.filter(e=>e.state==='cancelled').length,4);
 assert.ok(result.events.some(e=>e.state==='sent_confirmed'));
});

test('AT-01: aptidão exige confirmação, fonte, vínculo e a versão atual da ficha autorizada',()=>{
 const rows=scene(),record=row(rows,'A-114');
 assert.equal(bankReadinessFor(record,rows,'rafael','aurora'),true);
 assert.equal(bankReadinessFor(record,rows,'marina','aurora'),false);
 assert.equal(bankReadinessFor(record,rows,'rafael','horizonte'),false);
 record.bankReadinessProjection.formVersionRef='live-form-v1-demo';
 assert.equal(bankReadinessFor(record,rows,'rafael','aurora'),false);
 record.bankReadinessProjection.formVersionRef='live-form-v2-demo';record.bankReadinessProjection.confirmed=false;
 assert.equal(bankReadinessFor(record,rows,'rafael','aurora'),false);
});

test('REV-025/029: descrição do ciclo distingue retorno pós-venda de pós-remessa',()=>{
 const rows=scene();
 const sold=postmarkCopy(postmarkViewFor(row(rows,'A-116'),rows,'rafael','aurora'));
 const bank=postmarkCopy(postmarkViewFor(row(rows,'A-114'),rows,'rafael','aurora'));
 assert.match(sold.description,/após venda confirmada/);assert.doesNotMatch(sold.description,/bancári/);
 assert.match(bank.description,/após remessa bancária/);
 assert.match(sold.description,/permanentemente silenciada/);
});

// FV-COR-07: expected behavior comes from FV-AUD-03, not current output.
test('COR07 N03: envio final confirmado precede a perda que dele depende',()=>{
 const rows=scene(),record=row(rows,'A-111');
 const view=operationalHistoryFor(record,rows,'rafael','aurora');
 assert.ok(view.events.findIndex(e=>e.state==='sent_confirmed')<view.events.findIndex(e=>e.kind==='lost'));
 assert.ok(view.events.filter(e=>['lost','followup'].includes(e.kind)).every(e=>e.sequenceConfirmed));
});
test('COR07 N04: atualização cadastral tem evento explícito e restrito, vinculado à versão',()=>{
 const rows=scene(),record=row(rows,'A-114');
 const event=operationalHistoryFor(record,rows,'rafael','aurora').events.find(e=>e.kind==='registration');
 assert.ok(event,'Atualização confirmada deve estar na projeção sintética de acontecimentos');
 assert.match(event.label,/F03|cadastral/);
 assert.equal(operationalHistoryFor(record,rows,'marina','aurora').events.some(e=>e.kind==='registration'),false);
 record.registrationProjection.formVersionRef='outra-versao';
 assert.equal(operationalHistoryFor(record,rows,'rafael','aurora').events.some(e=>e.kind==='registration'),false);
});
test('COR07 N05: ficha F01 persistida não se torna publicação F03 sem autoria confirmada',()=>{
 const rows=scene(),record=row(rows,'A-114');
 record.aiCommunicationsProjection.entries=[];
 record.humanCycleProjection=undefined;
 record.registrationProjection.fields=record.registrationProjection.fields.filter(f=>f.sourceLabel.startsWith('F01'));
 assert.equal(aiCommunicationsFor(record,rows,'rafael','aurora').some(e=>e.source==='F03'),false);
});

test('COR07 N03: sem sequência entre fontes, não fabricar cronologia a partir de rótulos',()=>{
 const rows=scene(),record=row(rows,'A-110');
 let view=operationalHistoryFor(record,rows,'rafael','aurora');
 assert.ok(view.events.filter(e=>e.kind==='followup').every(e=>e.sequenceConfirmed===false));
 assert.ok(view.events.filter(e=>e.kind==='lead').every(e=>e.sequenceConfirmed===true));
 record.relationshipProjection.sequence=['lead','lead','followup-A-110-3'];
 view=operationalHistoryFor(record,rows,'rafael','aurora');
 assert.ok(view.events.filter(e=>e.kind==='followup').every(e=>e.sequenceConfirmed===false));
 assert.equal(view.future.length,3);
});
test('COR07 N04/N05: projeções explícitas não ampliam escopo nem aceitam versão contraditória',()=>{
 const rows=scene(),record=row(rows,'A-114');
 assert.equal(aiCommunicationsFor(record,rows,'rafael','aurora').filter(e=>e.source==='F03').length,1);
 for(const [actor,shop] of [['marina','aurora'],['daniel','aurora'],['rafael','horizonte']]){
   assert.equal(aiCommunicationsFor(record,rows,actor,shop).filter(e=>e.source==='F03').length,0);
   assert.equal(operationalHistoryFor(record,rows,actor,shop).events.some(e=>e.kind==='registration'),false);
 }
 const publication=record.aiCommunicationsProjection.entries.find(e=>e.source==='F03');
 for(const delta of [{resultConfirmed:false},{formVersionRef:'stale'},{audience:'case'},{published:false}]){
   const original=structuredClone(publication);Object.assign(publication,delta);
   assert.equal(aiCommunicationsFor(record,rows,'rafael','aurora').some(e=>e.source==='F03'),false);
   Object.assign(publication,original);
 }
});
