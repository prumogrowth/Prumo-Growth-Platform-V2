import {command, decimal, Family, material, proofArgs, receipt, sign, strictJson, VERSION} from "../../supabase/functions/prumo-admin-i82/contract.ts";
import {settings} from "../../supabase/functions/prumo-admin-i82/runtime.ts";
import {createHandler} from "../../supabase/functions/prumo-admin-i82/handler.ts";
const fixture=JSON.parse(Deno.readTextFileSync(new URL("./compat_vectors.json",import.meta.url)));
function assert(v:unknown):asserts v {if(!v)throw new Error("assertion");}
function equal(a:unknown,b:unknown){assert(JSON.stringify(a)===JSON.stringify(b));}
function rejects(fn:()=>unknown){let denied=false;try{fn();}catch{denied=true;}assert(denied);}
const envelope=(p:unknown)=>({version:VERSION,command:p});
const dto=fixture.vectors[0].command;
const config:Record<string,string>={PRUMO_I82_DISPOSABLE:"YES",PRUMO_I82_AUTH_URL:"http://127.0.0.1:54321",PRUMO_I82_DATABASE_URL:"postgresql://prumo_cfi01_pgtest_login:synthetic-only@127.0.0.1:54322/postgres",PRUMO_I82_ANON_KEY:"synthetic-anon-only",PRUMO_I82_HMAC_HEX:fixture.secret_hex,PRUMO_I82_KEY_ID:fixture.key_id,PRUMO_I82_ALLOW_ORIGIN:"http://localhost:3000"};

