# Decisões reservadas ao principal e aos responsáveis de domínio

Propostas para deliberação posterior. Nenhum item abaixo está implicitamente aprovado por esta auditoria ou pela CI. Não se pede nova aprovação de decisões funcionais D1/A2 já vigentes na S1; D1–D4 UI CFI são um conjunto distinto.

| Decisão | Responsável | Evidência já disponível | Consequência da decisão |
|---|---|---|---|
| Aceitar/adaptar request/result 0.1-candidate, versionamento, migração e depreciação | Codex principal com F02 | Mesmo pin/schema e módulos puros; E05 | G01; contrato de transporte pode ser especificado sem duplicar envelope |
| Cardinalidade por encerramento, novo pedido e substituição | Produto + principal | Unicidade real loja+ator+chave; hipóteses F02 diferentes | Evitar promover dedupe técnico a regra comercial |
| Lookup durável, handle, leitura mínima e origem autenticada da resposta | Principal + Segurança/Infra | PR #18 durável, porém binding externo; UI D3/D4 abertos | G02; recuperar sem expor segredo nem desserializar recibo do cliente |
| Novo login, sessão perdida e acesso do Gestor distinto ao contexto do capturador | Principal S0/S1 + Produto + Segurança | CFI hoje exige ator/sessão originais; I79 dá chefia/cargo, não esse direito | Definir continuidade e separação de atores antes de alterar execução |
| Recibo F03 final e referências/versionamento/cutoff das quatro provas | Principal + F01/F03/F02; Privacidade para conteúdo | Produtores experimentais E08; contexto CFI atual | G03/G07; leitura por fonte confiada em vez de aceitação de digest |
| Quem pode ratificar, distinção do capturador, finalidade/escopo/validade, negar/revogar | Produto + principal S0/S1 | I79 e direitos existentes; nenhum ato F02 implementado | G04; não inferir poderes de um rótulo Gestor ou da competência administrativa de Diretor |
| Efeito de transferência/desligamento/revogação sobre decisão já dada | Produto + principal + Segurança | I79 revoga I61 do vínculo anterior, sem mover casos | Definir invalidação/recheck do ato sem reativar direito antigo |
| Fontes e bindings de consentimento, opt-out, tentativa/template e disposição externa | Principal + Meta/Infra + Produto/Privacidade | C1–C7/T1–T6 e classificadores existentes | G05; incerto não recupera slot nem produz aprovação implícita |
| Principal M2M, ACL/audience/custódia/rotação, ACK e durabilidade | Segurança/Infra + principal + Meta | ACK-03/LOCK-04 candidatos; GoTrue é humano | Sem reutilizar Bearer/issuer humano como serviço técnico |
| TTL/default/máximo, janela de contato, retenção/minimização/expurgo por classe | Produto/Privacidade; Infra clock; principal execução | Clock/tombstones técnicos, fixtures 48h/24h–7d | G06; política versionada preserva terminais/idempotência depois de retenção |
| Checkpoint integrado, prioridades e ordem de locks efetiva | Principal S0/S1 | PRs #16/#18/#20/#26; F02 ainda não testada pós-delta I79 | Revisão e testes físicos incrementais, preservando prioridade I79/G2 |
| Homologação operacional e eventual autorização comercial | Responsável pelo produto e proprietários, após gates próprios | Nenhum teste atual substitui aceite operacional | Fora desta autorização; nenhuma liberação inferida |

O principal pode resolver escolhas técnicas já autorizadas no seu escopo. As decisões de negócio, privacidade e operação precisam de suas fontes responsáveis. Este arquivo não abre solicitações nem envia mensagens a nenhuma frente.
