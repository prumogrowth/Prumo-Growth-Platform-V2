# M08 — Lote físico multicanal, atomicidade e ACK (31/10/2026)

**Estado:** ensaio técnico Meta↔S0 em PG17 descartável APROVADO; ratificação operacional S0/Meta/Infra AINDA PENDENTE. **Sem endpoint HTTP, sem POST/Graph reais, sem S0 produtiva.**

## Evidência executada

**CI original:** [run 41189393878](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41189393878). **CI após auditoria e correções:** [run 41194019498](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41194019498), código Meta `dd27a01d6a44bd8496d52d9cc2455c8b5752f886`, fonte S0 física **somente leitura** `01ffdb093013664b73b18d23f92aac2202578210`.

**Execução Meta:** `integrations/whatsapp-meta/lab/emit-s0-physical-receipt.py` e `verify-s0-physical-receipt.mjs`. A suíte completa Meta aprovou **1.210/1.210 testes offline**; o job de interoperabilidade executou **18 verificações do recibo físico S0/PG17**, mais verificações no produtor S0.

Com um **único POST artificial** contendo dois WABAs/números da **mesma App e tenant** e quatro ocorrências (duas mensagens, dois status):

- HMAC Meta original sobre bytes físicos foi validado por consumidor Meta, independentemente do S0; digest do POST e contagens foram comparados com recibo S0 assinado por Ed25519.
- O S0 armazenou uma única transação PG17 e um único lote, quatro ocorrências, bytes originais idênticos, com readback pós-commit.
- Cinco lotes assinados com um canal válido e outro inválido foram **inteiramente rejeitados**, sem persistir canal válido isoladamente: outro tenant, outra App, canal desconhecido, evento tardio malformado e canal não autorizado por grant, mesmo sendo da mesma App e tenant.
- Replay do **mesmo nonce** foi rejeitado; pedido autenticado de `recover` com **novo nonce** recuperou o **mesmo** recibo assinado; mesmo batch ref com bytes diferentes foi `CONFLICT` sem segundo lote.
- Consumidor Meta negou integralmente a visualização de lote após HMAC alterado, canal revogado, migração fictícia de WABA para App externa ou alteração de bytes.
- O preflight multicanal ficou `SIGNED_MULTI_CHANNEL_UNRATIFIED`; **todos os flags de ACK, partition, persistência declarada, produção e efeito comercial permaneceram falsos**.

## Limites da prova

- A chave HMAC ASCII do ensaio foi gerada aleatoriamente em memória pelo laboratório S0, disponibilizada ao leitor Meta por **um arquivo privado de trust de laboratório separado do recibo** (ambos modo 0600), excluído no término do job. **Atenção:** os dois artefatos são gerados pelo mesmo produtor sintético, portanto a confiança de produção ainda exige chave/registro de S0 independentes e ratificados. Isso é demonstração controlada, **não custódia de segredo ou identidade operacional homologada**.
- O laboratório usa App, tenant, canais, M2M e chave Ed25519 sintéticos e controla recursos PG17 descartáveis. S0 não foi alterada.
- A prova física **não** valida o caminho HTTP externo, nem determina 200, retry, timeout real, fila produtiva, M2M fora do laboratório, deploy, escrow, monitoramento, consentimento ou LGPD em produção.
- A prova M08 não eleva ACK nem legitima particionar um POST. M07-D, M08-D e M27 continuam abertos. Ver [auditoria canônica M07/M08](AUDITORIA_M07_M08_2026-10-31.md) e [pendência formal M08-D](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/3).

## Decisões pendentes para o futuro canal entre frentes

- [ ] **S0 + Meta + Infra:** ratificar a definição de **um POST físico = uma unidade transacional integral**, política multicanal mesma App + mesmo tenant + grants explícitos, sem ACK parcial; decidir casos futuros de assinaturas, tipos novos, canais desconhecidos e quarentena.
- [ ] **S0 + Infra:** ratificar versão do contrato durável, readback, M2M, chave S0 confiada/rotacionada e revogada, autoridade de `recover` e tratamento de nonce/replay sem aceitar duplicação indevida.
- [ ] **S0 + Meta + Infra:** decidir estados de transporte HTTP e protocolo de repetição após `PENDING_RECONCILIATION`, `CONFLICT`, rejeição e resposta perdida. `ACK_ELIGIBLE` é **estado lab**, não código HTTP 200 externo.
- [ ] **Responsáveis:** aprovar matriz de testes positiva/negativa com requisitos de segurança, execução observável, limite de payload, isolamento por tenant e cenário real homologado.

**Encaminhamento:** anexar este documento à futura comunicação entre frentes. Não aguardar uma decisão para continuar outros desenvolvimentos offline da Meta; nenhuma conclusão aqui implica aceite por silêncio.
