/**
 * WA-17B: MCP-first template composition, NOT an MCP server or Graph client.
 * AI may compose exact human-requested text or generate draft copy if the
 * responsible actor delegated that permission. Neither implies approval.
 * An authenticated MCP backend must supply actor/tenant permissions, media
 * proof, source registry, durable audit and an allowlisted Meta Graph gateway.
 * BODY, HEADER, FOOTER, URL/PHONE/QUICK_REPLY are the narrow validated subset.
 * Other Meta variants appear in capability discovery, but fail closed here.
 */

export const TEMPLATE_CAPABILITIES = Object.freeze({
  implemented_offline:[
    'BODY_TEXT','HEADER_TEXT','HEADER_IMAGE','HEADER_VIDEO','HEADER_DOCUMENT',
    'FOOTER_TEXT','BUTTON_URL_STATIC','BUTTON_URL_DYNAMIC',
    'BUTTON_PHONE_NUMBER','BUTTON_QUICK_REPLY','VARIABLE_SOURCE_BINDINGS',
  ],
  reserved_requires_separate_validator:[
    'HEADER_LOCATION','BUTTON_COPY_CODE','BUTTON_FLOW','CATALOG','MULTI_PRODUCT',
    'AUTHENTICATION','NAMED_PARAMETERS','CAROUSEL','LIMITED_TIME_OFFER',
  ],
  lifecycle:[
    'DRAFT','REQUEST_REVIEW','READ_REVIEW_STATUS','CONFIGURE_VARIABLES',
    'PREVIEW','NEW_CONTENT_VERSION','INSPECT_AUDIT',
  ],
  transport:'MCP_AUTHENTICATED_BACKEND_REQUIRED',
  network_implemented:false,
  message_send_implemented:false,
});

export type AuthoringOrigin='HUMAN_SPECIFIED'|'AI_ASSISTED'|'AI_GENERATED';
export type Header =
  | Readonly<{kind:'TEXT';text:string;example?:string}>
  | Readonly<{kind:'IMAGE'|'VIDEO'|'DOCUMENT';asset_ref:string}>;
export type Button =
  | Readonly<{kind:'QUICK_REPLY';label:string}>
  | Readonly<{kind:'PHONE_NUMBER';label:string;phone_number:string}>
  | Readonly<{kind:'URL';label:string;url:string;example_suffix?:string}>;
export type MultiFormatInput=Readonly<{
  local_id:string;concessionaria_id:string;waba_ref:string;
  name:string;language:string;category:'UTILITY'|'MARKETING';
  origin:AuthoringOrigin;
  body:Readonly<{text:string;examples:readonly string[]}>;
  header?:Header;footer?:string;buttons?:readonly Button[];
}>;
export type VariableSlot=Readonly<{
  slot_key:string;position:number;part:'BODY'|'HEADER'|'URL_BUTTON';
}>;
export type MultiFormatDraft=Readonly<{
  input:MultiFormatInput;
  slots:readonly VariableSlot[];
  content_version:number;
  mapping_revision:number;
  mappings:Readonly<Record<string,string>>;
  stage:'DRAFT';
  meta_approved:false;
  network_performed:false;
}>;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const DIGITS=/^[0-9]{5,25}$/;
const NAME=/^[a-z][a-z0-9_]{0,127}$/;
const LOCALE=/^[a-z]{2}(?:_[A-Z]{2})?$/;
const SOURCE=/^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){1,3}$/;
const SAFE_VALUE=/^[A-Za-z0-9_-]{1,80}$/;
const ASSET=/^asset_[a-z0-9_-]{6,100}$/;
function demand(check:unknown,reason:string):asserts check{
  if(!check)throw Error(reason);
}
function keys(input:unknown,required:string[],optional:string[]=[]):Record<string,unknown>{
  demand(input!==null&&typeof input==='object'&&!Array.isArray(input),'INVALID_OBJECT');
  demand(Object.getPrototypeOf(input)===Object.prototype||Object.getPrototypeOf(input)===null,
    'UNTRUSTED_PROTOTYPE');
  const desc=Object.getOwnPropertyDescriptors(input);
  const names=Reflect.ownKeys(input);
  demand(names.every(n=>typeof n==='string'&&[...required,...optional].includes(n))&&
    required.every(n=>Object.hasOwn(desc,n))&&
    names.every(n=>Object.hasOwn(desc[n as string],'value')),'UNEXPECTED_FIELDS_OR_GETTERS');
  return input as Record<string,unknown>;
}
function positions(raw:string,maximum=20):number[]{
  demand(typeof raw==='string','INVALID_TEXT');
  const matches=[...raw.matchAll(/\{\{([0-9]+)\}\}/g)];
  const other=raw.replace(/\{\{[0-9]+\}\}/g,'');
  demand(!other.includes('{{')&&!other.includes('}}'),'INVALID_VARIABLE_TOKEN');
  const ids=[...new Set(matches.map(m=>Number(m[1])))].sort((a,b)=>a-b);
  demand(ids.length<=maximum&&ids.every((n,i)=>n===i+1),'NONCONTIGUOUS_POSITIONS');
  return ids;
}
function secureUrl(url:string):URL{
  demand(typeof url==='string'&&url.length<=2048,'INVALID_URL');
  let target:URL;
  try{target=new URL(url);}catch{throw Error('INVALID_URL');}
  demand(target.protocol==='https:'&&!target.username&&!target.password&&
    target.hostname.includes('.')&&
    !/(?:^|\.)(?:local|localhost|internal)$/.test(target.hostname)&&
    !/^\d{1,3}(?:\.\d{1,3}){3}$/.test(target.hostname)&&
    !target.hostname.includes(':')&&
    !['localhost','127.0.0.1','0.0.0.0'].includes(target.hostname),
    'UNSAFE_URL');
  return target;
}
const unique=(v:string[])=>new Set(v).size===v.length;

