-- I16 / INTEGRACAO ISOLADA: RPC canario temporario, NAO migration.
-- Testa helper REAL 052 por JWT REAL de GoTrue/PostgREST, sem expor
-- interfaces de gestao (051) nem criar grants em prumo_private.
-- O runner exige stack docker local, nao supabase hospedado.
create function public.s1_i16_prova_sessao()
returns jsonb language plpgsql security definer set search_path='' as $p$
declare v_ator uuid;
begin
 v_ator:=prumo_private.s1_exigir_identidade_sessao();
 return pg_catalog.jsonb_build_object('autorizado',true,'ator_id',v_ator);
end $p$;
revoke all on function public.s1_i16_prova_sessao()
 from public,anon,authenticated,service_role;
grant execute on function public.s1_i16_prova_sessao() to authenticated;
select pg_catalog.pg_notify('pgrst','reload schema');
