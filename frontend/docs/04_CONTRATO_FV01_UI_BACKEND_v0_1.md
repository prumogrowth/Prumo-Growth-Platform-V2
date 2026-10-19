# FV-01 — Contrato conceitual da interface visual ↔ núcleo S0 | v0.1

**Data:** 18/10/2026. **Estado:** [P] contrato candidato da frente visual; depende de revisão/aceite pela frente S0 [R]. **Implementação/testes:** não executados. **Fronteira:** este arquivo não cria endpoints, novos comandos C, consultas UQ, tabela, política RLS, workflow, implantação ou acesso real.

## 1. Fonte normativa e hierarquia

Aplicar as decisões aprovadas 13A, 21–23 e 41 (D41-01..06), D-ORG-01 de 18/10 (equipe profissional da Prumo), e a nova orientação de 18/10: **operador não digita rotineiramente os dados do cadastro**, pois a conclusão da conversa humana aciona extração pela OpenAI com gravação validada pelo S0. Docs. 24, 26 e 40 são contratos/projeções [P] existentes. A frente OpenAI já possui OAI-05 e E01 v0.2; não substituir sua porta interna.

Princípios imutáveis: oito status comerciais exatos; nenhuma ação visual efetiva autorização; gestor lê D2 completo em lojas concedidas mas não herda D3/D4 bruto; gestor autoatribuído atua como operador apenas no caso; identidade profissional é da Prumo; isolamento entre concessionárias; resposta humana e atos bancários sob alçada; remessa/venda/negativa comprovadas e humanas; retorno após banco/vendido para humano sem reativar IA Vendedora.

## 2. Autoridade e camadas

**Browser/frontend**: navega, exibe projeção minimizada, solicita ações explícitas, apresenta execução/pendência/erro e atualiza somente após confirmação. Nunca carrega credencial OpenAI/Meta, role secret do Supabase, dados bancários brutos sem projeção autorizada, nem decide status por inferência.

**S0/backend**: único responsável por autenticação real e sessão, concessão por loja, atribuição, elegibilidade, idempotência, versão, autorização de leitura/escrita, consulta UQ, comando C, validação de extração, preenchimento persistente e auditoria. Não confiar em role, ID de loja ou permissão afirmados pelo browser.

**OpenAI**: extrai *propostas* estruturadas a partir de snapshot permitido e minimizado enviado por S0; não escreve banco, não retorna mensagens ao cliente, não altera status e não é chamada diretamente pelo browser. Contratos internos de propriedade da frente OpenAI, OAI-05/E01.

**Meta**: mensagens, status de transporte, entrada/saída e mídia; somente pelo fluxo autenticado apropriado do backend, nunca direto do frontend.

## 3. Envelope candidato de leitura UI [P]

Reutilizar UQ01–UQ09 do doc.40; nenhuma UQ10 é criada. Entradas conceituais: sessão autenticada (fora de parâmetros confiados ao browser), id opaco de recurso, filtros/cursor permitidos, versao_da_consulta, request_id/correlation_id. Saída autorizada: schema_version, request_id, projection_name, as_of, current_resource_version, records/detail minimizados, next_cursor e outcome/error_code. O backend revalida concessões inclusive na paginação, atualização e anexos; cache local é descartado na revogação.

**DADOS DE EXEMPLO SINTÉTICOS APENAS**: O catálogo concreto de cadastro não está aprovado. Não inserir campos obrigatórios fictícios (CPF/e-mail/renda) no contrato normativo, nem assumir que conversas/áudio podem ser compartilhados com provedores sem validação externa.

