# WA-16 e WA-17 — fechamento da rodada de validação e pausa para alinhamento

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 20/10/2026. **PR de implementação:** #2, branch `docs/whatsapp-meta-concessionária de demonstração-poc-20261017`, mantido **Draft**. O responsável determinou pausa após esta rodada para esclarecer decisões, auditar o conjunto e reorganizar a documentação **antes de prosseguir para novas frentes**.

## Resumo verificável

| Escopo | Testes presentes no repositório | Execução independente nesta rodada | Execução nativa de CI do código atual |
|---|---:|---|---|
| WA-16: classificador de leitura após COMMIT incerto | 10 `node:test` | **10/10 verificações comportamentais V8 PASS** sobre funções reais com tipos TS removidos | **não confirmada** |
| WA-17A: catálogo de texto, submissão e fontes variáveis | 18 `node:test` | **16/16 verificações comportamentais V8 PASS** sobre funções reais com tipos TS removidos | **não confirmada** |
| WA-17B: templates multimídia e contratos MCP documentais | 16 `node:test` | **16/16 verificações comportamentais V8 PASS** sobre funções reais com tipos TS removidos; URL em parser simplificado | **não confirmada** |
| WA-16B/C: simulações ROLLBACK/COMMIT-resposta-ocultada, nova sessão, JSONB→TS | 11 verificações SQL `WA16P-01..11`, mais integração DB→TS | inspeção estrutural anterior confirmou arquivos, comandos e gates | **0/11 comprovados em PostgreSQL 17 nesta revisão** |

**Total: 44 testes nativos `node:test` escritos e identificados por IDs.** Nesta rodada foram executadas **42 verificações próprias** de comportamento em V8, mas **não os 44 testes originais** e **não os testes SQL**. Não chamar 42/42 de aprovação oficial do `node:test` ou CI. A validação WA-16 anterior em PostgreSQL permanece pendente, embora a WA-15C/WA-06D tivessem gates verdes de commits anteriores.

## Evidência de inspeção e smoke testing

Foi recuperado o conteúdo atual dos módulos diretamente do GitHub e executada sua lógica de funções em V8, removendo explicitamente apenas anotações TypeScript necessárias. No módulo WA-17B, a validação de URLs foi exercitada com um analisador de URL reduzido, **não a implementação nativa de `URL` do Node**.

- WA-16: leitura exata, ausente, conflitante, flags `retry_external/ack_allowed/production_authorized/delivery_confirmed` invariavelmente falsas; retorno inválido e dados forjados recusados; **10 casos de fumaça PASS**.
- WA-17A: rascunho manual, payload de revisão sem rede, recibo sem aprovação, status vinculado ao ID Meta, mapeamento e revisão, valores ausentes, fonte desautorizada, versão nova, isolamento entre concessionárias, campos inesperados e getter hostil; **16 casos de fumaça PASS**.
- WA-17B: origem de autoria por IA/humano, cabeçalhos de imagem/vídeo/documento/texto, botões URL/telefone/resposta rápida, variáveis no corpo e URL, caminhos e hosts inválidos, formatos reservados, ausência de autorização para disparo, contrato passivo de ferramentas MCP; **16 casos de fumaça PASS**.
- `mcp-template-tools.v0.json`: **12 operações de interface definidas**, nomes distintos, sem `principal_id`/`access_token` aceitos como argumentos de ferramentas. O servidor MCP é da **outra frente**; esta frente não implementa protocolo/transporte/servidor MCP.

Esses resultados são evidências úteis de comportamento, **mas inferiores a uma rodada de Node/PG17 oficial**; não substituem a prova SQL, rede ou serviço.

## Gate CI preparado para execução quando GitHub Actions permitir

O workflow `.github/workflows/whatsapp-meta-offline.yml` foi atualizado no commit `19f51da3869a9a087766fe735f6b5e0ed6b276b6` com etapa dedicada:

```bash
node --experimental-strip-types --test --test-concurrency=1 \
  integrations/whatsapp-meta/s0-unknown-commit-recovery.test.ts \
  integrations/whatsapp-meta/template-catalog-control.test.ts \
  integrations/whatsapp-meta/template-mcp-multiformat.test.ts
```

O gate exige `# tests 44`, `# pass 44`, `# fail 0` antes de executar a regressão integral `run-offline-tests.sh --all`. O job PostgreSQL cruzado mantém a etapa WA-16/WA16P após WA-15C, com sessões SQL independentes.

**Bloqueio observado:** a ação do GitHub que lista os workflows associados aos commits da WA-16/17 **retornou lista vazia mesmo após a nova alteração do workflow**. A causa (limite de minutos, restrição de Actions, agendamento, configuração do repositório ou outra) **não foi comprovada**. Não inventar justificativa nem run ID. Também não havia PostgreSQL 17 executável no ambiente local desta rodada. Não foram executados comandos contra Supabase hospedado.

**Estado correto:** WA-16 e WA-17 estão **implementadas e verificadas parcialmente, mas não homologadas pelo CI atual**. Nenhum acesso a Graph, Meta, disparos, templates reais, banco ou produção. Todos os PRs continuam Draft.

## Congelamento de escopo para próxima conversa

Por determinação do responsável, **não iniciar novos recursos** depois deste fechamento. Prioridade do próximo encontro:
1. Alinhar dúvidas/decisões que exijam resposta do responsável, sem presumir que tudo esteja definido.
2. Fazer auditoria geral de requisitos, contratos, documentação, divisão de frentes, implementação e evidências de testes.
3. Revisar e organizar documentação, corrigindo divergências e duplicações encontradas; manter decisões novas prevalecentes (MCP de outra frente, IA pode gerar templates sob delegação).

**Pendente para liberar a auditoria como “CI verde”:** identificar a causa de ausência de Actions, executar os 44 testes nativos e WA16P/DB→TS no PostgreSQL 17 isolado, inspecionar logs e corrigir os erros. Não dar continuidade silenciosa ao desenvolvimento enquanto a equipe está na etapa de alinhamento.
