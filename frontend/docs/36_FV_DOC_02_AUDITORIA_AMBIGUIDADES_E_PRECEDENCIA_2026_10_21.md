> **NOMENCLATURA VIGENTE [D-NOM-01] — 21/10/2026:** o papel anteriormente chamado **responsável** passa a chamar-se **Diretor**; **gestor** permanece **Gestor**; **operador** passa a chamar-se **Consultor**. A mudança é somente de nomes, sem alteração de alçadas, código ou permissões. Palavras genéricas como “responsável pelo caso” não mudam automaticamente. Ver [decisão de nomenclatura](./37_D_NOM_01_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md); terminologia abaixo pode refletir a data original do texto.

# FV-DOC-02 — Auditoria documental de precedência e lacunas (21/10/2026)
**Natureza:** auditoria DOCUMENTAL da frente visual/S0 com leitura das retificações S1; **não** revisão de código, não homologação. Decisões expressas do responsável estão consolidadas em [FV-DOC-01](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md). Fontes confrontadas: pacote histórico de 55 documentos com corte 17/10 (especialmente 00A/13A/31/41), documentos `frontend/docs/`, `docs/S0_043`, `docs/DECISOES_E_GATES` e retificações S1 I11/I12 (somente leitura).

## Mapa de ambiguidade e precedência
| Achado | Risco de leitura incorreta | Regra que prevalece / ação documental |
|---|---|---|
| **DOC-01 — Pausa e conta** | FV-G2-01/21 menciona motivo, período e ausências; legado S1 I11 associava pausa à suspensão do login. | **D-AL-01**: apenas parar novos leads; operador continua trabalhando em casos seus; confirmação simples, sem justificativa/data. |
| **DOC-02 — Movimentação entre equipes** | FV-UI-014/32, FV-UI-016/34 e S0-043 dizem “mesma equipe” sem separar claramente **caso antigo** de **lead novo**. | **D-AL-02** restringe *redistribuição de caso existente do pausado* à sua equipe. **D-AL-05** autoriza *distribuição regular de lead novo* entre equipes com concessão válida. |
| **DOC-03 — Dois tipos de fila** | “Fila protegida”, “sem substituto” e “lead novo sem destinatário” podem ser entendidos como equivalentes. | **D-AL-02** mantém caso existente COM o titular pausado quando não há substituto. **D-AL-06** cria fila SEM titular para lead NOVO. |
| **DOC-04 — Gestores e fila compartilhada** | Ausência de regra sobre mais de um gestor autorizado na mesma loja; supor um único gerente ou visibilidade global. | **D-AL-06**: gestores **autorizados à concessionária** veem pendentes e podem assumir; transação deve ter vencedor único [T]. Não outorga todas as lojas a todos os gestores. |
| **DOC-05 — Retomada da disponibilidade** | Documentos antigos não decidem o destino de leads ainda pendentes sem titular. | **D-AL-07**: distribuir automaticamente pendentes sem titular ao reaparecer operador elegível; nunca subtrair caso já assumido. |
| **DOC-06 — Primeiro contato humano** | Evento humano genérico poderia admitir autodeclaração de ligação/visita. | **D-AL-04**: sem registro manual; mensagem humana tecnicamente confirmada conta. Ligação Meta *atendida e verificada* apenas em evolução futura [V]. |
| **DOC-07 — IA e roteamento** | A IA poderia receber, por engano, dados de operadores/equipes como contexto ou ser bloqueada quando não há humano. | **D-AL-08**: IA atende cliente independentemente da disponibilidade; não conhece operadores, equipes, grants ou distribuição; S0/automações roteiam handoff. |
| **DOC-08 — Escopo de transferência manual** | Confundir gestor autorizando membro sem grant com grant geral de concessionária; I12 legado exige grant. | **D-AL-03**: caso específico, permissão operacional restrita após transferência confirmada, com revogação e RLS [T]. |
| **DOC-09 — Estado do badge** | FV-UI-014/32 diz “ainda não conectado ao app”; o módulo foi ligado à **demonstração** FV-UI-015, não ao S0 real. | **D-AL-09** governa comportamento. Aviso de temporalidade; nem prova de backend nem cores finais. |
| **DOC-10 — Titularidade Meta** | Documentos basais de 17/10 falam em App/WABA/emissor pertencentes à Prumo/gestora. | A decisão posterior **DEC-WA-05/S0 (18/10)** registra concessionária titular do ambiente Meta e Prumo integradora. Texto basal é histórico [H]; homologação externa pendente [V]. |
| **DOC-11 — Tecnologia nomeada** | “Firebase” aparece em transcrição da fala. | **D-AL-10:** foi erro de transcrição; arquitetura segue **Supabase**. |
| **DOC-12 — Equipe e loja** | D41/31 e documentos antigos descrevem gestor por loja; orientações mais recentes organizam supervisão por equipe, e fila nova por gestores autorizados à loja. | Exigir distinção e interseção de escopos. Nem equipe concede toda loja, nem fila de loja concede supervisão plena sobre outras equipes. RLS final [T]. |
| **DOC-13 — Evidência vs homologação** | Relatórios históricos ou 19F 69/100 interpretados como prontidão operacional. | Diferenciar sintético, testes isolados, contrato candidato, migração de sandbox e aceite real. FV-UI-013 permanece NÃO HOMOLOGADA formalmente. |

