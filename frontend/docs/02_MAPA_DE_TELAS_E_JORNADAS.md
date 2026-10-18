# 02 — Mapa inicial de telas e jornadas

**Fonte principal:** documento 24, *Caderno de telas, fluxos e critérios de aceite operacional*, v0.1, complementado pelas decisões D41-01..06 e D-ORG-01. O mapa abaixo serve como **inventário para design [P]**, não é layout homologado nem escopo fechado de MVP.

## Núcleo do operador da Prumo

| ID | Vista prevista [P] | Finalidade de interface |
| --- | --- | --- |
| O1 | Meus atendimentos | Lista dos casos efetivamente atribuídos ao operador; escopo da concessionária e indicadores de espera sem inventar novos status |
| O2 | Conversa e histórico | Mensagens, autoria, eventos e notas internas; opção candidata **Concluir atendimento** para solicitar extração pós-humana via S0; IA Vendedora não retorna |
| O3 | Ficha extraída, conferência e pendências | **Sem preenchimento manual habitual**: exibir campos elegíveis extraídos da conversa e persistidos pelo S0, origem/versão, faltas e contradições; correção humana C13 somente excepcional e autorizada [D/R] |
| O4 | Remessa e retorno do banco | Exibir resultado e permitir registros humanos autorizados somente quando sustentados por evidência real; modo protótipo deve rotular simulação |
| O5 | Novo contato após marcos | Encaminhamento humano após `cadastro enviado ao banco` ou `vendido`, com ciclo histórico preservado |

## Núcleo do gestor da Prumo

| ID | Vista prevista [P] | Finalidade de interface |
| --- | --- | --- |
| G1 | Filas | Visão de filas por concessionária sob gestão; acesso D2 a conversas completas, sem herdar D3/D4 |
| G2 | Distribuição | Atribuir/re-atribuir casos a profissionais elegíveis da Prumo e **autoatribuir-se** para executar atividades de operador no caso |
| G3 | Monitoramento | Tempos de espera, etapas operacionais e observações, sem confundir evento técnico com status de negócio |
| G4 | Importação e lotes | Acompanhamento dos lotes autorizados, qualidade e situação operacional, sem implementar o motor de importação |

## Responsável / administração

As vistas R1–R4 do documento 24 abrangem administração **via ChatGPT/MCP**. Não pressupor nesta branch que essas atividades devam virar um painel administrativo web independente ou que a UI possa executar comandos administrativos. Registrar como referência para entendimento do usuário e aguardar delimitação própria da experiência visual autorizada.

## Estados e mensagens de tela transversais

- **Contexto visível:** profissional da Prumo + papel + concessionária selecionada/concedida + caso atribuído, quando aplicável.
- **Feedback verdadeiro:** carregando, sem dados, sem permissão, falhou, operação pendente, operação confirmada; não confundir botão clicado com escrita efetivada.
- **Linha do tempo:** histórico versionado, autoria e origem; nenhuma evidência anterior apagada ao corrigir informações.
- **Separação:** status comercial canônico versus informação técnica de fila, canal, entrega, confirmação e atribuição.
- **Segurança de demonstração:** nunca mostrar documentos/CPFs reais, provas bancárias ou credenciais, nem fazer simulações aparentarem autorizações reais.
- **Usabilidade:** navegação por teclado, rótulos legíveis, contraste, telas responsivas e testes com leitores de tela como parte dos critérios futuros.

## Primeiro percurso de revisão visual [P]

1. Contexto de **gestor da Prumo** por concessionária autorizada e lista/fila de casos sintéticos.
2. Atribuição de um caso sintético a **operador da Prumo** e distinção entre designado, atendendo e transferência definitiva da IA.
3. Contexto do operador com **Meus atendimentos** → conversa/histórico → **Concluir atendimento** simulado → feedback de extração sintética → ficha/pendências, **sem rede nem formulário cadastral rotineiro**.
4. Gestor **autoatribuído**, atuando como operador no caso correspondente; ausência de concessão negando acesso.
5. Conferência de navegação em desktop/mobile, estados vazios e erros sem exposição de dados.

**Dependência prévia ao código:** confrontar este inventário com o protótipo S1-001 já existente na branch S0 para escolher evolução coordenada, sem reimplementar sua lógica de negócio na UI.

## Emenda ao caderno [D-direção/P] — percurso de extração pós-humana

A jornada O2 → O3 precisa mostrar dois momentos separados: **pedido de conclusão da conversa aceito** e **versão da ficha validada/persistida pelo backend**. Processamento parcial, lacuna, conflito, versão obsoleta e erro técnico exigem mensagens próprias; nenhum equivale a novo status comercial. Os dados extraídos não devem ser considerados verdadeiros somente pelo modelo: a validação de catálogo/proveniência e a persistência pertencem a S0.

**Nova divisão:** FV-01 (visual ↔ S0), FV-02 (solicitação de conclusão e leitura de resultado), OAI-05/E01 (S0 ↔ adaptador OpenAI, sob frente OpenAI). O botão **Concluir atendimento** é rótulo provisório [P], não conclusão de venda nem remessa bancária. Manter as correções humanas individuais excepcionais aprovadas nos docs 23/41, sem transformar a exceção em formulário habitual.

**Evidência:** [FV-02](05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md) e [auditoria](06_AUDITORIA_CONTRATOS_FV_2026_10_18.md). A S1 sintética existente na branch S0 não representa esse fluxo novo até revisão cruzada.
