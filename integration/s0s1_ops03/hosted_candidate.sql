-- OPS-03 experimental compatibility adapter. LAB ONLY; NO HOSTED VARIANT.
-- Reuses the certified I86 algorithm unchanged as a laboratory control.
-- REVOKE still delegates its atomic Auth DML to I86 ONLY in the disposable DB.
-- There is NO supported-hosted session strategy implemented by this adapter.
begin;
-- Both the installer and every call retain the certified I86 PG17/principal/
-- READ COMMITTED/disposable-database guard. Missing I86 also aborts installation.
select prumo_i86_manual.guard();
create schema prumo_ops03_manual;
revoke all on schema prumo_ops03_manual from public,anon,authenticated,service_role,
 prumo_s1_admin_edge_local,prumo_cfi01_pgtest_login;

create function prumo_ops03_manual.guard()
returns void language plpgsql security invoker set search_path='' as $guard$
begin
 perform prumo_i86_manual.guard();
end $guard$;

create function prumo_ops03_manual.inspect_subject(p_target uuid)
returns jsonb language plpgsql security invoker set search_path='' as $inspect$
begin
 perform prumo_ops03_manual.guard();
 return prumo_i86_manual.inspect_subject(p_target);
end $inspect$;

create function prumo_ops03_manual.apply_act(
 p_act uuid,p_action text,p_target uuid,p_expected_sha256 text,
 p_operator_record_ref text,p_manual_record_ref text,p_evidence_sha256 text)
returns jsonb language plpgsql security invoker set search_path='' as $apply$
begin
 perform prumo_ops03_manual.guard();
 return prumo_i86_manual.apply_act(p_act,p_action,p_target,p_expected_sha256,
  p_operator_record_ref,p_manual_record_ref,p_evidence_sha256);
end $apply$;

create function prumo_ops03_manual.reconcile_act(p_act uuid,p_evidence_sha256 text)
returns jsonb language plpgsql security invoker set search_path='' as $reconcile$
begin
 perform prumo_ops03_manual.guard();
 return prumo_i86_manual.reconcile_act(p_act,p_evidence_sha256);
end $reconcile$;

revoke all on all functions in schema prumo_ops03_manual from public,anon,authenticated,
 service_role,prumo_s1_admin_edge_local,prumo_cfi01_pgtest_login;
commit;
