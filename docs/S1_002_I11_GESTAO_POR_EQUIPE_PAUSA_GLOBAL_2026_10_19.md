> **AVISO DE PRECEDÊNCIA S1-002 — 22/10/2026:** consultar primeiro o [índice atual](S1_002_00_LEIA_PRIMEIRO_2026_10_22.md) e o [contrato funcional vigente](S1_002_01_CONTRATO_FUNCIONAL_VIGENTE_2026_10_22.md). **Pausa de intake não é suspensão; chefia principal única é decisão [D]; novos leads podem cruzar equipes, mas carteira pausada não.** Texto, migrações e testes abaixo permanecem como registros do estágio original; não são prova de implementação da decisão mais recente. **Libera Credi é o produto da instituição financeira; o software chama-se, por enquanto, plataforma.**

# S1-002/I11 — Gestores por equipe, grants pelos responsáveis e pausa global

> **AVISO DE PRECEDÊNCIA — 22/10/2026:** **Importante:** a pausa `intake` é diferente de suspensão de conta; redistribuição da carteira pausada é seletiva e mesma equipe; lead NOVO regular pode atravessar equipes elegíveis e pode entrar em fila sem titular. Chefia principal única foi ratificada [D], não segue pendente como hipótese do I11. [Contrato funcional S1 vigente (22/10/2026)](S1_002_01_CONTRATO_FUNCIONAL_VIGENTE_2026_10_22.md) · [matriz de aderência](S1_002_02_MATRIZ_ADERENCIA_E_PENDENCIAS_2026_10_22.md).


> **[D] Atualização de nomenclatura (21/10/2026):** **diretor** substitui o nome de papel **responsável (da plataforma)**; **gestor** permanece **gestor**; **consultor** substitui **operador**. As competências permanecem iguais, e a estrutura técnica/identificadores ainda **não** foram renomeados. A terminologia antiga neste documento deve ser interpretada por esta equivalência. [Decisão normativa de nomenclatura](S1_002_DECISAO_NOMENCLATURA_PAPEIS_2026_10_21.md).


**AVISO DE CONTRATO VIGENTE (20/10/2026):** a descrição histórica de pausa que suspende `equipe_prumo_s1.estado`, remove a leitura do operador e redistribui toda a carteira **FOI SUPERADA** pela issue #10. Pausa gerencial atual é exclusivamente `intake_paused`, sem suspender login, retirar grants ou acesso a casos ainda atribuídos. Somente casos sem contato humano iniciado, comprovado pelo S0, podem ser redistribuídos a outra pessoa disponível da mesma equipe e com grant da concessionária; sem destino elegível, o titular permanece. Leitura e resposta sobre casos não transferidos continuam habilitadas. A migration I11 antiga e seus testes não são aceites da nova regra. [Contrato vigente da issue #10](S1_002_ISSUE10_CORRECAO_PAUSA_INTAKE_2026_10_20.md).

**[D] Correção expressa de negócio — 19/10/2026.** Substitui a interpretação por concessionária de I10. Dono desta frente: S1-002. Aplica-se ao produto Prumo/LiberaCred, mantendo os contratos de casos comerciais no núcleo S0.

## 1. Três relações que não podem ser confundidas

- **Pessoa → equipe (gestor):** cada gestor é responsável por um conjunto de operadores da Prumo, sem carregar concessões de loja. Um gestor pode ter cinco operadores e outro três. Alterar as lojas autorizadas para um operador **não** altera sua chefia nem quem gere suas férias/afastamentos ou fila.
- **Operador → concessionárias (recebimento):** **responsáveis da plataforma** configuram quais concessionárias a IA/sistema podem direcionar leads a cada operador; A+B hoje, C amanhã. **Gestor não concede, não suspende e não revoga uma concessionária individual para esse operador.** O fluxo de caso sempre respeita loja de origem e credenciais de recebimento.
- **Operador → disponibilidade global:** o gestor que coordena aquele operador pode colocá-lo temporariamente **fora da distribuição em todas as concessionárias**, por exemplo ausência de uma semana. Isso impede novos leads e redistribui atendimentos ativos do operador conforme as alçadas/lojas dos substitutos. A pausa é da **pessoa**, não do vínculo com A ou B. Os grants continuam guardados; ao retorno, o operador volta a estar elegível para novos casos, sem recuperar automaticamente os que já foram transferidos.

Responsáveis são os únicos que **adicionam** operadores/gestores, fazem desligamento definitivo e configuram grants de lojas. Gestor administra equipe preexistente (pausa, volta, distribuição, movimento de casos, supervisão), sem ingressos/desligamentos definitivos. O operador não administra os colegas. O gestor não precisa possuir concessão da loja A para liderar alguém que recebe casos de A.

## 2. Implementação sintética segura na S1-002

A migration `202610190048_s1_gestao_equipe_pausa_global.sql` introduz duas relações PRIVADAS separadas: `s1_responsaveis_plataforma` (responsáveis independentes de concessionária) e `s1_gestor_operadores` (gestor → operadores). **Um gestor para muitos operadores**. A restrição de **um gestor ativo por operador é hipótese técnica [P]**, não decisão explícita do usuário; precisa de validação de política RH antes da produção. A função de autorização de I10 é **substituída**: deixa de verificar grants do gestor a lojas, exige pertencer à equipe para administrar, exige escopo de concessionária apenas quando a operação move/redistribui um atendimento concreto e continua negando a alteração de grants pelo gestor.

