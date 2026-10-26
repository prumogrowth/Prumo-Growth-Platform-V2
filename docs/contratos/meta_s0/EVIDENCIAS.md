# Evidências — auxiliar Meta/S0

**CI final SUCCESS no SHA executável 92703c34fd4a2b9bae0d00768969c7c53cc16da3.**

[Actions 40370618576](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40370618576), job 121740049996, Node 22.23.3. Metadata e logs decodificados consultados pelo conector; contagens TAP e passos conferidos:

- **52/52 testes candidatos**, zero falhas, skips ou cancelamentos.
- **161/161 regressões Meta preexistentes**, zero falhas, skips ou cancelamentos.
- **7/7 blobs reutilizados inalterados** e diff restrito aos caminhos auxiliares.
- Dois testes encerram de fato processo filho abruptamente: antes de rename e após commit durável/antes de resposta. Restart comprova ausência de lote parcial ou recuperação do mesmo recibo completo, respectivamente.
- Resultados de modelo em memória nunca anunciam ACK durável. No adapter de arquivo, indicador exclusivamente laboratorial somente após file+directory sync.
- Provas de replay M2M, escopo, TTL/chave/rota, CAS, gates negativos, rollback, resposta perdida, concorrência modelada, incerteza, evidência tardia, quarentena e conciliação sem liberação.

Execução inicial também passou: SHA 82703d26f449d5758dc2d716b823bf09ce7f47b9, run 40370139300, job 121738350583, 50+161 testes. A revisão final acrescentou correlação técnica server-owned, digest/escopo/recibo na auditoria e teste de conflito na revisão. Não houve retry de falha ou teste enfraquecido.

**Limites:** ambiente cloud indisponível, portanto não houve execução local. As corridas novas são de um modelo serial com mutex; não são provas físicas de PostgreSQL/S1. FileStore é fixture single-process descartável. O sucesso não certifica M2M produtivo, installer/RLS novos, HA, Graph, ACK HTTP ou integração S0/S1. As certificações PG17/GoTrue anteriores permanecem históricas, separadas.

Reconsulta dos PRs #7/#8/#9/#11 confirmou os mesmos HEADs do manifesto. Só a branch auxiliar recebeu commits; diff aditivo contra cb7fc3e, sem mudança nos arquivos ou branches oficiais. Checkpoints, nomes dos 52 testes e extratos TAP estão em EVIDENCIAS.json. Proveniência por blob está em integration/meta_s0_candidate/source-manifest.json.

Arquivos de evidência e guia de revisão são documentais posteriores ao SHA executável. Nenhuma modificação de código/workflow/testes acompanha esse fechamento.
