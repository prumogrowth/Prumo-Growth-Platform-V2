# Prumo — C07: reconciliação de incerteza e falhas, somente simulação

**Data:** 17/10/2026. **Estado:** implementado e testado no PostgreSQL 17 descartável; **NÃO é operação Meta, homologação bancária ou ativação comercial**.

## 1. Bases e limites normativos
- `26_Contratos_Conceituais_Eventos_APIs_v0_1.md`, C07/C08/C09/C23, CT-14/15: resultado incerto não autoriza reenvio cego, callback sem correlação permanece pendente, falha/aceite não provam envio.
- `37_Playbooks_Excecoes_Banco_WhatsApp_Estados_v0_1.md`, PB-06/07/08 e DEC-13–15 **[R/V]**: template final falho/incerto não inicia 24h nem marca perdido. Segunda falha qualificada exige deliberação própria, NÃO deriva de dois eventos técnicos.
- `39_Protocolo_Validacao_Confiabilidade_RLS_Retencao_Recuperacao_v0_1.md`, REC-04, RES-04/12: incerteza após queda do executor, retentativa sem duplicação e duas reconciliações concorrentes.
- `41_Decisao_Aprovada_Matriz_Permissoes_Gestor_Operador_MCP_v1_0.md`: gestor lê registros da própria loja; nunca dar a operador ou MCP escopo global ou mutação arbitrária.

**Invariante multiloja:** o telefone de um cliente pode existir em A/B/C com históricos independentes. O número emissor de atendimento da Prumo pertence exclusivamente a uma concessionária. Não foi criada identificação global de pessoa.

## 2. Implementação

### Migration 020 — fila rastreável e revisão versionada
- `pendencias_reconciliacao_c07_sinteticas` cria pendências de `SEM_CORRELACAO`, `RESULTADO_INCERTO`, `FALHA_REPORTADA` e `SINAIS_CONTRADITORIOS` por evento e loja. A classificação NÃO interpreta sinais simulados como provas da Meta.
- Trigger após a entrada de callback simulado faz a triagem transacional. Entrega, aceite, leitura e falha contraditórios permanecem na trilha técnica, sem sobrescrever registros anteriores.
- `associacoes_callback_c07_sinteticas` registra vinculação **fictícia confirmada em revisão** apenas após comparar emissor da loja e referência exata. O callback originalmente não correlacionado permanece intacto.
- `auditoria_reconciliacao_c07_sintetica` registra ator, justificativa, versão anterior, decisão e eventual vínculo. `conciliar_pendencia_c07_sintetica` exige gestor ativo da loja, chamada interna privilegiada, `expected_version` e justificativa de 10–500 caracteres; repetição exata é idempotente.
- Decisões permitidas apenas em simulação: `ENCERRAR_SEM_PROVA` ou `VINCULAR_SINTETICAMENTE`. **Nenhuma** prova envio real, qualifica falha, resolve decisão Meta, permite recontato ou faz transição comercial.
- `diagnosticar_falhas_c07_sintetico` conta **tentativas distintas** com falha/incerteza, incluindo evento vinculado manualmente. Retorna `NAO_AVALIADAS_DEC_15`, nunca `segunda falha qualificada`.

### Migration 021 — bloqueio conservador de novas tentativas
- O planejador C05 recusa novo plano do mesmo ciclo quando já existe observação de falha/incerteza, mesmo após encerramento de revisão e cancelamento de plano anterior.
- A reserva C06 não libera a próxima tentativa do plano quando existe observação de falha/incerteza, mesmo que seja outro ID de evento do mesmo envio.
- Eventuais callbacks atrasados ou contraditórios não recriam um envio cancelado, não executam retry e não iniciam contagem de 24 horas. Nenhuma função envia algo à Meta.
- A versão da função C05 preserva respostas C04 `estado_plano` e `executavel_simulacao`; a primeira regressão descobriu a perda desses campos, corrigida antes do aceite.

## 3. Evidências
- [PostgreSQL 17 #39078241536 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39078241536): `C07-REC-01..05`, regressões C01/C02/C04/C05/C07/C08 e simulações de falha/opt-out.
- [PostgreSQL 17 #39078390224 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39078390224): `C07-REC-RACE` com dois clientes PostgreSQL concorrentes. Uma decisão auditada; reentrega idempotente.
- Script Auth/REST foi **preparado** com `AUTH-11` para a tabela de callback, fila, associações e auditoria C07. **Não foi executado** nesta etapa, conforme política de economia GitHub; não confundir teste escrito com PASS.
- Todos os dados, destinatários, envios e mensagens são fictícios.

## 4. Bloqueios para uso real
- Nenhuma autenticação de webhook Meta, ID externo oficial validado, prova legítima de envio, dead-letter operacional, API Meta conectada ou fila de trabalho com UI real.
- `p_ator` é argumento de função interna usada por `postgres`; antes de expor isso, um adaptador autenticado deverá derivar ator/loja do contexto confiável, nunca da mensagem do navegador.
- Fechamento da revisão `ENCERRAR_SEM_PROVA` não libera retry: é apenas registro de análise. Faltam decisões DEC-13/14/15, política de classificação de falhas e homologação Meta.
- O histórico é protegido contra escrita de usuários comuns e alterações feitas pelas funções de domínio; não é trilha criptograficamente imutável frente ao superusuário.
- Faltam RLS via Auth/REST real após as migrations 019–021, tests de recovery, LGPD, retenção, Storage D3/D4, Banco e critérios de produção. Preservar PR como DRAFT e Supabase remoto sem migrações comerciais.

**Gate:** GO apenas para continuar engenharia segura em sandbox. NO-GO para produção, merge, Meta, banco real, envio/retentativa automática ou declaração de `perdido` com base em callback fictício.
