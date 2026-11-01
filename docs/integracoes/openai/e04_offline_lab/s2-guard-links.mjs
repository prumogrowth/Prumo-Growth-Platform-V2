/**
 * OFF-02: narrow, offline-only access to original S2 synthetic guards.
 * The front-facing provider payload never imports or invokes these as an authority.
 * Every input here is an untrusted caller-provided laboratory fixture.
 */
import {evaluateOfflineJourney} from './journey.mjs';
import {evaluateF03CommitCandidate} from './f03-commit-gate.mjs';
import {reconcileF02Plan} from './plan-lifecycle.mjs';
import {assessTemplateFrequency,classifyMetaMarketingError} from './template-frequency.mjs';
import {summarizeTransportEvidence} from './transport-evidence.mjs';

export function runSyntheticGuard(name, fixture) {
  try {
    if (!fixture || typeof fixture!=='object' || Array.isArray(fixture))return {status:'INVALID_INPUT'};
    let x;
    switch(name) {
      case 'journey': x=evaluateOfflineJourney(fixture.flow); break;
      case 'f03-commit': x=evaluateF03CommitCandidate(fixture.input); break;
      case 'f02-lifecycle': x=reconcileF02Plan(fixture.scope,fixture.plan,fixture.events); break;
      case 'f02-frequency': x=assessTemplateFrequency(fixture.scope,fixture.attempt,fixture.policy,fixture.history); break;
      case 'meta-131049': x=classifyMetaMarketingError(fixture.scope,fixture.event); break;
      case 'transport-evidence': x=summarizeTransportEvidence(fixture.scope,fixture.events); break;
      default: return {status:'INVALID_INPUT'};
    }
    // Return an explicit synthetic label, never 'allowed to send/apply'.
    return {status:'S2_SYNTHETIC_GUARD_ONLY',guard:name,verdict:x.status};
  }catch{return {status:'MODEL_FAILURE'};}
}
