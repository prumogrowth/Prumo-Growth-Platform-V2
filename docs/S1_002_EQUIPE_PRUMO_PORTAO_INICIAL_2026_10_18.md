# S1-002/I1 — Portão inicial da equipe Prumo (18/10/2026)

**Status:** candidato de engenharia sintética em branch privada separada; PR Draft a abrir. Não há migração no Supabase hospedado, merge, frontend autenticado ou dados reais.

## Base D-ORG-01, sem reconstrução da S0
`public.atores` já modela identidade, `public.vinculos_papel_escopo` concessões multiloja e `public.atribuicoes_humanas` atribuição por caso. O vínculo profissional continua com a **Prumo**, jamais com a concessionária. Esta etapa agrega somente `public.equipe_prumo_s1(ator_id,estado)`, sem concessionária/empregador, com estados `pendente/ativo/suspenso/desligado`, e `equipe_prumo_eventos_s1`, auditoria SQL de transições.

A migration `202610180038_s1_equipe_prumo_gate.sql` acrescenta **políticas restritivas `FOR ALL TO authenticated`** nas tabelas públicas com RLS existentes no momento da instalação. Ser `ativo` na equipe é condição **adicional** às permissões S0 de escopo, papel e caso; não cria permissões. Somente o próprio profissional lê sua linha de equipe. Nenhuma escrita de estado/auditoria é concedida a `anon` ou `authenticated`; funções novas são triggers SECURITY INVOKER no esquema privado, não RPCs.

## Verificação planejada
Executar `bash scripts/run-s1-002-local.sh` apenas com `PRUMO_TEST_DATABASE_URL` apontando para PostgreSQL 17 local descartável `prumo_s0_test_*`. O script roda regressões S0 **antes** da 038, aplica 038 e valida `S1E-01..07` com BEGIN/ROLLBACK. CI independente em `.github/workflows/s1-002-postgres.yml`, com orçamento limitado. **Antes de conferir o job, nenhum teste S1E deve ser chamado PASS.**

## Limites de segurança/decisão (ainda pendentes)
1. **Fonte administrativa confiável:** identidade real de quem aprova admissão, suspensão, desligamento, motivos e segregação de deveres não foi decidida nem implementada. DML de protótipo ocorre apenas por `postgres` descartável; a tabela não é RH nem prova trabalhista.
2. **Remanejamento de carteira:** suspensão corta acesso por RLS, mas deixa `atribuicoes_humanas` tecnicamente ativas; reativação pode expor caso antigo. Próximo incremento deverá encerrar/redistribuir transacionalmente com locks, auditoria por caso, revalidação de autorização e política de reativação. Revogação por concessionária também deve disparar esse processo sem prejudicar outras concessões.
3. **Escala/dedicação:** ainda não modelada; jamais concede acesso. `shopId` da S1-001 é somente contexto de demo.
4. **Cobertura:** políticas adicionadas apenas às tabelas existentes com RLS e operações de papel `authenticated`; não substituem proteções internas de wrappers comerciais `SECURITY DEFINER postgres`. Novas tabelas exigem revisão; Auth/REST GoTrue após 038 e regressão S0 *após* 038 ainda não foram provados. D3/D4 não foram concedidos.
5. **Meta/WhatsApp:** não muda contrato ou código do PR #2. Conservar DEC-WA-01/02/03/05, exclusividade emissor e telefone de cliente isolado por loja. A frente Meta deve saber que suspender agente humano não equivale a revogar canal/APP, nem autoriza ignorar direitos humanos no futuro backend. DEC-WA-04/06 continuam pendentes.

**GO somente para ensaios locais sintéticos após validação; NO-GO** para API pública privilegiada, produção, merge, migração hospedada, autenticação de equipe real, instituição financeira, Meta, OpenAI e n8n.

## Evidência executada

[PostgreSQL 17 #39145994842 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39145994842), commit `bbe123aa18098848d9f9c936f4f0e02be57447af`. Foram conferidos os sete marcadores S1E-01..07, incluindo suspensão A+B e duas atribuições mantidas tecnicamente ativas. A regressão S0 passou no mesmo job **antes da instalação da 038**; não inferir GoTrue/REST integrado nem nova prova das wrappers legadas. 


## Complemento contratual CF-OP-02/I2 — redistribuição automática

A regra de negócio agora exige remanejamento AUTOMÁTICO no instante de suspensão/desligamento/revogação de concessão, bloqueando novas atribuições e mantendo em caso operacional a conversa pendente, concluída com janela ativa e cadeia de templates pós-humana. O I1 atual ainda deixa atribuições antigas; portanto não confundir 7/7 S1E aprovados com contrato I2 implementado. Responsabilidades, casos elegíveis provisórios, regras de não vazamento e testes futuros: [S1-002/I2](S1_002_I2_CONTRATO_REMANEJAMENTO_AUTOMATICO_CF_OP_02_v0_1.md). Coordenação com S0 em PR #7 e issue #6. **Nenhum teste I2 ou migração adicional executados aqui.**
