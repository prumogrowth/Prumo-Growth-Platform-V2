# 03 — Materiais de referência e critérios de preparação

**Data:** 18/10/2026. **Objetivo:** deixar fontes e prioridades explícitas antes de iniciar o código visual. Materiais auditados são consultados, mas **não replicados integralmente** no repositório para evitar cópias divergentes.

## Fontes documentais do projeto

Acervo recebido: **`Liberacred_Documentacao_Completa_55_Arquivos_2026-10-17.zip`**, pacote de 55 arquivos documentais. Respeitar índice e rastreabilidade do acervo; documentos com decisões posteriores têm precedência sobre textos históricos.

| Prioridade de leitura | Fonte | Uso esperado |
| --- | --- | --- |
| 1 | `00A_Indice_Mestre_Operacional_Auditado_2026_10_17_v0_1.md` | Precedência, fontes e estado normativo |
| 1 | `13A_Emendas_Normativas_Eventos_e_Transicoes_2026_10_17_v0_1.md`; docs. **21–23** | Transições, recusa bancária, retorno pós-venda e qualidade do cadastro |
| 1 | `41_Decisao_Aprovada_Matriz_Permissoes_Gestor_Operador_MCP_v1_0.md` | Permissões D41-01..06 aprovadas |
| 1 (mais recente) | `docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md` na branch S0 | Equipe Prumo, concessões por loja e papéis; atualização normativa de 18/10 |
| 2 | `24_Caderno_Telas_Fluxos_Aceite_Operacional_v0_1.md` | Tela O1–O5, G1–G4, R1–R4 e aceites propostos |
| 2 | `11_Arquitetura_Geral_Consolidada_v4_8.md`; `31_Matriz_Permissoes_Papeis_Dados_Operacoes_v0_1.md`; `36_Matriz_Granular_Permissoes_Minuta_Aceite_v0_1.md` | Contexto estrutural, com prevalência de D41/D-ORG |
| 2 | `28_Especificacao_Confiabilidade_Privacidade_Recuperacao_v0_1.md`; `29_Matriz_Testes_Aceitacao_Eventos_Cobertura_Total_v0_1.md` | Erros/recuperação, acesso e cenários de teste propostos |
| 3 | `32_Backlog_Construcao_Dependencias_Riscos_GoNoGo_v0_1.md`; `38_Plano_Entregas_Incrementais_MVP_Criterios_Ativacao_v0_1.md` | Priorização e dependências, sem antecipar MVP |
| 3 | `42_Auditoria_Prontidao_Pre_Implementacao_GitHub_Supabase_v0_1.md`; `43_Playbook_Inicio_Tecnico_GitHub_Supabase_Custos_n8n_v0_1.md` | Limites de implementação, segregação de ambientes e dados sintéticos |
| Governança | `19F_Controle_Progresso_Evolutivo_69_por_cento_v0_1.md` | Referência de planejamento em 17/10 (69/100); criar branch não aumenta pontuação |

## Fontes vivas já encontradas no GitHub

- **Fundação S0 / S1 sintética:** [branch `feat/s0-fundacao-prumo`](https://github.com/prumogrowth/Prumo-Growth---Platform/tree/feat/s0-fundacao-prumo), principalmente `frontend/s1/README.md`, `docs/S1_001_JORNADA_HUMANA_VISUAL_2026_10_18.md` e `docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md`.
- **OpenAI:** [branch `feat/s2-openai-adapter-sintetico`](https://github.com/prumogrowth/Prumo-Growth---Platform/tree/feat/s2-openai-adapter-sintetico), responsável por sua integração; não duplicar.
- **Meta/WhatsApp:** [branch `docs/whatsapp-meta-concessionária de demonstração-poc-20261017`](https://github.com/prumogrowth/Prumo-Growth---Platform/tree/docs/whatsapp-meta-concessionária de demonstração-poc-20261017), responsável por seu adaptador; não duplicar.
- **Branch deste trabalho:** [`feat/frontend-plataforma-visual`](https://github.com/prumogrowth/Prumo-Growth---Platform/tree/feat/frontend-plataforma-visual).

## Organização inicial desta branch

```text
frontend/
├── README.md
├── docs/
│   ├── 01_ESCOPO_E_FRONTEIRAS.md
│   ├── 02_MAPA_DE_TELAS_E_JORNADAS.md
│   └── 03_MATERIAIS_E_PREPARACAO.md
└── design/
    └── README.md
```

O código visual será acrescentado **após** alinhamento com a S1 pré-existente. Não criar um segundo motor de transições ou regras de autorização em JavaScript para substituir o núcleo do backend. Não instalar dependências nem escolher hospedagem/domínio como pressuposto.

## Critérios para a próxima etapa

1. **Revisão de não sobreposição:** comparar telas O/G e S1-001 existente; identificar o que é novo (layout, acessibilidade, fluxo) versus o que pertence à frente S0.
2. **Escolha consciente da abordagem frontend [P/R]:** arquitetura e bibliotecas só após checar compatibilidade com o código já iniciado; manter possibilidade de desenvolvimento local.
3. **Primeiro incremento:** tela visual sintética e isolada, sem conexão a Supabase/OpenAI/Meta/Banco, com navegação clara entre gestor e operador **sem fingir que seletor de personagem é autenticação**.
4. **Validação:** revisão visual, responsive, teclado, estados de erro/vazio, testes determinísticos com dados artificiais; documentar o que ainda não foi testado.
5. **Integração futura:** coordenar PR com responsáveis das outras frentes. Sem merge automático na `main`, sem deployments e sem dados reais.

**Fora de foco nesta fase:** contratos jurídicos, formalização bancária, escolha de domínio/hospedagem, credenciais, custos de produção e integrações comerciais **reais**. **Dentro do escopo:** contratos TÉCNICOS conceituais de frontend ↔ S0, com auditoria sem execução/implantação.

## Atualização documental 18/10/2026 — contratos FV

Os contratos originais do pacote auditado continuam fonte de contexto, porém o fluxo de preenchimento manual habitual em O3/SI03 está superado pela direção atual do responsável. Ler o delta em [FV-01](04_CONTRATO_FV01_UI_BACKEND_v0_1.md), [FV-02](05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md) e no [relatório de auditoria](06_AUDITORIA_CONTRATOS_FV_2026_10_18.md).

A frente OpenAI já documentou o contrato **OAI-05 — Extração de cadastro após encerramento do atendimento humano** e **E01 v0.2 — multicaptacidade**, disponíveis na branch `feat/s2-openai-adapter-sintetico`. Sua existência NÃO significa que houve revisão S0, implementação de extração, aceite de payload ou autorização externa.

Nenhum incremento de planejamento/progresso automático e nenhum deploy. A pendência central é conciliação interfrentes para o comando S0 de conclusão e a leitura de status da extração.
