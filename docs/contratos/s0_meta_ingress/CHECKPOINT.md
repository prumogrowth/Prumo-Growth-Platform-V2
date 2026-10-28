# S0–Meta–Ingress–01 — checkpoint final para a orquestração

28/10/2026, America/Sao_Paulo. **S0_META_INGRESS_01_LAB_CLOSED**, recomendação técnica restrita ao laboratório, submetida à auditoria da orquestração. Não autoriza recebimento de eventos reais.

## Identificação e integridade

- Branch: `exp/s0-meta-ingress-01-20261028`.
- [PR Draft48](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/48), sem merge.
- Base direta congelada: `3cab3d57619cc1157698a08ac26f34e0c363f6dd`, branch-alvo `exp/s0-s1-i85-bootstrap-auth-diretor-20261028` conferida nesse SHA antes da abertura.
- Código final certificado: `9e3077d222df2b3184ee6ea568fdac7c9da75567`.
- Commit inicial: `564d89102dbd22a86e222d60a198510054fa901f`; revisão final exige grant técnico explícito por chave/canal e acrescenta T49.
- Este fechamento documental é posterior ao código. Seu SHA exato fica registrado no PR e no relatório entregue após o commit, evitando autorreferência impossível. Usa `[skip ci]`; não atribuir a CI abaixo ao commit documental. Nenhum arquivo executável/workflow/contrato operacional muda nesse fechamento.
- Diff total: 47 arquivos novos; 15 próprios em integration, 27 blobs originais copiados sem alterações, quatro documentos e um workflow. Manifesto completo em `integration/s0_meta_ingress/file-manifest.json`.
- Verificador: **PASS**, base fixa, histórico linear, diff integral/index/worktree/untracked inclusive ignorados. **364 arquivos herdados intactos**, 27 blobs de fonte íntegros. I85/I79–I84, contratos oficiais, migrations e workflows herdados preservados.
- Nenhuma consulta ao conteúdo da conversa/branch I86, incorporação, alteração de autoridade humana, deploy ou serviço hospedado.

## CI final e artifacts

[CI40730388157](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40730388157): **SUCCESS**, todos os quatro jobs e steps concluídos no SHA de código acima. Logs dos quatro jobs consultados; SHA do checkout e contagens conferidos.

| Job | ID | Resultado |
|---|---|---|
| ownership | 122964793613 | Escopo PASS; 12/12 adversariais; 27 blobs; 364 herdados |
| models | 122964929591 | 213/213 sem skips: 52 modelos originais PR14 + 161 regressões Meta |
| inherited-regression | 122964929702 | 288 backend; 7 filesystem I85 + 9 boundary I84, normal e Python -O |
| postgres-physical | 122964929740 | 49/49 PG17/HTTP, zero falhas/erros/skips; cleanup e catálogo iguais |

Artifacts publicados, metadata e digests declarados pelo GitHub conferidos. O JSON produzido e totais TAP foram lidos nos logs dos jobs; os ZIPs não foram reabertos localmente.

| Artifact | ID | SHA256 declarado pelo GitHub |
|---|---|---|
| s0-meta-ingress-01-physical-40730388157 | 12835201002 | `da858a538aa51f0e9623c098e43498253caffba50c5683acbe6edea4814db155` |
| s0-meta-ingress-01-models-40730388157 | 12833794261 | `aefe150b919cc4e99708e3d32f53ae983f5933fd25c4650d3c45c530e8021ac9` |

Relatório estruturado em `EVIDENCIAS.json`, com jobs, configuração PG e resultado de descarte. CI intermediária40730074152 também passou nos quatro jobs do código inicial (48 físicos); não substitui a prova final T49. Execução local final: os mesmos49 físicos aprovados em PG17.6, 213 modelos/Meta, 12 escopo, 288 backend e 16 normal/-O.

Primeira rodada local: Docker mudou porta dinâmica no restart, causando falha do harness e do cleanup dependente daquela conexão. Correções: porta local reservada e descarte em finally independente da disponibilidade SQL; resíduos próprios removidos. Três testes originais inicialmente falharam por duas fixtures dinâmicas não materializadas; copiadas byte a byte e incluídas no manifesto. Essas falhas exploratórias não são contadas como fechamento. Nenhum teste foi relaxado para obter sucesso.

## Resultado e alcance das provas

Duas autenticações independentes sintéticas, registro técnico confiado e grants por canal; multicanal somente mesma App/concessionária; bytes originais e ocorrências integrais/ordenadas; atomicidade, idempotência e conflitos duráveis; recibo Ed25519 gerado por readback e contexto do consumidor; recuperação após resposta perdida sem duplicar registro; revogação/rotação e concorrências negativas/positivas. Tudo permanece ARCHIVED_UNRESOLVED e sem efeitos comerciais.

PostgreSQL17.6 com fsync/full_page_writes/synchronous_commit on; SIGKILL real em oito janelas de processo e SIGKILL do container PostgreSQL, redo WAL e recuperação com volume conservado. Commit confirmado sobreviveu; transação aberta foi desfeita; recibo persistiu. Não certifica HA, réplica, failover ou perda física do host/disco.

Descarte final CI e local: **container ausente, volume ausente, custódia ausente, catálogo herdado SQL igual**. Credenciais sintéticas não aparecem em logs/artifacts; não se promete zeroização física de memória do Python/host. Login runtime não é service_role nem humano; instalador/runtime interno continuam fronteiras confiadas do lab.

## Entregas e dependências

Contrato operacional candidato e decisão multicanal: `CONTRATO_CANDIDATO_V1.md`. Autorização, resistência, riscos e pedidos de integração: `MATRIZES_E_INTERFACES.md`. Implementação/fixture/testes/manifestos/verificadores: `integration/s0_meta_ingress/`. Workflow próprio: `.github/workflows/exp-s0-meta-ingress-01.yml`.

Aceitos apenas para laboratório: wire M2M, App comprovada, lote atômico multicanal com grant por canal, ledger/idempotência/nonce, recibo autenticado, estados técnicos e recuperação. C1–C7 dos auxiliares continuam sem ratificação operacional. ACK externo permanece com Meta/Infra.

Dependências externas restantes: homologação de transporte/HTTP e ingressor Meta, fonte autoritativa real de App/WABA/número/canal/concessionária, custódia/rotação/trust anchors, política de inválidos e retry/backpressure, privacidade/retenção, observabilidade, capacidade e HA. Normalizador multicanal novo precisa homologação de interoperabilidade; fontes originais não foram alteradas.

Pedidos de integração documentados com arquivo ou caminho a definir, motivo, contrato e alternativa laboratorial. Nenhum componente compartilhado precisou de mudança para esta entrega. Não ampliar grants S0/S1 ou allowlist por inferência. Nenhuma questão bloqueante de governança humana I86 surgiu; administração operacional do registro técnico deverá receber contrato próprio da orquestração, sem conceder autoridade humana aqui.

**Recomendação:** encerrar somente a frente laboratorial como S0_META_INGRESS_01_LAB_CLOSED. Manter bloqueados eventos reais, listener/ACK produtivo, Graph/dispatch, catálogo PR19, migrations produtivas, deploy, merge e composição com I86 até deliberação independente da orquestração.
