# S1-002/I10 — Matriz de autoridade: responsável, gestor e operador

**Decisão de negócio [D] explicitamente confirmada em 19/10/2026.** Proprietária: S1-002. Referências: D-ORG-01, D41, CF-OP-02 e I9. Esta decisão prevalece sobre qualquer indicação anterior de que um gestor não pode administrar operadores.

## Regra aprovada

| Ação | Responsável | Gestor | Operador |
| --- | --- | --- | --- |
| Adicionar novo operador | Sim, somente responsável | Não | Não |
| Adicionar novo gestor | Sim, somente responsável | Não | Não |
| Remoção/desligamento definitivo de operador | Sim, somente responsável | Não | Não |
| Remoção/desligamento definitivo de gestor | Sim, somente responsável | Não | Não |
| Desativar temporariamente operador existente | Sim | Sim, no escopo sob sua gestão | Não |
| Reativar operador temporariamente desativado | Sim | Sim, no escopo sob sua gestão | Não |
| Mover atendimento de um operador para outro | Sim | Sim, na própria concessionária | Não |
| Redistribuir carteira e ajustar distribuição | Sim | Sim, na própria concessionária | Não |
| Administrar outro gestor ou um responsável | Responsável dentro da própria competência | Não | Não |

"Gestor pode administrar operadores" abrange as demais operações operacionais autorizadas, **sem** ampliar os dois poderes exclusivos do responsável: inclusão de novos profissionais e desligamento definitivo. O gestor precisa estar ativo na Prumo e com concessão válida da concessionária. Um operador que possua também papel de gestor/responsável na loja não pode ser tratado como subordinado operador por mera existência da concessão `operador`.

**Preservar a separação D41:** um gestor pode distribuir e supervisionar toda a carteira D2 de sua concessionária, mas não vira executor de um caso sem autoatribuição autorizada. Somente S0 decide e registra status comercial, mensagens, atendimento concluído ou retornos, e nenhuma redistribuição pode ampliar janela Meta nem reabrir venda.

## Escopo do comando e da suspensão

Um profissional Prumo pode atuar em A+B. O gestor de A pode intervir na carteira e na disponibilidade do operador **somente na loja A**, sem suspender globalmente o operador de B. **`equipe_prumo_s1.estado` é global**, então seria erro usá-lo diretamente para uma desativação temporária isolada por gestor. A implementação posterior deve representar suspensão/reativação **por vínculo de loja**, refletir imediatamente a alteração nas políticas RLS e destinatário de novos inbound, e disparar redistribuição transacional apenas para os casos da loja A. A remoção definitiva por responsável é diferente de suspensão temporária: preservar registros e autorias, e não fazer `DELETE` físico de histórico.

## Implementação sintética I10

`202610190047_s1_matriz_autoridades_responsavel_gestor.sql` adiciona apenas o predicado privado `s1_pode_administrar_operador(solicitante,loja,acao,alvo)` para demonstrar os limites na base PG17. A função recebe identidade por argumento **apenas em simulação interna**, com `EXECUTE` revogado para `anon/authenticated/service_role`. **Não é um ponto de entrada seguro para usuários nem uma RPC exposta.** A implementação real requer autenticação confiável, seleção de loja autorizada no backend, validação de alvo e caso, edição limitada/atômica e trilha append-only. O predicado conservador recusa alvo pendente no papel gestor: pendente representa novo ingresso de pessoa, reservado ao responsável.

Os cenários S1P-01..10 devem provar inclusão e desligamento restritos, supervisão operacional do gestor, divisão A/B, proibição de administração de outros gestores/responsáveis, níveis inativos e nenhuma exposição da função parametrizada ao cliente.

## Dependências explícitas [R/V]

1. Escolher a operação backend/S0 que autoriza remanejamento manual e recebe nova atribuição, mantendo autoria e único dono.
2. Formalizar pausa/reativação por concessionária na S1-002 e aderência às RLS existentes no núcleo (sem interferir em lojas independentes).
3. Integrar Auth/GoTrue/PostgREST/gateway, registrar solicitante validado no histórico e testar cenários de privilégios e competição entre gestores.
4. Operação de ingresso de profissional existente no Auth versus convite/criação de credencial deve ser contratada entre núcleo e S1; o gestor nunca pode fazê-lo.
5. Sem merge, SQL hospedado, dados reais ou habilitação pública nesta atualização. Percentual global não é alterado por documentação ou teste de matriz.


## Evidência de validação I10 — PostgreSQL 17 sintético

[CI #39233937724 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39233937724), SHA `da9560d7859bdf51d771b1f996356e840fc346d6`, job `117998333814`: **S1P-01..10, 10/10 PASS**, incluindo responsável como único autorizador de inclusão e desligamento, gestor para redistribuir/mover/suspender temporariamente apenas operador previamente vinculado da própria loja, negação a gestor inativo, operador, casos de papel misto e concessão em outra loja, além do predicado não exposto a `authenticated`. Regressões históricas no mesmo job também passaram (S1A 9/9, S1H 8/8, AUD1 7/7 e AUD2 5/5, entre outras).

**Atenção:** o predicado é apenas prova interna de matriz [D] em SQL sintético. Não habilita operação administrativa real, JWT válido, REST, suspensão per-store, operação de inclusão/desligamento nem adoção em produção. O bloqueio I9 de DML direto continua correto. Teste de login real e execução de comandos autenticados ainda pendentes [R/V].
