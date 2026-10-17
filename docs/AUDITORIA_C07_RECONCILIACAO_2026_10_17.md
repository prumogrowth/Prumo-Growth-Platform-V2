# Auditoria C07 — reconciliação de resultados incertos e falhas (17/10/2026)

**Abrangência:** repositório privado `prumogrowth/Prumo-Growth---Platform`, branch `feat/s0-fundacao-prumo`, migrações 019–022 e regressões anteriores. Não é auditoria de instalação de produção. Não houve comunicação real com Meta, Banco, OpenAI ou n8n.

**Parecer:** **GO somente para prosseguir engenharia sintética controlada; NO-GO para produção, merge ou migrations remotas.** Um teste PASS cobre os cenários executados, não prova ausência de todo defeito.

## 1. Referências normativas confrontadas

- Documento **26** (C07, C08, C09 e C23): canal e identificador externo confiáveis, idempotência, callbacks tardios/fora de ordem, reconciliação e proibição de reenvio fictício; sem prova efetiva de envio, não se avança o estado comercial.
- Documento **37**, PB-06/07/08 e **DEC-13/14/15 [R/V]**: aceite/timeout/falha técnica não iniciam as 24h; duas falhas de callback no mesmo envio não são duas falhas qualificadas; retentativa depende de decisão humana e fornecedor.
- Documento **39** (REC-04, RES-04 e RES-12): simular queda/resultado incerto e duas reconciliações concorrentes sem duplo efeito. Essa evidência não valida retorno real da Meta.
- Documento **41**: gestor limitado à concessionária vinculada, operador sem leitura global ou escrita arbitrária; funções privadas não acessíveis pela Data API.

**Regra A/B/C mantida:** mesmo telefone de cliente pode aparecer em várias concessionárias com históricos separados; um número emissor de atendimento Prumo pertence exclusivamente a uma concessionária.

## 2. Resultados da auditoria

| ID | Achado | Ação | Prova |
|---|---|---|---|
| AUD-C07-01 | Repetição de chave idempotente no C05 retornava `executavel_simulacao=true` sempre que o plano estivesse `ativo`, inclusive após falha ou resultado incerto no mesmo ciclo | Migração **022** revalida prova fictícia, opt-out, vínculo humano, canal, estado comercial, tentativas programadas, templates e sinais técnicos de falha/incerteza | **PASS C07-AUD-01**: plano ativo com callback de falha retorna `ALREADY_APPLIED` e `executavel_simulacao=false` |
| AUD-C07-02 | Consulta de pendências do diagnóstico não contemplava associação manual posterior de callback originalmente não correlacionado | Migração **022** considera também `associacoes_callback_c07_sinteticas` na junção de pendências ao ciclo | SQL validou a migration; a suíte não contém um cenário isolado que demonstre diferença de contagem, pois a vinculação atual encerra a pendência no mesmo commit |
| AUD-C07-03 | Necessidade de preservar provas de versões anteriores após nova função C05 | Regressão existente `C04-REPLAY` continua aplicada; migração 022 parte da versão 021 | PASS da suíte PG 17 completa |
| AUD-C07-04 | Controle de concorrência e fronteira de loja | Preservada revisão versionada com `expected_version`; teste de duas conexões e negativa interlojas | PASS `C07-REC-RACE`, `C07-REC-03`, `C07-REC-05` |
| AUD-C07-05 | Falha/incerteza não é comprovação de envio e nem autorização de retry | Mantido bloqueio C05/C06 depois de sinal correlacionado; `falhas_qualificadas=NAO_AVALIADAS_DEC_15` | PASS `C07-REC-01/02/04` |

**Evidência:** [GitHub Actions PostgreSQL 17 #39079075704 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39079075704). Inspecionados os logs `C07-AUD-01`, `C07-REC-01..05`, `C07-REC-RACE`. Suíte completa também executou os testes anteriores C01/C02/C04/C05/C07/C08 num banco descartável.

## 3. Controles positivos já observados

- Incerteza, falha e contradição não mudam status comercial, não programam novo envio e não iniciam relógio final de 24 horas.
- Callback sem correlação confiável continua na fila; vínculo manual exige referência e canal idênticos, gestor ativo, versão e justificativa; evento original não é apagado.
- Reentrega de callback não cria nova pendência. Duas revisões idênticas concorrentes geram uma decisão auditada e um retorno `ALREADY_APPLIED`.
- Contagem de falhas é por tentativas técnicas distintas, **não** por número bruto de eventos; não conclui automaticamente que duas falhas são qualificadas.
- RLS no PostgreSQL local limita leitura por gestor de loja e nega escrita direta de papéis comuns nas novas tabelas.

## 4. Riscos e bloqueios remanescentes

1. **Auth/REST integrado ainda sem execução após migrations 019–022.** `AUTH-11` foi escrito, mas ainda não executado via GoTrue/PostgREST. Um teste em papel SQL não equivale a teste efetivo da Data API. A execução exige opt-in do responsável pelo custo via workflow GitHub e deve preceder homologação.
2. **Identidade de chamada interna.** As funções `prumo_private` restringem ao papel `postgres`, mas recebem IDs de ator nos parâmetros; um adaptador seguro deverá derivar o gestor do contexto autenticado, nunca aceitar ID arbitrário do cliente. Não expor esses RPCs.
3. **Callback externo desconhecido** não permite localizar com segurança qual ciclo bloquear até ser correlacionado; precisa fila/triagem, identificação de origem e política DEC-14. Não assumir que o bloqueio por ciclo cobre sinais não vinculados.
4. **Diagnóstico não é política de retentativa.** DEC-13/14/15 continuam **[R/V]**, inclusive tempo de espera, distinção de falha real e timeout, classificação e destino humano.
5. Não existem assinaturas/verificação de origem Meta, callback oficial, logs de envio real, transporte de mensagens, prova do primeiro/final template, confirmação de aviso+24h, ou reenvio autorizado.
6. Falta ensaio end-to-end de recuperação/restauração, política aprovada de retenção LGPD, imutabilidade frente a administrador privilegiado e auditoria de infraestrutura implantada.
7. As migrações candidatas estão **somente no GitHub**. O Supabase hospedado deve permanecer sem essas tabelas/migrações comerciais até autorização humana específica.

## 5. Próximo gate recomendado

Para continuar **programando**: GO sintético. Para aceitar **C07 pela Data API**: executar uma vez, deliberadamente, o teste Auth/REST atualizado e rever negativas/RLS dos quatro objetos C07, dentro do orçamento. Para habilitar **WhatsApp real**: NO-GO até conclusão de DEC-13/14/15, homologação Meta/LGPD, provas de envio, filas de recuperação, autorização e testes operacionais.

**Limite da conclusão:** a auditoria confirma integridade dos cenários executados; não certifica automaticamente operação segura com clientes reais.
