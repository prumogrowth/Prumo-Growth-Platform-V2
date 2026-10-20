/**
 * WA-16C reads genuine fixture S0-042 JSONB recovery outcomes from stdin.
 * Proves that the actual TypeScript classifier stays fail-closed with PG data.
 * No DB credentials, network, Graph request or commercial side effects.
 */
import { readFileSync } from 'node:fs';
import { classifyUnknownCommitRecovery as classify } from '../s0-unknown-commit-recovery.ts';
const content=readFileSync(0,'utf8');
if(content.length<2||content.length>8192) throw Error('WA16C_INVALID_FIXTURE_SIZE');
const root=JSON.parse(content) as unknown;
if(!root || typeof root!=='object'||Array.isArray(root)||
   Reflect.ownKeys(root).length!==3 ||
   !['found','absent','conflict'].every(k=>Object.hasOwn(root,k)))
  throw Error('WA16C_INVALID_RECOVERY_SHAPE');
const entries=root as Record<string,unknown>;
const expected={
  found:'LAB_CONFIRMED_DURABLE',
  absent:'LAB_ABSENT_STILL_UNCERTAIN',
  conflict:'LAB_CONFLICT_QUARANTINE',
} as const;
for(const [kind,decision] of Object.entries(expected)){
  const r=classify(entries[kind]);
  if(r.decision!==decision || r.retry_external || r.ack_allowed ||
     r.production_authorized || r.delivery_confirmed)
    throw Error('WA16C_WRONG_DB_DECISION_'+kind);
}
process.stdout.write('PASS WA16C-TSDB: PG17 JSONB classified safely by real TypeScript module\n');