As funções internas `s1_pausar_operador_da_equipe` e `s1_reativar_operador_da_equipe` (SQL de teste, EXECUTE revogado para API) usam o estado já existente `equipe_prumo_s1.estado`. Na pausa `ativo → suspenso`, o gatilho I2 encerra/redistribui **em todas as lojas** e restringe as leituras por RLS. Ao retorno `suspenso → ativo`, o operador volta ao conjunto elegível para novos casos; não reconquista casos antigos que tenham outro titular. Auditoria append-only contém **código mínimo de indisponibilidade, nunca diagnóstico médico**; não armazenar imagem do atestado neste fluxo.

**Contratos preservados:** único titular ativo, concessionária original do atendimento, autorização do novo receptor por concessionária, histórico de atribuição e das pausas. O gestor ainda só pode executar atendimento como operador se se autoatribuir conforme D41. Não altera os oito estados comerciais, nada Meta/OpenAI, nenhuma configuração de concessionária feita por gestor, e nenhuma credencial real.

## 3. Critérios e limites

- Provas propostas `S1T-01..13` em PG17 fictício: gestões de equipes diferentes, responsáveis concedendo C em matriz, gestor sem grant de nenhuma loja supervisionando operador A+B, pausa global redistribui dois casos A+B e deixa terceiro C intacto, grants A+B permanecem, leitura do afastado é bloqueada, retorno não recupera carteira antiga, operações indevidas e metadados livres rejeitados, função privada inacessível a `authenticated`.
- **Não há comando real de login/REST/GoTrue**; a função recebe solicitante por argumento exclusivamente no sandbox sob `postgres`. Isso seria vulnerável se aberta a usuários; não expor. Ainda falta endpoint seguro que amarre `auth.uid` confiável à chefia, autorização dos responsáveis para editar as tabelas privadas, e alocação manual verificando tanto origem quanto destino na equipe do gestor.
- Ainda não é regra aprovada que a redistribuição **automática** de um afastado só possa enviar para a mesma equipe. Por enquanto o destino é qualquer operador Prumo ativo com grant válido da loja, conforme I2; o gestor só pode comandar manualmente nos próprios supervisionados. A restrição de destinatário à mesma equipe deve ser fechada antes de produção, sem presumir decisão.
- A migração 047 antiga continua no histórico e os testes legados S1P-01..10 rodam **ANTES** da migration 048; jamais atribuir sua hipótese de gestor por loja ao estado vigente do produto. **Todos os resultados S1T exigem CI antes de aprovação.** Não houve merge/deploy.


## Resultado executado e limites — 19/10/2026

[**GitHub Actions PostgreSQL 17 #39242471186 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39242471186), commit ensaiado `4700a0b6f10ab0142a00de7948ab90733afaca57`, job `118026344950`. Logs inspecionados: **S1T-01..14 — 14/14 PASS**, incluindo concessão adicional da **loja C** ao mesmo operador sem alterar o vínculo com seu gestor; pausa global do operador A+B, redistribuição das duas lojas sem revogar concessões, equipe C separada, retorno sem retomada indevida e negações de autoridade entre gestores. Os testes legados S1P-01..10 passaram **antes da migration 048, como prova histórica de hipótese superada**, não como regra vigente. As regressões S1A, S1R, S1X, S1H e AUD1/AUD2 também passaram.

**Veredito restrito:** contrato I11 corrigido e mecanismo físico de pausa/retorno ensaiado somente em PostgreSQL sintético. As tabelas de autoridade/gestão foram preenchidas por executor `postgres` fictício; não existe integração Auth/GoTrue/REST, API de responsável para grants, comando gerencial seguro com `auth.uid()`, nem controle de distribuição por equipe ponta a ponta. Nenhum merge, deploy ou dado real.

---

## Retificação de contrato — issue #10 (20/10/2026)

**As seções históricas que descrevem suspensão da conta, redistribuição integral e bloqueio de leitura não são mais o comportamento de produto desejado.** Elas documentam apenas o que a migration 048 fazia à época dos testes I11. Pela nova decisão [D], pausa de novos leads é dimensão diferente de estado de conta e concessões: o gestor não suspende a conta, não revoga grants e não exige justificativa, motivo ou data de volta. Redistribuição automática só dos casos com ausência de início humano **comprovada transacionalmente pelo S0**, dentro da mesma equipe e com grant válido; casos iniciados e sem substituto continuam atribuídos. Não inferir que o núcleo já prove isso.

A fixture de desenvolvimento `supabase/tests/s1_053_issue10_disponibilidade_local_only.sql` aplica, após regressão histórica, a separação de disponibilidade com CAS, trilha mínima, bloqueio de novas atribuições e negação dos comandos legados; **deliberadamente não redistribui** sem prova S0. Não é migration operacional e não altera o Supabase hospedado. [Documento de correção e dependências](S1_002_ISSUE10_CORRECAO_PAUSA_INTAKE_2026_10_20.md). [CI dedicado #39458246432](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39458246432): 11/11 novas provas PASS, além da regressão histórica. **NO-GO produção/merge/deploy**, nova API GoTrue/HMAC ainda pendente.
