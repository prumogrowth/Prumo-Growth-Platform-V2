# D-NOM-01 — Nomenclatura oficial dos papéis da plataforma Prumo
**Decisão do responsável pelo desenvolvimento da plataforma:** 21/10/2026. **Esclarecimento posterior (22/10):** LiberaCred é exclusivamente o produto da instituição financeira; a plataforma ainda não possui nome próprio. **Status:** decisão de nomenclatura [D], imediata **na documentação vigente**; sem modificação de permissões, estrutura de equipes ou software nesta rodada.

## Termos oficiais para documentação nova e interface futura

| Denominação anterior | Denominação vigente | Continuidade funcional |
| --- | --- | --- |
| Responsável (da plataforma) | **Diretor** | Mantém as atribuições anteriormente aprovadas para o papel de responsável: administração de contas, composição de equipes, concessões gerais de concessionárias e demais alçadas já previstas, sem ampliação automática. |
| Gestor | **Gestor** | Nome e competências mantidos: coordenação de equipe, pausa/retomada do recebimento de novos leads, transferência e supervisão nos limites aprovados. |
| Operador | **Consultor** | Mantém as atribuições anteriormente aprovadas para o papel de operador: atendimento humano e atividades autorizadas nos casos designados; não recebe novas alçadas automaticamente. |

**Regra interpretativa:** em decisões anteriores, ler "responsável" **como Diretor** quando designa o perfil administrativo da plataforma e "operador" **como Consultor** quando designa o profissional humano de atendimento. Referências a "responsável" no sentido genérico de *pessoa responsável pelo caso, pelo cliente, por um serviço ou pela decisão* não devem ser substituídas indiscriminadamente por "Diretor". "Gestor" permanece "Gestor".

**O que NÃO mudou:** funções e responsabilidades, concessões de loja, autorizações por caso, hierarquia, regras de distribuição e pausa, handoff, indicadores, escopos de leitura D2/D3/D4, status comerciais e limites da IA Vendedora. A mudança é **exclusivamente terminológica** neste momento. Não implica criação de novos papéis, migração de usuários, mudança de titularidade ou promoção de capacidade.

## Compatibilidade com código e contratos antigos
Nomes técnicos legados — por exemplo `operador`, `responsavel`, `role='operador'`, tabelas `s1_responsaveis_plataforma`, arquivos históricos e nomes de APIs/migrations — **não são renomeados por esta decisão documental**. Permanecem como **identificadores técnicos legados**, cuja futura tradução/exibição para `Consultor` / `Diretor` deve ser definida e homologada separadamente, com atenção à compatibilidade retroativa, bancos, testes, RLS, Auth e integração entre frentes. **Não inferir que o código, frontend visual ou S1 já exibem os novos nomes**.

## Precedência e rastreabilidade
Esta decisão **D-NOM-01** prevalece, somente quanto à **nomenclatura dos papéis**, sobre vocabulário antigo de [FV-DOC-01](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md), [FV-UI-014](./32_FV_UI_014_INDICADOR_UNICO_E_PAUSA_SELETIVA_2026_10_20.md), [FV-UI-016](./34_FV_UI_016_MARCO_PREVIA_G2_2026_10_20.md), [escopo do frontend](./01_ESCOPO_E_FRONTEIRAS.md), S0-043/S0-044, S1 I10/I11/I12 e os documentos históricos do projeto. Não substitui as decisões funcionais contidas nesses materiais.

Consultar primeiro [o índice canônico da frente](./00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md). Na S0, ver [S0-045](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/S0_045_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md). S1 não foi alterada por esta atualização; quando for integrar a nomenclatura de interfaces, precisará coordenar contratos e identificadores sem quebrar a operação.

**Gate:** documentação apenas. Sem alteração em código, tabelas, migrations, Auth/RLS, serviços, dados reais, outras branches, merge ou deploy. FV-UI-013 e índice 19F permanecem inalterados.
