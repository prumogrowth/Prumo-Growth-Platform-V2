# WA-18B — Complemento decisório: edição Meta, variáveis congeladas, opt-out e falhas de cadência
> **Atualização (WA-18C) com precedência sobre a dúvida residual de falhas e acréscimo de categorias internas:** o responsável definiu que um envio tecnicamente confirmado **zera o contador de falhas imediatamente, mesmo sem resposta do cliente**. As duas falhas precisam ser de templates consecutivos do mesmo fluxo, independentemente do tempo decorrido. Também decidiu que templates devem ter **categorias internas e políticas de disponibilidade por IA/operador/campanha/abertura/recontato**, separadas de `MARKETING`/`UTILITY` da Meta, para evitar promessa comercial inadequada. A modelagem exata dessas categorias ainda é proposta, não implementação. Veja [WA-18C](./wa18c-falhas-consecutivas-taxonomia-interna-templates-2026-10-20.md).


**Data:** 20/10/2026. **Natureza:** resposta expressa do responsável e auditoria da S0 já implementada. **Somente documentação; nada executado em Graph/SQL real, sem merge/deploy.** Este complemento **substitui** os itens incompatíveis de `wa18-alinhamento-decisorio-respostas-responsavel-2026-10-20.md`. O trabalho permanece em pausa para revisão e alinhamentos.

## 1. Novas decisões expressas do responsável

