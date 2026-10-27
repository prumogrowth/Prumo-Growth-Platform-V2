# S0-045 — Atualização documental dos papéis: Diretor / Gestor / Consultor
**Data:** 21/10/2026. **Origem:** decisão expressa do responsável pelo produto [D]. **Escopo:** nomenclatura oficial; nenhuma alteração técnica ou autorização nesta entrega.

| Nome usado antes | Nome oficial vigente | Efeito |
| --- | --- | --- |
| **Responsável** (perfil administrador da plataforma) | **Diretor** | Mesmas atribuições previamente aprovadas de responsável, especialmente gestão administrativa de contas, papéis, equipes e concessões gerais. |
| **Gestor** | **Gestor** | Mantém exatamente o nome e as atribuições já aprovadas. |
| **Operador** | **Consultor** | Mesmas atribuições previamente aprovadas de operador de atendimento humano. |

[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]

**Compatibilidade:** identidades e literais legados como `operador`, `responsavel`, `role`, `equipe_prumo_s1`, `s1_responsaveis_plataforma`, migrations, RLS, APIs, testes, nomes de arquivos e contratos S1 permanecem **intocados**. A renomeação da UI/código exige planejamento e revisão separada de compatibilidade; o frontend, S0 e S1 **não devem** traduzir identificadores de autorização usando texto de exibição, nem considerar essa decisão como migração de perfil.

**Regras funcionais preservadas:** diretor concentra o que antes pertencia ao responsável; gestor supervisiona a equipe e pode pausar novos leads de consultor; consultor continua atendendo seus casos durante pausa; distribuição, loja, grants, autorização excepcional por caso, fila de gestores e separação IA/núcleo seguem [S0-043](./S0_043_PAUSA_SELETIVA_E_INDICADOR_CONVERSA_2026_10_20.md) e [S0-044](./S0_044_ALINHAMENTO_FILA_GESTORES_IA_2026_10_21.md), sem nenhuma mudança semântica.

**Fonte canônica de nomenclatura na frente visual:** [D-NOM-01](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/frontend-plataforma-visual/frontend/docs/37_D_NOM_01_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md). Não houve alteração da branch S1, bancos hospedados ou produção. **Documentação apenas.**
