# FV-REV-01 v0.4 — Correções pós-auditoria da Etapa 1

30/10/2026. Repositório `prumogrowth/Prumo-Growth-Platform-V2`; mesma branch `codex/fv-rev-01-conversas-20261030`. HEAD remoto auditado e confirmado antes de alterações: `efc7e255faa896dbe4f797f4ceef1a2b1ae5774f`. Checkout inicial limpo. Nenhuma branch foi recriada, rebaixada ou substituída.

A referência desta revisão são as seis correções explícitas da missão de auditoria FV-REV-01 v0.4 (29/10/2026). Um arquivo integral separado não estava anexado ao executor. Esta atualização prevalece sobre as descrições de apresentação correspondentes do documento 98; funcionalidades, estados e limites da Etapa 1 permanecem.

## Matriz das correções

| Correção | Implementação | Evidência de aceitação |
| --- | --- | --- |
| COR-01 — FV-REV-004 | Ícone de filtro de 44×44 ao lado dos três pontos, antes da busca. Conteúdo existente reaproveitado em popover rolável e limitado à viewport. Enter abre/fecha; Escape, clique fora e saída de foco fecham sem redefinir filtros ou consulta. Anúncio de Todos identifica corretamente todos os atendimentos; números do resumo no popover mantêm contraste legível no tema escuro. | Chromium mede alinhamento com Configurações, posição acima da busca, alvo de toque, limites do popover e teclado; Node verifica preservação de estados. |
| COR-02 — FV-REV-004 | Concessionária compacta na segunda linha, com nome completo acessível e título. Somente `shopId` do caso previamente autorizado é usado para obter o nome existente. Nome/horário e prévia/concessionária/atenção continuam em duas linhas principais. | Chromium verifica visibilidade, alinhamento, espaço da prévia e contraste; Node cobre loja normal e concessão excepcional apenas por caso. |
| COR-03 — FV-REV-010/033 | Não lida verde: `#1f6b45`/branco em claro, `#9bddb4`/`#123822` em escuro. Lida sem resposta mantém contorno e preenchimento amarelo/laranja, sem número. Quantidade, forma, título e rótulo acessível preservados. | Chromium verifica dominância verde, cor quente, texto/quantidade, contraste ≥4,5:1 e apresentação real nos dois temas e quatro larguras. |
| COR-04 — FV-REV-013/033 | Identidade verde aplicada somente a `#request-completion`, criado pelos mesmos predicados. Confirmação e processamento permanecem. Outros botões primários não recebem essa identidade. | Chromium verifica visibilidade, geometria, cor/contraste e confirmação; regressões anteriores preservam elegibilidade e independência comercial. |
| COR-05 — FV-REV-016 | Formulário e ferramentas ficam visualmente ocultos quando não elegíveis. Na janela expirada, grupo próprio apresenta somente as capacidades autorizadas; dois botões compactos lado a lado, um botão ou indisponibilidade. Janela desconhecida/bloqueada e supervisão permanecem conservadoras. Rótulos das ações conservam contraste em repouso e hover. Avisos de pedido local e transporte não foram removidos. | Chromium exige `hidden` efetivo e bounding box ausente dos controles substituídos; mede botões visíveis e sua disposição para 0/1/2 capacidades. Node verifica transições e negativas. |
| COR-06 — FV-REV-017 | Histórico vendido/perdido apresenta somente a faixa terminal no lugar da composição. Sem formulário, ferramentas, nota de composição ou aviso de janela residual. Alertas materiais do fluxo continuam disponíveis se houver. | Chromium e Node verificam ambos os resultados, ausência visual de composição e retorno correto ao composer de um caso ativo elegível. |

## Preservação

A aplicação, os módulos e as fixtures existentes foram reaproveitados. Não houve alteração em fixtures, oito estados comerciais, vínculos, funções de autorização, classificação da última mensagem confirmada, leitura do titular, `cf-op-02.mjs`, controlador de comunicação ou áudio. Não foram criados recursos de autenticação, capacidades, transporte, upload, chamadas Meta/F02/F03 ou efeitos comerciais.

Áudio e emoji continuam disponíveis na composição elegível. A substituição usa a elegibilidade já existente; a invalidação de áudio em perda de elegibilidade permanece. Ocultar a composição não apaga texto ou reconstrói seus controles. X, reabertura, notas não submetidas, foco e navegação mantêm as garantias da Etapa 1. Equipe, distribuição, monitoramento, lotes, histórico, extração, banco e recontatos permanecem nas áreas atuais; nenhuma reorganização da Etapa 2 foi executada.

## Testes e integridade

Nenhuma suíte anterior foi removida. Os helpers de interação passaram a localizar as ações em `#followup-actions`; as expectativas de teclado seguem a posição aprovada do filtro no cabeçalho. Jornadas antigas fecham explicitamente o popover antes de interagir com a lista subjacente. Ao fechar o laboratório por preparação programática, a jornada aguarda o retorno nativo de foco antes de abrir o popover; isso evita uma corrida com o evento assíncrono `close` sem alterar timeouts ou suprimir verificações. Esses ajustes não relaxam permissões, confirmação ou prova de transporte.

`revision-conversations.test.mjs` acrescenta quatro regressões Node. `browser.revision.py` preserva a matriz de 16 combinações (1440/900/390/320 × claro/escuro × Consultor/Gestor) e acrescenta as seis verificações visuais. Cada combinação exercita capacidades 0/1/2, janela aberta/expirada/desconhecida/bloqueada, ausência de autorização e terminais. O teste verifica visibilidade, bounding boxes, cores, contraste e comportamento, além da existência no DOM.

O gate oficial continua Git/ancestralidade/inventário/bytes → Python adversarial → todas as suítes Node → Chromium legado, comunicação e revisão. Allowlist de branches, gates e controle de proveniência permanecem. O manifesto é repinado ao conteúdo commitado antes da execução certificada. Falhas ambientais e timeouts devem ser relatados separadamente; este documento não substitui os resultados reais do JSON e dos logs no SHA efetivamente testado.

## Prévia e evidências

O workflow empacota o mesmo runtime integral em ZIP ESM e HTML único, com instruções e `PROVENIENCIA.json`. As capturas são regeneradas somente após aprovação do gate, com o SHA e hashes registrados: 108 cenas da matriz FV-REV-01 mais as 22 cenas anteriores dos módulos preservados. Desktop, tablet, celular, Consultor/Gestor e ambos os temas permanecem cobertos. A captura de janela expirada exige ausência visual do formulário; vendido/perdido exigem somente a faixa terminal.

## Pendências

Confronto adicional com eventual documento integral ainda não anexado; aceite visual da orquestração; dispositivos físicos e tecnologias assistivas; contratos e integrações reais de S0/S1/Meta/F02/F03 e política produtiva de mídia. Não há autorização ou implementação da Etapa 2 nesta entrega. Sem merge, deploy, integração real ou publicação de site.
