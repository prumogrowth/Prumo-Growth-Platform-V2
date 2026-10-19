import test from 'node:test';
import assert from 'node:assert/strict';
import { copyCFDemoFixtures, mayMockFreeText } from '../cf-op-02.mjs';
import { postmarkViewFor, postmarkCopy, isValidContinuationProjection } from '../postmark-view.mjs';

const postmarkCases=()=>copyCFDemoFixtures();
const postmarkFind=(id,records=postmarkCases())=>records.find(x=>x.id===id);

test('O5-01: marco banco fica intacto e outro ciclo humano tem ID e status próprios',()=>{
  const rows=postmarkCases(),original=postmarkFind('A-105',rows),fresh=postmarkFind('A-114',rows);
  assert.equal(original.status,'cadastro enviado ao banco');
  assert.equal(fresh.status,'em atendimento pelo operador');
  assert.equal(fresh.postmarkProjection.source,'bank_submitted');
  assert.notEqual(original.id,fresh.id);
  assert.equal(isValidContinuationProjection(fresh),true);
  assert.equal(mayMockFreeText(original,'rafael','aurora'),false);
  assert.equal(mayMockFreeText(fresh,'rafael','aurora'),true);
});

test('O5-02: ciclo após venda não muda histórico de vendido',()=>{
  const rows=postmarkCases(),original=postmarkFind('A-115',rows),newCase=postmarkFind('A-116',rows);
  assert.equal(original.status,'vendido');
  assert.equal(original.inboxProjection,'historical');
  assert.equal(newCase.status,'em atendimento pelo operador');
  assert.equal(newCase.inboxProjection,'active');
  assert.equal(mayMockFreeText(original,'rafael','aurora'),false);
  assert.equal(isValidContinuationProjection(newCase),true);
});

test('O5-03: link deve ser recíproco e produzido pelo S0 projetado',()=>{
  const rows=postmarkCases();
  const from=postmarkViewFor(postmarkFind('A-105',rows),rows,'rafael','aurora');
  const to=postmarkViewFor(postmarkFind('A-114',rows),rows,'rafael','aurora');
  assert.equal(from.kind,'origin');assert.equal(from.relatedCaseId,'A-114');
  assert.equal(to.kind,'continuation');assert.equal(to.relatedCaseId,'A-105');
  assert.equal(from.linked,true);assert.equal(to.linked,true);
  assert.match(postmarkCopy(to).description,/IA Vendedora/);
});

test('O5-04: supervisor no escopo consegue ler vínculo, mas não ganha atribuição',()=>{
  const rows=postmarkCases(),detail=postmarkViewFor(postmarkFind('A-114',rows),rows,'marina','aurora');
  assert.equal(detail.linked,true);
  assert.equal(detail.canOperateCurrentCase,false);
  assert.equal(mayMockFreeText(postmarkFind('A-114',rows),'marina','aurora'),false);
});

test('O5-05: perfil suspenso e loja não concedida não descobrem caso relacionado',()=>{
  const rows=postmarkCases();
  for(const [actor,shop] of [['otavio','aurora'],['rafael','horizonte'],['inexistente','aurora']]){
    const result=postmarkViewFor(postmarkFind('A-114',rows),rows,actor,shop);
    assert.equal(result.visibility,'forbidden');assert.equal(result.relatedCaseId,null);
  }
});

test('O5-06: se o vínculo da outra ponta não existe/está fora do escopo, ocultar ID',()=>{
  const rows=postmarkCases().filter(row=>row.id!=='A-105');
  const result=postmarkViewFor(postmarkFind('A-114',rows),rows,'rafael','aurora');
  assert.equal(result.kind,'restricted');
  assert.equal(result.relatedCaseId,null);
  assert.equal(result.linked,false);
});

test('O5-07: versão divergente não cria relação entre casos',()=>{
  const rows=postmarkCases();rows.find(x=>x.id==='A-114').postmarkProjection.linkVersionRef='outra-versao';
  const result=postmarkViewFor(postmarkFind('A-105',rows),rows,'rafael','aurora');
  assert.equal(result.linked,false);
  assert.equal(result.relatedCaseId,null);
});

test('O5-08: origem com status que não corresponde ao evento não autoriza vínculo',()=>{
  const rows=postmarkCases();rows.find(x=>x.id==='A-115').status='em atendimento pela IA';
  const result=postmarkViewFor(postmarkFind('A-116',rows),rows,'rafael','aurora');
  assert.equal(result.linked,false);
});

test('O5-09: nova etapa não pode reviver IA e depende da prova projetada',()=>{
  const record=postmarkFind('A-114');
  assert.equal(record.postmarkProjection.sellerAiSilenced,true);
  assert.equal(isValidContinuationProjection({...record,postmarkProjection:{
    ...record.postmarkProjection,sellerAiSilenced:false
  }}),false);
  assert.equal(isValidContinuationProjection({...record,postmarkProjection:{
    ...record.postmarkProjection,confirmedCreated:false
  }}),false);
});

test('O5-10: vínculo não autoriza cruzar lojas mesmo com identificadores coincidentes',()=>{
  const rows=postmarkCases();rows.find(x=>x.id==='A-114').shopId='horizonte';
  const result=postmarkViewFor(postmarkFind('A-105',rows),rows,'marina','aurora');
  assert.equal(result.linked,false);
  assert.equal(result.relatedCaseId,null);
});

test('O5-11: ator sem atribuição não vê relação se o caso alvo não está em sua carteira',()=>{
  const rows=postmarkCases();
  const result=postmarkViewFor(postmarkFind('A-105',rows),rows,'bianca','aurora');
  assert.equal(result.visibility,'forbidden');
  assert.equal(result.relatedCaseId,null);
});

test('O5-12: nenhuma criação local de novo ciclo é feita pela projeção',()=>{
  const rows=postmarkCases(),ids=rows.map(x=>x.id),status=rows.map(x=>x.status);
  postmarkViewFor(postmarkFind('A-115',rows),rows,'rafael','aurora');
  postmarkViewFor(postmarkFind('A-116',rows),rows,'rafael','aurora');
  assert.deepEqual(rows.map(x=>x.id),ids);
  assert.deepEqual(rows.map(x=>x.status),status);
});

test('O5-13: sem vínculo confirmado, não inventar abertura de contato',()=>{
  const rows=postmarkCases();const a=postmarkFind('A-111',rows);
  const result=postmarkViewFor(a,rows,'rafael','aurora');
  assert.equal(result.kind,'none');
  assert.equal(result.relatedCaseId,null);
  assert.match(postmarkCopy(result).title,/Nenhum novo ciclo confirmado/);
});