export function composeMcpTemplateDraft(raw:MultiFormatInput):MultiFormatDraft{
  const i=keys(raw,['local_id','concessionaria_id','waba_ref','name','language',
    'category','origin','body'],['header','footer','buttons']);
  demand(UUID.test(i.local_id as string)&&UUID.test(i.concessionaria_id as string),
    'INVALID_TENANT_SCOPE');
  demand(DIGITS.test(i.waba_ref as string),'INVALID_WABA');
  demand(NAME.test(i.name as string)&&LOCALE.test(i.language as string),
    'INVALID_META_TEMPLATE_NAME_OR_LANGUAGE');
  demand(i.category==='UTILITY'||i.category==='MARKETING','UNSUPPORTED_CATEGORY');
  demand(['HUMAN_SPECIFIED','AI_ASSISTED','AI_GENERATED'].includes(i.origin as string),
    'INVALID_AUTHORING_ORIGIN');
  const body=keys(i.body,['text','examples']);
  demand(typeof body.text==='string'&&body.text.length>0&&body.text.length<=1024,
    'INVALID_BODY_TEXT');
  const ids=positions(body.text as string);
  demand(Array.isArray(body.examples)&&body.examples.length===ids.length&&
    (body.examples as unknown[]).every(e=>typeof e==='string'&&e.length>0&&e.length<=100),
    'INVALID_BODY_EXAMPLES');
  const slots:VariableSlot[]=ids.map(position=>({
    slot_key:'body.'+position,part:'BODY',position,
  }));
  let header:Header|undefined;
  if(i.header!==undefined){
    const h=keys(i.header,['kind'],['text','example','asset_ref']);
    demand(['TEXT','IMAGE','VIDEO','DOCUMENT'].includes(h.kind as string),
      'HEADER_REQUIRES_SPECIALIZED_VALIDATOR');
    if(h.kind==='TEXT'){
      keys(i.header,['kind','text'],['example']);
      demand(typeof h.text==='string'&&h.text.length>0&&h.text.length<=60,
        'INVALID_HEADER_TEXT');
      const hslots=positions(h.text as string,1);
      demand(hslots.length===0||
        (typeof h.example==='string'&&h.example.length>0&&h.example.length<=60),
        'INVALID_HEADER_EXAMPLE');
      hslots.forEach(position=>slots.push({
        slot_key:'header.'+position,part:'HEADER',position,
      }));
      header={kind:'TEXT',text:h.text as string,...(h.example?{example:h.example as string}:{})};
    }else{
      keys(i.header,['kind','asset_ref']);
      demand(ASSET.test(h.asset_ref as string),'INVALID_INTERNAL_MEDIA_ASSET');
      header={kind:h.kind,asset_ref:h.asset_ref as string} as Header;
    }
  }
  let footer:string|undefined;
  if(i.footer!==undefined){
    demand(typeof i.footer==='string'&&i.footer.length<=60,'INVALID_FOOTER');
    demand(positions(i.footer).length===0,'FOOTER_VARIABLES_NOT_SUPPORTED');
    footer=i.footer;
  }
  const buttons:Button[]=[];
  if(i.buttons!==undefined){
    demand(Array.isArray(i.buttons)&&i.buttons.length<=3,
      'UNSUPPORTED_BUTTON_COUNT');
    for(let index=0;index<i.buttons.length;index++){
      const b=keys(i.buttons[index],['kind','label'],['url','example_suffix','phone_number']);
      demand(['URL','QUICK_REPLY','PHONE_NUMBER'].includes(b.kind as string),
        'BUTTON_REQUIRES_SPECIALIZED_VALIDATOR');
      demand(typeof b.label==='string'&&b.label.trim().length>0&&
        b.label.length<=25,'INVALID_BUTTON_LABEL');
      if(b.kind==='QUICK_REPLY'){
        keys(i.buttons[index],['kind','label']);
        buttons.push({kind:'QUICK_REPLY',label:b.label as string});
      }else if(b.kind==='PHONE_NUMBER'){
        keys(i.buttons[index],['kind','label','phone_number']);
        demand(/^\+[1-9][0-9]{7,14}$/.test(b.phone_number as string),
          'INVALID_BUTTON_PHONE');
        buttons.push({kind:'PHONE_NUMBER',label:b.label as string,
          phone_number:b.phone_number as string});
      }else{
        keys(i.buttons[index],['kind','label','url'],['example_suffix']);
        const url=b.url as string;secureUrl(url.replace(/\{\{1\}\}/g,'example'));
        const uids=positions(url,1);
        const dynamic=uids.length===1;
        demand(!dynamic||(
          url.endsWith('{{1}}')&&
          (url.match(/\{\{1\}\}/g)||[]).length===1
        ),'DYNAMIC_URL_REQUIRES_FINAL_SUFFIX');
        demand(!dynamic||(typeof b.example_suffix==='string'&&
          SAFE_VALUE.test(b.example_suffix)),'INVALID_URL_EXAMPLE_SUFFIX');
        demand(dynamic||b.example_suffix===undefined,
          'STATIC_URL_CANNOT_HAVE_EXAMPLE_SUFFIX');
        if(dynamic)slots.push({
          slot_key:'button.'+index+'.url.1',part:'URL_BUTTON',position:1,
        });
        buttons.push({kind:'URL',label:b.label as string,url,
          ...(dynamic?{example_suffix:b.example_suffix as string}:{})});
      }
    }
    demand(unique(buttons.map(x=>x.label)),'DUPLICATE_BUTTON_LABEL');
  }
  const input:MultiFormatInput=Object.freeze({
    local_id:i.local_id as string,concessionaria_id:i.concessionaria_id as string,
    waba_ref:i.waba_ref as string,name:i.name as string,language:i.language as string,
    category:i.category as 'UTILITY'|'MARKETING',origin:i.origin as AuthoringOrigin,
    body:Object.freeze({text:body.text as string,
      examples:Object.freeze([...(body.examples as string[])])}),
    ...(header?{header:Object.freeze(header)}:{}),
    ...(footer!==undefined?{footer}:{}),
    ...(i.buttons!==undefined?{buttons:Object.freeze(buttons.map(b=>Object.freeze(b)))}:{}),
  });
  return Object.freeze({input,slots:Object.freeze(slots.map(x=>Object.freeze(x))),
    content_version:1,mapping_revision:0,mappings:Object.freeze({}),
    stage:'DRAFT' as const,meta_approved:false as const,network_performed:false as const});
}

