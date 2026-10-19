# S1-002 — Auditoria corretiva de casos humanos sobre ciclos históricos | 18/10/2026

**Status:** [D] alinhamento com normas aprovadas; [P] reparo físico na branch S1-002; [R] homologação S0 do envelope pós-humano e demais frentes. PR #5 continua Draft sem merge/deploy. Somente dados simulados em PostgreSQL local.

## Falha real identificada

As migrations S1-002 039/041 e 042/043 assumiam `vendido` ou `perdido` como terminal para TODO `CASO_HUMANO` que apontasse ao ciclo. Isso é falso: doc.22 ATD-VENDIDO-RET-01 [D] obriga nova solicitação **exclusivamente humana** após contato espontâneo de cliente já vendido, preservando o ciclo original como `vendido` e o histórico bancário. Doc.26 C02 confirma novo `CASO_HUMANO` referenciando o ciclo, sem reclassificá-lo. O próprio S0 já fornece `casos_humanos.motivo_simulado` na migração 009: `retorno_pos_venda`, `retorno_pos_remessa`, `manter_humano`, `revisao_humana`. A nova solicitação humana poderia perder sua atribuição e ficar fora de recuperação apenas porque o ciclo ANTERIOR era vendido. O teste de 100 pendências I7 não incluía retorno pós-venda; PASS anterior não provava este cenário.

## Reparação proprietária S1-002, migration 044

- `prumo_private.s1_remanejar_ator`: considerar os marcadores S0 `vendido + retorno_pos_venda` e `perdido + revisao_humana` como **casos humanos operacionais distintos** do ciclo comercial histórico. Deixar que recebam redistribuição/filas por elegibilidade Prumo e loja. Apenas ciclo terminal SEM seu marcador correspondente recebe `ENCERRADO_HISTORICO`.
- `prumo_private.s1_recuperar_fila_protegida`: mesma distinção. Caso pós-venda/revisão pode sair da fila para outro Prumo ativo autorizado da mesma loja, respeitando impedimento de atribuir automaticamente ao antigo operador. Original vendido/perdido sem motivo de retorno só encerra pendência histórica.
- Sincronização: adicionar bloqueio de linhas de caso e ciclo comercial nos caminhos transacionais para que alteração concorrente de status não seja ignorada no instante de decidir atribuição; conciliação fina da ordem de locks S0/S1 depende de homologação e testes interfrentes.
- Não mudar qualquer dos oito estados comerciais, não registrar nova venda, não inferir recusa bancária, não ativar IA Vendedora, não alterar S0/Meta/OAI/FV, não criar calendário ou poder de RH.

**Casos normativos:** para `cadastro enviado ao banco`, retorno espontâneo com `retorno_pos_remessa` já era encaminhado a humano (status não terminal); preservar isso. Para `perdido`, `revisao_humana` é o marcador de uma nova solicitação humana no S0 simulado, não prova de recusa/venda e não reversão de status comercial.

## Testes adicionados [P até prova do CI]

`AUD1-01..07`: mesma loja com casos terminais originais versus retorno pós-venda, revisão pós-perda e retorno após remessa; suspensão do operador; redistribuir apenas as solicitações humanas ativas e manter histórico terminal; fila B com reativação de novo operador; ao novo grant recuperar retorno pós-venda sem mudar `vendido`; pendência histórica terminal continua sem novo titular; não misturar lojas via RLS; nunca atualizar estado comercial por causa de redistribuição. Retestar as baterias I2, I6, I7 **depois** da migration 044.

## Pendências identificadas na auditoria

1. Contrato completo de `caso humano operacional` (concluído, janela da conversa, retorno, remessa) ainda depende de projeção/validação S0 e futura integração, pois S0 em sandbox possui apenas `motivo_simulado`.
2. Pode haver dados legados sem o motivo correto; não é seguro inferir retorno por idade ou CPF. Essas fichas devem ser tratadas como **pendência de classificação**, não convertidas por heurística nesta frente.
3. Ainda faltam prova de corrida REAL entre S0 mudando status e S1 trocando responsável, autenticação GoTrue/REST real, algoritmo de escala/capacidade, alerta ao gestor e executor autenticado do backlog.
4. Testes de scripts PG17 não constituem autorização para serviço hospedado. Sem alterações em main, sem mensageria externa e sem avanço da porcentagem global.

**Veredito até CI:** divergência conceitual comprovada, reparação SQL candidata, ensaio ainda pendente.
