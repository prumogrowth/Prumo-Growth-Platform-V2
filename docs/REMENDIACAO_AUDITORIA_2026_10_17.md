# Prumo — correções pós-auditoria (17/10/2026)

## Segurança do Supabase remoto — executado

Projeto exclusivo: `Prumo Growth - Platform` (id `projeto-supabase-omitido`).
A função pré-existente `public.rls_auto_enable()` retorna `event_trigger` e é usada pelo gatilho `ensure_rls`. Era `SECURITY DEFINER` e tinha EXECUTE herdado pelos papéis da API.

Ajuste DCL aplicado no remoto:

```sql
revoke execute on function public.rls_auto_enable()
 from public, anon, authenticated;
```

Consulta de verificação: `anon_execute = false`, `authenticated_execute = false` e `postgres_execute = true`.
Nova chamada ao `get_advisors(type='security')`: **zero avisos**.
Nenhuma tabela ou migration comercial foi aplicada ao projeto remoto. A função e o event trigger foram preservados.

Referência Supabase: https://supabase.com/docs/guides/database/functions

## Fundação S0 candidata, ainda não implantada

- Migrations 001/002: lojas, identidades, vínculos, leads, ciclos, oito status, isolamento inicial.
- Migration 003: canais sintéticos, lotes, itens, reencontros, eventos de status, casos, atribuições, conversas e mensagens.
- Migration 004: leitura D2 do gestor em todas as conversas da loja; operador limitado ao caso ativo; resposta simulada por operador vinculado e designado, sem envio real.
- Migration 005: FKs compostas para preservar correspondência de lead/ciclo/caso, mesmo dentro da loja.
- Suíte: IDs sintéticos de A/B, dupla atribuição negada, reimportação, mensagem duplicada, gestor vs operador, autoatribuição e revogação.

IMPORTANTE: esquema S0 sintético não representa implementação de remessa real, integração Meta, cadastro financeiro D3/D4 ou MCP. Esquema/exemplos ainda passam por revisão de segurança e teste Supabase Auth real antes de deploy remoto.

## Portões ainda abertos

Autenticação e RLS sob Supabase Auth real, atomicidade de transições e interface transacional de importação/atribuição, proteção por campos para D3/D4, auditoria imutável com evento servidor, aprovação de retenção LGPD, teste de backup/restauração e autorização humana para qualquer deploy. S1–S4 seguem bloqueadas para uso real. Sem contratação nesta rodada.
