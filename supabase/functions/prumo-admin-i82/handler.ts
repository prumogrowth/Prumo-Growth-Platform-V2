import {command, Document, Family, strictJson, VERSION} from "./contract.ts";
import {authenticate, AuthenticationDenied, boundedBody, core, settings} from "./runtime.ts";

export function createHandler(read:(key:string)=>string|undefined) {
  // Invalid/hosted configuration does not print secret values or stack traces.
  let c:ReturnType<typeof settings>|undefined;let invoke:ReturnType<typeof core>|undefined;
  try { c=settings(read);invoke=core(c); } catch { /* fail closed, no startup networking */ }
  let inflight=0;
  return async(req:Request):Promise<Response>=>{
    const correlation_id=crypto.randomUUID();const origin=req.headers.get("origin");
    const headers:Record<string,string>={"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store","X-Content-Type-Options":"nosniff","X-Request-ID":correlation_id};
    if(c?.origin && origin===c.origin){headers["Access-Control-Allow-Origin"]=c.origin;headers.Vary="Origin";}
    const respond=(status:number,state:string,commit:string,receipt:Document|null=null)=>new Response(JSON.stringify({version:VERSION,correlation_id,state,commit,scope:"ADMINISTRATIVE_ONLY",receipt}),{status,headers});
    if(!c || !invoke)return respond(503,"UNAVAILABLE","NOT_ATTEMPTED");
    if(origin && origin!==c.origin)return respond(403,"DENIED","NOT_ATTEMPTED");
    const url=new URL(req.url);const path=url.pathname.replace(/^\/functions\/v1(?=\/prumo-admin-i82\/)/,"");
    const family:Family|null=path==="/prumo-admin-i82/v1/i79"?"i79":path==="/prumo-admin-i82/v1/i80"?"i80":null;
    if(!family || url.search)return respond(404,"NOT_FOUND","NOT_ATTEMPTED");
    if(req.method==="OPTIONS") {
      if(!origin || req.headers.get("access-control-request-method")!=="POST")return respond(403,"DENIED","NOT_ATTEMPTED");
      const requested=(req.headers.get("access-control-request-headers")??"").toLowerCase().split(",").map(s=>s.trim()).filter(Boolean);
      if(requested.some(h=>!["authorization","apikey","content-type"].includes(h)))return respond(403,"DENIED","NOT_ATTEMPTED");
      headers["Access-Control-Allow-Methods"]="POST";headers["Access-Control-Allow-Headers"]="authorization,apikey,content-type";
      return new Response(null,{status:204,headers});
    }
    if(req.method!=="POST"){headers.Allow="POST, OPTIONS";return respond(405,"METHOD_NOT_ALLOWED","NOT_ATTEMPTED");}
    if(req.headers.get("content-encoding") || !/^application\/json(?:;\s*charset=utf-8)?$/i.test(req.headers.get("content-type")??""))return respond(415,"INPUT_REJECTED","NOT_ATTEMPTED");
    const length=req.headers.get("content-length");if(length && (!/^\d+$/.test(length) || Number(length)>8192))return respond(413,"INPUT_REJECTED","NOT_ATTEMPTED");
    if(inflight>=4){headers["Retry-After"]="1";return respond(429,"BUSY","NOT_ATTEMPTED");}
    inflight++;
    try {
      let p:Document;
      try {p=command(family,strictJson(new TextDecoder("utf-8",{fatal:true}).decode(await boundedBody(req.body,8192))));}
      catch{return respond(400,"INPUT_REJECTED","NOT_ATTEMPTED");}
      let principal;
      try {principal=await authenticate(req.headers.get("authorization"),c);}
      catch(error){return error instanceof AuthenticationDenied?respond(401,"DENIED","NOT_ATTEMPTED"):respond(503,"UNAVAILABLE","NOT_ATTEMPTED");}
      try {
        const receipt=await invoke(family,p,principal);
        return respond(200,receipt.outcome as string,"CONFIRMED",receipt);
      } catch(error) {
        const code=(error as {code?:string}).code;
        // Server-only, bounded diagnostics: no error message/detail, SQL,
        // parameters, credentials, JWT, request payload or Auth response.
        const kind=(error as {name?:string}).name;
        const locations=String((error as {stack?:string}).stack??"").split("\n").slice(1,5)
          .map(line=>line.match(/(?:file|ext|node):[^\s)]+:\d+:\d+/)?.[0]).filter(Boolean);
        console.warn(JSON.stringify({event:"I82_CORE_FAILURE",kind:["Error","TypeError","PostgresError"].includes(kind??"")?kind:"ERROR",code:code&&/^[A-Z0-9_]{2,40}$/.test(code)?code:"UNCLASSIFIED",locations}));
        const state=({"42501":"DENIED","23514":"DENIED","40001":"STALE","23505":"CONFLICT",...(family==="i80"?{"55P03":"CONCURRENT_CHANGE","P3180":"EXPIRED","P3181":"BLOCKED"}:{})} as Record<string,string>)[code??""];
        if(state)return respond(["DENIED"].includes(state)?403:409,state,"REJECTED");
        return respond(503,"UNAVAILABLE","UNKNOWN"); // includes COMMIT I/O/result uncertainty
      }
    } finally {inflight--;}
  };
}
