// HTTP translation only. SQL I79/I80 remains authoritative for all permissions.
export const VERSION = "prumo.admin.v1";
export type Family = "i79" | "i80";
export type Document = Record<string, unknown>;
export class Invalid extends Error {}
export const uuid = (v: unknown): string => {
  if (typeof v !== "string" || v.length !== 36 || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(v) || v === "00000000-0000-0000-0000-000000000000") throw new Invalid();
  return v;
};
const record = (v: unknown): Document => {
  if (!v || typeof v !== "object" || Array.isArray(v)) throw new Invalid();
  return v as Document;
};
const exact = (v: unknown, fields: string[]): Document => {
  const o = record(v);
  if (Object.keys(o).sort().join("|") !== fields.sort().join("|")) throw new Invalid();
  return o;
};
const oneOf = (v: unknown, options: unknown[]): void => { if (!options.includes(v)) throw new Invalid(); };
const nullableUuid = (v: unknown): void => { if (v !== null) uuid(v); };
const sha = (v: unknown): void => { if (typeof v !== "string" || v.length !== 64 || !/^[0-9a-f]{64}$/.test(v)) throw new Invalid(); };
const count = (v: unknown, max = 2000): void => { if (!Number.isSafeInteger(v) || (v as number) < 0 || (v as number) > max) throw new Invalid(); };
export const decimal = (v: unknown, zero = true): string => {
  if (typeof v !== "string" || v.trim() !== v || !/^(0|[1-9][0-9]{0,18})$/.test(v) || BigInt(v) > 9223372036854775807n || (!zero && v === "0")) throw new Invalid();
  return v;
};

// Reject duplicate decoded keys, malformed UTF-8/JSON and deep input before
// JSON.parse can silently discard an earlier command or identity field.
export function strictJson(text: string): unknown {
  let i = 0;
  const ws = () => { while (/\s/.test(text[i] ?? "") && i < text.length) i++; };
  const string = (): string => {
    const start = i++;
    while (i < text.length) {
      const c = text[i++];
      if (c === "\\") { i++; continue; }
      if (c === '"') return JSON.parse(text.slice(start, i));
    }
    throw new Invalid();
  };
  const value = (depth: number): void => {
    if (depth > 6) throw new Invalid();
    ws();
    if (text[i] === "{") {
      i++; ws(); const keys = new Set<string>();
      if (text[i] === "}") { i++; return; }
      while (true) {
        ws(); if (text[i] !== '"') throw new Invalid();
        const k = string(); if (keys.has(k) || keys.size >= 32) throw new Invalid(); keys.add(k);
        ws(); if (text[i++] !== ":") throw new Invalid(); value(depth + 1); ws();
        const c = text[i++]; if (c === "}") return; if (c !== ",") throw new Invalid();
      }
    }
    if (text[i] === "[") throw new Invalid(); // no arrays in these command DTOs
    if (text[i] === '"') { string(); return; }
    const token = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(i));
    if (!token) throw new Invalid(); i += token[0].length;
  };
  value(0); ws(); if (i !== text.length) throw new Invalid();
  return JSON.parse(text);
}