/**
 * A media sample handle MUST be supplied separately by an authenticated Meta
 * media-upload adapter and matched to the internal asset. AI-provided asset_ref
 * alone never constitutes Graph-ready header media.
 */
export function prepareMcpTemplateReview(
  draft:MultiFormatDraft,verifiedMediaHandle?:string,
){
  demand(draft.stage==='DRAFT'&&!draft.meta_approved,'NOT_DRAFT');
  const i=draft.input;
  const components:unknown[]=[];
  if(i.header){
    if(i.header.kind==='TEXT'){
      const h:any={type:'HEADER',format:'TEXT',text:i.header.text};
      if(i.header.example)h.example={header_text:[i.header.example]};
      components.push(h);
    }else{
      demand(typeof verifiedMediaHandle==='string'&&
        /^[A-Za-z0-9_+:.=-]{10,2048}$/.test(verifiedMediaHandle),
        'VERIFIED_MEDIA_HANDLE_REQUIRED');
      components.push({type:'HEADER',format:i.header.kind,
        example:{header_handle:[verifiedMediaHandle]}});
    }
  }
  components.push({type:'BODY',text:i.body.text,
    ...(i.body.examples.length?{example:{body_text:[i.body.examples]}}:{})});
  if(i.footer)components.push({type:'FOOTER',text:i.footer});
  if(i.buttons?.length){
    components.push({type:'BUTTONS',buttons:i.buttons.map(b=>{
      if(b.kind==='QUICK_REPLY')return {type:'QUICK_REPLY',text:b.label};
      if(b.kind==='PHONE_NUMBER')
        return {type:'PHONE_NUMBER',text:b.label,phone_number:b.phone_number};
      return {type:'URL',text:b.label,url:b.url,
        ...(b.example_suffix?{example:[b.url.replace('{{1}}',b.example_suffix)]}:{})};
    })});
  }
  // WDC-09: review output carries a point-in-time copy of the positional
  // binding snapshot. The future authenticated service MUST recheck this
  // revision against the persisted version when it records Meta approval;
  // this preview neither submits nor grants approval.
  const slotKeys=draft.slots.map(slot=>slot.slot_key);
  const bindingsComplete=slotKeys.every(key=>
    Object.hasOwn(draft.mappings,key)&&typeof draft.mappings[key]==='string');
  const bindingCopy=Object.freeze(Object.fromEntries(slotKeys
    .filter(key=>Object.hasOwn(draft.mappings,key))
    .map(key=>[key,draft.mappings[key]])));
  return Object.freeze({operation:'PREPARE_META_REVIEW' as const,
    waba_ref:i.waba_ref,content_version:draft.content_version,
    binding_snapshot:Object.freeze({mapping_revision:draft.mapping_revision,
      complete:bindingsComplete,mappings:bindingCopy}),
    payload:Object.freeze({name:i.name,language:i.language,
      category:i.category,components:Object.freeze(components)}),
    requires_mcp_service_auth:true as const,network_performed:false as const,
    meta_approved:false as const,send_authorized:false as const});
}

