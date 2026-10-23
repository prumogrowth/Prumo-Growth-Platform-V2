# WA-42 — Revogação concorrente de chave interna e divergência dos envelopes Meta/S0

**23/10/2026 · [PR #17 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/17) · somente PG17 descartável, nenhuma alteração S1, Meta Graph ou Supabase hospedado.**

## 1. Objetivo e fronteira

A WA-41 isolou sob `prumo_s0_meta_signer_lab` a verificação da MAC interna e o consumo do nonce. Permaneceu uma corrida: o verificador lia a chave ativa sem `FOR SHARE` (porque o papel não possui `UPDATE`), enquanto `postgres` podia desativá-la. **Esta etapa adiciona serialização explícita ao caminho recomendado de revogação**, sem conceder `UPDATE` à função verificadora nem qualquer privilégio ao ingressor.

O novo arquivo `supabase/migrations/202610230046_s0_meta_key_revocation_lock_fixture.sql` altera somente o verificador Meta da WA-41 (mantendo como proprietário o papel signer `NOLOGIN`) e cria a função `meta_revogar_chave_fixture_s0(uuid)` do administrador de laboratório. Ambas adquirem a **mesma trava advisory transacional** derivada do UUID da chave. Enquanto uma assinatura aguarda a mesma chave, a revogação espera a transação anterior; se a revogação adquirir primeiro, a assinatura posterior deverá ler a chave inativa e falhar. O nonce e a evidência forense da WA40 continuam na mesma transação. **A garantia só vale se toda revogação seguir essa função**; administradores com capacidade de `UPDATE` direto na tabela podem contornar a convenção. A disciplina de acesso/rotação em produção precisa ser ratificada por Infra/S0.

**Controle de privilégios:** a função de revogação é `SECURITY INVOKER`, destinada apenas ao usuário fictício `postgres` no banco descartável; `PUBLIC`, `anon`, `authenticated`, `service_role`, S0 gateway/signer humano e os dois papéis Meta fictícios não podem chamá-la. Nada cria credencial de serviço real ou número de WhatsApp.

## 2. Provas físicas e critérios de falha

- `supabase/tests/s0_wa_046_meta_revocation_contract.sql`: **12 verificações** de proprietário não privilegiado, restrições de grants, presença da trava nos dois lados, bloqueios de alteração dos segredos, revogação idempotente e rollback da fixture.
- `supabase/tests/s0_wa_046_assert_key_revocation_race_pg17.py`: **11 verificações** com sessões PostgreSQL 17 realmente distintas. Uma sessão segura a trava da chave, a segunda tenta revogá-la e deve aparecer em `pg_stat_activity` aguardando `Lock`, e uma terceira tenta usar MAC válida. A revogação deve concluir, a terceira sessão deve ser negada com SQLSTATE 42501 e **não pode existir nonce nem registro forense dessa tentativa**. Verifica que a concessão de função permanece negada ao ingressor e que não há flags de envio habilitadas.
- `scripts/run-s0-local.sh` e `.github/workflows/wa39-s0-meta-offline.yml`: continuam rodando os testes S0 completos, WA39 (18), WA40 (25) e WA41 (16), mais as novas verificações WA42, tudo offline e sem tokens.

Os testes não provam resistência a relógios distribuídos, HMAC Meta real nem rotação de segredo na infraestrutura hospedada.

## 3. Contrato de interoperabilidade pendente — não presumir compatibilidade

As especificações examinadas no [PR Meta #2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) incluem `integrations/whatsapp-meta/wa34-service-forensic-handoff.ts` e `wa35-signed-ingress-handoff-fixture.ts`. A WA35 verifica primeiro HMAC Meta dos bytes exatos e monta o envelope WA34 de laboratório. O receptor do [PR S0 #17](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/17) **NÃO compreende esse envelope**. As diferenças são decisões abertas, não bugs a contornar com heurísticas:

| Aspecto | Emissor Meta WA34/35 | Receptor S0/044/046 | Gate pendente |
|---|---|---|---|
| Canonicalização | HMAC de `JSON.stringify(packetKeys.map(...))` com ordenação própria | HMAC de campos com separador `\|` e prefixo `prumo-meta-handoff-lab-v1` | Selecionar protocolo único, bytes/versão e vetor criptográfico compartilhado |
| Identidade de chave | Chave interna fora do packet, obtida de porta fictícia | `p_chave` UUID necessário, chave vinculada ao App técnico | Inventário/rotação de chave, mapeamento de key ID e audiência |
| Origem/audiência | `issuer='WA34_SYNTHETIC_META_INGRESS'`, `audience='WA34_SYNTHETIC_S0_READER'` | Não inclui emissor/audiência explícitos, só propósito fixo | Autenticação do processo, audiência exata, proibir troca de destino |
| IDs de concessionária e caso | `app_ref`, `concessionaria_id`, `case_ref`, `binding_revision` | App/WABA/phone **numéricos**, `canal` e `intencao` UUID, `attempt/correlation`; resolução via binding S0/041-042 | Lookup autoritativo S0: sem tomar equivalência de strings como prova |
| Nonce e tempo | `nonce_ref` alfanumérico, `issued_at_ms/expires_at_ms` | Nonce UUID, segundos UNIX, validade 30s passados/5s futuros | Definir TTL, relógio e unicidade no receptor |
| Status e evento | `event_ref` derivado de hash sintético; `provider_kind`, hash bruto Meta | `event_ref`, `kind`, `body_hash` recebido | Sem assumir que `statuses[].id` seja ID único de callback; dedupe por política ratificada |
| Flags de autoridade | Sempre falsas | Sempre falsas | Permanecer falso até sistema autorizado independente |

**Decisão técnica atual:** não converter/aceitar automaticamente WA34 → S0/044. O adaptador, quando vier, deverá ser **server-side**, autenticar a fonte, obter IDs da S0 confiável, validar versão/loja/revisão, emitir assinatura vinculada à audiência S0 e preservar nonce/rollback. Nunca assinar a partir de campos de cliente/IA nem copiar chave de App Secret como chave interna. Nenhum código de envio Graph decorre do sucesso forense.

## 4. Coordenação e aviso para S1

**Nenhuma alteração ou decisão nova da S1 é necessária para executar a WA-42.** A trava incide exclusivamente em chave interna da integração Meta e não modifica equipe, concessões, atribuições ou identidade humana. Portanto, não há nesta etapa uma solicitação imediata de desenvolvimento para encaminhar à frente S1.

**Dependência futura que deverá ser comunicada antes de implementar a operação real:** a frente S1 precisará definir quando uma alteração de atribuição/concessão/escopo de equipe invalida a autorização para uma ação **comercial**, qual a ordem conjunta de locks S1→S0 e se um callback técnico tardio pode continuar sendo apenas arquivado sem reabrir o caso. Não declarar essa parte aprovada com base em WA39–42; registrar essa decisão via responsável S1 e revisar seus contratos antes de codificar.

## 5. Critérios de parada

Os caminhos SQL WA39–42 continuam de laboratório: o wrapper de domínio ainda executa como `postgres`, `SET ROLE` não é uma credencial de serviço real, a HMAC interna não prova origem Meta, o envelope WA34 não é interoperável com S0/044 e a infraestrutura Supabase hospedada ainda não foi preparada por sua frente. **Sem merge, deploy, números reais, API Graph, IA ou ACK de webhook.**
