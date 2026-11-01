# OFF-15 — Pré-homologação independente: fronteiras entre F01/F02/F03

**Data:** 01/11/2026. **Status:** novo lote de testes de segurança, exclusivamente **OFFLINE**. Este trabalho pertence à **preparação da etapa 12**, não à integração física nem à aceitação de contratos. Não implementa endpoints ou funcionalidades de negócio.

## Motivo e independência

O roteiro OpenAI está com a **etapa 08B/08C dependente das definições S0/S1/Meta**. Em vez de criar outro adaptador que pressupõe um contrato inexistente, esta frente avança no que independe da S0: prevenir que relatórios e *fixtures* de laboratório sejam convertidos indevidamente em autorização comercial, de envio, conteúdo, escrita ou produção.

**Base imutável:** OFF-14 [`df5a2ecafbd468cc0f45a83a2a21826ad4d96c75`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/commit/df5a2ecafbd468cc0f45a83a2a21826ad4d96c75), [CI 864/864](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41296787271). Incremento novo apenas de teste/documentação/workflow, sem alterar os códigos dos quatro consumidores testados.

## Escopo de teste

Arquivo `e04_offline_lab/tests/off15-cross-boundary-regression.test.mjs`: 44 regressões cruzadas sobre quatro módulos **já versionados**:

- **F01 posse** `reviewF01S0Ownership`: handoff / readback reivindicados sem autenticação S0.
- **F01 conhecimento** `reviewF01CommercialSources`: fonte aprovada em fixture não é oferta semântica/real.
- **F02 transporte** `previewWa39F02Projection`: `API_ACCEPTED` não é prova de envio.
- **F03 histórico** `reviewF03S0Metadata`: `REVIEW_ONLY_NOT_FROZEN` não é histórico completo.

### Matriz adversarial de 44 testes

| Grupo | Total | Requisito |
|---|---:|---|
| Revisões positivas continuam sem autoridade | 4 | Resultados coerentes permanecem `UNVERIFIED` |
| Envelope de domínio A forjado com versão de B | 12 | Rejeição de esquema/campos mesmo ao mudar versão |
| Resultado positivo A forjado como entrada B | 12 | Nenhum *handoff* implícito entre consumidores |
| Campo `publishAuthorized/fieldApplicationAuthorized/...` injetado | 4 | Rejeitar alegações de autorização |
| Dados cíclicos | 4 | Falha fechada sem estouro |
| Propriedade accessor/getter hostil | 4 | Não executar código do chamador na validação |
| Escopo de concessionária incompatível | 4 | `DENIED` sem refletir identificadores |
| **Total** | **44** | Sem grants e com saídas congeladas |

**Limites da evidência:** revisões são assertivas em inputs sintéticos, executadas pelo Node 22.16.0 no GitHub Actions. Não testam PostgreSQL/GoTrue físico, autenticação do host S0, provas de Graph, concorrência SQL, LLM real, LGPD/semântica comercial, conteúdo/mídia, API ou publicação. Não fornecem autorização e não substituem as Issues #5/#6/#7/#9/#11/#12.

## Marco da etapa 12 (parcial)

**12A — regressão transversal e isolamento de contratos: teste preparatório**, independentemente de S0 e Meta.

**12B — testes físicos autenticados, concorrência, readback e contrato aceito: BLOQUEADO até interfaces versionadas/homologadas pelas frentes.**

**12C — aceite final e entrega operacional: NÃO INICIADO / sem autorização.**

A aprovação do CI dos **908 testes** (864 herdados + 44 novos) conclui somente **12A como laboratório**, nunca a etapa 12 por inteiro.

Arquivos desta branch: suíte nova; este documento; roteiro mestre de progresso; workflow de teste. Nenhuma modificação `backend/`, `integrations/`, `frontend/`, `supabase/`, scripts de execução de produção, modelos ou banco.

**Nenhum merge, deploy, dado real, tentativa de envio, alteração comercial ou aprovação S0/Meta.**