| Tela/ação | Leitura de referência (doc.40) | Escrita/autoridade de referência (doc.26) | Particularidade do frontend |
| --- | --- | --- | --- |
| O1 Meus atendimentos | UQ01 | Nenhuma ao abrir | Somente casos atribuídos ao operador da Prumo |
| O2 Conversa/histórico | UQ02 e UQ09 | C12 para resposta humana; **FV-02** para solicitação de conclusão humana [P/R] | Mostrar aceitação técnica ≠ mensagem entregue; não reativar IA Vendedora |
| O3 Ficha extraída/conferência | UQ03 (necessita projeção de extração [R]) | Escrita automática exclusivamente S0 após OAI-05; C13 é **exceção normativa**, não edição normal | **Fluxo nominal somente leitura/conferência/pendências**, sem formulário de digitação cadastral; origem e versão explícitas |
| O4 Remessa e desfecho | UQ04 | C15–C18 somente humanos autorizados, com comprovação | Extração não remete/vende/recusa |
| O5 Novo contato pós-marco | UQ05, UQ02 | C14 (evento S0), C12 | Novo caso humano sem mudar ciclo histórico |
| G1/G2 Fila/distribuição | UQ06, UQ02 D2 por escopo | C11 | Gestor só opera como OP quando designado/autoatribuído |
| G3 Indicadores | UQ08 e UQ09 conforme alçada | Nenhuma automaticamente | Nenhuma leitura de D3/D4 brutos por mera supervisão |
| G4 Lotes | UQ07 | C01 se alçada específica aprovada | Importar lista não prova consentimento nem inicia conversa |
| R1–R4 Administração | C19–C22, fora do frontend operacional | MCP com confirmação conforme D41-03 | Não recriar poderes administrativos como tela web por suposição |

## 4. Semântica de respostas e feedback

A interface precisa distinguir:
- **Leitura**: LOADING, EMPTY, READY, FORBIDDEN, ERROR (estados de exibição [P], não status comerciais).
- **Comando**: REQUESTED, ACCEPTED_FOR_PROCESSING, APPLIED, ALREADY_APPLIED, PENDING_EXTERNAL, UNCERTAIN_EXTERNAL ou erro conforme o dicionário do doc.26; códigos definitivos deverão ser conciliados com S0 [R].
- **Erros previstos**: FORBIDDEN_SCOPE, VALIDATION_FAILED, CONFLICT_VERSION, NOT_ELIGIBLE, PROOF_REQUIRED, DEPENDENCY_UNVERIFIED, UNRESOLVED_RULE e SERVICE_UNAVAILABLE (nomes atuais candidatos do doc.40).
- Mensagem de UX somente afirma **cadastro preenchido** após projeção de nova versão efetivamente persistida e validada pelo S0. Um 200 de transporte ou pedido de extração aceito **não comprova gravação**.
- Caso removido por revogação/reatribuição: descarte imediato de detalhes e ações no browser, sem expor existência do caso fora do escopo.

## 5. Conferência e correção extraordinária

A **digitação rotina de nome, e-mail e demais informações** deixa de compor O2/O3. Em O3, exibir campos autorizados **que vieram da conversa e foram persistidos pelo S0**, origem, versão, pendências, contradições e indicação de conferência, respeitando D3. O operador pode voltar à conversa humana para esclarecer lacunas; isso não reativa IA Vendedora.

**Conflito aparente a não resolver unilateralmente:** doc.23 [D] e D41-04 [D] permitem correção humana individual excepcional versionada via C13; a nova orientação retirou **preenchimento manual habitual**, não revogou expressamente a correção excepcional. Logo, não oferecer edição geral como fluxo nominal; mecanismo de correção pontual só sob alçada, auditoria e decisão de UX própria [R]. Revogar também a exceção exigiria nova decisão normativa.

## 6. Invariantes e não objetivos

- Concluir conversa **não** é marcar vendido/perdido, enviar ao banco, criar nono status nem encerrar definitivamente o ciclo.
- Cadastro incompleto ou conflitante não é entregue como completo nem preenchido por hipótese; tratar pendência sem suspensão automática da plataforma.
- Idempotência e versão protegem dupla conclusão e resposta atrasada da extração; o frontend não gera snapshot confiável nem escolhe transcrição.
- Não modificar backend/Supabase, tabelas, RLS, Meta, OpenAI, n8n, domínios ou hospedagem por este contrato.
- Nenhum anexo real, dados pessoais de clientes, segredo ou canal bancário real em fixtures/capturas.
- Os rótulos de UI, design system e campos finais são [P/R]; nenhuma contratação nem integração efetivada.

