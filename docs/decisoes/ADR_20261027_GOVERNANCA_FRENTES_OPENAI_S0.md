# ADR — Auditoria e edição entre frentes OpenAI (F01/F02/F03) e S0
**Decisão do responsável do projeto: 27/10/2026.**
- **Nossa frente OpenAI** é responsável por auditar e corrigir F01, F02, F03, S2, prompts e lógica de IA; comparações F01↔F02↔F03 são nossas, não uma tarefa a delegar à S0.
- **S0 é de outra frente.** Podemos ler, investigar, comparar e auditar S0 diretamente, **sem solicitar que a S0 faça auditoria de leitura**. Código, contratos, migrations, permissões, RPCs, identidade e artefatos de propriedade S0 **não podem ser alterados por nós**. Se a análise provar necessidade de mudança S0, encaminhar achado técnico preciso à frente S0 com prova, alteração pedida e aceite.
- Arquivos com prefixo `s0_f03` podem envolver lógica F03, mas sua origem/autoridade transacional permanece S0; distinguem-se correção de lógica OpenAI própria e alteração de portas S0.
- Auditoria não é ratificação do contrato S0, autorização humana/comercial ou permissão para deploy. Sem merges, Supabase remoto, chamadas OpenAI/Meta reais. Continua vigente a arquitetura alvo Supabase backend + OpenAI API direta, n8n opcional (Issue #27).
- Referência de auditoria aplicada: `docs/OAI_E04_F01_F02_F03_S0_AUDITORIA_CONTRATOS_20261027.md`.
