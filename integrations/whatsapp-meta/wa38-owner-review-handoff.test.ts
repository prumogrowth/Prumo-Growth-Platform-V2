/**
 * WA38 is a documentary review request, NOT an owner signoff or
 * authorized machine endpoint. These are traceability tests only.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {WA36_REQUIREMENTS} from './wa36-ratification-gate.ts';
import {WA37_CHECKS} from './wa37-acceptance-handoff.ts';

const doc=readFileSync(new URL(
 '../../docs/integracoes/whatsapp-meta/wa38-handoff-revisao-s0-s1-meta-infra-2026-10-23.md',
 import.meta.url),'utf8');

for(let i=0;i<WA37_CHECKS.length;i++){
 const x=WA37_CHECKS[i];
 test('WA38-'+String(i+1).padStart(2,'0')+
  ' requirement '+x.id+' traces positive and negative owner probes',()=>{
   assert.ok(WA36_REQUIREMENTS.some(r=>r.id===x.id&&r.owner===x.owner));
   assert.ok(doc.includes(x.id),'missing WA36 decision '+x.id);
   assert.ok(doc.includes(x.positive),'missing proposed positive '+x.positive);
   assert.ok(doc.includes(x.negative),'missing proposed negative '+x.negative);
 });
}
test('WA38-13 source snapshot is explicit and does not claim other PRs merged',()=>{
 assert.ok(doc.includes('75095fe9b6050c704df37c663bb92595bc6513b6'));
 assert.ok(doc.includes('7867403fad752353af90d57feb1cf2594b476dd4'));
 assert.ok(doc.includes('948891714f632adb6179cf3a11f362a6eb914f91'));
 assert.ok(doc.includes('4f1edcb88d33c65157f8d6020c89c98e27727e85'));
 assert.ok(doc.includes('Draft'));
});
test('WA38-14 DEC-WA-05 owner approval and real-panel evidence remain separate',()=>{
 assert.ok(doc.includes('DEC-WA-05'));
 assert.ok(doc.includes('Decisão de negócio APROVADA'));
 assert.ok(doc.includes('prova dos vínculos reais e onboarding AINDA PENDENTES'));
 assert.ok(doc.includes('TENANT-Q01'));
});
test('WA38-15 S0 batch, callback event and 8-to-9 digit risks acknowledged',()=>{
 assert.ok(doc.includes('S0-Q03'));
 assert.ok(doc.includes('S0-Q04'));
 assert.ok(doc.includes('028'));
 assert.ok(doc.includes('029'));
 assert.ok(doc.includes('statuses[].id'));
 assert.ok(doc.includes('8↔9'));
});
test('WA38-16 questions cover S0 S1 Meta Infra explicitly',()=>{
 for(const code of ['S0-Q01','S0-Q02','S0-Q03','S0-Q04',
   'S1-Q01','S1-Q02','META-Q01','META-Q02','INFRA-Q01','INFRA-Q02',
   'TENANT-Q01'])assert.ok(doc.includes(code),code);
});
test('WA38-17 no local report can represent an external signoff',()=>{
 assert.ok(doc.includes('nenhuma revisão externa é assumida'));
 assert.ok(doc.includes('não é, por si, ratificação'));
 assert.ok(doc.includes('não foram executados em ambiente homologado'));
 assert.ok(doc.includes('PR #2 permanece **Draft**'));
});