## 7. Dependências para aprovação

**S0 [R]:** aprovar comando de conclusão, status técnico de processamento, projeção UQ03 e versionamento; conciliar caso que está em atendimento humano por exceção e via IA. **OpenAI [R]:** manter contrato OAI-05/E01, mapear retorno sem efeitos colaterais. **Governança [R/V]:** catálogo oficial de campos, política de autopreenchimento por classe, correção excepcional, LGPD/Meta/Banco. **Frontend:** testes e telas com dados sintéticos, sem fingir acesso operacional.

**Situação:** contrato redigido e auditável; revisão interfrentes ainda pendente. Não é aceite de API nem GO para produção.

## Adendo de conciliação CFI-01 — 18/10/2026 [P/R]

Auditoria de compatibilidade realizada em [CFI-01](07_CONCILIACAO_INTERFRENTES_FV_S0_OAI_v0_1.md), com [36 cenários candidatos](08_MATRIZ_ACEITE_CONTRATUAL_FV_S0_OAI_v0_1.md). O conjunto C01–C24/UQ01–UQ09 dos docs 26/40 **não contém contrato físico aprovado** para conclusão humana com extração posterior. Preservar C12 (conversa humana) e C13 (correção excepcional), sem reclassificar o novo fluxo como C13 ou handoff C10. UQ03 continua fonte conceitual de ficha/versionamento, mas precisa de confirmação S0 quanto à projeção de progresso da extração.

**Dono das decisões técnicas ainda [R]:** núcleo S0 para comando de conclusão, idempotência e nova versão; S0 + OpenAI para padronização do envelope interno `human_close_extract`. A E01 atual já usa o nome `human_close_extract` como OAI-05, mas os exemplos de campos, ausências e correlação ainda diferem. Não inventar tradução automática ou API em `frontend/`. Nenhuma alteração nas normas D41/D-ORG ou permissões decorrente desta conciliação.

## Adendo FV-G2-01 — direção nova do responsável (19/10/2026)

**Supersessão de premissa gestorial:** as expressões anteriores deste FV-01 “gestor lê D2 completo em lojas concedidas” e “G1/G2 fila por concessionária” **não estabelecem mais leitura de todos os operadores de uma loja**. A decisão mais recente define **gestor vinculado a operadores específicos da Prumo**; o responsável decide a composição dessas equipes e as concessionárias concedidas aos operadores.

O gestor pode **solicitar pausa temporária de novos leads para o operador inteiro**, em todas as lojas previamente concedidas, mas **não pode** pausar somente A/B, conceder C, remover definitivamente profissionais ou escolher destinatários sem elegibilidade aprovada. A pausa de novos leads é distinta de suspensão de conta/revogação de concessão. A redistribuição mantém loja, autoria e histórico, sob S0/S1-002; destino e fila protegida exigem regras backend.

**A UI FV-UI-010 é 100% sintética**: já exibe equipes por gestores e botões de solicitação local de pausa/retomada; nenhuma operação é aplicada. Para APIs reais, a S0/S1 deve reconciliar a nova matriz com as restrições atuais por loja/tenant e o contrato antigo S1-002/I10 antes de autorização; não usar filtros no navegador para simular segurança.

Referências: [FV-G2-01](21_FV_G2_01_GESTAO_POR_OPERADORES_E_PAUSA_GLOBAL_2026_10_19.md), [auditoria FV-UI-010](22_AUDITORIA_G2_EQUIPE_POR_OPERADORES_PAUSA_GLOBAL_2026_10_19.md), [issue #9](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/9). Esta emenda ajusta o **entendimento do frontend**, não altera contratos aprovados de outras equipes automaticamente.
