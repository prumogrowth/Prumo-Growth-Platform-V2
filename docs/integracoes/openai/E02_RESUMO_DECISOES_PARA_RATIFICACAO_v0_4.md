# E02-REV v0.4 — Encaminhamento enxuto de decisões para os donos

**22/10/2026.** Este documento é uma **minuta de revisão**, não mensagem efetivamente enviada, não aceite S0/S1/Meta/Prumo e não liberação de E04. A OpenAI prepara decisões para seus proprietários sem editar outras branches/issues.

## 1. Sete respostas objetivas que desbloqueiam design físico

| Decisão | Pergunta ao responsável | Consequência se não houver decisão | Evidência em proposta |
|---|---|---|---|
| **D1 — F03 identidade** | Qual identificador/ritual verificável liga múltiplos números a uma pessoa **dentro de uma loja**, sem fusão por similaridade? | F03 não pode garantir histórico multi-casos nem isolamento antifraude | CFI3-R02; SYN-07, 33, 69 |
| **D2 — F03 cutoff e histórico** | Como S0 atesta **manifesto de fontes de todos os casos** até fechamento humano, sem fingir que o hash do caso atual o cobre? | Recibo S0 continua `VERIFIED_CONTRACT_PENDING`, sem histórico integral | CFI3-R01/03/04/08; SYN-08, 33, 34, 36, 37 |
| **D3 — F03 aplicação** | Qual esquema de catálogo/ficha/versões distintos e qual recheck atômico permitem aplicar propostas sem perder dados atuais? | Nenhuma aplicação automática F03 segura | CFI3-R05/06/09; SYN-09, 14, 15, 38, 42, 43 |
| **D4 — Humano** | Como UI/S0/S1 implementam conclusão e retorno de essencial ao Consultor/Gestor **sem edição manual de ficha**? | Contrato de Frontend antigo permanece incompatível | CFI3-R07; SYN-39, 40, 41 |
| **D5 — F02 pós-humano** | Qual evento autoriza solicitação **separada** à F02; quais finalidades/versões/limites ficam disponíveis por loja? | Recontato pós-humano não pode ser planejado/enviado como novo contrato | F02C-R01/02/05; SYN-47, 48, 49, 55, 56 |
| **D6 — C09/Meta** | Quais estados/fases permitem C09, como se prova `sent` final e o que é erro definitivo consecutivo? | Perda por silêncio/erro é bloqueada sem motor determinístico S0 | F02C-R03/04/07; SYN-50, 51, 52, 53, 54 |
| **D7 — Conhecimento/MCP/privacidade** | Qual ACL/versão para base/fato e operação MCP de confirmação/auditoria protegida; quais mídias podem ser recuperadas/exportadas? | Sem RAG/habilidades/MCP físico ou envio multimodal | REV-07/08/09; SYN-57..70 |

**Precedência:** diretrizes AL-IA vigentes; não aprovar por omissão mudança de `vendido`, prova bancária, permissão local, cadastro manual ou F02 automática. Integração Banco permanece adiada.

## 2. Como registrar decisão válida

Para cada D1–D7: **frente titular**, campo/regra exata, versão de contrato, decisão `ACEITO | COM_RESSALVAS | DEVOLVIDO`, link do aceite humano, compromissos e casos de regressão. Resposta informal, texto da IA ou silêncio **não** ratificam schema, efeito SQL ou permissão de mídia.

**Prioridade sugerida por dependência técnica [P]:** D1–D4 para liberar desenho físico F03; D5–D6 para F02/C09; D7 para conhecimento/MCP. A coordenação pode revisar em paralelo, mas não deve promover estágio bloqueado só porque outro tema foi aprovado.

## 3. Provas preparadas pela OpenAI

- [CFI-01 v0.3](./CFI_01_CONCILIACAO_PONTE_F03_INTERFRENTES_v0_3.md) e [manifesto histórico F03](./CFI_01_MANIFESTO_HISTORICO_F03_CANDIDATO_v0_1.md).
- [CF-OP-02/C09 v0.3](./CF_OP_02_C09_CONCILIACAO_F02_INTERFRENTES_v0_3.md).
- [E02-REV v0.3 — checklist com 12 gates](./E02_PACOTE_REVISAO_CRUZADA_E_GATES_v0_3.md).
- [E02-FIX/oráculos v0.4 — 70 casos](./E02_CADERNO_70_ORACULOS_E_OBSERVAVEIS_v0_4.md), todos **EXPECTED**, sem ACTUAL medido.

**Gate vigente:** G-FASE-DO-PROJETO requer **liberação expressa** de implementação E04. "Prossiga" genérico autoriza avanço documental, não revoga o gate. E05 necessita autorização separada de credenciais, orçamento, ambiente e privacidade.
