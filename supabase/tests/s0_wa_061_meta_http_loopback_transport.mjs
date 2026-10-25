/**
 * WA57 / PG17 disposable-only HTTP loopback transport for WA56.
 * No hosted webhook, real Meta ACK, Graph, production IAM, Supabase, or S1.
 * Never bind 0.0.0.0, ::, a public host, or a user-supplied address.
 */
import http from 'node:http';

const ROUTE='/__wa57_lab/status';
const HEADERS=new Set(['host','connection','content-type',
 'content-length','x-hub-signature-256']);
const MAX_BYTES=262144;
/* WA59: caps are on this disposable listener, not production budgets.
 * Maximum body buffering: 4 * 262144 bytes (+ transient network buffers).
 * Maximum simultaneously accepted TCP connections: 16.
 */
const MAX_INFLIGHT=4,MAX_SOCKETS=16,IDLE_MS=1200;
const fail=(code)=>Object.freeze({decision:code,lab_only:true,
 meta_ack_emitted:false,ack_allowed:false,send_authorized:false});
function response(res,status,decision){
 if(res.headersSent||res.destroyed)return;
 const out=JSON.stringify(fail(decision));
 res.writeHead(status,{'content-type':'application/json; charset=utf-8',
  'content-length':Buffer.byteLength(out),
  'cache-control':'no-store','x-content-type-options':'nosniff',
  'x-wa57-lab-only':'true','connection':'close'});
 res.end(out);
}
function headers(req){
 try {
  const raw=req.rawHeaders;
  if(!Array.isArray(raw)||raw.length===0||raw.length%2!==0||
    raw.length/2>HEADERS.size)return null;
  const map=new Map();
  for(let i=0;i<raw.length;i+=2){
   if(typeof raw[i]!=='string'||typeof raw[i+1]!=='string')return null;
   const name=raw[i].toLowerCase(),v=raw[i+1];
   if(!HEADERS.has(name)||map.has(name)||!/^[a-z0-9-]+$/.test(name))
    return null;
   map.set(name,v);
  }
  if(!map.has('host')||!map.has('content-length')||
    !map.has('content-type')||!map.has('x-hub-signature-256')||
    map.get('content-type')!=='application/json'||
    !/^sha256=[a-f0-9]{64}$/.test(map.get('x-hub-signature-256'))||
    map.has('connection')&&!['close','keep-alive'].includes(map.get('connection')))
    return null;
  const length=map.get('content-length');
  if(!/^[1-9][0-9]{0,5}$/.test(length))return null;
  const size=Number(length);
  if(size<1||size>MAX_BYTES)return null;
  return {size,signature:map.get('x-hub-signature-256'),host:map.get('host')};
 }catch{return null;}
}
const loopback=s=>s==='127.0.0.1'||s==='::ffff:127.0.0.1';
/**
 * Secure lab envelope; exposes only start()/stop()/address(). The caller
 * cannot choose a network host and cannot obtain the raw Server object.
 */
