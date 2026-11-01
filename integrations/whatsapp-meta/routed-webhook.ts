/**
 * WA-04B — isolated, scriptable Meta GET/POST routing simulation.
 * Not an HTTP endpoint, ACK authority, Supabase client or secret store.
 * Trusted route / revision / clock / registry MUST originate outside the request.
 */
import { selectMetaCredential, resolveSignedMetaChannel,
  type TrustedMetaRegistry, type TrustedMetaScope } from './credential-routing.ts';
import { inspectMetaVerifyGet } from './verify-get.ts';
import { inspectMetaWebhook, type MetaIngressEvent } from './inbound.ts';

export type TrustedRoutingPorts = {
  /** Privileged, freshly sourced registry; not from the Meta request. */
  currentRegistry(): TrustedMetaRegistry | Promise<TrustedMetaRegistry>;
  /** Privileged ephemeral secret lookup by an internal slot, never logged. */
  resolveSecret(secretSlot: string): string | undefined | Promise<string | undefined>;
  /** Host clock; the webhook request must not provide or control this. */
  nowMs(): number;
};
export type TrustedRoute = {
  readonly route_ref: string;
  readonly expected_revision: number;
};
export type RoutableGet = {
  readonly raw_query: string;
  readonly route: TrustedRoute;
};
export type RoutablePost = {
  readonly raw_body: Uint8Array;
  readonly signature_header: string | null;
  readonly route: TrustedRoute;
};
type Failure = 'ROUTING_DENIED' | 'SECRET_UNAVAILABLE' | 'VERIFICATION_DENIED' |
  'SIGNATURE_OR_ENVELOPE_DENIED' | 'CHANNEL_DENIED' | 'ROUTING_CHANGED';
export type RoutedGetDecision =
  | { readonly ok: true; readonly challenge: string; readonly production_authorized: false }
  | { readonly ok: false; readonly reason: Failure; readonly production_authorized: false };
export type ScopedTechnicalEvent = Readonly<{
  event: MetaIngressEvent;
  scope: TrustedMetaScope;
}>;
export type RoutedPostDecision =
  | { readonly ok: true; readonly events: ScopedTechnicalEvent[];
      readonly authenticated_app_ref: string;
      readonly ack_allowed: false;
      readonly production_authorized: false }
  | { readonly ok: false; readonly reason: Failure;
      readonly ack_allowed: false; readonly production_authorized: false };

const denyGet = (reason: Failure): RoutedGetDecision =>
  ({ ok: false, reason, production_authorized: false });
const denyPost = (reason: Failure): RoutedPostDecision =>
  ({ ok: false, reason, ack_allowed: false, production_authorized: false });
/** Host/test fixture inputs are not permitted to execute getters while
 * choosing an App, HMAC secret or endpoint route. */
function ownFields(raw:unknown,fields:readonly string[]):Record<string,unknown>|null{
 try{
  if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
  const p=Object.getPrototypeOf(raw);
  if(p!==Object.prototype&&p!==null)return null;
  const d=Object.getOwnPropertyDescriptors(raw),keys=Reflect.ownKeys(raw);
  if(keys.length!==fields.length||keys.some(k=>
   typeof k!=='string'||!fields.includes(k)||!Object.hasOwn(d[k],'value'))||
   fields.some(k=>!Object.hasOwn(d,k)))return null;
  return Object.fromEntries(fields.map(k=>[k,d[k].value]));
 }catch{return null;}
}
function snapshotRoute(raw:unknown):TrustedRoute|null{
 const route=ownFields(raw,['route_ref','expected_revision']);
 return route&&validRoute(route as TrustedRoute)?route as TrustedRoute:null;
}

const validRoute = (route: TrustedRoute | undefined): route is TrustedRoute =>
  !!route && typeof route.route_ref === 'string' &&
  /^[A-Za-z0-9_.:-]{1,128}$/.test(route.route_ref) &&
  Number.isSafeInteger(route.expected_revision) && route.expected_revision > 0;
const validSecret = (value: unknown): value is string =>
  typeof value === 'string' && value.length > 0 && value.length <= 4096;

/** Call this only after the host selects an App from a trusted endpoint route. */
export async function inspectRoutedMetaGet(
  request: RoutableGet, ports: TrustedRoutingPorts,
): Promise<RoutedGetDecision> {
  const source=ownFields(request,['raw_query','route']);
  const route=snapshotRoute(source?.route);
  if(!source||!route||typeof source.raw_query!=='string')
    return denyGet('ROUTING_DENIED');
  const local={route,raw_query:source.raw_query as string};
  try {
    const before = selectMetaCredential(await ports.currentRegistry(), {
      purpose: 'GET_VERIFY_TOKEN', trusted_route_ref: local.route.route_ref,
      expected_revision: local.route.expected_revision, at_ms: ports.nowMs(),
    });
    if (!before.ok) return denyGet('ROUTING_DENIED');
    const secret = await ports.resolveSecret(before.secret_slot);
    if (!validSecret(secret)) return denyGet('SECRET_UNAVAILABLE');
    // Recheck because registry/clock could change while secret is resolved.
    const after = selectMetaCredential(await ports.currentRegistry(), {
      purpose: 'GET_VERIFY_TOKEN', trusted_route_ref: local.route.route_ref,
      expected_revision: local.route.expected_revision, at_ms: ports.nowMs(),
    });
    if (!after.ok || after.app_ref !== before.app_ref ||
        after.secret_slot !== before.secret_slot) return denyGet('ROUTING_CHANGED');
    const verified = await inspectMetaVerifyGet(local.raw_query, secret);
    if (verified.status !== 200) return denyGet('VERIFICATION_DENIED');
    const final = selectMetaCredential(await ports.currentRegistry(), {
      purpose: 'GET_VERIFY_TOKEN', trusted_route_ref: local.route.route_ref,
      expected_revision: local.route.expected_revision, at_ms: ports.nowMs(),
    });
    if (!final.ok || final.app_ref !== before.app_ref ||
        final.secret_slot !== before.secret_slot) return denyGet('ROUTING_CHANGED');
    return { ok: true, challenge: verified.body, production_authorized: false };
  } catch {
    // Deliberately avoid exposing resolved secrets, registry contents or errors.
    return denyGet('ROUTING_DENIED');
  }
}