export function mapMcpTemplateSources(
  draft:MultiFormatDraft,revision:number,
  mappings:Readonly<Record<string,string>>,
  trustedSources:readonly string[],
):MultiFormatDraft{
  demand(draft?.stage==='DRAFT'&&draft.meta_approved===false,
    'MAPPING_REQUIRES_UNAPPROVED_DRAFT');
  demand(revision===draft.mapping_revision,'STALE_MAPPING_REVISION');
  const slots=draft.slots.map(x=>x.slot_key);
  // Do not execute user-defined getters or inherit keys from a hostile
  // mapping object. Values must originate from the trusted scoped registry.
  keys(mappings,slots);
  demand(Array.isArray(trustedSources)&&
    trustedSources.every(x=>typeof x==='string'&&SOURCE.test(x)),
    'INVALID_SOURCE_REGISTRY');
  demand(Object.keys(mappings).length===slots.length&&
    slots.every(x=>Object.hasOwn(mappings,x)&&
      SOURCE.test(mappings[x])&&trustedSources.includes(mappings[x])),
    'INVALID_OR_UNAUTHORIZED_MAPPING');
  return Object.freeze({...draft,mappings:Object.freeze({...mappings}),
    mapping_revision:revision+1});
}

/**
 * Tool names/protocol are a design contract for a future MCP server, not
 * registered MCP tools and not an authority to execute Meta API requests.
 */
export const MCP_TEMPLATE_TOOLS = Object.freeze([
  'templates.capabilities',
  'templates.list',
  'templates.get',
  'templates.create_draft',
  'templates.edit_draft_components',
  'templates.preview',
  'templates.configure_variable_sources',
  'templates.prepare_review',
  'templates.submit_for_meta_review',
  'templates.sync_meta_status',
  'templates.new_content_version',
  'templates.audit_history',
] as const);
