"""I59 actual GoTrue/PostgREST follow-up, loaded by I44's ephemeral runner.

Never creates hosted actors or changes credentials; inherits I44 synthetic
actors and valid JWTs. The canonical FK is applied BEFORE I44 seeded rows.
"""
# Query list visibility remains exactly I44's owner/team/same-contact scope.
assert cases(m1)=={CA,CB,CD} and cases(m4)=={CC}
assert cases(c3)==set(), "I59 exception was revoked in preceding I44 tests"
assert len(rows("mensagens", m1))==4  # I44-04 inserted one authorized current-case reply
print("PASS I59-REST-01: real JWT keeps team history; revoked exception stays invisible")

# The valid linked conversation must not be relabeled as another contact in
# the same shop, as that would manufacture access to a different history.
sql("""do $i59$ begin
 begin
 update public.conversas set lead_id='62330000-0000-4000-8000-000000000002'
 where id='62770000-0000-4000-8000-000000000002';
 raise exception 'I59 invalid same-shop relabel succeeded';
 exception when foreign_key_violation then null;end;
end $i59$;""")
assert cases(c2)=={CD} and cases(m4)=={CC}
assert len(rows("conversas",m1))==3
print("PASS I59-REST-02: mismatched case/contact UPDATE rejected before real REST can expose it")
sql("""do $i59$ begin
 begin
 update public.conversas set caso_id='62550000-0000-4000-8000-000000000003'
 where id='62770000-0000-4000-8000-000000000002';
 raise exception 'I59 switched historical case without matching contact';
 exception when foreign_key_violation then null;end;
end $i59$;""")
assert cases(c5)=={CC} and cases(out)==set()
assert len(rows("mensagens",c5))==1
print("PASS I59-REST-03: case substitution denied; other team and outsider remain segregated")

# Verify catalog state after real RLS fixture and rest of I44 tests.
assert sql("""select count(*) from pg_catalog.pg_constraint
 where conname='s0_conversa_caso_lead_i59' and conrelid='public.conversas'::regclass
 and contype='f' and convalidated""")=="1"
assert sql("""select count(*) from public.conversas co
 join public.casos_humanos h
  on h.concessionaria_id=co.concessionaria_id and h.id=co.caso_id
 where co.caso_id is not null and co.lead_id is distinct from h.lead_id""")=="0"
print("PASS I59-REST-04: validated canonical FK has zero mismatched conversation/case/contact rows")
print("I59 GoTrue RLS 4/4 synthetic tests, no hosted deployment")
