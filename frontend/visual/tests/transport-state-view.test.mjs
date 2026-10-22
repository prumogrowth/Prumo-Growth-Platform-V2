import test from 'node:test';
import assert from 'node:assert/strict';
import {copyCFDemoFixtures} from '../cf-op-02.mjs';
import {stageMockMessageTransport,TRANSPORT_PRESENTATION_STATES} from '../transport-state-view.mjs';
const rows=()=>copyCFDemoFixtures();
const byCase=(id)=>{const record=rows().find(x=>x.id===id);
  const message=record.messages.find(x=>x.side==='out');return {record,message};};
const view=(record,message,actor='rafael',shop='aurora')=>
  stageMockMessageTransport(record,message,actor,shop);

test('FV-22-10 API_ACCEPTED mostra ACK, mas nunca prova envio/entrega/leitura',()=>{
 const {record,message}=byCase('A-102');const x=view(record,message);
 assert.equal(x.visibility,'synthetic');
 assert.equal(x.state,'api_accepted');assert.match(x.label,/NÃO comprovado/);
 assert.equal(x.provedSent,false);assert.equal(x.provedDelivery,false);
 assert.equal(x.provedRead,false);assert.equal(x.needsRefresh,true);
});

test('FV-22-10 envio comprovado na fixture é distinto de remessa bancária e da versão viva',()=>{
 const {record,message}=byCase('A-105');const x=view(record,message);
 assert.equal(x.visibility,'synthetic');assert.equal(x.provedSent,true);
 assert.equal(x.provedDelivery,false);assert.equal(x.provedRead,false);
 assert.equal(x.failedConfirmed,false);
 assert.equal(record.status,'cadastro enviado ao banco');
});

test('FV-22-10 incerteza não é falha final nem comprova resposta humana',()=>{
 const {record,message}=byCase('A-106');
 const x=view(record,message,'marina');
 assert.equal(x.state,'uncertain');assert.equal(x.provedSent,false);
 assert.equal(x.failedConfirmed,false);assert.equal(x.needsRefresh,true);
});

test('FV-22-10 nenhum texto gerado localmente recebe prova de transporte',()=>{
 const {record,message}=byCase('A-102');
 const local={...message,deliveryState:'local_demo_not_sent'};
 const injected={...record,messages:[local]};
 assert.equal(view(injected,local).visibility,'unavailable');
});

test('projeção ausente, alterada ou assinada por outra loja falha fechada',()=>{
 const {record,message}=byCase('A-102');
 for(const change of [
   p=>{p.source='browser';}, p=>{p.shopRef='horizonte';},
   p=>{p.caseRef='A-999';}, p=>{p.messageRef='forged';},
   p=>{p.versionRef='';}, p=>{p.proofRef='fabricated';},
   p=>{p.state='sold';}, p=>{p.confirmed=true;}, p=>{p.apiAckRef=null;}
 ]){
   const altered={...message,transportProjection:{...message.transportProjection}};
   change(altered.transportProjection);
   const row={...record,messages:[altered]};
   assert.equal(view(row,altered).visibility,'unavailable');
 }
});

test('prova é obrigatória para SENT, DELIVERED, READ e falha definitiva',()=>{
 const {record,message}=byCase('A-105');
 for(const state of ['sent_confirmed','delivered','read','failed_confirmed']){
   const p={...message.transportProjection,state};
   const m={...message,transportProjection:p},row={...record,messages:[m]};
   const x=view(row,m);assert.equal(x.visibility,'synthetic');
   if(state==='failed_confirmed'){
     assert.equal(x.provedSent,false);assert.equal(x.failedConfirmed,true);
   }else assert.equal(x.provedSent,true);
   if(state==='read')assert.equal(x.provedRead,true);
   for(const malformed of [{...p,proofRef:null},{...p,confirmed:false}]){
     const other={...m,transportProjection:malformed};
     assert.equal(view({...row,messages:[other]},other).visibility,'unavailable');
   }
 }
});

test('estado pedido não equivale ACK, SENT ou erro definitivo',()=>{
 const {record,message}=byCase('A-102');
 const candidate={...message,transportProjection:{...message.transportProjection,
   state:'requested',apiAckRef:undefined}};
 const row={...record,messages:[candidate]};
 assert.equal(view(row,candidate).state,'requested');
 assert.equal(view(row,candidate).provedSent,false);
 assert.equal(view(row,candidate).failedConfirmed,false);
});

test('sem escopo do titular ou caso da mesma concessionária, não há recibo',()=>{
 const {record,message}=byCase('A-102');
 for(const [person,shop] of [['marina','aurora'],['daniel','aurora'],
   ['rafael','horizonte'],['bianca','aurora'],['otavio','aurora']]){
   assert.equal(view(record,message,person,shop).visibility,'unavailable');
 }
});

test('taxonomia de estados técnicos não modifica os oito estados comerciais',()=>{
 assert.deepEqual(TRANSPORT_PRESENTATION_STATES,[
   'requested','api_accepted','uncertain','sent_confirmed','delivered','read','failed_confirmed']);
 const {record,message}=byCase('A-102'),before=JSON.stringify(record);
 view(record,message);
 assert.equal(JSON.stringify(record),before);
});
