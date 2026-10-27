import postgres from "postgres";
import { Family, Document, Principal, proofArgs, receipt, sign, uuid } from "./contract.ts";

export class AuthenticationDenied extends Error {}
export type Settings = {authUrl:string; anon:string; database:string; databaseAddress:string; keyId:string; secret:Uint8Array; origin:string};
export function settings(read: (key:string)=>string|undefined): Settings {
  if (read("PRUMO_I82_DISPOSABLE") !== "YES") throw new Error("I82_CONFIG_BLOCKED");
  const auth = new URL(read("PRUMO_I82_AUTH_URL") ?? "");
  const db = new URL(read("PRUMO_I82_DATABASE_URL") ?? "");
  const hosts = ["127.0.0.1", "localhost"];
  if (auth.protocol !== "http:" || ![...hosts,"supabase_kong_prumo-s0-auth-ci"].includes(auth.hostname) || auth.username || auth.password || auth.search || auth.hash || auth.pathname !== "/") throw new Error("I82_CONFIG_BLOCKED");
  const login=read("PRUMO_I83_DEDICATED")==="YES"?"prumo_s1_admin_edge_local":"prumo_cfi01_pgtest_login";
  if (read("PRUMO_I83_DEDICATED") && read("PRUMO_I83_DEDICATED")!=="YES") throw new Error("I82_CONFIG_BLOCKED");
  if (!["postgres:","postgresql:"].includes(db.protocol) || ![...hosts,"supabase_db_prumo-s0-auth-ci"].includes(db.hostname) || db.username !== login || !db.password || db.pathname !== "/postgres" || db.search || db.hash) throw new Error("I82_CONFIG_BLOCKED");
  // npm's Node DNS adapter in the pinned local Edge Runtime cannot resolve
  // the DB container name. Installer pins its own Docker-network IPv4 only;
  // no client-supplied host or extra DB privilege is accepted.
  const pin=read("PRUMO_I82_DATABASE_IPV4");let databaseAddress=db.hostname;
  if(db.hostname==="supabase_db_prumo-s0-auth-ci") {
    if(!pin || !/^\d{1,3}(\.\d{1,3}){3}$/.test(pin))throw new Error("I82_CONFIG_BLOCKED");
    const octets=pin.split(".").map(Number);
    if(octets.some(n=>n>255) || !(octets[0]===10 || (octets[0]===172 && octets[1]>=16 && octets[1]<=31) || (octets[0]===192 && octets[1]===168)))throw new Error("I82_CONFIG_BLOCKED");
    databaseAddress=pin;
  } else if(pin)throw new Error("I82_CONFIG_BLOCKED");
  const hex=read("PRUMO_I82_HMAC_HEX") ?? "";
  const anon=read("PRUMO_I82_ANON_KEY") ?? "";
  if (hex.length<64 || hex.length>256 || /[^0-9a-f]/.test(hex) || hex.length%2 || /[^\x21-\x7e]/.test(anon) || !anon) throw new Error("I82_CONFIG_BLOCKED");
  const origin=read("PRUMO_I82_ALLOW_ORIGIN") ?? "";
  if (origin) { const u=new URL(origin); if(u.protocol!=="http:" || !hosts.includes(u.hostname) || u.origin!==origin) throw new Error("I82_CONFIG_BLOCKED"); }
  return {authUrl:auth.origin, database:db.href, databaseAddress, anon, keyId:uuid(read("PRUMO_I82_KEY_ID")), secret:Uint8Array.from(hex.match(/../g)!,h=>parseInt(h,16)), origin};
}

