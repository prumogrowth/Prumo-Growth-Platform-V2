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


## Resultado executado I9 — PostgreSQL 17 descartável (19/10/2026)

[**CI #39230800805 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39230800805); commit ensaiado `4a83f82b71d2dd72e8640cfc0b4e8851e1690019`; job `117987994582`. Logs auditados: **S1A-01..09, 9/9 PASS**. Confirmados leitura RLS apenas do próprio estado, proibição de mutação de equipe por gestor/operador, metadados de teste sem elevação, acesso `service_role` recusado **mesmo quando recebe artificialmente GRANT e BYPASSRLS**, eventos RH inalterados e inserções legítimas pelo executor interno do banco. Regressões PG17: S1H 8/8, S1SC 4/4, S1E 7/7, S1R 9/9 em três passagens, S1X 7/7 em duas passagens, S1C 5/5, S1D 5/5, S1Q 10/10 em duas passagens, S1QC 4/4, S1B 10/10 em duas passagens, AUD1 7/7 e AUD2 5/5. A exceção esperada `PROFISSIONAL_PRUMO_INELEGIVEL` nos ensaios negativos não constitui falha do job.

**Limitação explícita:** esse teste é role/PostgreSQL local com `auth.uid()` simulado por `request.jwt.claim.sub`. Não houve JWT criptograficamente validado, login GoTrue, chamada PostgREST, revogação efetiva de sessão nem homologação da autoridade administrativa. O administrador definitivo de RH segue [R] para decisão humana futura; não foi assumido por gestor de concessionária. Nenhum dado real, merge ou implantação.

## Errata normativa I9 → I10 — autoridade decidida em 19/10/2026

O bloqueio I9 era correto **como barreira técnica provisória**, mas a redação anterior sugeria que o papel do gestor não tinha qualquer autoridade administrativa. **A decisão de negócio expressa posteriormente a substitui nessa parte:** `responsavel` é o único autorizado a **adicionar operador ou gestor e efetuar desligamento definitivo**. `gestor` pode **administrar operadores preexistentes de suas lojas**, inclusive mover atendimentos, redistribuir carteiras, suspender e reativar temporariamente; não pode adicionar usuário novo, efetuar desligamento definitivo, modificar um responsável ou assumir poderes de outro gestor. `operador` não administra equipe. Ver [contrato I10](S1_002_I10_AUTORIDADES_RESPONSAVEL_GESTOR_2026_10_19.md).

A migration I9 **continua bloqueando DML direto** de `authenticated/anon/service_role`. Isso **não revoga as permissões comerciais decididas**: exige que as futuras operações sejam comandos autenticados específicos com verificação por concessionária, privilégio, caso e auditoria. A implementação física de suspensão por loja **não pode** ser apenas `equipe_prumo_s1.estado='suspenso'`, pois esse campo é global à Prumo e afetaria outras lojas; precisa de revogação/pausa de escopo da própria loja compatível com RLS S0, e regra de reativação que não seja inclusão de profissional novo. Enquanto esse contrato interfrentes não for implementado, **não atribuir incorretamente "implementado" ao comando de gestor**.


A regra I11 define **gestores por equipe, não concessionária** e pausa temporária global do operador sob chefia; concessões de lojas continuam exclusivas dos responsáveis. O bloqueio I9 permanece para API externa, não proíbe a autoridade operacional aprovada de gestor em futuro backend autenticado.
