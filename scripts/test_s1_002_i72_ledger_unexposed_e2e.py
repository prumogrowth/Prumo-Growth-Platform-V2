"""I72 ephemeral PostgREST exposure proof after I71. No hosted access.

Disables the direct API table endpoint without changing I71 invoker RPC,
rolling quota, concurrent reservations, RLS or private retention.
"""
if os.environ.get("CI")!="true" or os.environ.get("PRUMO_S1_I37_EPHEMERAL")!="YES":
 raise AssertionError("I72 disposable CI only")
assert sql("select pg_catalog.has_column_privilege('authenticated',"
 "'public.s1_70_export_reservas','ator_id','INSERT')")=="t"
before=int(sql("select count(*) from public.s1_70_export_reservas"))
sql(path="supabase/tests/s1_104_export_ledger_unexposed_local_only.sql")
sql("notify pgrst,'reload schema'")
assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before
print("PASS I72-E2E-01: same ledger rows preserved and invoker grants re-bound after schema move")

# PostgREST must not route table-based INSERT even when actor UUID and shop
# are valid. No need to spend an authorized quota to prove non-exposure.
direct={"ator_id":g1,"concessionaria_id":store_a,
        "tipo":"lotes","unidades_reservadas":1}
def direct72():
 return http("POST","/rest/v1/s1_70_export_reservas",
             bearer=token53,body=direct,base=api)
for attempt in range(30):
 st,err=direct72()
 if st==404:break
 time.sleep(.2)
assert st==404,(st,err)
assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before
print("PASS I72-E2E-02: valid manager cannot POST a direct quota reservation through public REST")

st,err=http("GET","/rest/v1/s1_70_export_reservas?select=*",
            bearer=token53,base=api)
assert st==404,(st,err)
st,err=http("POST","/rest/v1/s1_70_export_reservas",
            bearer=anon,body=direct,base=api)
assert st in (401,403,404),(st,err)
print("PASS I72-E2E-03: ledger has no public read endpoint; anonymous user cannot write")

# Selecting the ledger's internal schema via header MUST NOT enable access.
# Existing shared HTTP helper has no custom-headers argument.
from urllib.request import Request as _I72Request, urlopen as _I72Open
from urllib.error import HTTPError as _I72HTTPError
_i72_req=_I72Request(api+"/rest/v1/s1_70_export_reservas",
 data=json.dumps(direct).encode("utf-8"),method="POST",
 headers={"Content-Profile":"prumo_export_ledger",
          "Content-Type":"application/json",
          "apikey":anon,"Authorization":"Bearer "+token53})
try:
 with _I72Open(_i72_req,timeout=20) as _i72_response:
  st=_i72_response.status
except _I72HTTPError as _i72_error:
 st=_i72_error.code
assert st==406,st
print("PASS I72-E2E-04: Content-Profile cannot expose internal schema")

st,payload=export71("lotes",token=token53,lim=1)
assert st==200 and payload["estado"]=="OK" and len(payload["linhas"])==1,(st,payload)
assert int(sql("select count(*) from prumo_export_ledger.s1_70_export_reservas"))==before+1
print("PASS I72-E2E-05: real GoTrue manager still exports through I71 invoker; reservation increments once")

st,payload=export71("lotes",token=tok6)
assert st==200 and payload=={"estado":"VAZIO","linhas":[]},(st,payload)
assert sql("select pg_catalog.has_table_privilege('authenticated',"
 "'prumo_export_ledger.s1_70_export_reservas','SELECT')")=="f"
assert sql("select pg_catalog.has_schema_privilege('anon',"
 "'prumo_export_ledger','USAGE')")=="f"
assert sql("select count(*) from prumo_s1_i65_test.exposicoes()")=="0"
print("PASS I72-E2E-06: revoked/unauthorized export boundaries and I65 ACL scanner intact")

# The original privileged cleanup, also re-bound, still removes aged events.
sql("""update prumo_export_ledger.s1_70_export_reservas
 set registrada_em=pg_catalog.clock_timestamp()-interval '31 days'
 where id=(select min(id) from prumo_export_ledger.s1_70_export_reservas)""")
rem=sql("select aceitos_excluidos::text from "
 "prumo_private.s1_71_purgar_registros(pg_catalog.clock_timestamp())")
assert rem=="1",rem
print("PASS I72-E2E-07: private administrator retention still reaches relocated accepted events")
print("I72 7/7 real GoTrue/PostgREST ledger isolation E2E; disposable only")

# I73: same disposable GoTrue stack; no duplicate CI startup.
_i73=Path('scripts/test_s1_002_i73_export_executor_e2e.py')
exec(compile(_i73.read_text(encoding='utf-8'),str(_i73),'exec'),globals())
