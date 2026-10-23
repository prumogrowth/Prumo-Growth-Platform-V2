# WA-32 — Webhook assinado e correlação forense estrita com tentativa S0 (offline)

**22/10/2026 · [PR #2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · Escopo exclusivo WhatsApp/Meta.** Continuação das [WA-29](./wa29-claim-unico-pre-despacho-revogacao-concorrente-pg17-2026-10-22.md), [WA-30](./wa30-recuperacao-envio-incerto-ledger-offline-pg17-2026-10-22.md) e [WA-31](./wa31-evidencia-tardia-pos-revogacao-forense-pg17-2026-10-22.md). **Nada disso cria endpoint ou porta autenticada S0 real.**

## Objetivo e implementação

A WA-31 provou que podemos **arquivar sinais sintéticos tardios após revogação**, mas não atestou a origem externa. A WA-32 encadeia, em memória e sem rede, a **verificação HMAC-SHA256 já existente** em `routed-webhook.ts` com uma **porta de consulta S0 fictícia** que procura a tentativa por App, concessionária, canal, WABA, número remetente Meta, `wamid` e destinatário exato. Nenhuma correspondência por número de cliente normalizado, por `wamid` isolado ou por identificador de App declarado no corpo é admitida.

- `integrations/whatsapp-meta/wa32-signed-status-s0-forensic-bridge.ts`: usa `inspectRoutedMetaPost` com credencial selecionada por **rota confiável**. Não aceita mensagens inbound como recibos de status. Faz `LOOKUP` e `RECHECK` da tentativa sob portas S0 injetadas; recusa linhas duplicadas/ausentes, tipo malformado, tenant/canal/ator de correlação incompatível, revisão alterada e troca de estado da claim. Reconsulta o registro de Apps/canais **ao final**, recusando revogação ou troca do canal durante as leituras. O resultado público só contém contagens e decisão técnica, sem telefone, `wamid`, token, mensagem, ID da tentativa ou caso.
- `wa32-signed-status-s0-forensic-bridge.test.ts`: **24 testes Node** com HMAC criptograficamente calculado usando **chaves fictícias locais**, adversários entre lojas, status/inbound mistos, identificadores trocados, perda de binding, rechecagem alterada, erros da porta e revogação do canal.
- `integrations/whatsapp-meta/lab/wa32_pg17_scoped_binding_read.sql`: lê, sob usuário privilegiado do **runner descartável**, claims fictícias reais do `wa29_lab`/WA31. Usa mapeamento sintético explícito para App/telefone/`wamid` que o banco **não** armazena como registro legítimo de vínculo.
- `wa32-assert-signed-pg17.ts`: executa **18 verificações cruzadas** com linha da loja A já invalidada e linha da B ainda ativa, ausência de claim, separação A/B, HMAC inválido, corpo adulterado, destinatário/`wamid` incompatíveis, mudança de revisão durante rechecagem e negativa por App desativado. Todos os resultados mantêm `ack_allowed:false`, `retry_external:false`, `send_authorized:false` e `production_authorized:false`.
- `.github/workflows/whatsapp-meta-offline.yml`: integra esse gate **após WA-31** na suíte PostgreSQL 17, conferindo individualmente seus 18 marcadores.

## Contrato proposto, ainda não homologado

1. Um servidor genuinamente confiável selecionaria a rota e o segredo por App **antes** de ler o webhook; HMAC válido autentica apenas a integridade do corpo sob o segredo selecionado, **não** valida a tentativa S0 nem o consentimento.
2. A S0 deveria fornecer por canal restrito uma linha de binding **já autenticada**, unicidade da correlação `App/WABA/phone/wamid/recipient` e revisão durável. A porta WA-32 é um mock; qualquer JSON fornecido por cliente ou por IA não constitui tal prova.
3. Após a verificação e rechecagens seria necessária uma **transação S0 real** para anexar o evento forense de forma idempotente, sob ordem de locks ratificada S1→S0, sem que revogação tardia impeça registro de auditoria nem permita um novo envio.
4. A validação de assinatura, a vinculação ao destino e a persistência não estão numa transação única nesta POC. Revogação entre o **último read** e COMMIT continua possível; solução produtiva depende do núcleo autenticado da S0. Receber um status `sent` no laboratório **não** comprova entrega Meta nem autoriza alteração comercial.
5. A política de retenção/minimização LGPD, resposta HTTP/ACK, rejeição em recepção real, outbox, credenciais legítimas, WABA produtiva, `wamid` verdadeiro e rota hospedada **não foram implementados**.

**Sem rede externa, envios, migração, merge, deploy, segredos, mudanças em S0/S1/OpenAI/frontend ou credenciais Meta reais.** PR #2 permanece Draft.
