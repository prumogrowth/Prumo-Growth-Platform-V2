/**
 * WA-04A — OFFLINE candidate for Meta credential and channel routing.
 * References are secret NAMES, NEVER secret values. No Deno.env, Graph, fetch,
 * database access or proof of S0 business authorization is implemented here.
 * A future privileged backend supplies the trusted registry and invocation.
 */
export type MetaSecretPurpose = 'GET_VERIFY_TOKEN' | 'POST_APP_SECRET' | 'GRAPH_ACCESS_TOKEN';
export type TrustedChannel = {
  readonly canal_id: string;
  readonly waba_id: string;
  readonly phone_number_id: string;
  readonly active: boolean;
};
export type TrustedAppRecord = {
  readonly app_ref: string;
  readonly route_ref: string;
  readonly concessionaria_id: string;
  readonly active: boolean;
  readonly revision: number;
  readonly valid_from_ms: number;
  readonly valid_until_ms: number;
  readonly secret_slots: {
    readonly get_verify_token: string;
    readonly post_app_secret: string;
    readonly graph_access_token: string;
  };
  readonly channels: readonly TrustedChannel[];
};
export type TrustedMetaRegistry = {
  readonly contract_version: 'wa-meta-credential-routing.v0.1-proposed';
  readonly apps: readonly TrustedAppRecord[];
};
export type TrustedMetaScope = {
  readonly app_ref: string;
  readonly concessionaria_id: string;
  readonly canal_id: string;
  readonly waba_id: string;
  readonly phone_number_id: string;
};
export type MetaCredentialRequest =
  | { readonly purpose: 'GET_VERIFY_TOKEN' | 'POST_APP_SECRET';
      /** ONLY from trusted endpoint routing, NEVER from payload/query. */
      readonly trusted_route_ref: string;
      readonly at_ms: number; readonly expected_revision: number }
  | { readonly purpose: 'GRAPH_ACCESS_TOKEN';
      /** ONLY from authenticated and freshly revalidated S0 authorization. */
      readonly trusted_scope: TrustedMetaScope;
      readonly at_ms: number; readonly expected_revision: number };
export type MetaCredentialDecision =
  | { readonly ok: true; readonly app_ref: string;
      readonly purpose: MetaSecretPurpose; readonly secret_slot: string;
      readonly revision: number; readonly production_authorized: false }
  | { readonly ok: false; readonly reason:
      'INVALID_INPUT' | 'INVALID_REGISTRY' | 'NO_MATCH' | 'DISABLED_OR_EXPIRED' |
      'STALE_REVISION' | 'CHANNEL_NOT_BOUND'; readonly production_authorized: false };
export type SignedChannelDecision =
  | { readonly ok: true; readonly scope: TrustedMetaScope;
      readonly production_authorized: false }
  | { readonly ok: false; readonly reason:
      'INVALID_INPUT' | 'INVALID_REGISTRY' | 'NO_MATCH' | 'DISABLED_OR_EXPIRED' |
      'STALE_REVISION' | 'CHANNEL_NOT_BOUND'; readonly production_authorized: false };
const fail = (reason: Extract<MetaCredentialDecision, { ok: false }>['reason']) =>
  ({ ok: false as const, reason, production_authorized: false as const });
const id = (s: unknown): s is string => typeof s === 'string' &&
  /^[a-zA-Z0-9_.:-]{1,128}$/.test(s);
const slot = (s: unknown): s is string => typeof s === 'string' &&
  /^[A-Z][A-Z0-9_]{2,127}$/.test(s) && !s.startsWith('SUPABASE_');
const millis = (n: unknown): n is number =>
  typeof n === 'number' && Number.isSafeInteger(n) && n >= 0;
const revision = (n: unknown): n is number =>
  Number.isSafeInteger(n) && (n as number) > 0;