Deno.test("codec: all six commands and bigint boundary match independent Python vectors",async()=>{
  for(const v of fixture.vectors){
    const p=command(v.family,envelope(v.command));const args=proofArgs(v.family,p,fixture.principal,fixture.key_id,fixture.issued,fixture.nonce);
    equal(args,v.args);equal(material(v.family,args),v.material);
    equal(await sign(v.family,args,Uint8Array.from(fixture.secret_hex.match(/../g),(h:string)=>parseInt(h,16))),v.mac);
  }
});
Deno.test("DTO: reject every client actor/session/permission field",()=>{
  for(const key of ["actor_id","session_id","diretor_id","role","permissions","service_role"]){
    rejects(()=>command("i79",envelope({...dto,[key]:fixture.principal.actor})));
    rejects(()=>command("i79",{...envelope(dto),[key]:fixture.principal.actor}));
  }
  rejects(()=>command("i79",{"command|version":dto}));
});
Deno.test("DTO: bigint decimal preserves full PostgreSQL range without Number coercion",()=>{
  equal(decimal("9223372036854775807"),"9223372036854775807");
  for(const v of [1,true,0,9007199254740992,"01","+1","1e3","-1","9223372036854775808","1\n"]){rejects(()=>decimal(v));}
});
Deno.test("DTO: action scopes and explicit nulls unchanged",()=>{
  for(const v of fixture.vectors){
    command(v.family,envelope(v.command));rejects(()=>command(v.family,envelope({...v.command,cargo:"diretor"})));
    rejects(()=>command(v.family,envelope({...v.command,manager_id:undefined})));
  }
  rejects(()=>command("i79",envelope({...dto,manager_id:fixture.principal.actor})));
});
Deno.test("DTO: no Unicode newline key or noncanonical identifiers",()=>{
  for(const idempotency_key of ["i82-test\n","i82-é-test","x".repeat(129),"a|b12345"]){rejects(()=>command("i79",envelope({...dto,idempotency_key})));}
  for(const target_id of [dto.target_id+"\n",dto.target_id.toUpperCase().replace("3","A"),"00000000-0000-0000-0000-000000000000"]){rejects(()=>command("i79",envelope({...dto,target_id})));}
});
Deno.test("JSON: duplicate literal or escaped keys, arrays, trailing data and depth rejected",()=>{
  for(const s of ['{"action":1,"action":2}','{"a":1,"\\u0061":2}','{"a":[1]}','{}{}','{"a":'.repeat(9)+'0'+'}'.repeat(9),'{"a":NaN}'])rejects(()=>strictJson(s));
  equal(strictJson('{"a":null,"b":0}'),{a:null,b:0});
});
Deno.test("receipt: binding exact shape and decimal relation checked before commit",()=>{
  const p=command("i79",envelope(dto));
  const r={outcome:"APPLIED",request_id:fixture.nonce,action:"REGISTER",target_id:p.target_id,cargo:p.cargo,manager_id:null,previous_relationship_id:"0",relationship_id:null};
  receipt("i79",r,p);
  for(const bad of [{...r,actor_id:fixture.principal.actor},{...r,target_id:fixture.key_id},{...r,relationship_id:"1"}])rejects(()=>receipt("i79",bad,p));
});
Deno.test("receipt: inventory contains no private fields or unordered pagination",()=>{
  const p=command("i80",envelope(fixture.vectors.find((v:{family:Family,command:{action:string}})=>v.command.action==="INVENTORY").command));
  const r={outcome:"INVENTORY",items:[{target_id:fixture.nonce,cargo:null,estado:"pendente",bounded:true,inventory_sha256:"a".repeat(64)}],has_more:false,next_cursor:null};
  receipt("i80",r,p);rejects(()=>receipt("i80",{...r,secret:"x"},p));
  rejects(()=>receipt("i80",{...r,items:[r.items[0],r.items[0]]},p));
});
Deno.test("config: hosted URLs privileged SQL users absent opt-in and remote origins blocked",()=>{
  settings(k=>config[k]);
  for(const patch of [{PRUMO_I82_DISPOSABLE:"NO"},{PRUMO_I82_AUTH_URL:"https://example.supabase.co"},{PRUMO_I82_DATABASE_URL:"postgresql://postgres:x@localhost/postgres"},{PRUMO_I82_ALLOW_ORIGIN:"https://frontend.example"}])rejects(()=>settings(k=>({...config,...patch} as Record<string,string|undefined>)[k]));
  const docker={...config,PRUMO_I82_DATABASE_URL:"postgresql://prumo_cfi01_pgtest_login:synthetic-only@supabase_db_prumo-s0-auth-ci:5432/postgres",PRUMO_I82_DATABASE_IPV4:"172.18.0.2"};
  equal(settings(k=>docker[k as keyof typeof docker]).databaseAddress,"172.18.0.2");
  for(const ip of ["169.254.169.254","8.8.8.8","172.999.0.2","localhost",""]){rejects(()=>settings(k=>({...docker,PRUMO_I82_DATABASE_IPV4:ip} as Record<string,string>)[k]));}
});
Deno.test("HTTP: invalid DTO no auth networking, secret echo, or chosen correlation",async()=>{
  const h=createHandler(k=>config[k]);const r=await h(new Request("http://localhost/prumo-admin-i82/v1/i79",{method:"POST",headers:{"content-type":"application/json","x-request-id":fixture.principal.actor},body:JSON.stringify(envelope({...dto,actor_id:fixture.principal.actor}))}));
  equal(r.status,400);const b=await r.json();equal(b.commit,"NOT_ATTEMPTED");assert(b.correlation_id!==fixture.principal.actor);equal(b.receipt,null);
  const text=JSON.stringify(b);assert(!text.includes(config.PRUMO_I82_DATABASE_URL));equal(r.headers.get("cache-control"),"no-store");
});
Deno.test("HTTP: only local allowlisted CORS and fixed POST routes",async()=>{
  const h=createHandler(k=>config[k]);
  equal((await h(new Request("http://localhost/prumo-admin-i82/v1/i79"))).status,405);
  equal((await h(new Request("http://localhost/prumo-admin-i82/v1/i79",{method:"OPTIONS",headers:{origin:"http://localhost:3000","access-control-request-method":"POST"}}))).status,204);
  equal((await h(new Request("http://localhost/prumo-admin-i82/v1/i79",{method:"OPTIONS",headers:{origin:"https://untrusted.example","access-control-request-method":"POST"}}))).status,403);
  equal((await h(new Request("http://localhost/prumo-admin-i82/v1/i79?actor_id=x"))).status,404);
});
Deno.test("HTTP: missing local opt-in unavailable without networking or leaked config",async()=>{
  const h=createHandler(()=>undefined);const r=await h(new Request("http://localhost/prumo-admin-i82/v1/i79"));equal(r.status,503);equal((await r.json()).commit,"NOT_ATTEMPTED");
});
