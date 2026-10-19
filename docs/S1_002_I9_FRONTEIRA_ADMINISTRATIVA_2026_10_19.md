# S1-002/I9 — Fronteira de acesso administrativo negativa | 19/10/2026

**Proprietário:** apenas S1-002, branch Draft PR #5. **Natureza:** reforço de segurança SQL com mocks Auth em PostgreSQL local, **não** Auth real Supabase/GoTrue.

## Objetivo

A gestão de equipe Prumo não pode ser confundida com o escopo gestor da concessionária. Ter o papel `gestor` em qualquer loja, ou possuir um token `authenticated` ou `service_role`, **não significa ser aprovador do RH Prumo**. Ainda não existe no contrato aprovado a atribuição de autoridade física a um responsável pelo cadastro e suspensão de empregados. Portanto a escolha segura é bloquear toda API de mutação administrativa até esse contrato.

## Implementação

Migração 046 reforça a revogação do acesso de escrita nas tabelas `public.equipe_prumo_s1` e `public.equipe_prumo_eventos_s1` para `anon`, `authenticated`, `service_role`; mantém **apenas SELECT do próprio estado** pela política existente para `authenticated`. Gatilho `s1_exigir_executor_interno_equipe` recusa UPDATE, INSERT, DELETE de equipe e INSERT no histórico quando executados com `current_user` diferente de `postgres` (executor de banco fictício), **mesmo com grants acidentais e BYPASSRLS**. SQL de teste, commits e cron existentes continuam rodando sob `postgres` no PG17 descartável.

Não foi criada API pública, `SECURITY DEFINER`, aceitação de `user_metadata`, segredo exposto, função RH ou bypass no frontend. Isso **não** concede autoridade comercial/RH a quem possuir acesso administrativo `postgres`; as operações locais são somente fixtures. Um futuro `SECURITY DEFINER` de propriedade `postgres` poderia contornar esse controle, portanto é expressamente proibido criar esse acesso antes do modelo de autorização, identidade e aprovação.

## Testes S1A-01..09

Fixtures fictícias com gestor, operador e pendente. Verificam `anon/authenticated/service_role` sem DML; leitura apenas do próprio registro; UPDATE de gestor negado; INSERT de operador negado; `user_metadata` forjado sem elevar permissões; pendente sem vista da equipe de terceiros. O ensaio concede **temporariamente** (transação integralmente revertida) INSERT/UPDATE/DELETE ao `service_role`, ativa `BYPASSRLS` nessa role sintética, e prova que mesmo assim o trigger impede alterações na equipe e eventos. Toda escrita é revertida por ROLLBACK; teste não usa tokens reais.

**Critério:** job PostgreSQL 17 completo SUCCESS e 9 marcadores PASS, além de regressões I1–I8. Antes disso, pendente [P].

## Bloqueios explícitos

- Política de aprovador RH (quem solicita, quem aprova, quem executa, evidência, revogação e supervisão) ainda [R].
- Não há servidor GoTrue/PostgREST local integrado nem prova criptográfica de assinatura/expiração JWT, sessão, `app_metadata` confiável ou revogação de sessão. `request.jwt.claim.sub` no fake auth é parâmetro local de teste, não autenticação real.
- O `service_role` real normalmente contorna RLS; trigger SQL protegido é defesa adicional **neste sandbox**, não controle completo de superusuário ou de rotinas `SECURITY DEFINER`.
- Integrações S0, visual, Meta e Banco, expediente/capacidade, rotina de backlog e auditoria LGPD exigem homologações próprias.
- Sem merge, deploy, Supabase hospedado, dados reais, assinatura real de RH nem aumento artificial do percentual global.
