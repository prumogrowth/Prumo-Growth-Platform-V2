# Prumo — onde estão o código e o banco (17/10/2026)

## Inventário verificado

| Ambiente | Estado atual | O que a verificação comprova |
|---|---|---|
| GitHub privado `prumogrowth/Prumo-Growth---Platform` | Migrações versionadas **001–006 e 008–022**, funções e testes na branch `feat/s0-fundacao-prumo`, PR #1 **DRAFT** | Código-fonte proposto, sem merge |
| PostgreSQL descartável no GitHub Actions | Recebe migrações e dados **inteiramente fictícios** a cada teste `s0-postgres` | Regressões SQL, permissões de papéis simulados e concorrência |
| Supabase local efêmero GoTrue/PostgREST no GitHub Actions | Recria projeto local, aplica migrações candidatas e testa JWT/RLS/REST | Integração Auth/REST de sandbox, sem conta comercial |
| Supabase hospedado `Prumo Growth - Platform` | Consulta de **17/10/2026**: **nenhuma tabela comercial em public e nenhuma migração comercial registrada** | Ainda não está implantada a fundação comercial no banco remoto |

O projeto Supabase hospedado já foi provisionado anteriormente, vinculado à conta conectada, e recebeu um ajuste de segurança administrativo: restrição de EXECUTE da função `public.rls_auto_enable()` a papéis apropriados. Isso **não** corresponde à implantação das migrações do domínio. Não dizer que absolutamente nenhuma mudança administrativa ocorreu no Supabase.

## Processo recomendado antes de qualquer migração hospedada

1. Manter o PR em rascunho e testar o SQL em PostgreSQL descartável; corrigir regressões com novas migrations versionadas.
2. Executar a suíte integrada Auth/REST no marco de validação C07 **uma vez** mediante etiqueta `run-auth-integration`, com limite de 12 minutos. É um teste local; não é comando de deploy.
3. Revisar uma lista definitiva e ordenada das migrações candidatas (007 foi retirada antes de implantação), objetos `public`, índices, gatilhos, `prumo_private`, RLS, grants e funções com `security invoker`.
4. Analisar autenticação real do backend, ausência de conta de serviço no navegador, dados D3/D4, LGPD, políticas de exclusão/retenção, backup/restauração e taxas/limites do plano gratuito.
5. Somente após aprovação humana **específica** preparar uma migração para ambiente homologável. Separar autorização para banco de homologação de autorização para produção comercial.
6. Registrar evidências de migrations aplicadas, RLS via API, teste de isolamento A/B/C, rollback/recuperação e observabilidade antes de movimentar clientes reais.

**Restrições imutáveis:** telefone do cliente pode existir em várias concessionárias; emissor da plataforma é exclusivo por concessionária; não há auto-reenvio após incerteza, nem status `perdido` sem prova real exigida. Nenhuma integração Meta/Banco/OpenAI é ativada por simplesmente aplicar migrações.

**Gate de hoje:** desenvolvimento e testes locais autorizados; **merge e implantação comercial remota não autorizados**.

## Marco de validação C07 — 17/10/2026

Executado **uma única vez** o fluxo integrado GoTrue/PostgREST [#39079580129 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39079580129) com Auth-01..11 PASS, aproximadamente dois minutos de tempo decorrido. A etiqueta de acionamento foi retirada. Isso verifica a arquitetura no **Supabase local descartável**, não significa aplicar as migrações no projeto hospedado. O próximo gate segue sendo aprovação específica para homologação/implantação, após plano de retenção, backup, backend autenticado e decisão de segurança.
