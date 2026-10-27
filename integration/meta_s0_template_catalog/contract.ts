/**
 * META-S0-TEMPLATE-CATALOG-05 / 0.1-candidate. No transport or send rights.
 * Types describe an INTERNAL normalized record, never raw Meta API semantics.
 */
import type {MultiFormatInput} from '../../integrations/whatsapp-meta/template-mcp-multiformat.ts';
import type {TrustedTemplateScope} from '../../integrations/whatsapp-meta/graph-template.ts';
export const VERSION='prumo.meta-s0.template-catalog/0.1-candidate' as const;
export const FLAGS=Object.freeze({
  send_authorized:false,production_authorized:false,ack_allowed:false,
  retry_automatically:false,commercial_effect_authorized:false,
  meta_approval_verified:false,
} as const);
export type Scope=Readonly<TrustedTemplateScope>;
export type Revision=string; // canonical positive int64 decimal, NOT case/cycle version
export type Status='APPROVED'|'PENDING'|'PAUSED'|'REJECTED'|'DISABLED';
export type ApprovedComponent=
 | Readonly<{type:'HEADER';format:'TEXT';text:string}>
 | Readonly<{type:'BODY'|'FOOTER';text:string}>
 | Readonly<{type:'BUTTONS';buttons:readonly Readonly<{type:'QUICK_REPLY';text:string}>[]}>;
export type CatalogQuery=Readonly<{
  template_name:string;language_code:string;
  expected_template_revision_ref:string;
  expected_catalog_revision:Revision;expected_binding_revision:Revision;
}>;
export type SupportedDefinition=Readonly<Omit<MultiFormatInput,'header'|'buttons'> & {
 header?:Readonly<{kind:'TEXT';text:string;example?:string}>;
 buttons?:readonly Readonly<{kind:'QUICK_REPLY';label:string}>[];
}>;
export type CatalogRecord=Readonly<{
  contract:typeof VERSION;scope:Scope;binding_revision:Revision;
  catalog_revision:Revision;template_revision_ref:string;
  content_version:Revision;mapping_revision:Revision;
  provider_template_id:string;meta_status:Status;schema_complete:true;
  parameter_format:'POSITIONAL_TEXT_ONLY';
  /** Existing WA17B definition, validated using its existing composer. */
  definition:SupportedDefinition;
  /** COMPLETE current normalized provider manifest; no examples/unknown components. */
  approved_components:readonly ApprovedComponent[];
  mappings:Readonly<Record<string,string>>;
  /** Prumo-owned payload policy: Meta approves labels/schema, NOT these values. */
  quick_reply_policy:Readonly<{
    mode:'STATIC_BACKEND_CATALOG';policy_ref:string;revision_ref:string;
    buttons:readonly Readonly<{kind:'QUICK_REPLY';index:number;payload:string}>[];
  }>;
  source:Readonly<{
    kind:'LAB_FIXTURE';source_ref:string;observation_ref:string;
    approval_evidence:'SYNTHETIC_NOT_META_APPROVAL';
    status_observed_at_ms:number;manifest_observed_at_ms:number;
  }>;
}>;
export type CatalogHead=Readonly<{
  source_ref:string;source_epoch:Revision;record_sha256:string;
  catalog_revision:Revision;binding_revision:Revision;template_revision_ref:string;
  provider_template_id:string;meta_status:Status;
}>;
export type CatalogBundle=Readonly<{record:CatalogRecord;head:CatalogHead}>;
export type FixtureSourcePort=Readonly<{
  /** Fake atomic read of one exact template/locale/scope. NOT authenticated I/O. */
  readCurrent(query:CatalogQuery):Promise<unknown>;
}>;
export type Denial=
 'SOURCE_NOT_IMPLEMENTED'|'UNTRUSTED_SOURCE'|'INVALID_INPUT'|'SCOPE_MISMATCH'|
 'STALE_REVISION'|'STALE_OBSERVATION'|'CATALOG_NOT_APPROVED'|
 'INTEGRITY_MISMATCH'|'INCOMPLETE_MANIFEST'|'UNSUPPORTED_COMPONENTS'|
 'INVALID_BUTTON_POLICY'|'INVALID_BINDINGS'|'SOURCE_ROLLBACK_OR_CONFLICT'|
 'HANDLE_NOT_ISSUED_HERE'|'HANDLE_CHANGED'|'DEPENDENCY_UNAVAILABLE'|'BUILDER_REJECTED';
export function denied(reason:Denial) {
  return Object.freeze({decision:'DENIED' as const,reason,snapshot:null,...FLAGS});
}
/** No source-of-truth has been implemented or approved. No JSON may enable it. */
export async function readProductionTemplateCatalog(_query:unknown) {
  return denied('SOURCE_NOT_IMPLEMENTED');
}
