/** WA67: isolated lab-only raw JSON ambiguity guard.
 * Do not transplant to official S0 without Codex review. The existing gate
 * verifies HMAC before this scan; bridge rechecks independently.
 *
 * JSON.parse overwrites duplicate names (including escaped aliases) and
 * accepts lone escaped UTF-16 surrogates. This scan rejects both without
 * altering JSON bytes or normalizing valid Unicode. All accepted bytes still
 * participate in the original SHA-256 forensic record.
 */
export function wa67StrictJsonKeys(bytes){
 if(!Buffer.isBuffer(bytes)||bytes.length<1||bytes.length>262144)return false;
 try{
  // ignoreBOM:true preserves any leading U+FEFF for explicit rejection.
  const src=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(bytes);
  if(!src||src.charCodeAt(0)===0xfeff)return false;
  JSON.parse(src); // Authoritative JSON grammar, before duplicate-key scan.
  let pos=0,names=0,nodes=0;
  const gap=()=>{while(pos<src.length&&(
   src[pos]===' '||src[pos]==='\r'||src[pos]==='\n'||src[pos]==='\t'))pos++;};
  function quoted(){
   if(src[pos]!=='"')throw Error('NOT_STRING');
   const from=pos++;
   while(pos<src.length){
    const c=src[pos++];
    if(c==='\\'){pos++;continue;}
    if(c==='"')break;
   }
   if(src[pos-1]!=='"')throw Error('UNCLOSED');
   const value=JSON.parse(src.slice(from,pos));
   // Valid astral codepoints are combined by codepoint iteration; reject a
   // surrogate only when it is unpaired after JSON escape decoding.
   for(const scalar of value){
    const cp=scalar.codePointAt(0);
    if(cp>=0xd800&&cp<=0xdfff)throw Error('LONE_SURROGATE');
   }
   return value;
  }
  function value(depth){
   if(++nodes>4096||depth>48)throw Error('COMPLEXITY_CAP');
   gap();
   if(src[pos]==='{'){
    pos++;gap();const seen=new Set();
    if(src[pos]==='}'){pos++;return;}
    for(;;){
     gap();const name=quoted();
     if(++names>2048||seen.has(name))throw Error('DUPLICATE_OR_TOO_MANY');
     seen.add(name);gap();
     if(src[pos++]!==':')throw Error('BAD_COLON');
     value(depth+1);gap();
     if(src[pos]==='}'){pos++;return;}
     if(src[pos++]!==',')throw Error('BAD_OBJECT');
    }
   }
   if(src[pos]==='['){
    pos++;gap();
    if(src[pos]===']'){pos++;return;}
    for(;;){
     value(depth+1);gap();
     if(src[pos]===']'){pos++;return;}
     if(src[pos++]!==',')throw Error('BAD_ARRAY');
    }
   }
   if(src[pos]==='"'){quoted();return;}
   const start=pos;
   while(pos<src.length&& !(
    src[pos]===','||src[pos]===']'||src[pos]==='}'||
    src[pos]===' '||src[pos]==='\t'||src[pos]==='\n'||src[pos]==='\r'))pos++;
   if(pos===start)throw Error('EMPTY_VALUE');
  }
  value(0);gap();
  return pos===src.length;
 }catch{return false;}
}
