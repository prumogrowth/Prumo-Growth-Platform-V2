# E04 / S0-F03 — Aliases de identidade S0/028, versão CAS e 245 testes físicos

**Data:** 24/10/2026. **Repositório oficial exclusivo:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`. Desenvolvimento em `feat/oai-s0-f03-history-port-20261023`, PR Draft #1 contra `feat/s0-cfi01-f03-auth-preflight-20261020`, não contra `main`. E04 estritamente sintético e sem dados pessoais ou API comercial.

## Evidência verificável

[GitHub Actions #40081896755](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40081896755), commit `1b10f05e3d591377f406efcd7fb91c9c3a907556`, job `f03-pg17-disposable` **SUCCESS** no **PostgreSQL 17.11**. Logs:

- `Ran 84 tests ... OK` — **84/84** da S0 CFI-01.
- `Ran 161 tests ... OK` — **161/161** da F03, incluindo **73 testes PG17 físicos**, 24 do leitor, 31 do manifesto de histórico, 15 da ponte de autorização do HMAC e 18 testes unitários da reserva CAS.
- **245/245 PASS**, com **16 novos testes físicos de aliases** (58–73) efetivamente executados, não apenas preparados.

## Desenvolvimento implementado

O [executor local](../scripts/run-s0-f03-pg17-local.sh) passa a incluir, em banco descartável: [preparo de dois papéis NOLOGIN sem privilégios](../supabase/tests/s0_f03_alias_lab_roles_local_only.sql) exigidos pelo DDL, a **migração S0/028 existente** `supabase/migrations/202610180028_s0_identidade_aliases_sinteticos.sql`, e [gatilhos F03 de identidade](../supabase/tests/s0_f03_identity_alias_version_local_only.sql) após as fixtures de versões e catálogo/ficha sintéticos.

Os gatilhos foram ligados às **tabelas já previstas pela S0/028** `prumo_private.aliases_identidade_s0` e `prumo_private.eventos_identidade_s0`, e não a um repositório paralelo de telefones. Em INSERT/UPDATE/DELETE com mudança efetiva, `versao_identidade` do cliente na respectiva concessionária aumenta **na mesma transação de escrita**. UPDATE sem mudança efetiva ou INSERT em conflito com `DO NOTHING` não incrementa. Se uma fonte F03 ainda não foi inicializada para aquele cliente, a S0 preexistente continua funcionando e a reserva CAS permanece bloqueada pela ausência de versão.

No UPDATE, foi expressamente proibida a transferência silenciosa de um alias para outro lead/loja, assim como a troca de alias/cliente/loja de um evento de decisão de identidade. Ao inserir/alterar um evento, o gatilho verifica que a referência do alias pertence ao **mesmo lead e à mesma loja**. Os novos gatilhos têm escopo de laboratório PG17 e NÃO constituem migração hospedada.

## Testes adversariais executados

A [suíte F03 PG17](../backend/tests/test_s0_f03_pg17_integration.py) passou a ter **73 métodos físicos**, incluindo:
1. Inclusão de alias confirmado ou não confirmado invalida o vetor anterior e recusa reserva F03 desatualizada.
2. Inserção duplicada ou atualização que não muda valores não produz inflação de versão.
3. Mudança de comprovação do número, remoção de alias, inserção/alteração/remoção de evento de identidade alteram a versão.
4. Tentativa de mover alias para outro cliente ou evento para outro alias/lead é recusada com SQLSTATE `42501`.
5. Escrita em outra concessionária não modifica a versão da loja corrente.
6. A **própria função S0/028** `prumo_private.resolver_contato_s0`, chamada com número sintético e identidade exata, inseriu alias + evento, incrementou a versão e tornou uma reserva consultiva de versão antiga `STALE_REVIEW_REQUIRED`.
7. Operação da S0 sem vetor F03 ainda inicializado não falha nem concede reserva.

## Limites ainda não resolvidos

- `pendencias_identidade_s0` registra conflitos sem um cliente (lead) definido. Por não haver vínculo determinístico, **não inventar cliente para incrementar sua versão**; falta um bloqueio abrangente baseado na resolução manual ratificada pela S0 antes de utilizar o histórico em F03.
- A validade da identidade pode ser afetada por outros fluxos e por dados anteriores à migração/fixture; é necessário ratificar todas as fontes de escrita e o histórico multi-telefone antes de acesso ao conteúdo. A garantia física atual limita-se aos gatilhos cobertos e às linhas versionadas.
- Os dados de **ficha e catálogo permanecem sintéticos**, sem integração ao cadastro operacional nem aplicação real com CAS. A reserva é apenas `REVIEW_ONLY`, não é comando de modificação do cliente.
- Áudio, anexos, transcrições, política/rotação da chave HMAC e leitura LGPD de conteúdo pela IA continuam não homologados. A F01 não deve retomar atendimento após handoff humano; F02 segue independente da F03.
- Nada desta rodada habilita E05, Meta/WhatsApp real, chamadas à OpenAI, Supabase hospedado, deploy ou merge. Branch S0 de base e `main` permanecem sem alterações.

**Próxima implementação recomendada:** proteger a F03 contra **pendências não resolvidas de identidade** com um indicador de bloqueio ratificado pela S0 por cliente/loja e ciclo, sem resolver ambiguidade por conta própria. Depois conectar versões de ficha/catálogo ao futuro cadastro operacional e exigir aplicação final transacional autorizada.
