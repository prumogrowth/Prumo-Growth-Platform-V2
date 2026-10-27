# Encaminhamentos necessários — para revisão do Codex principal

Propostas não enviadas a outras frentes. S0/S1 têm responsabilidade conjunta no principal: **nenhum pedido de implementar identidade/chefia/autoridade é dirigido novamente à antiga conversa S1**. A I79 vigente deve ser consultada antes de qualquer execução.

## H01 — mapa de proveniência e handover F01/F03/F02

**Destino proposto:** responsáveis F01/F03/F02, com coordenação do principal. **Gate/contrato:** G03/G07; `OAI_E04_F02_S0_INTEGRATION_HANDOFF_V1.json`, `ClaimedS0Evidence`, A16.

**Evidência já existente:** F02 `dc18e410…`, CI 40480580349; produtores F03/C08/origem/intenção e mapa E08; PR #18 `88af4aea…` autentica contexto, porém armazena testemunhas alegadas. O pedido não é desenvolver novamente esses produtores.

**Lacuna comprovada:** falta identificar o objeto canônico de cada prova e o evento físico de passagem humana; hashes isolados não permitem ao registro S0 verificá-los.

**Solicitação única:** devolver uma tabela com produtor já existente, objeto/ID, canonicalização/hash, chave/versão/verificador, escopo loja/lead/caso/encerramento/canal, cutoff/ordenação, revisão/completude, regra de revogação e negativos existentes. Para F03, explicitar versões de caso/ficha/atribuição distintas de ciclo e apontar a fonte autorizada/minimizada. Para F01, apontar evento, causalidade e ordem; não pedir novo mecanismo de fechamento.

**Responsabilidade:** frentes informam seus contratos/produtores; principal escolhe mapeamento e eventual adapter S0. **Aceite:** cada prova resolvível sem confiar em digest do chamador; ausência/cutoff/escopo trocado recusados; cenário integrado proposto com fontes atuais. A resposta continua revisão técnica, sem atestar cancelamento Meta ou aprovação humana.

## H02 — consolidar pendências Meta já abertas, sem duplicar solicitações

**Destino proposto:** principal S0/S1 reúne Meta/Infra/Segurança e Produto/Privacidade. **Gate/contrato:** G05/G06; DISPATCH-01/02, ACK-03, LOCK-04, TEMPLATE-CATALOG-05, decisões C1–C7/T1–T6 existentes.

**Evidência já existente:** PR #14 `31bb84fa…`, CI 40370618576; catálogo candidato `d453a22f…`; observação por ID/paginação e replies dos PRs #21/#22/#24/#25 são offline. O principal já tem a análise de adaptação e a composição forense experimental.

**Lacuna comprovada:** registro F02 não possui fonte autenticada de opt-out/consentimento/disposição/template; contratos de reserva/M2M/ACK/locks não estão ratificados.

**Solicitação consolidada:** na revisão que já está aberta, apontar a fonte e a revisão de cada gate, identidade técnica e ACL do append, semântica de durabilidade/ACK, observação incerta e regras de conciliação. Adicionar somente a relação desses estados com G05 e a nova chefia I79. Não pedir outro catálogo, webhook, classificador, emissor de fixture ou nova execução WA39–WA68.

**Responsabilidade:** principal define composição transacional; Meta/Infra custódia e observação externa; Segurança principal técnico; Produto/Privacidade regras de contato e retenção. **Aceite:** decisões/fonte/versão explícitas, negativas por tenant/rota/replay, incerteza preservada e plano de corridas físicas aprovado. Credenciais reais/Graph/produção continuam fora desta autorização.

## H03 — política de tempo e dados

**Destino proposto:** Produto/Privacidade, consolidado pelo principal. **Gate/contrato:** G06; janela `ReviewWindow`, C6, T5 e D3 de lookup.

**Evidência já existente:** PR #18 usa clock DB, prazo voluntário e tombstones; F02 tem 48h e 24h–7d explicitamente experimentais; I79 preserva dependências de mídia/D3/D4/retenção.

**Lacuna comprovada:** nenhum desses mecanismos determina duração de negócio nem retenção por classe. **Solicitação:** definir tabela por classe de dado com finalidade/base legal, campos necessários, acesso, TTL/default/máximo quando aplicável, política/versionamento, retenção/expurgo e conservação mínima de tombstone/idempotência. Distinguir prazo do pedido, validade de decisão, janela Meta e retenção.

**Responsabilidade:** Produto/Privacidade decidem; Infra garante clock/disponibilidade; principal implementa. **Aceite:** política aprovada e rastreável sem extrair regra de fixture, incluindo comportamento depois de apagamento e sem ressuscitar pedido terminal.

## Sem encaminhamento imediato ao Frontend

O HEAD da branch visual consultado foi `8c9498d72cf9551edc50d7f0da8d15c48049e835`; a branch posterior FV-UX-01, `4f03396467a9ce6fc927671a8b4b66a3ea101e79`, também foi conferida documentalmente. A conciliação CFI segue candidata; FVA-02 e FV-UX-01 mantêm demonstração local sem transporte/autenticação operacionais (E13). D1–D4 UI já estão registrados pelo S0. Pedir tela, autenticação ou lookup agora duplicaria dependências ainda não decididas pelo principal.

Depois de resolver G01/G02/G04, o principal poderá consolidar **uma** proposta UI com contrato/resultados/versionamento já revisados, erros/recovery sem segredo e critério de uma confirmação em sandbox autenticado. Isso é condição futura, não uma solicitação de implementação enviada nesta auditoria.