/**
 * Simulate POST HMAC + tenant/channel binding, but NEVER issue an HTTP ACK.
 * Uses ONLY the HMAC slot selected from the trusted route, not any tenant ID
 * in the untrusted payload. One signature may cover multiple WABAs belonging
 * to the same App. Any unmapped event rejects the WHOLE batch.
 *
 * On success the returned scoped events contain protected participant metadata
 * and must NEVER be logged, sent to clients or used as a durable receipt.
 */
export async function inspectRoutedMetaPost(
  request: RoutablePost, ports: TrustedRoutingPorts,
): Promise<RoutedPostDecision> {
  const source=ownFields(request,['raw_body','signature_header','route']);
  const route=snapshotRoute(source?.route);
  if(!source||!route||!(source.raw_body instanceof Uint8Array)||
     source.raw_body.byteLength>256*1024||
     (source.signature_header!==null&&typeof source.signature_header!=='string'))
    return denyPost('ROUTING_DENIED');
  const local={route,raw_body:source.raw_body,
    signature_header:source.signature_header as string|null};
  try {
    // Snapshot the request before any async operation. The low-level parser
    // takes its own snapshot before HMAC and JSON parsing.
    const rawCopy = Uint8Array.from(local.raw_body);
    const before = selectMetaCredential(await ports.currentRegistry(), {
      purpose: 'POST_APP_SECRET', trusted_route_ref: local.route.route_ref,
      expected_revision: local.route.expected_revision, at_ms: ports.nowMs(),
    });
    if (!before.ok) return denyPost('ROUTING_DENIED');
    const secret = await ports.resolveSecret(before.secret_slot);
    if (!validSecret(secret)) return denyPost('SECRET_UNAVAILABLE');
    const after = selectMetaCredential(await ports.currentRegistry(), {
      purpose: 'POST_APP_SECRET', trusted_route_ref: local.route.route_ref,
      expected_revision: local.route.expected_revision, at_ms: ports.nowMs(),
    });
    if (!after.ok || after.app_ref !== before.app_ref ||
        after.secret_slot !== before.secret_slot) return denyPost('ROUTING_CHANGED');
    const parsed = await inspectMetaWebhook(rawCopy, local.signature_header, secret);
    if (!parsed.ok) return denyPost('SIGNATURE_OR_ENVELOPE_DENIED');
    const registry = await ports.currentRegistry();
    const final = selectMetaCredential(registry, {
      purpose: 'POST_APP_SECRET', trusted_route_ref: local.route.route_ref,
      expected_revision: local.route.expected_revision, at_ms: ports.nowMs(),
    });
    if (!final.ok || final.app_ref !== before.app_ref ||
        final.secret_slot !== before.secret_slot) return denyPost('ROUTING_CHANGED');
    const events: ScopedTechnicalEvent[] = [];
    for (const event of parsed.events) {
      const binding = resolveSignedMetaChannel(registry, {
        trusted_route_ref: local.route.route_ref,
        authenticated_app_ref: before.app_ref,
        waba_id: event.waba_id, phone_number_id: event.phone_number_id,
        expected_revision: local.route.expected_revision, at_ms: ports.nowMs(),
      });
      if (!binding.ok) return denyPost('CHANNEL_DENIED');
      events.push({ event, scope: binding.scope });
    }
    // Since the clock may cross expiry during a large multi-event batch,
    // require the route to remain current at the very end.
    // Read the registry AGAIN after every binding check. Reusing `registry`
    // here would accept callbacks if revocation occurs during channel checks.
    // Still not a distributed transaction; the privileged S0 durable handoff
    // must revalidate the same app/channel revision atomically at commit.
    const latestRegistry = await ports.currentRegistry();
    const last = selectMetaCredential(latestRegistry, {
      purpose: 'POST_APP_SECRET', trusted_route_ref: local.route.route_ref,
      expected_revision: local.route.expected_revision, at_ms: ports.nowMs(),
    });
    if (!last.ok || last.app_ref !== before.app_ref ||
        last.secret_slot !== before.secret_slot) return denyPost('ROUTING_CHANGED');
    for (const item of events) {
      const latest = resolveSignedMetaChannel(latestRegistry, {
        trusted_route_ref: local.route.route_ref,
        authenticated_app_ref: before.app_ref,
        waba_id: item.event.waba_id, phone_number_id: item.event.phone_number_id,
        expected_revision: local.route.expected_revision, at_ms: ports.nowMs(),
      });
      if (!latest.ok || latest.scope.concessionaria_id !== item.scope.concessionaria_id ||
          latest.scope.canal_id !== item.scope.canal_id ||
          latest.scope.app_ref !== item.scope.app_ref) return denyPost('ROUTING_CHANGED');
    }
    return { ok: true, authenticated_app_ref: before.app_ref, events,
      ack_allowed: false, production_authorized: false };
  } catch {
    return denyPost('ROUTING_DENIED');
  }
}
