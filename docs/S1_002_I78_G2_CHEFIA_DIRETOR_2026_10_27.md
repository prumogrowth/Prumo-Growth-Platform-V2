# S1-002 / I78 — Gate G2: chefia única, autoridade do Diretor e ativação sem chefia

**Data:** 27/10/2026. **Branch de escrita:** `feat/s1-002-equipe-prumo`. **Código certificado:** `f8268bc35c4701a8b522a66504e080628673b11d`. Ambiente PostgreSQL 17 e integração G1/GoTrue **descartáveis**. Sem merge, deploy, alterações S0, Meta ou Supabase hospedado.

## Norma vigente versus camadas históricas

O [contrato funcional S1 vigente](S1_002_01_CONTRATO_FUNCIONAL_VIGENTE_2026_10_22.md), §§1–3, estabelece papéis visíveis **Diretor / Gestor / Consultor**. Diretoria administra cadastro, desligamento e concessões de lojas; Gestor atua sobre sua equipe sem essas competências. Um Consultor deve ter **exatamente um Gestor principal ativo** (D1), e pausa de **intake** não suspende login nem retira carteira anterior; A2 impede qualquer nova atribuição ao destino com intake pausado.

A migration histórica `202610190048_s1_gestao_equipe_pausa_global.sql` já criou índice parcial único `s1_um_gestor_ativo_por_operador` (`operador_id` WHERE `encerrado_em IS NULL`), um diretor representado tecnicamente por `s1_responsaveis_plataforma` e pares de chefia em `s1_gestor_operadores`. **O índice garante NO MÁXIMO um gestor ativo**, não pelo menos um. O uso antigo de `estado='suspenso'` e redistribuição integral em funções I11 é **superado** pelas decisões I51/I52; não promover essas funções como rotina de pausa atual.

Outro ponto: o esquema não dispõe, nesta frente, de um classificador global de cargo `Gestor` independente de já ter subordinados. A verificação conservadora da candidata reconhece o destino se existir outro vínculo de chefia ativo; isso é **restrição da demonstração**, não contrato final para um Gestor recém-cadastrado.

## Implementação I78 na S1

- `supabase/tests/s1_109_i78_g2_chefia_diretor_local_only.sql`: oito verificações, **BEGIN/ROLLBACK**; autenticação e identidades são sintéticas da fixture PG17. Reutiliza índice/estrutura/autoridade existentes sem nova migration.
- Cria **somente no schema temporário** `pg_temp.i78_transferir_chefia`, um candidato de transferência exclusivo do Diretor com CAS na relação ativa anterior; bloqueia profissional/Diretor/destino em ordem e verifica autoridade antes de alterar vínculos. Encerra o vínculo anterior e insere o sucessor na mesma transação. Não é serviço oficial, não usa JWT GoTrue nem constitui prova de duas sessões concorrentes.
- `.github/workflows/s1-002-postgres.yml`: integra a fixture ao job **PG17 oficial existente**, logo após a etapa S0/S1 I52–I74, sem workflow extra e sem modificar migrations.

### Testes confirmados

| Marcador | Evidência |
| --- | --- |
| I78-G2-01 | Índice parcial único existente e predicado de vínculo não encerrado |
| I78-G2-02 | Predicado interno de competências: somente Diretor cadastra; Gestor de outra equipe não administra Consultor |
| I78-G2-03 | Inserção física de segundo vínculo ativo é rejeitada com `unique_violation` e não altera o titular |
| I78-G2-04 | Pessoa **ativa na equipe de laboratório** sem chefia pode existir; evidencia insuficiência da cardinalidade `at most one` para garantir `exactly one`. Não é prova de onboarding real de Consultor, pois o catálogo de cargo ainda é incompleto |
| I78-G2-05 | Transferência candidata negada ao Gestor que tenta agir como Diretor; vínculo inicial permanece |
| I78-G2-06 | Transferência efetuada por Diretor sintético, com fechamento do vínculo anterior e exatamente um sucessor |
| I78-G2-07 | Requisição com relação antiga (CAS stale) é rejeitada; sem segundo Gestor ativo |
| I78-G2-08 | Sem DML direto de `authenticated` nas tabelas privadas de diretoria/chefia |

**Execução final na própria branch:** [GitHub Actions #40475205913](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40475205913), job PG17 `122091627557` **SUCCESS**, com 8/8 marcadores I78; I75B/I75C e regressões I64–I74 preservadas, `I74 6/6` e rollback das policies/objetos experimentais. Job G1 `122091627917` **SUCCESS**, revalidando I77 e seus **36 testes reais**, **272 unitários** do PR #20, histórico S0/I63 **19+19**, CFI/F02 **56**, SQL legado S1. Não se deve somar esses grupos como um único total de testes únicos.

**Intercorrência anterior (não aceita):** [run #40474811714](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40474811714) aprovou I78-01..06, mas I78-07 parou em um verificador conservador de papel Gestor **antes** do CAS: Gestor antigo não tinha mais subordinados. Corrigimos **somente a fixture**, adicionando subordinado sintético ao Gestor antigo antes da negativa stale, commit `f8268bc35c4701a8b522a66504e080628673b11d`. Não afrouxamos autoridade nem suprimimos o cenário de CAS. A execução final acima prova 8/8.

## Limites / dependências

**Aceite técnico I78: PASS de bancada; G2 continua PARCIAL.** A demonstração não converte `pg_temp` em função operacional e não torna Diretor/Consultor autenticados via GoTrue. Os bloqueios documentados em [Issue #23](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/23) são:

1. Cadastro e ativação transacionais: impedir que um Consultor elegível em operação fique ativo **sem chefia principal**; admitir cadastro pendente separado de ativação. A identificação de cargo é necessária para aplicar a regra apenas ao Consultor.
2. Cargo Gestor canônico independente da existência de subordinados, e papel Diretor derivado de identidade confiável (JWT/sessão e autoridade de serviço).
3. API administrativa de criação/desligamento/grants do Diretor e operação de transferência de chefia versionada, atômica, com auditoria append-only e provas reais de corrida/revogação.
4. UI e fluxos de gestão, incluindo pausa de **intake**, retomada, transferência manual de casos e acessos supervisionados, sem reabrir A2 ou confundir pausa com suspensão da conta.
5. Homologação integrada S0/S1 com usuário real de teste, revogação de sessão e permissões, além do eventual provisionamento de funções privadas para produção.

**Próximo desenvolvimento recomendado:** I79/G2 — especificar/certificar um contrato de identidade/cargo/chefia em laboratório que não deduza `Gestor` da posse atual de subordinados; depois compor um gateway autenticado para Diretor sem reimplementar S0. Não alterar S0 oficial nem atribuir percentual de conclusão global com base nestes testes.