export async function boundedBody(body: ReadableStream<Uint8Array>|null, max: number): Promise<Uint8Array> {
  if (!body) return new Uint8Array();
  const reader=body.getReader(); const chunks:Uint8Array[]=[]; let size=0;
  let timer:ReturnType<typeof setTimeout>;
  const deadline=new Promise<never>((_,reject)=>{timer=setTimeout(()=>reject(new Error("BODY_TIMEOUT")),5000);});
  try {
    while(true) { const {value,done}=await Promise.race([reader.read(),deadline]); if(done)break; size+=value.length; if(size>max)throw new Error("BODY_LIMIT"); chunks.push(value); }
  } finally { clearTimeout(timer!);await reader.cancel().catch(()=>{}); reader.releaseLock(); }
  const all=new Uint8Array(size);let pos=0;for(const b of chunks){all.set(b,pos);pos+=b.length;}return all;
}

export async function authenticate(authorization: string|null, c: Settings): Promise<Principal> {
  if (!authorization || authorization.length>8200 || !/^Bearer [A-Za-z0-9_.-]{20,8192}$/.test(authorization) || /[\r\n]/.test(authorization)) throw new AuthenticationDenied();
  const response=await fetch(c.authUrl+"/auth/v1/user", {method:"GET",redirect:"manual",signal:AbortSignal.timeout(5000),headers:{Authorization:authorization,apikey:c.anon,Accept:"application/json"}});
  if ([301,302,303,307,308,401,403,404].includes(response.status)) {await response.body?.cancel();throw new AuthenticationDenied();}
  if(response.status!==200){await response.body?.cancel();throw new Error("AUTH_UNAVAILABLE");}
  const user=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await boundedBody(response.body,65536)));
  try {
    const token=authorization.slice(7).split(".");if(token.length!==3 || token.some(p=>!p))throw new Error();
    const payload=token[1].replace(/-/g,"+").replace(/_/g,"/");
    const claims=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(Uint8Array.from(atob(payload+"=".repeat((4-payload.length%4)%4)),v=>v.charCodeAt(0))));
    if(user.role!=="authenticated" || claims.role!=="authenticated" || uuid(user.id)!==uuid(claims.sub) || !Number.isSafeInteger(claims.exp) || claims.exp<=Date.now()/1000)throw new Error();
    return {actor:uuid(user.id),session:uuid(claims.session_id)};
  } catch {throw new AuthenticationDenied();}
}

// Exactly the existing SQL application login and signed ports. Never query a
// domain table, SET ROLE, impersonate a JWT role, or retry after an I/O failure.
export function core(c: Settings) {
  const client=postgres(c.database,{host:c.databaseAddress,max:2,prepare:false,ssl:false,connect_timeout:5,idle_timeout:5,max_lifetime:60,onnotice:()=>{},connection:{application_name:"prumo-i82-local"}});
  return async(family:Family,p:Document,principal:Principal):Promise<Document>=>{
    const args=proofArgs(family,p,principal,c.keyId,Math.floor(Date.now()/1000),crypto.randomUUID());
    args.push(await sign(family,args,c.secret));
    // Explicit CASTs and placeholders only; no client-controlled SQL names.
    const query=family==="i79"
      ? "select prumo_private.s1_i79_admin_signed($1::uuid,$2::uuid,$3::text,$4::uuid,$5::text,$6::uuid,$7::bigint,$8::text,$9::uuid,$10::bigint,$11::uuid,$12::text) as result"
      : "select prumo_private.s1_i80_signed($1::uuid,$2::uuid,$3::text,$4::uuid,$5::text,$6::uuid,$7::text,$8::uuid,$9::uuid,$10::integer,$11::text,$12::uuid,$13::bigint,$14::uuid,$15::text) as result";
    return await client.begin(async tx=>{
      await tx`set local lock_timeout='8s'`;await tx`set local statement_timeout='15s'`;
      const rows=await tx.unsafe(query,args as never[]);
      if(rows.length!==1)throw new Error("CORE_RESULT_INVALID");
      return receipt(family,rows[0].result,p); // BEFORE COMMIT, including deferred failure
    }) as Document; // promise resolves only after COMMIT acknowledgment
  };
}
