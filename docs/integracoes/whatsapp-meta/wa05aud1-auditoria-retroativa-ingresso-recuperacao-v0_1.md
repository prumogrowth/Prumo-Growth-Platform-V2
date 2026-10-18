# WA-05-AUD1 — auditoria independente das etapas WA-05A e WA-05B

**Data:** 18/10/2026. **Status:** revisão e reparos sintéticos concluídos. Escopo somente da frente WhatsApp/Meta do PR #2, com leitura dos contratos compartilhados da S0; não é uma auditoria integral do código SQL/REST do PR #1, nem homologação da Meta.

## 1. Escopo, evidências e compatibilidade

Analisados `transactional-ingress.ts` (WA-05A), `recovery-journal.ts` (WA-05B), seus testes, as interfaces de HMAC/roteamento WA-01/04, `durable-receipt.ts` e o documento `interface-compartilhada-s0-meta-v0_1.md`.

- **WA-05A:** a inspeção HMAC e a revalidação de vínculo antes de inserir ocorrências em uma transação **fictícia e local** seguem compatíveis com a premissa da S0: nenhum resultado da fixture deve autorizar ACK HTTP, substituir a confirmação ACID ou enviar mensagens reais. Seus **18 testes TX** foram executados na regressão conjunta e não mostraram novo defeito reproduzível nesta auditoria.
- **WA-05B:** a recuperação por batch, leases e idempotência de efeitos **somente internos** estava funcional nos cenários anteriores, mas havia lacunas em entradas hostis e segregação do trabalhador. As correções abaixo foram aplicadas e os cenários adversariais publicados.
- O token definitivo ainda depende de verificação externa por outra pessoa. **Nenhum segredo, Supabase hospedado, Meta real, deploy ou migration foi consultado ou modificado.**

## 2. Achados reproduzidos e reparos

O laboratório de regressões temporárias reproduziu **quatro falhas iniciais** (4/4 FAIL antes do reparo), seguidas de mais uma lacuna (1/1 FAIL antes de corrigir):

| ID | Falha evidenciada | Reparo aplicado |
| --- | --- | --- |
| AUD-05-01 | Metadados com getter dinâmico podiam ter um valor validado, outro no fingerprint e outro na cópia persistida em memória | Exige descritor de dados inerte e copia a fixture **uma única vez antes da validação e do fingerprint**; `admit` e `recover` avaliam a mesma cópia |
| AUD-05-02 | Getter hostil podia lançar exceção durante `admit` ou `recover` | Negativa sanitizada `LAB_INVALID`/`LAB_MISMATCH`, sem exceção nem estado parcial |
| AUD-05-03 | `claim(owner,...)` podia reservar ocorrência de qualquer concessionária/App, sem sequer receber contexto de escopo | `claim` exige `TrustedWorkerScope` fictício, com **App + concessionária + canal** idênticos aos da ocorrência; ausência ou divergência falha fechada |
| AUD-05-04 | `finish` podia concluir ocorrência sem verificar concessionária/canal e refletir `ALREADY_DONE` a outro escopo | Também exige `TrustedWorkerScope`, verificando o escopo antes de examinar `done`, owner e lease |
| AUD-05-05 | O journal clonava e conservava campos extras arbitrários (`raw_customer_phone`, texto, etc.) fora do contrato | Rejeita campos desconhecidos do lote e de cada ocorrência **antes de clonar e armazenar**, evitando retenção adicional de dados em fixtures |

A validação de escopo também rejeita getters malformados sem exceções. **`TrustedWorkerScope` não autentica ninguém**: é um parâmetro declarado proveniente de uma futura porta interna privilegiada da S0. Até o núcleo validar realmente origem/JWT/canal e conferir privilégios, o simulador permanece não operacional.

## 3. Arquivos e provas locais

Arquivos alterados e publicados no PR #2:

- `integrations/whatsapp-meta/recovery-journal.ts` — hash Git final `5fe9168e89ae7e72e683fb3c58d94966a23c911f`.
- `integrations/whatsapp-meta/recovery-journal.test.ts` — testes RECOV-01..26 adaptados à exigência do escopo; hash `8bcb6a1e62c59f5d7ea7c0c1efe5b63a29780ec9`.
- `integrations/whatsapp-meta/recovery-audit.test.ts` — **12 testes adversariais permanentes** AUD-REC-01..12; hash `dd7993192633f791972a900c606c4072ea4d5d6e`.

Node.js `v22.16.0`: execução completa de `node --experimental-strip-types --test *.test.ts` na cópia local dos módulos Git (20 arquivos de testes, 14 módulos) → **306/306 PASS**, incluindo os **294 testes anteriores** e os **12 novos**. TypeScript `v5.8.3`: `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck --esModuleInterop --types node *.ts` → **PASS**. Hashes dos três arquivos auditados correspondem ao conteúdo versionado no GitHub.

Esses resultados **não** executaram GitHub Actions remoto, transação real, PostgreSQL, armazenamento protegido, webhook de produção ou autenticação real da Meta. A auditoria anterior cobriu 294 testes sintéticos, mas **não** incluía estas 12 situações.

## 4. Limitações e critérios para continuar

**GO** para a próxima especificação sintética WA-05C, mantendo as decisões DEC-WA-04/06 e a liberação do token como dependências.

**NO-GO** para uso operacional porque:
- O `FakeS0RecoveryJournal` é um `Map` privado e perde o estado se outro objeto for criado; `LAB_COMMITTED` não representa confirmação ACID, nem o `payload_digest` prova integridade dos bytes.
- O `FakeTransactionalInbox` não fornece transação real conjunta de **payload protegido + inbox + tarefa**, nem mecanismo de retenção/restore; simula apenas a ordem lógica das verificações. A presença da fixture `FakeProtectedPayloads` não prova cofre nem segurança LGPD.
- Um trabalhador com escopo **declarado**, mas não autenticado, não prova RLS ou autorização S0; as interfaces operacionais deverão impedir manipulação de `app_ref`, `concessionaria_id` e `canal_id` pelo solicitante.
- Os efeitos externos (Graph API, IA, envio humano/template) podem ter sido aceitos antes de uma falha de resposta. O controle de repetição do journal só cobre o contador **interno** em memória, e **nunca** autoriza reenviar externamente sem conciliação.
- `decideBatchAck()` recebe uma estrutura de recibo, mas não comprova sua autenticidade/durabilidade. **Nenhum `200` HTTP ou `DurableBatchReceipt` é gerado pelas fixtures WA-05A/B.**
- Alguns testes antigos (como TX-17) permitem mais de um resultado fictício dependendo do ponto exato de corrida; **não são prova de linearizabilidade ou atomicidade distribuída**. Essa garantia requer testes transacionais reais pela frente S0 após aprovação de ambiente.

## 5. Mapa mental

Atualizar a evidência de WA-05B e o total de testes no acompanhamento da branch `feat/s0-fundacao-prumo`. **Não acrescentar nó no primeiro diagrama Mermaid**: a inbox durável antes do ACK já representa o subsistema. Registrar estes controles como teste/auditoria, não como implementação durável ou decisão aprovada.