export function command(family: Family, raw: unknown): Document {
  const envelope = exact(raw, ["version", "command"]);
  if (envelope.version !== VERSION) throw new Invalid();
  const p = { ...exact(envelope.command, family === "i79"
    ? ["action", "target_id", "cargo", "manager_id", "expected_relationship_id", "idempotency_key"]
    : ["action", "target_id", "cargo", "manager_id", "expected_sha256", "preview_id", "cursor", "limit", "idempotency_key"]) };
  if (typeof p.idempotency_key !== "string" || p.idempotency_key.length < 8 || p.idempotency_key.length > 128 || /[^A-Za-z0-9._:-]/.test(p.idempotency_key)) throw new Invalid();
  if (family === "i79") {
    oneOf(p.action, ["REGISTER", "ACTIVATE", "TRANSFER"]); uuid(p.target_id);
    oneOf(p.cargo, ["gestor", "consultor"]); nullableUuid(p.manager_id); decimal(p.expected_relationship_id);
    if ((p.action === "REGISTER" && (p.manager_id !== null || p.expected_relationship_id !== "0")) ||
      (p.action === "ACTIVATE" && (p.expected_relationship_id !== "0" || (p.cargo === "consultor") !== (p.manager_id !== null))) ||
      (p.action === "TRANSFER" && (p.cargo !== "consultor" || p.manager_id === null || p.expected_relationship_id === "0"))) throw new Invalid();
  } else {
    oneOf(p.action, ["INVENTORY", "PREVIEW", "APPLY"]);
    for (const k of ["target_id", "manager_id", "preview_id", "cursor"]) nullableUuid(p[k]);
    count(p.limit, 50);
    if (p.action === "INVENTORY") {
      if ((p.limit as number) < 1 || ["target_id", "cargo", "manager_id", "expected_sha256", "preview_id"].some(k => p[k] !== null)) throw new Invalid();
    } else {
      uuid(p.target_id); oneOf(p.cargo, ["gestor", "consultor"]); sha(p.expected_sha256);
      if ((p.cargo === "gestor" && p.manager_id !== null) || p.limit !== 0 || p.cursor !== null ||
        (p.action === "PREVIEW" && p.preview_id !== null) || (p.action === "APPLY" && p.preview_id === null)) throw new Invalid();
    }
  }
  return p;
}

