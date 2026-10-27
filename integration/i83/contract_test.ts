import {settings} from "../../supabase/functions/prumo-admin-i82/runtime.ts";
const c:Record<string,string>={PRUMO_I82_DISPOSABLE:"YES",PRUMO_I83_DEDICATED:"YES",PRUMO_I82_AUTH_URL:"http://127.0.0.1:54321",PRUMO_I82_DATABASE_URL:"postgresql://prumo_s1_admin_edge_local:noncredential-test@127.0.0.1:54322/postgres",PRUMO_I82_ANON_KEY:"not-admin-secret",PRUMO_I82_HMAC_HEX:"11".repeat(48),PRUMO_I82_KEY_ID:"33333333-3333-4333-8333-333333333333"};
function denied(v:Record<string,string>){let ok=false;try{settings(k=>v[k]);}catch{ok=true;}if(!ok)throw Error("configuration should be denied");}
Deno.test("I83 dedicated server profile accepts only its dedicated login",()=>{
 settings(k=>c[k]);
 denied({...c,PRUMO_I82_DATABASE_URL:c.PRUMO_I82_DATABASE_URL.replace("prumo_s1_admin_edge_local","prumo_cfi01_pgtest_login")});
 denied({...c,PRUMO_I83_DEDICATED:"NO"});denied({...c,PRUMO_I83_DEDICATED:""});
});
Deno.test("I83 absent key/password or privileged substitute fails closed",()=>{
 denied({...c,PRUMO_I82_HMAC_HEX:""});denied({...c,PRUMO_I82_KEY_ID:""});
 denied({...c,PRUMO_I82_DATABASE_URL:"postgresql://postgres:x@127.0.0.1:54322/postgres"});
 denied({...c,PRUMO_I82_DATABASE_URL:"postgresql://prumo_s1_admin_edge_local@127.0.0.1:54322/postgres"});
});