const validScope = (s: unknown): s is TrustedMetaScope => {
  if (!s || typeof s !== 'object') return false;
  const value = s as TrustedMetaScope;
  return id(value.app_ref) && id(value.concessionaria_id) && id(value.canal_id) &&
    id(value.waba_id) && /^\d{5,25}$/.test(value.phone_number_id);
};
function validRegistry(reg: TrustedMetaRegistry): boolean {
  if (!reg || reg.contract_version !== 'wa-meta-credential-routing.v0.1-proposed' ||
      !Array.isArray(reg.apps) || reg.apps.length > 100) return false;
  const appRefs = new Set<string>(), routes = new Set<string>();
  // Globally unique Meta Phone Number ID and S0 channel ID across ALL apps.
  // A WABA may host several numbers in one App, but never span two Apps.
  const senderIds = new Set<string>(), channelIds = new Set<string>();
  const wabaOwner = new Map<string, string>(), secretNames = new Set<string>();
  let totalChannels = 0;
  for (const app of reg.apps) {
    if (!app || !id(app.app_ref) || !id(app.route_ref) ||
        !id(app.concessionaria_id) || typeof app.active !== 'boolean' ||
        !revision(app.revision) || !millis(app.valid_from_ms) ||
        !millis(app.valid_until_ms) || app.valid_until_ms <= app.valid_from_ms ||
        appRefs.has(app.app_ref) || routes.has(app.route_ref) ||
        !app.secret_slots || !Array.isArray(app.channels)) return false;
    appRefs.add(app.app_ref); routes.add(app.route_ref);
    const names = [app.secret_slots.get_verify_token, app.secret_slots.post_app_secret,
      app.secret_slots.graph_access_token];
    if (Object.keys(app.secret_slots).length !== 3 ||
        names.some(x => !slot(x) || secretNames.has(x))) return false;
    for (const name of names) secretNames.add(name);
    for (const channel of app.channels) {
      if (!channel || !id(channel.canal_id) || !id(channel.waba_id) ||
          typeof channel.active !== 'boolean' ||
          !/^\d{5,25}$/.test(channel.phone_number_id)) return false;
      const owningApp = wabaOwner.get(channel.waba_id);
      if (senderIds.has(channel.phone_number_id) || channelIds.has(channel.canal_id) ||
          (owningApp !== undefined && owningApp !== app.app_ref)) return false;
      senderIds.add(channel.phone_number_id); channelIds.add(channel.canal_id);
      wabaOwner.set(channel.waba_id, app.app_ref);
      if (++totalChannels > 1000) return false;
    }
  }
  return true;
}
function current(app: TrustedAppRecord, now: number): boolean {
  return app.active && now >= app.valid_from_ms && now < app.valid_until_ms;
}
function exactChannel(app: TrustedAppRecord, s: TrustedMetaScope): boolean {
  return app.app_ref === s.app_ref && app.concessionaria_id === s.concessionaria_id &&
    app.channels.some(c => c.active && c.canal_id === s.canal_id &&
      c.waba_id === s.waba_id && c.phone_number_id === s.phone_number_id);
}
/** Select a name for a privileged secret resolver; never return a token. */
export function selectMetaCredential(reg: TrustedMetaRegistry,
  command: MetaCredentialRequest): MetaCredentialDecision {
  if (!command || !millis(command.at_ms) || !revision(command.expected_revision) ||
      !['GET_VERIFY_TOKEN', 'POST_APP_SECRET', 'GRAPH_ACCESS_TOKEN'].includes(command.purpose))
    return fail('INVALID_INPUT');
  if (!validRegistry(reg)) return fail('INVALID_REGISTRY');
  const app = command.purpose === 'GRAPH_ACCESS_TOKEN'
    ? (validScope(command.trusted_scope) ?
      reg.apps.find(x => x.app_ref === command.trusted_scope.app_ref) : undefined)
    : (id(command.trusted_route_ref) ?
      reg.apps.find(x => x.route_ref === command.trusted_route_ref) : undefined);
  if (!app) return fail('NO_MATCH');
  if (!current(app, command.at_ms)) return fail('DISABLED_OR_EXPIRED');
  if (app.revision !== command.expected_revision) return fail('STALE_REVISION');
  if (command.purpose === 'GRAPH_ACCESS_TOKEN' &&
      !exactChannel(app, command.trusted_scope)) return fail('CHANNEL_NOT_BOUND');
  const secret_slot = command.purpose === 'GET_VERIFY_TOKEN'
    ? app.secret_slots.get_verify_token : command.purpose === 'POST_APP_SECRET'
      ? app.secret_slots.post_app_secret : app.secret_slots.graph_access_token;
  return { ok: true, app_ref: app.app_ref, purpose: command.purpose,
    secret_slot, revision: app.revision, production_authorized: false };
}
/**
 * Must be called only AFTER HMAC validation against the slot selected for a
 * trusted route. Supplied fields here are NOT proof of HMAC or channel tenancy.
 */
export function resolveSignedMetaChannel(reg: TrustedMetaRegistry, query: {
  trusted_route_ref: string; authenticated_app_ref: string;
  waba_id: string; phone_number_id: string;
  at_ms: number; expected_revision: number;
}): SignedChannelDecision {
  if (!query || !id(query.trusted_route_ref) || !id(query.authenticated_app_ref) ||
      !id(query.waba_id) || !/^\d{5,25}$/.test(query.phone_number_id) ||
      !millis(query.at_ms) || !revision(query.expected_revision)) return fail('INVALID_INPUT');
  if (!validRegistry(reg)) return fail('INVALID_REGISTRY');
  const app = reg.apps.find(x => x.route_ref === query.trusted_route_ref &&
    x.app_ref === query.authenticated_app_ref);
  if (!app) return fail('NO_MATCH');
  if (!current(app, query.at_ms)) return fail('DISABLED_OR_EXPIRED');
  if (app.revision !== query.expected_revision) return fail('STALE_REVISION');
  const channel = app.channels.find(c => c.active && c.waba_id === query.waba_id &&
    c.phone_number_id === query.phone_number_id);
  if (!channel) return fail('CHANNEL_NOT_BOUND');
  return { ok: true, scope: { app_ref: app.app_ref,
    concessionaria_id: app.concessionaria_id, canal_id: channel.canal_id,
    waba_id: channel.waba_id, phone_number_id: channel.phone_number_id },
    production_authorized: false };
}
