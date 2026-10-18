/**
 * WA-04C: offline, non-authoritative proposal for Meta App credential lifecycle.
 * No secrets, vault, Supabase, Meta, persistence, http or production activation.
 * The request is a laboratory fixture, NOT a privileged administrative command.
 */
import { selectMetaCredential, type TrustedMetaRegistry, type TrustedAppRecord } from './credential-routing.ts';

type AppContext = {
  readonly app_ref: string;
  readonly concessionaria_id: string;
  readonly expected_revision: number;
  readonly at_ms: number;
  readonly operation_ref: string;
};
export type LifecycleProposalRequest = AppContext & (
  | { readonly action: 'REVOKE_APP' }
  | { readonly action: 'REVOKE_CHANNEL'; readonly canal_id: string }
  | { readonly action: 'STAGE_ROTATION'; readonly next_secret_slots: TrustedAppRecord['secret_slots'] }
);
export type LifecycleProposalResult =
  | { readonly ok: true; readonly proposal_only: true; readonly production_authorized: false;
      readonly action: LifecycleProposalRequest['action']; readonly app_ref: string;
      readonly next_revision: number; readonly candidate_registry: TrustedMetaRegistry;
      readonly external_token_verification_pending: boolean }
  | { readonly ok: false; readonly production_authorized: false; readonly reason:
      'INVALID_INPUT' | 'REGISTRY_OR_APP_DENIED' | 'SCOPE_MISMATCH' |
      'REVISION_MISMATCH' | 'CHANNEL_NOT_ACTIVE' | 'INVALID_NEW_SLOTS' };

const deny = (reason: Extract<LifecycleProposalResult,{ok:false}>['reason']): LifecycleProposalResult =>
  ({ok:false,reason,production_authorized:false});
const validId = (s: unknown): s is string =>
  typeof s === 'string' && /^[A-Za-z0-9_.:-]{1,128}$/.test(s);
const validSlot = (s: unknown): s is string =>
  typeof s === 'string' && /^[A-Z][A-Z0-9_]{2,127}$/.test(s) && !s.startsWith('SUPABASE_');

/**
 * Produces an isolated *candidate* snapshot: no effect is applied to S0, vault,
 * credentials or webhooks. Staging a rotation DISABLES the App in the candidate
 * until a separately designed externally verified activation process exists.
 */
export function planMetaLifecycleTransition(
  registry: TrustedMetaRegistry, request: LifecycleProposalRequest,
): LifecycleProposalResult {
  if (!request || !validId(request.operation_ref) || !validId(request.app_ref) ||
      !validId(request.concessionaria_id) ||
      !Number.isSafeInteger(request.at_ms) || request.at_ms < 0 ||
      !Number.isSafeInteger(request.expected_revision) || request.expected_revision < 1 ||
      request.expected_revision >= Number.MAX_SAFE_INTEGER ||
      !['REVOKE_APP','REVOKE_CHANNEL','STAGE_ROTATION'].includes(request.action))
    return deny('INVALID_INPUT');
  const app = registry?.apps?.find(a => a?.app_ref === request.app_ref);
  if (!app) return deny('REGISTRY_OR_APP_DENIED');
  if (app.concessionaria_id !== request.concessionaria_id) return deny('SCOPE_MISMATCH');
  if (app.revision !== request.expected_revision) return deny('REVISION_MISMATCH');
  // Reuse the existing strict global registry/validity guard on a trusted route.
  // This proposal only models changes to a currently active, valid App.
  const before = selectMetaCredential(registry, {
    purpose:'POST_APP_SECRET', trusted_route_ref:app.route_ref,
    expected_revision:request.expected_revision, at_ms:request.at_ms,
  });
  if (!before.ok || before.app_ref !== request.app_ref) return deny('REGISTRY_OR_APP_DENIED');
  const next = structuredClone(registry);
  const selected = next.apps.find(a=>a.app_ref === request.app_ref)!;
  const rev = request.expected_revision + 1;
  let changed: TrustedAppRecord;
  if (request.action === 'REVOKE_APP') {
    changed = {...selected,active:false,revision:rev};
  } else if (request.action === 'REVOKE_CHANNEL') {
    if (!validId(request.canal_id)) return deny('INVALID_INPUT');
    const channel = selected.channels.find(c=>c.canal_id === request.canal_id && c.active);
    if (!channel) return deny('CHANNEL_NOT_ACTIVE');
    changed = {...selected,revision:rev,channels:selected.channels.map(c=>
      c.canal_id === request.canal_id ? {...c,active:false} : c)};
  } else {
    const slots = request.next_secret_slots;
    if (!slots || Object.keys(slots).length !== 3) return deny('INVALID_NEW_SLOTS');
    const nextNames = [slots.get_verify_token,slots.post_app_secret,slots.graph_access_token];
    const alreadyUsed = new Set(registry.apps.flatMap(a=>
      Object.values(a.secret_slots)));
    if (nextNames.some(s=>!validSlot(s) || alreadyUsed.has(s)) ||
        new Set(nextNames).size !== 3) return deny('INVALID_NEW_SLOTS');
    changed = {...selected,active:false,revision:rev,secret_slots:{...slots}};
  }
  const candidate_registry: TrustedMetaRegistry = {...next,apps:next.apps.map(a=>
    a.app_ref === request.app_ref ? changed : a)};
  return {ok:true,proposal_only:true,production_authorized:false,
    action:request.action,app_ref:request.app_ref,next_revision:rev,candidate_registry,
    external_token_verification_pending: request.action === 'STAGE_ROTATION'};
}