export function createWa57OfflineLoopback(raw){
 if(!raw||typeof raw!=='object'||Array.isArray(raw))return null;
 let bridge;
 try{
  if(Reflect.ownKeys(raw).length!==1||
    !Object.hasOwn(Object.getOwnPropertyDescriptors(raw),'bridge')||
    !Object.hasOwn(Object.getOwnPropertyDescriptor(raw,'bridge'),'value'))
    return null;
  bridge=raw.bridge;
 }catch{return null;}
 if(!bridge||typeof bridge.receive!=='function')return null;
 let started=false,disposed=false,active=0;
 const server=http.createServer(async(req,res)=>{
  let admitted=false;
  try{
   if(req.socket.localAddress!=='127.0.0.1'||
      !loopback(req.socket.remoteAddress)||
      req.httpVersion!=='1.1'||req.method!=='POST'||
      req.url!==ROUTE){
    req.resume();response(res,404,'LAB_HTTP_ROUTE_DENIED');return;
   }
   const h=headers(req);
   if(!h||h.host!=='127.0.0.1:'+req.socket.localPort){
    req.resume();response(res,400,'LAB_HTTP_HEADERS_DENIED');return;
   }
   // Reserve scarce parsing/forensic capacity before buffering any body.
   // Busy rejection is local-only and never starts a WA56/WA55 operation.
   if(active>=MAX_INFLIGHT){
    response(res,503,'LAB_HTTP_BUSY');req.resume();return;
   }
   active++;admitted=true;
   const chunks=[];let seen=0;
   for await(const part of req){
    seen+=part.length;
    if(seen>h.size||seen>MAX_BYTES){
     response(res,413,'LAB_HTTP_BODY_OVERSIZE');return;
    }
    chunks.push(Buffer.from(part));
   }
   if(!req.complete||seen!==h.size){
    response(res,400,'LAB_HTTP_BODY_MISMATCH');return;
   }
   // WA58: before starting the irreversible S0 append, discard an already
   // closed HTTP response. Once the bridge begins, a lost response cannot
   // revoke a committed append: retransmission must be idempotent in PG17.
   if(res.destroyed||res.writableEnded)return;
   const body=Buffer.concat(chunks,seen);
   const verdict=await bridge.receive(body,h.signature);
   if(!verdict||verdict.decision!=='LAB_META_RAW_TO_WA55_FORENSIC_ONLY'||
      !verdict.receipt||
      verdict.receipt.entrypoint!=='WA55_PG17_SINGLE_LAB_ONLY'||
      verdict.receipt.lab_only!==true||
      verdict.meta_provenance_production_proven!==false||
      verdict.service_authenticated!==false||
      verdict.ack_allowed!==false||verdict.send_authorized!==false||
      verdict.production_authorized!==false||
      verdict.case_transition_authorized!==false){
    response(res,403,'LAB_HTTP_FORENSIC_DENIED');return;
   }
   // Only a localhost test receipt. This is not an ACK to Meta.
   response(res,202,'LAB_HTTP_FORENSIC_STORED_ONLY');
  }catch{
   response(res,503,'LAB_HTTP_UNAVAILABLE');
  }finally{
   if(admitted)active--;
  }
 });
 server.maxConnections=MAX_SOCKETS;
 server.timeout=IDLE_MS; // idle/incomplete socket closes without ACK or archive
 server.maxHeadersCount=8;
 server.headersTimeout=5000;server.requestTimeout=5000;
 server.keepAliveTimeout=1000;server.maxRequestsPerSocket=1;
 server.on('checkContinue',(req,res)=>{req.resume();response(res,417,'LAB_HTTP_EXPECT_DENIED');});
 server.on('checkExpectation',(req,res)=>{req.resume();response(res,417,'LAB_HTTP_EXPECT_DENIED');});
 server.on('clientError',(err,socket)=>{
  if(!socket.destroyed)
   socket.end('HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n');
 });
 return Object.freeze({
  async start(){
   if(started||disposed)throw Error('WA57_LIFECYCLE_DENIED');
   await new Promise((resolve,reject)=>{
    server.once('error',reject);
    server.listen(0,'127.0.0.1',()=>{server.off('error',reject);resolve();});
   });
   started=true;
   const a=server.address();
   if(!a||a.address!=='127.0.0.1'){server.close();throw Error('WA57_NOT_LOOPBACK');}
   return Object.freeze({host:a.address,port:a.port,route:ROUTE,lab_only:true});
  },
  address(){
   const a=started&&!disposed?server.address():null;
   return a&&a.address==='127.0.0.1'?Object.freeze({host:a.address,
    port:a.port,route:ROUTE,lab_only:true}):null;
  },
  async stop(){
   if(!started||disposed)throw Error('WA57_LIFECYCLE_DENIED');
   disposed=true;
   await new Promise((resolve,reject)=>server.close(e=>e?reject(e):resolve()));
  }
 });
}