## Verificação pontual S1: estado documental mais recente
A branch S1 consultada já contém retificações explícitas no início/fim de I11 e I12 e documento de correção da **issue #10**. I11 antigo suspendia a conta; a retificação estabelece intake separado e prova seletiva antes da redistribuição. I12 antigo exigia grant geral; a retificação admite exceção restrita por caso, **ainda não operacional**. Existem ensaios sintéticos/fixture; **não** presumir que o comando seguro, RLS, GoTrue e fila de gestores estejam integrados ou liberados. S1 continua proprietária desses ajustes; não modificar sua branch nesta etapa.

## Correção proposta e executada nesta frente
- Fonte [FV-DOC-01](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md) reúne o que foi **decidido**, separado do que foi **implementado**.
- Índice [COMECE POR AQUI](./00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md) define ordem de leitura e aponta normas anteriores intactas.
- Os documentos históricos de maior risco recebem **avisos aditivos**, não exclusão de conteúdo; histórico e evidência original permanecem.
- Correção equivalente de precedência prevista na S0 para futuros integradores; NÃO reescrever SQL/migrations/rotas por inferência.

## Lacunas contratuais [T] encaminhadas à auditoria técnica FUTURA
Evento versionado e validação do primeiro contato; intake independente de conta; grants de loja e exceções por caso em D2/D3/D4/anexos; fila compartilhada com autorizações de gestores; concorrência entre autoseleção e autoatribuição; redistribuição cross-team de novos leads, mas same-team de carteira pausada; revalidação de identidade/grant, algoritmos de distribuição, idempotência, logs; isolamento da IA de metadados administrativos; continuidade ao handoff. Nenhum item é classificado como bug de produção sem examinar código, dados e ambiente.

**Escopo da revisão:** somente documentos da própria frente (Frontend e notas de S0); S1/Meta/Banco sem alteração, sem código, migração, deploy ou mudança do índice 19F.

## DOC-14 — Ambiguidade de nomenclatura dos papéis (21/10/2026)

O vocabulário anterior (“responsável” e “operador”) é histórico **quando designa os papéis da plataforma**; ler respectivamente **Diretor** e **Consultor**. “Gestor” não mudou. Fontes técnicas e históricos não devem ser renomeados por substituição textual, e uma menção genérica a “responsável pelo caso” não designa necessariamente o papel Diretor. A precedência é da [D-NOM-01](./37_D_NOM_01_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md). A futura atualização de interface, Auth, APIs, S0/S1 e testes exige plano próprio e não foi realizada aqui.