### WA18B-01 — Edição de template aprovado é permitida *se a Meta permitir*
A interpretação anterior de imutabilidade integral foi corrigida: o responsável aceita editar um template aprovado **quando a API e o estado do template efetivamente permitirem**, inclusive por IA administrativa delegada via futuro MCP, com segunda confirmação do responsável e auditoria. Não presumir que toda alteração mantém o estado `APPROVED`; consultar regras da API por operação/estado e acompanhar eventual reanálise. **Manter snapshots/versões internas imutáveis dos envios anteriores**, mesmo quando a Meta conserva o mesmo identificador técnico ou altera conteúdo. Não converter edição em aprovação automática. Referência oficial: [Edit template — Postman Meta](https://www.postman.com/meta/whatsapp-business-platform/request/bpcsm6i/edit-template).

### WA18B-02 — O vínculo de variáveis de cada versão aprovada é congelado
- `{{1}} -> cliente.nome`, `{{2}} -> motocicleta.modelo_interesse` etc. são definidos na preparação administrativa do template e **não podem ser trocados nessa versão depois da aprovação**. A edição admissível via Meta requer nova revisão de conteúdo/mapeamento com histórico/versionamento, sem mutar o vínculo usado nos envios históricos.
- **A plataforma, e nunca a IA Planejadora/Vendedora, resolve os valores de cada variável na hora do envio.** A Planejadora escolhe template/versão/ordem/quantidade/horário; o backend lê dados permitidos da concessionária correta, valida tipo, formato e ausência de valor e constrói parâmetros da Meta. Ausência de valor bloqueia aquele disparo e é registrada; não preencher com hipótese da IA nem texto improvisado.
- **Catálogo de fontes derivado do esquema dos leads:** a estrutura definitiva da tabela de leads ainda não está decidida, portanto não fixar agora lista de campos. Quando novas colunas de negócio forem criadas, elas poderão aparecer como fontes candidatas no registro de variáveis (nome, telefone, email, modelo de interesse, etc.) sem escrever contratos por coluna individual. **Não equivale a liberar indiscriminadamente segredos, IDs internos, evidências financeiras, dados sensíveis, permissões ou metadados técnicos.** Registrar elegibilidade e finalidade por fonte; o dado efetivamente autorizado é selecionado pelo backend e pela política Meta/LGPD.
- Fontes derivadas do cadastro são `field_id`/chaves estáveis: não confiar em nome de coluna arbitrário fornecido pela IA, não fazer SQL dinâmico com dados de entrada, não permitir referências de outra concessionária, e não tratar coluna removida/renomeada como valor disponível.
- Variáveis de BODY, HEADER e URL dinâmica de botão exigem validação e snapshot de fontes por versão. A plataforma guarda referência ao campo, não copia informação pessoal para o texto-base.

### WA18B-03 — Regra EXATA de duas falhas consecutivas, sem chamar IA para falhas comuns

> **FECHAMENTO 21/10 — a dúvida residual deste item foi respondida na WA-18C:** um template subsequente com **envio efetivo confirmado** zera o contador, **sem exigir resposta do cliente**; não depende do intervalo entre tentativas. Apenas duas falhas definitivas em tentativas consecutivas do mesmo fluxo produzem `perdido` técnico. Estado incerto não é sent nem falha confirmada. Além disso, “categorias internas” neste documento é terminologia SUPERADA: utilizar **finalidades de template** distintas de categoria Meta, com múltiplas finalidades e autorização independente. Ver [fonte canônica](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md) e [WA-18C](./wa18c-falhas-consecutivas-taxonomia-interna-templates-2026-10-20.md).


- O backend conta **duas falhas de envio consecutivas e tecnicamente comprovadas de templates do mesmo fluxo/cadência**. A primeira falha permite seguir para a próxima tentativa já planejada, sem acionar a IA Planejadora. A segunda falha consecutiva **cancela os envios restantes do plano** e atualiza o lead/ciclo para `perdido` com motivo `falha_sistemica_envio_template` (código conceitual, nome final em auditoria), com evidências e histórico preservados.
- Nunca contabilizar como falha comprovada: timeout isolado, falta de callback, `API_ACCEPTED`, estado `UNCERTAIN_EXTERNAL`, reprocessamento de webhook repetido ou falha sem escopo/tentativa correlacionada. Antes de contar, resolver incertezas conforme política WA-16; reenvio cego continua proibido.
- A IA Planejadora **não é acionada por erros normais de envio**; não tem autoridade para neutralizar automaticamente o contador. Regra de duas falhas é determinística do backend.
- Reabertura de lead `perdido` por falha sistêmica só por **nova importação/campanha iniciada por responsável** e revalidação de elegibilidade, não pelo próprio motor.
- **Ponto técnico ainda sujeito à auditoria:** distinguir qual sinal positivo interrompe a série de duas falhas, e qual evidência de Meta é considerada definitivamente falha. Não inventar timeout, prazo nem classificação sem evidência.

### WA18B-04 — Problemas de disponibilidade/validade de template são OUTRA via
- Se Meta **rejeitar, pausar, suspender ou invalidar** um template, bloquear o uso desse template e **acionar a IA Planejadora** nos fluxos afetados, com contexto mínimo de loja/WABA, template/versão, motivo/estado da Meta, plano vigente, elegibilidade e **somente modelos já disponíveis e aprovados**.
- A Planejadora **pode substituir, retirar, reordenar e mudar a quantidade de templates e horários** do plano, sem pedir criação de um novo template; se não houver alternativa, reduz/remove a etapa sem inventar novo modelo. A escolha deve permanecer submetida aos gates de plataforma (janela, opt-out, situação comercial, escopo, concorrência, número permitido de tentativas).
- A Planejadora **não entra no MCP administrativo para criar templates quando falta um substituto**, não aguarda template inédito nem deixa fluxo automaticamente pendente de aprovação futura. IA administrativa do responsável via MCP é processo separado.
- Persistir revisão do plano, cancelamento dos envios antigos, versão de catálogo escolhida e auditoria da decisão; não ressuscitar agendamentos obsoletos.

## 2. Resposta comprovada sobre o opt-out: já há suporte sintético na S0

**Existe tabela física em laboratório, não apenas ideia.** Migração `supabase/migrations/202610170016_c04_elegibilidade_optout_sintetico.sql`, PR #1:
- `public.supressoes_contato_sinteticas`: `id`, `concessionaria_id`, `lead_id`, `canal_id`, `finalidade`, `evento_origem`, `criado_em`, FK de lead e canal na mesma concessionária, índice `(concessionaria_id,lead_id,canal_id,finalidade)` e RLS com leitura por gestor autorizado.
- `prumo_private.registrar_optout_sintetico`: registro idempotente por evento no escopo, valida lead/canal, cancela `planos_recontato_sinteticos` ativos e `envios_template_sinteticos` programados/reservados do respectivo escopo e registra `eventos_envio_template_sinteticos`. Não apaga mensagem nem contexto histórico. A função só autoriza `current_user='postgres'` local.
- `prumo_private.verificar_contato_sintetico`: se existe supressão no mesmo `loja+lead+canal+finalidade`, retorna `INELEGIVEL/OPT_OUT` antes de confirmar elegibilidade sintética.
- Migração `202610170018_c04_inbound_pos_optout_humano.sql`: inbound espontâneo depois de opt-out **não é consentimento novo e não reativa automaticamente IA**; roteia o caso previsto para revisão humana.
- Documentação [C04](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/C04_ELEGIBILIDADE_OPTOUT_SIMULADO_2026_10_17.md) contém testes e distinção de laboratório. **Não há opt-out real/Meta/LGPD homologado.**

**Diferença importante para auditar:** a nova decisão de produto é o contato com a **concessionária A**, e não B. Como a tabela sintética restringe por **canal + finalidade**, a futura política operacional terá de garantir que um pedido inequívoco de parar contato **com A** bloqueie os envios proativos pertinentes por A, inclusive em eventual mudança técnica de canal dentro da mesma loja. Não inferir bloqueio global de B, tampouco herdar opt-in de A na B. A amplitude das finalidades está sujeita à Meta/LGPD; não inventar decisão sobre todas as finalidades a partir de `recontato_comercial_sintetico`.

## 3. Lacuna física comprovada sobre duas falhas

Em `supabase/migrations/202610170020_c07_reconciliacao_falhas_sintetica.sql`, `prumo_private.diagnosticar_falhas_c07_sintetico` **já conta sinais reportados por tentativas distintas, incertezas e pendências**, mas retorna expressamente `falhas_qualificadas = NAO_AVALIADAS_DEC_15`, `acao = SOMENTE_DIAGNOSTICO` e `reenvio_automatico = PROIBIDO`. Portanto o **contador determinístico final de duas falhas consecutivas com `perdido` técnico ainda NÃO está implementado**, embora a diretriz de duas falhas já estivesse no doc 11 e no 35. Esta sessão **fecha a saída comercial** após a segunda falha comprovada, sem produzir migration agora.

## 4. Conflitos documentais a reconciliar na auditoria

- **WA-18 anterior** dizia “template aprovado imutável”; o responsável corrigiu: **editar conteúdo pode ser permitido conforme a Meta**, com revisão/versionamento. **Imutabilidade é do vínculo de variáveis da versão já aprovada**, não uma proibição absoluta de editar via API Meta.
- **WA-17A/B** admitiam `configureVariableSources` depois de aprovado: essa capacidade deve ser bloqueada no contrato operacional de edição da mesma versão e testada numa futura etapa autorizada. Não foi corrigido código nesta fase de alinhamento.
- Documentos `13_Matriz_Estados_Eventos_Responsabilidades_v0_6.md` e `26_Contratos_Conceituais_Eventos_APIs_v0_1.md` tratavam duas falhas como cancelamento sem `perdido` automático; agora há decisão expressa: **duas falhas definitivas consecutivas → cancelar o plano e `perdido` com motivo técnico**. A execução exige correlação/verificação e teste de concorrência.
- `C04` é protótipo por loja/lead/canal/finalidade, enquanto decisão nova exige que o opt-out da concessionária A não interfira na B e seja respeitado nos envios proativos da A.
- As demais decisões anteriores (WABA individual por concessionária, MCP de outra frente, identidade individual e segunda confirmação, templates isolados) continuam.

## 5. Próxima discussão possível, apenas se necessária

**Único refinamento técnico de contabilização mais importante:** quando uma tentativa falha definitivamente, e a próxima tentativa tem sinal técnico positivo, qual evento quebra a consecutividade? `sent` comprovado, `delivered` comprovado ou resposta humana recebida? A resposta Meta `API_ACCEPTED` não deve resetar o contador sozinha sem decisão expressa. Enquanto não definido, usar regra conservadora e **não inventar**.

**Outra validação futura de segurança:** como derivar **variáveis elegíveis** da tabela de leads sem expor automaticamente campos protegidos/sensíveis, incluindo campos gerados futuramente, e sem acoplar aprovação de template a nomes de coluna que mudem.

## 6. Status

Somente documento e coordenação; nenhum SQL novo, nenhuma alteração do código WA-16/17, nenhum servidor MCP, Graph ou Supabase real. PRs #1/#2/#5 continuam Draft. CI da WA-16/17 nativa continua não comprovada nesta rodada, e isso não muda com o alinhamento.
