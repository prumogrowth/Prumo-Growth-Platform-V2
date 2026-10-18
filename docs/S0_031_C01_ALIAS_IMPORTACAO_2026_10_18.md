# S0/031 — C01 sintético com resolvedor de aliases BR (DEC-WA-01/02)

**Escopo:** incremento aditivo e opt-in sobre as migrations 001–030, sem reescrever C01 ou C02 legados. Executável somente pelo papel SQL `postgres` nas bases sintéticas de teste. Não é API, não existe identidade Meta validada, não há prova de titularidade de telefone nem operação comercial real.

## Decisões e compatibilidade

- A regra de telefone de **cliente** é por `concessionaria_id`: o mesmo número pode existir nas lojas A/B/C, sem partilha de lead/ciclo/histórico; o **número emissor** continua único globalmente.
- DEC-WA-01: variantes brasileiras 8↔9 podem referenciar um único lead *somente com evidência móvel confiável e associação sem conflitos*. Na S0/031, `mobile_confirmado_sintetico` é uma declaração **artificial de fixture**; em produção, jamais aceitar o booleano de planilha como comprovação.
- DEC-WA-02: reutilizar `lotes_importacao`, `itens_lote`, `reencontros_lote`, `leads_loja` e `ciclos_comerciais`. Sem segundo modelo comercial.
- DEC-WA-03: idempotência de lote e uma transação para os efeitos internos. Não conectar ao inbox/outbox Meta ainda.
- DEC-WA-05: os Apps/WABAs/números da Meta pertencem a cada concessionária, segundo a decisão posterior do PR #2, não à gestora. Não é autorização de onboarding.
- DEC-WA-04 (ambiente) e DEC-WA-06 (segredos, retenção, backup e política de quarentena) continuam pendentes.

## Implementação

Migração `supabase/migrations/202610180031_s0_c01_alias_importacao_sintetica.sql` adiciona somente `prumo_private.importar_lote_identidade_s0(uuid,uuid,text,jsonb)` em `SECURITY INVOKER`, `search_path=''`, guardada por `current_user='postgres'` e por checagem de gestor vinculado à loja. Não concede EXECUTE a papéis expostos.

Formato da fixture (exemplo **não operacional**):
```json
[
  {"telefone":"+5581900001111","mobile_confirmado_sintetico":true},
  {"telefone":"+558100001111","mobile_confirmado_sintetico":true}
]
```

Cada linha com telefone válido e flag booleana é encaminhada ao mesmo `resolver_contato_s0` das migrations 028/030, com origem `IMPORTACAO_SINTETICA`. Um novo lead cria **um** ciclo; um reencontro registra a vinculação ao lote sem novo ciclo. Variantes confirmadas do mesmo número na mesma loja convergem para o mesmo `lead_id` sob trava advisory do resolvedor. Conflitos entre leads distintos e coincidências legadas sem evidência suficiente viram `itens_lote.resultado='rejeitado'` com motivos `IDENTIDADE_CONFLITANTE` ou `IDENTIDADE_EM_REVISAO`, sem fusão silenciosa.

Telefones inválidos, flags não booleanas e sinais móveis incompatíveis são rejeitados por linha, sem abortar as linhas válidas do lote. **Rejeição por linha é resultado explícito C01 e não equivalente a quarentena técnica de mensagem inbound.** Não promover rejeições automaticamente a operação bancária.

O fingerprint do lote usa marcador de domínio `PRUMO-S0-C01-ALIAS-V1|` antes do hash SHA-256 sobre JSONB. Isso impede que a operação legada com a mesma chave+payload seja reconhecida incorretamente como replay válido do novo contrato. A mesma chave e payload idênticos na nova função retorna `ALREADY_APPLIED`; payload divergente retorna `CONFLICT_IDEMPOTENCY_KEY`. As duas funções continuam internas, e o chamador não pode alternar versões de contrato silenciosamente.

## Cobertura de teste

- `supabase/tests/s0_wa_031_c01_identidade.sql`: lote misto com telefones válidos/inválidos, variantes 9→8, reencontro, repetição, conflito de chave entre implementações C01, lojas A/B independentes, continuidade C02 com variante, legado sem comprovação, dois leads conflitantes, gestor fora de escopo e EXECUTE bloqueado.
- `scripts/test_s0_wa_031_c01_concurrency.sh`: PostgreSQL descartável com duas sessões em paralelo para C01↔C02 e C01↔C01, validando cardinalidade de leads, ciclos, aliases, mensagens e reencontros.
- Ambas estão incorporadas ao `scripts/run-s0-local.sh`, que recusa bancos remotos e só opera `localhost` com nome `prumo_s0_test_*`.
- Aceite efetivo depende de CI de PostgreSQL 17 da versão de código correspondente, a registrar em `tests/S0_ACEITE.md`. Não presumir sucesso de um teste ainda pendente.

## Riscos e próximos gates

1. **Não substitui** a importação `importar_lote_sintetico` nem a entrada `receber_mensagem_sintetica`. Quem utilizar rotas legadas continuará com correspondência exata; migrar o contrato comercial exige revisão/autorização separadas.
2. Sinais booleanos da fixture não são prova Meta nem de titularidade civil. Números reciclados/compartilhados, origem da comprovação e revogação/expiração do alias ainda demandam especificação.
3. Não há consumidor que processe payload Meta real a partir de inbox, autorização do worker, retenção segura, DLQ funcional, API de serviço, segredo de produção, webhook ACK real ou disparos na outbox.
4. Permanece pendente o menor privilégio das wrappers comerciais `SECURITY DEFINER postgres` e a compatibilidade de 028–031 com Supabase Auth/REST local gerenciado. Nenhum CI pesado é disparado automaticamente.
5. Os IDs/segredos de canal da DEC-WA-05 só podem ser registrados e validados após gates próprios; nenhum emissor comercial pode ser alterado.

**GO:** próxima engenharia de integração em banco sintético. **NO-GO:** aplicação das migrations no Supabase hospedado, conexão WhatsApp/Meta real, merge, operação bancária, API pública ou produção.
