# Prumo — decisões e portões S0 (17/10/2026)

| Recurso | Situação |
|---|---|
| GitHub | Free privado, sem previsão de upgrade |
| Supabase | Free em ambiente exclusivo, projeto `projeto-supabase-omitido`; Pro ~US$25/mês planejado quando exigido |
| n8n | não contratado; avaliar em S2 |
| OpenAI API | pendente; simulações primeiro |
| WhatsApp Meta | pendente de canal, políticas, opt-in/out e homologação |
| instituição financeira | integração/autorizações reais pendentes; remessas humanas comprovadas |

## Decisão posterior de 17/10/2026
**Regra esclarecida:** mesmo cliente pode contatar A, B e C, com registros independentes e RLS por loja. O número **emissor da Prumo** não pode ser compartilhado por concessionárias; já possui índice UNIQUE global. Migração 007 errada foi excluída antes de qualquer deploy. Consulte `docs/REGRA_NUMEROS_ATENDIMENTO_CLIENTE_2026_10_17.md`. O documento da interpretação global do cliente está retratado.

## Portões
1. Fonte vigente: 00A, 13A, 21–23, 41. Documento 01 é histórico e não determina implementação.
2. Ensaiar esquema/RLS/grants com dados A/B em Postgres **descartável** antes de qualquer deploy.
3. Gestor lê conversas D2 próprias; não recebe D3/D4 brutos por supervisão. A escrita de operador exige caso atribuído, ainda não implementado em S0.
4. SQL/migrações requerem revisão em branch e aceite técnico; **NÃO implantar remotamente automaticamente**.
5. Supabase Free remoto é desenvolvimento, nunca produção sem os portões aplicáveis.
6. Operação real depende de GO/NO-GO humano por capacidade e validação Meta/Banco/LGPD. Nenhuma assinatura é feita automaticamente.

**Estado:** branch S0 publicada em PR draft #1. Testes limitados de isolamento A/B aprovados em PostgreSQL 17 descartável ([CI PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39059980947)). Transações sintéticas, casos e testes de isolamento foram ampliados, mas Auth/REST real, recuperabilidade, integrações e revisão humana permanecem pendentes. Nenhuma migration foi aplicada ao Supabase remoto.
