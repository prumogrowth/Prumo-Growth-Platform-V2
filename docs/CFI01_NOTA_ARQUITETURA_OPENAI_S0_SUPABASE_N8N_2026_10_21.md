# CFI-01 — Decisão ainda aberta: canal OpenAI/S0, Supabase e n8n

**21/10/2026 — nota de delimitação arquitetural. NÃO é ratificação do responsável, migration ou deploy.**

## O que está definido versus ainda pendente

- **[D] S0** é a autoridade sobre identidades, sessões, concessões por concessionária, caso e atribuição, oito estados comerciais, fechamento humano, aplicação/validação de campos, prova bancária, auditoria e transações. Nem F03 nem n8n podem promover decisão do modelo a direito de gravar. A IA sugere/extrai; S0 confere e decide.
- **[D] Supabase/PostgreSQL** já foi escolhido como base técnica exclusiva da implementação S0 atual (projeto técnico Prumo Growth - Platform), e é exercitado em laboratório GoTrue/PG17. Essa escolha **NÃO** implica acesso SQL direto do modelo OpenAI ao banco.
- **[P] Backend S0** é a fronteira recomendada para as chamadas de captura/rechecagem/aplicação: identidade verificável, perímetro restrito e transações server-side. Não dar a modelos credenciais de banco, service-role ou funções privilegiadas.
- **[R] n8n como intermediário entre OpenAI e Supabase**: **NÃO HÁ DECISÃO DEFINITIVA** de presença/ausência ou de topologia. O n8n é candidato para automações, webhooks, filas, agendamentos, retries e integrações Meta, sem ser fonte de verdade e sem substituir permissões da S0.
- **[D relatado em documentação 17/10]** n8n não havia sido contratado. Preparar S0, migrations, Auth/RLS e testes **não depende de n8n**. Não contratar sem avaliação e autorização.
- **[R] Distribuição técnica final** de chamadas modelo↔backend, jobs, n8n, filas e SQL deve ser avaliada na sessão de decisão conforme criticidade, latência, idempotência, observabilidade, LGPD, operação e custo.

## Topologia conceitual, não aprovada para produção

```text
OpenAI / F01-F02-F03 (interpretação, extração, proposta)
                 ↕ serviço/orquestração [distribuição PENDENTE]
         Backend e autoridade S0 [invariante]
                 ↕ operações restritas/transacionais
          Supabase Auth + PostgreSQL

n8n [OPCIONAL / PENDENTE]: aciona automações e solicita tarefas ao backend;
não deve substituir a autorização S0 nem possuir acesso SQL privilegiado
por conta de uma proposta do modelo.
```

Os scripts `backend/s0_cfi01_*.py` do PR #12 testam **servidor backend→GoTrue/SQL** com usuários e casos fictícios. **Não representam OpenAI→Supabase diretamente**; o n8n não participa desta prova. A falha atual do SQL owner atômico em Supabase Auth/REST (run #39626744578, `DENIED` após warnings de privilégio em `auth.sessions`) é questão de autorização do backend S0, independente da seleção do orquestrador. O PG17 isolado (run #39626726094) passou 70/70 físicos e 133/133 unitários. Não declarar o gate GoTrue+atomic aprovado até corrigir e rerodar.

## Fontes do projeto

- `11_Arquitetura_Geral_Consolidada_v4_8.md` §9: quadro **[P]** com backend, Supabase/PostgreSQL, n8n e OpenAI; distribuição final não escolhida.
- `04_Dados_Integracoes_e_MCP_v4_6.md` §9: integridade/decisões em backend/Postgres, n8n apenas potencial orquestrador.
- `43_Playbook_Inicio_Tecnico_GitHub_Supabase_Custos_n8n_v0_1.md` §6: contratação de n8n adiada e só justificável em marco de integrações reais.
- `projeto_liberacred_consolidacao_ideias_v0_2_auditada.md` §6 e §14.3: orquestrador determinístico; plataforma completa modular; infraestrutura não rigidamente congelada no estágio de ideias.

**Consequência para engenharia imediata:** continuar corrigindo S0/CFI01 sem introduzir dependência obrigatória de n8n nem modelar acesso SQL direto da OpenAI. Levar topologia para a conversa do responsável como decisão **[R]**. PR #8 e PR #12 continuam Draft, sem merge/deploy.