const states = [null, "pendente", "ativo", "suspenso", "desligado"];
const blockers = new Set(["INVENTORY_TOO_LARGE", "MISSING_TEAM_USE_I79_REGISTER", "AUTH_IDENTITY_MISSING", "DIRECTOR_AUTHORITY_CONFLICT", "CLASSIFIED_ROLE_CONFLICT", "MULTIPLE_ACTIVE_RELATIONS", "MANAGER_HAS_PARENT_LINK", "CONSULTANT_HAS_SUBORDINATES", "INACTIVE_MANAGER_HAS_ACTIVE_CONSULTANTS", "MANAGER_REQUIRED", "MANAGER_NOT_CLASSIFIED_ACTIVE", "PENDING_CHEFIA_USE_I79_ACTIVATION", "NOTHING_TO_REGULARIZE", "CLASSIFIED_USE_I79_TRANSFER"]);
export function receipt(family: Family, raw: unknown, p: Document): Document {
  const r = record(raw);
  if (family === "i80" && p.action === "INVENTORY") {
    exact(r, ["outcome", "items", "has_more", "next_cursor"]);
    if (r.outcome !== "INVENTORY" || !Array.isArray(r.items) || r.items.length > (p.limit as number) || typeof r.has_more !== "boolean") throw new Invalid();
    let previous = p.cursor as string | null;
    for (const item of r.items) {
      const o = exact(item, ["target_id", "cargo", "estado", "bounded", "inventory_sha256"]);
      uuid(o.target_id); sha(o.inventory_sha256); oneOf(o.cargo, [null, "diretor", "gestor", "consultor"]); oneOf(o.estado, states);
      if (typeof o.bounded !== "boolean" || (previous !== null && (o.target_id as string) <= previous)) throw new Invalid();
      previous = o.target_id as string;
    }
    if (r.has_more ? (!r.items.length || uuid(r.next_cursor) !== previous) : r.next_cursor !== null) throw new Invalid();
    return r;
  }
  if (r.target_id !== p.target_id || r.cargo !== p.cargo || r.manager_id !== p.manager_id) throw new Invalid();
  if (family === "i79") {
    exact(r, ["outcome", "request_id", "action", "target_id", "cargo", "manager_id", "previous_relationship_id", "relationship_id"]);
    oneOf(r.outcome, ["APPLIED", "ALREADY_APPLIED"]); uuid(r.request_id);
    if (r.action !== p.action || r.previous_relationship_id !== p.expected_relationship_id) throw new Invalid();
    if (p.cargo === "consultor" && p.action !== "REGISTER") {
      decimal(r.relationship_id, false); if (r.relationship_id === p.expected_relationship_id) throw new Invalid();
    } else if (r.relationship_id !== null) throw new Invalid();
  } else if (p.action === "PREVIEW") {
    exact(r, ["outcome", "preview_id", "target_id", "cargo", "manager_id", "inventory_sha256", "snapshot_sha256", "blockers", "impact", "expires_at"]);
    uuid(r.preview_id); sha(r.snapshot_sha256);
    if (r.inventory_sha256 !== p.expected_sha256 || !Array.isArray(r.blockers) || r.blockers.some(b => !blockers.has(b)) || r.outcome !== (r.blockers.length ? "BLOCKED" : "READY")) throw new Invalid();
    const v = exact(r.impact, ["state_preserved", "current_relationship_id", "complete", "consultant_intake_gate_after", "must_recheck_assignment_authority", "change_relationship", "revoke_exception_ids", "grant_count", "assignment_count", "case_count", "intake_paused"]);
    oneOf(v.state_preserved, states);
    if (v.current_relationship_id !== null) decimal(v.current_relationship_id, false);
    for (const k of ["complete", "consultant_intake_gate_after", "change_relationship"]) if (typeof v[k] !== "boolean") throw new Invalid();
    if (v.must_recheck_assignment_authority !== true || ![null, true, false].includes(v.intake_paused as boolean | null) || !Array.isArray(v.revoke_exception_ids) || new Set(v.revoke_exception_ids).size !== v.revoke_exception_ids.length) throw new Invalid();
    v.revoke_exception_ids.forEach(uuid);
    for (const k of ["grant_count", "assignment_count", "case_count"]) { if (v.complete) count(v[k]); else if (v[k] !== null) throw new Invalid(); }
    if (typeof r.expires_at !== "string" || !/(Z|[+-]\d\d:\d\d)$/.test(r.expires_at) || !Number.isFinite(Date.parse(r.expires_at))) throw new Invalid();
  } else {
    exact(r, ["outcome", "request_id", "preview_id", "target_id", "cargo", "estado", "manager_id", "relationship_id", "revoked_exception_count", "before_sha256", "after_sha256"]);
    oneOf(r.outcome, ["APPLIED", "ALREADY_APPLIED"]); uuid(r.request_id);
    if (r.preview_id !== p.preview_id || r.before_sha256 !== p.expected_sha256) throw new Invalid();
    sha(r.after_sha256); oneOf(r.estado, states.slice(1)); count(r.revoked_exception_count);
    if (r.relationship_id !== null) decimal(r.relationship_id, false);
    if ((p.manager_id === null) !== (r.relationship_id === null)) throw new Invalid();
  }
  return r;
}

export type Principal = { actor: string; session: string };
export function proofArgs(family: Family, p: Document, principal: Principal, key: string, issued: number, nonce: string): unknown[] {
  return family === "i79"
    ? [principal.actor, principal.session, p.action, p.target_id, p.cargo, p.manager_id, p.expected_relationship_id, p.idempotency_key, key, issued, nonce]
    : [principal.actor, principal.session, p.action, p.target_id, p.cargo, p.manager_id, p.expected_sha256, p.preview_id, p.cursor, p.limit, p.idempotency_key, key, issued, nonce];
}
export function material(family: Family, args: unknown[]): string {
  return [family === "i79" ? "s0-s1-i79-admin-v1" : "s0-s1-i80-regularization-v1", ...args.map(x => x === null ? "-" : String(x))].join("|");
}
export async function sign(family: Family, args: unknown[], secret: Uint8Array): Promise<string> {
  const key = await crypto.subtle.importKey("raw", secret, {name:"HMAC", hash:"SHA-256"}, false, ["sign"]);
  const mac = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(material(family, args))));
  return [...mac].map(v => v.toString(16).padStart(2, "0")).join("");
}
