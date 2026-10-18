\set ON_ERROR_STOP on
begin;
insert into public.concessionarias(id,nome_operacional) values
 ('b2000000-0000-4000-8000-000000000001','WA-ID loja A ficticia'),
 ('b2000000-0000-4000-8000-000000000002','WA-ID loja B ficticia');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('b3000000-0000-4000-8000-000000000001','b2000000-0000-4000-8000-000000000001','WA_S0_TEST_A'),
 ('b3000000-0000-4000-8000-000000000002','b2000000-0000-4000-8000-000000000002','WA_S0_TEST_B');

do $id$
declare a jsonb;b jsonb;c jsonb; d jsonb;
begin
 a:=prumo_private.receber_mensagem_identidade_s0(
 'b3000000-0000-4000-8000-000000000001',
 '+5581900000000','wamid.FIXTURE_A1','texto sintetico A',true);
 b:=prumo_private.receber_mensagem_identidade_s0(
 'b3000000-0000-4000-8000-000000000001',
 '+558100000000','wamid.FIXTURE_A1','texto sintetico A',true);
 c:=prumo_private.receber_mensagem_identidade_s0(
 'b3000000-0000-4000-8000-000000000001',
 '+558100000000','wamid.FIXTURE_A2','texto sintetico B',true);
 d:=prumo_private.receber_mensagem_identidade_s0(
 'b3000000-0000-4000-8000-000000000002',
 '+5581900000000','wamid.FIXTURE_A1','texto sintetico A',true);
 if a->>'outcome'<>'APPLIED' or b->>'outcome'<>'ALREADY_APPLIED'
    or a->>'mensagem_id'<>b->>'mensagem_id'
    or c->>'outcome'<>'APPLIED' or d->>'outcome'<>'APPLIED'
    or a->>'mensagem_id'=d->>'mensagem_id'
 then raise exception 'FAIL WA-ID-01: replay/variantes/lojas';end if;
 if (select count(*) from public.leads_loja
   where concessionaria_id='b2000000-0000-4000-8000-000000000001')<>1
 or (select count(*) from prumo_private.aliases_identidade_s0
   where concessionaria_id='b2000000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.mensagens
   where concessionaria_id='b2000000-0000-4000-8000-000000000001')<>2
 or (select count(*) from public.leads_loja
   where concessionaria_id='b2000000-0000-4000-8000-000000000002')<>1
 then raise exception 'FAIL WA-ID-01: cardinalidade';end if;
end $id$;
\echo 'PASS WA-ID-01: 9->8 + replay idempotente + duas lojas independentes'

do $id$
declare x jsonb; y jsonb; z jsonb;
begin
 x:=prumo_private.receber_mensagem_identidade_s0(
 'b3000000-0000-4000-8000-000000000001',
 '+558177777777','wamid.REVERSE1','texto sintetico reverso',true);
 y:=prumo_private.receber_mensagem_identidade_s0(
 'b3000000-0000-4000-8000-000000000001',
 '+5581977777777','wamid.REVERSE2','texto sintetico reverso',true);
 if x->>'outcome'<>'APPLIED' or y->>'outcome'<>'APPLIED'
 or (select count(*) from public.leads_loja
      where concessionaria_id='b2000000-0000-4000-8000-000000000001')<>2
 then raise exception 'FAIL WA-ID-02: ordem reversa';end if;
 if (select count(*) from prumo_private.aliases_identidade_s0 a
   where a.concessionaria_id='b2000000-0000-4000-8000-000000000001'
     and a.numero_sintetico in ('+558177777777','+5581977777777')
     and a.lead_id=(select lead_id from prumo_private.aliases_identidade_s0
       where concessionaria_id='b2000000-0000-4000-8000-000000000001'
       and numero_sintetico='+558177777777'))<>2
 then raise exception 'FAIL WA-ID-02: alias de lead';end if;
end $id$;
\echo 'PASS WA-ID-02: 8->9 mesmo lead com trilha de aliases'

do $id$
declare r jsonb;
begin
 -- Eight-digit number without mobile proof cannot be auto-merged.
 r:=prumo_private.receber_mensagem_identidade_s0(
 'b3000000-0000-4000-8000-000000000001',
 '+558122223333','wamid.FIXED1','texto de fixo ficticio',false);
 if r->>'outcome'<>'APPLIED' then raise exception 'FAIL WA-ID-03: exact';end if;
 r:=prumo_private.receber_mensagem_identidade_s0(
 'b3000000-0000-4000-8000-000000000001',
 '+5581922223333','wamid.FIXED2','nao associar fixo',true);
 if r->>'outcome'<>'NEEDS_REVIEW' or
 (select count(*) from prumo_private.pendencias_identidade_s0
 where id_externo='wamid.FIXED2')<>1
 then raise exception 'FAIL WA-ID-03: fixed merge';end if;
end $id$;
\echo 'PASS WA-ID-03: evidencia ambigua preservada sem fusao automatica'

insert into public.leads_loja(concessionaria_id,telefone_cliente_normalizado)
 values ('b2000000-0000-4000-8000-000000000001','+5581987654321'),
        ('b2000000-0000-4000-8000-000000000001','+558187654321');
do $id$
declare r jsonb;
begin
 r:=prumo_private.receber_mensagem_identidade_s0(
 'b3000000-0000-4000-8000-000000000001',
 '+5581987654321','wamid.CONFLICT','texto colidido',true);
 if r->>'outcome'<>'IDENTITY_CONFLICT'
   or (select count(*) from prumo_private.pendencias_identidade_s0
      where id_externo='wamid.CONFLICT')<>1
 then raise exception 'FAIL WA-ID-04: choque legado';end if;
end $id$;
\echo 'PASS WA-ID-04: colisao entre leads preservada em pendencia'

do $acl$
begin
 if has_table_privilege('anon','prumo_private.aliases_identidade_s0','SELECT')
 or has_table_privilege('authenticated','prumo_private.pendencias_identidade_s0','SELECT')
 or has_table_privilege('service_role','prumo_private.eventos_identidade_s0','SELECT')
 or has_function_privilege('authenticated','prumo_private.resolver_contato_s0(uuid,text,text,boolean)','EXECUTE')
 or has_function_privilege('prumo_s0_gateway','prumo_private.receber_mensagem_identidade_s0(uuid,text,text,text,boolean)','EXECUTE')
 then raise exception 'FAIL WA-ID-05: ACL dos dados/servicos';end if;
end $acl$;
\echo 'PASS WA-ID-05: ACLs privadas e sem API Meta publica'
rollback;
