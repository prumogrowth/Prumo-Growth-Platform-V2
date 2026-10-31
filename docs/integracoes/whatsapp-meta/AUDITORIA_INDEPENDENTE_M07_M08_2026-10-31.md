# Auditoria de conformidade M07 e M08 — Frente WhatsApp/Meta

**Data:** 31/10/2026. **Escopo:** branch isolada `feat/meta-s0-physical-interop-ack-guard-20261031` + contrato S0 PG17 congelado em `01ffdb093013664b73b18d23f92aac2202578210`. **Status geral:** conforme **para continuar o desenvolvimento exclusivamente offline**, com ressalvas explícitas. **Não homologado para HTTP, Graph, merge ou produção.**

## Método e evidências

Auditoria do código real (`durable-receipt.ts`, `cloud-http-ack-authority-audit.ts`, `cloud-ack-runtime-guard.mjs`, `cloud-batch-scope-preflight.ts`, `cloud-s0-ed25519-receipt-interop.ts`), do produtor/consumidor PG17 descartável, do workflow e dos contratos WDC vigentes. Foram inspecionadas tanto as afirmações de segurança quanto limites dos testes e do pin de fonte.

- [Execução integral aprovada](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41194019498) — SHA Meta `dd27a01d6a44bd8496d52d9cc2455c8b5752f886`: **1.210/1.210 testes offline, 36/36 Ed25519, 369/369 regressões focadas**, scanner de fontes aprovado e **18 verificações físicas Meta↔S0** no PG17 descartável (sem skip/falha).
- O produtor físico também provou **cinco rejeições integrais** de lote misto sem gravação parcial, recuperação autenticada com novo nonce e recibo idêntico, rejeição de replay e conflito para mesmos identificadores com bytes diferentes.
- [Checklist M01–M30](CHECKLIST_CONCLUSAO_META.md), [especificação M07](M07_SEGURANCA_RECIBOS_E_HTTP_ACK_2026-10-31.md), [especificação M08](M08_LOTE_MULTICANAL_ATOMICO_2026-10-31.md), [WDC vigente](00-decisoes-vigentes-precedencia-documental-2026-10-21.md), [especificação funcional](01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md).

**Nota:** os totais de testes são grupos que se sobrepõem, não devem ser somados para alegar testes exclusivos.

## Achados corrigidos tecnicamente durante auditoria

| ID | Severidade inicial | Evidência / problema | Ação e conclusão |
|---|---|---|---|
| AUD-07-01 | Alta, no scanner offline | `stripComments` usava regexp que apagava código executável após a sequência `//` **dentro de uma string**, podendo ocultar `status:200` e `action:'ACK'` do canário. Reproduzido em Node local. | Substituído por leitura lexical simples que distingue strings de comentários; regressões ACK-GUARD-18–21 adicionadas. **Mitigado para esse vetor**, sem afirmar cobertura total de linguagem/bundle. |
| AUD-07-02 | Média, no scanner offline | Exceção inteira de `verify-get.ts` poderia esconder um ACK POST indevido no mesmo arquivo. | Exceção estreitada às formas GET legítimas revisadas; regressões ACK-GUARD-15–17. GET `200` após desafio segue distinto de POST ACK. |
| AUD-08-01 | Alta, validade da prova de laboratório | Recibo e chave/escopo de confiança apareciam juntos no artefato de prova, permitindo autoafirmação do produtor do teste. | Separados em **arquivo de recibo** e **arquivo privado de confiança de laboratório**, com validação de campos/permissões; regressão prova-sem-chave. **A fonte da confiança continua sintética e é criada no mesmo ensaio**: não equivale a chave independente operacional da S0. |
| AUD-08-02 | Média, evidência | Campos booleanos de `m08_lab_evidence` eram alegações do próprio produtor; não bastavam como prova externa de atomicidade/replay. | Alegações removidas do artefato; as asserções executáveis permanecem no produtor físico; resultado positivo exige o exit code e logs do CI com PG17. |
| AUD-CI-01 | Média, cobertura | O job físico não era exigido em caminhos de pull request relevantes. | Configuração revisada para executar a prova física em PRs relevantes, além de push; SHA exato das fontes testadas registrado. |

**Verificação do hardening pré-existente:** `decideBatchAck` agora retorna somente `DENIED_NO_HTTP_AUTHORITY`, sem `status` ou `action`; verificador Ed25519 exige assinatura, chave pública e contexto esperado; preflight HMAC não admite ACK/partição. Os 1.210 testes e o PG17 físico passaram após as correções. Essa conclusão vale **para o código e perfis de teste indicados**, não para versões futuras.

## Pendências explícitas — sem disfarçar como concluídas

| ID | Classificação | Pendência | Donos / momento |
|---|---|---|---|
| AUD-R01 | **Bloqueadora de produção, não de desenvolvimento offline** | Ratificar identidade de serviço, chave pública S0 pré-confiada **fora do próprio produtor do recibo**, custódia/rotação/revogação e canal M2M. Dois arquivos no mesmo teste não substituem esta autoridade. | S0 + Infra + Meta: M07-D, M08-D, M10, M27 |
| AUD-R02 | **Bloqueadora de produção** | Definir e homologar **quando** o serviço poderá responder HTTP 200 de POST físico, e política para indisponibilidade, quarentena, conflito, commit incerto, replay, janela de resposta perdida e retry; nenhuma estrutura simulada tem tal autoridade. | S0 + Infra + Meta: M07-D, M08-D, M11/12/27/28 |
| AUD-R03 | **Bloqueadora de produção** | Demonstrar isolamento/atomicidade sobre registro de concessões, Apps e canal realmente vigente no sistema operacional; o PG17 e a registry sintética não provam a integração real S0. | S0 + Meta: M08-D/M12/M28 |
| AUD-R04 | **Risco residual do canário, não defeito reproduzido no perfil atual** | Detector por texto-fonte **não é análise semântica**, não fiscaliza todos os aliases, importações dinâmicas, bundles, HTTP em outros módulos/repos nem comportamento implantado. Adicionar revisão de runtime e compilado, testes de handler, proteção de branch/CI obrigatório antes de produção. | Meta + Infra: M07-D/M29 |
| AUD-R05 | **Controle de escopo** | Referência S0 está congelada no SHA do laboratório histórico; qualquer nova interface/versão da S0 requer revalidação dos contratos, HMAC, assinatura, nonce e testes cruzados. | S0 + Meta: M08-D/M27 |
| AUD-R06 | **Controle de confidencialidade** | Segredo Meta usado nos testes é **artificial e efêmero**; arquivos privados mode 0600 são descartados no CI. Não utilizar esse mecanismo como vault, key rotation ou gestão de segredo produtivo. | Infra + Meta: M10/M23/M29 |

**Dependências formalizadas:** [M07-D — issue #2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) e [M08-D — issue #3](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/3). A futura comunicação entre frentes poderá importar estas matrizes. Nenhum aceite por silêncio.

## Veredito de auditoria

**Liberado prosseguir a novos marcos de código/ensaios offline na própria frente WhatsApp/Meta.** Não há falha reproduzida no recorte M07/M08 que exija interromper *todo* o desenvolvimento: os vetores internos identificados foram corrigidos e a execução final foi aprovada. **M07 e M08 continuam [ ] no checklist**, com seus subitens técnicos [x] e ratificações [ ].

**NÃO liberado:** status HTTP 200 de webhook POST produtivo, Graph real, credenciais reais, integração autorizante S0/S1, atualizações comerciais, merge, deploy ou operação. A validação operacional fica condicionada às decisões expressas interfrentes e a uma nova auditoria de integração.
