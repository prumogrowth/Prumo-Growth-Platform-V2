# S0 — preparação autenticada UI/CFI-01: binding comparado antes do COMMIT

26/10/2026. Branch própria: `exp/s0-cfi01-recheck-precommit-20261026`. **Melhoria interna independente de ratificação do contrato UI/S0. D1–D4 permanecem pendentes.**

## Recuperação e escopo

- PR #9: HEAD `ff623482fca0eb1857a64b51959e3716bc0216d7`, checkpoint CFI-01 certificado `1b4f2841d513fb971c93379636414bf686784beb`.
- PR #11: HEAD `ddec1b80444bfde871d43a02d0ee94b9ed7cde11`, código de contrato candidato `99238f8a3304b8cc70ef14421b74842b0740b016`. Base desta proposta, sem merge/cherry-pick.
- Frontend atual consultado: `e44a14dbc89e8c443bed08ea06c20a1f16f4ac12`. Avanços recentes são reparos de testes FVA-02/manifesto/timeout; `s0-command-result.mjs` permanece blob `044cfb95fee6eb8916dadf7de6f77aecdd3d2471`.
- S1 atual consultado: `e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe`. Export parser permanece blob `cb9fb9cf541308fdec1c5c21f6ee02a7a6675145`; contrato de equipe/schema canônico não foi alterado aqui.
- **Issue #10/S1-G3 e Meta/S0 do PR #8 são tarefas auxiliares separadas.** Não foram incorporadas branches, implementações, inventários ou conclusões dessas tarefas. Serão revisadas quando entregues. Não se declara nenhum bloqueio de G3/Meta resolvido por esta proposta.

## Problema confirmado no fluxo existente

O gateway já validava a resposta SQL antes do COMMIT. Porém, a ponte `S0CFI01F03ReceiptBridgeLocal.recheck` comparava o resultado ao **binding completo esperado pelo servidor depois** desse COMMIT. Com o mesmo caso/evento/chave e metadados esperados divergentes (loja, atribuição, digest, watermark ou contagem), a função SQL podia revalidar corretamente o recibo físico, consumir nonce e registrar auditoria, e só então a ponte devolvia STALE por não corresponder ao binding esperado.

Isso não concedia acesso a outro caso nem autorização comercial: os gates vivos GoTrue/S1/SQL já existiam. Era uma diferença entre o resultado esperado pelo chamador interno e os efeitos transacionais do recheck. O teste 14 do checkpoint documentava a limitação; esta proposta acrescenta a garantia de rollback e fortalece sua asserção.

Havia outra inconsistência possível: `capture` lia o dicionário original outra vez ao montar o binding depois da chamada ao gateway. Uma alteração pelo chamador nesse intervalo podia trocar a chave no binding, embora a captura SQL tivesse usado a chave anterior. O payload agora é copiado antes da chamada.

## Implementação efetiva

Código da melhoria: `61cc58848393057f51696e446880ad6fe1c2fdbc`. Revisão final de execução: `350a9dd1d8a46165b3d8b42841a46101cec9d664`, que altera somente o registry suportado no workflow experimental.

1. **Gateway existente:** `recheck_internal_receipt(..., expected_receipt=...)` aceita uma expectativa opcional **exclusivamente interna**, do tipo concreto `S0InternalReceiptLocal`. Dicionários, DTOs de tipo diferente e metadados inválidos são INPUT_REJECTED antes de I/O; validação reaproveita `parse_receipt_metadata` existente.
2. **Mesma transação:** depois de decodificar a linha SQL, compara todos os oito campos do recibo esperado ao recibo real. Divergência provoca exceção interna antes de sair do contexto da conexão; psycopg desfaz nonce e auditoria e o resultado é STALE, sem metadados/diagnóstico sensível.
3. **Ponte existente:** sempre fornece o recibo esperado nessa chamada. A comparação posterior permanece como defesa adicional; a igualdade deixa de depender apenas de um teste posterior ao commit.
4. **Captura:** copia o payload antes do trabalho GoTrue/SQL e usa esse snapshot para o binding retornado. Mantém a chave associada à captura efetivamente assinada.
5. **Compatibilidade:** chamadas internas antigas sem `expected_receipt` continuam executando o recheck físico existente. Não certificam metadados arbitrários fornecidos à parte. A ponte que trabalha com binding completo usa sempre a expectativa. Nenhum campo foi adicionado ao contrato público candidato.

A expectativa não é identidade nem grant. Mesmo com DTO válido, cada recheck passa pelo GoTrue e pelos gates de sessão, concessão, equipe, caso/ciclo/atribuição, mensagens, HMAC e nonce do SQL existente. A assinatura/canônico SQL e a função privada não mudaram. Os metadados esperados não atravessam o wire UI e não são um novo bearer.

**Sem DDL, grant, policy, função SQL, endpoint, dispatcher, lookup, storage de binding, versão de protocolo ou regra comercial novos.** A preparação do PR #11 continua retornando CASE_VERSION_BINDING_REQUIRED para versão de caso e RECHECK_SERVER_BINDING_REQUIRED para o recheck UI.

## Arquivos e preservação de referências

- `backend/s0_cfi01_atomic_commands_local.py`: validação de expectativa e comparação antes de COMMIT, mantendo a API anterior compatível.
- `backend/s0_cfi01_f03_receipt_bridge_local.py`: fornecimento da expectativa e snapshot do payload de captura.
- `backend/tests/test_s0_cfi01_expected_receipt.py`: dois testes de fronteira sem rede; DTO válido continua exigindo identidade, e JSON/metadados inválidos não chegam a I/O.
- `integration/cfi01/test_transactional_communication.py`: teste 14 reforçado para exigir rollback do nonce; nenhum cenário removido ou ignorado.
- `integration/cfi01/test_restricted_backend.py`: quatro cenários reais adicionais, mantendo os 28 anteriores.
- `backend/tests/compat_sources/s0_atomic_checkpoint_1b4.py`, README e `integration/ui_cfi01/source_manifest.json`: preservam **exatamente** o código antigo de `1b4f284` como fixture de proveniência. O teste de hashes do PR #11 passou a apontar para essa referência histórica, em vez de proibir a evolução do runtime atual. A fixture nunca é importada como runtime; nenhum teste de hash foi desativado.
- `.github/workflows/exp-s0-cfi01-precommit-binding.yml`: CI exclusivo desta branch, derivado do workflow existente; preserva os checks e encerra o stack descartável também em falha.

Schemas e implementações da UI candidata, os 34 vetores, `identity_boundary.py`, fixtures SQL e migrations permanecem inalterados. O checkpoint original está preservado no histórico e na referência de teste; esta proposta é um novo checkpoint para revisão, não substituição silenciosa da certificação anterior.

## Evidência e significado dos testes

**CI final [40369167064](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40369167064), job `121734932364`: SUCCESS no SHA exato `350a9dd1d8a46165b3d8b42841a46101cec9d664`.** Logs conferidos: 173/173 unitários, 18 famílias Auth/REST, dez marcadores CFI originais e 32/32 cenários reais do backend restrito, inclusive os quatro novos. `Stopped supabase local development setup.` confirmou o cleanup. Nenhum teste real foi ignorado nessa execução final.

| Camada | Resultado / limite |
|---|---|
| Local unitário | 173/173: 171 anteriores e dois novos de validação. Esses dois usam um provedor que sempre nega, sem rede; não são prova de GoTrue |
| Local PG17.11 | 28 regressões físicas existentes, mais probe de metadados divergentes com rollback e recheck posterior do binding correto. Identidade sintética, explicitamente separada dos E2Es reais |
| CI real | Regressão Auth/REST/RLS existente, dez cenários CFI originais e 32 cenários transacionais do backend restrito. Resultado final SUCCESS; SHAs/steps no JSON adjacente, com logs conferidos |

Cenários novos 29–32:

- Alterar, um de cada vez, loja, atribuição, digest, watermark e contagem no binding interno: STALE sem nonce/auditoria adicional; o binding original ainda passa depois.
- Controle com a API física interna antiga, que não recebe expectativa completa, versus comparação vinculada: mostra a diferença de escopo sem afirmar que a API antiga tenha autorizado um binding arbitrário.
- Alterar o dicionário original do chamador depois da captura real: o binding retorna a chave que foi assinada e o recheck funciona.
- Rechecks correto e divergente em paralelo: somente o correto faz COMMIT; um nonce e uma linha de auditoria adicionais.

O cenário 31 instrumenta apenas a mutação do payload após delegar à captura real; não fornece Principal, resposta SQL ou recibo falsos. Os demais testes reais usam GoTrue/PostgREST/PG17 e senha/chave HMAC aleatórias como no PR #9. As negativas anteriores de sessão/concessão/equipe, replay, concorrência física, falha de auditoria, versões obsoletas e resposta SQL inválida permanecem na suíte.

A primeira tentativa do run 40367908518 (job `121730506139`) passou 173 testes unitários, mas o registry respondeu `toomanyrequests` durante o pull das imagens. Auth/REST e E2Es foram **skipped**, portanto essa tentativa não certifica os testes reais. O job foi reexecutado no mesmo SHA (job `121732811714`), sem alterar código, versões ou checks, e sofreu o mesmo rate limit. Nenhuma dessas duas tentativas certifica os E2Es. Após diagnóstico, a revisão `350a9dd` usa Docker Hub somente no passo de start experimental. O CLI v2.84.2 suporta explicitamente `docker.io` em [internal/utils/docker.go](https://github.com/supabase/cli/blob/v2.84.2/internal/utils/docker.go); tags e checks são mantidos. O manifesto Docker Hub da tag postgres17.6.1.095 estava disponível, enquanto o GHCR continuava devolvendo toomanyrequests. Não foi possível comparar os manifestos; não se declara identidade binária entre registries. Resultado final e todas as tentativas ficam nas evidências, sem ocultar falhas de infraestrutura.

Nenhum resultado local com identidade sintética é contado como E2E real. A execução final desta proposta obteve CI SUCCESS no seu SHA exato e cleanup confirmado; não usa o sucesso histórico de `1b4f284` ou `99238f8` como substituto da nova certificação. O próximo checkpoint executável é `350a9dd1d8a46165b3d8b42841a46101cec9d664`, certificado nesta branch e com D1–D4 bloqueadas.

## D1–D4: análise e encaminhamento à coordenação

| Decisão | Fonte autoritativa / fato já existente | Ponto a aprovar | Recomendação e motivo |
|---|---|---|---|
| **D1 — comando/resposta/UI** | PR #11 é só candidato; Frontend ainda rejeita CFI-01 no classificador conceitual | S0 + Frontend/produto: nomes, versão, projeção e texto visual | Envelope técnico separado; não reutilizar C11/C13/C15 nem exibir ficha aplicada a partir de recibo/recheck |
| **D2 — versões** | Hoje `ciclos_comerciais.versao_registro` é consultada e bloqueada pelo SQL; atribuição é revalidada por UUID/estado vivo. Não há binding aprovado da versão de caso da UI a essa coluna | S0 + Frontend/S1: leitura autorizada que fornece o token, significado de cada versão e serialização | Discriminador explícito e decimal string int64; enquanto a fonte de caso não for ratificada, manter CASE_VERSION_BINDING_REQUIRED. Nenhuma versão de ficha/catálogo/atribuição derivada por suposição |
| **D3 — binding de recheck** | Binding concreto já existe na memória do backend e é conferido contra recibo e permissões reais. Agora sua comparação está no limite transacional | S0 + Frontend/S1/privacidade: lookup/handle, associação a ator/sessão/caso e captura, retries, expiração, retenção e correlação durável | Reaproveitar recibo/auditoria S0 com resolução server-owned. A correção atual **não escolhe** registry/handle, não persiste capture_request_id e não transforma referência do browser em autoridade |
| **D4 — autenticação/elegibilidade** | Backend verifica GoTrue por chamada e sessão viva no SQL; senha SQL isolada não substitui HMAC nem concessão/atribuição | S0 + Frontend/S1/segurança: transporte Bearer TLS versus sessão cookie/BFF e proteção CSRF, fluxo de renovação/logout, mapeamento dos rótulos visuais aos gates atuais | Reutilizar GoTrue/executor restrito; manter credencial fora do envelope candidato e não confiar em flags da UI. Não ampliar direito de supervisor por leitura, nem criar exceções comerciais |

**Quatro decisões continuam PENDENTES, sem ratificação unilateral.** Não houve aprovação conjunta nova encontrada nos checkpoints consultados. Parecer técnico e recomendação não equivalem à aprovação de produto, privacidade ou segurança de implantação.

## Reprodução e próximo avanço

No checkout desta proposta, os mesmos comandos do PR #9:

```sh
python3 -m unittest discover -s backend/tests -v
python3 -m pip install -r backend/requirements-s0-local.txt
supabase start --exclude realtime,storage-api,imgproxy,mailpit,postgres-meta,studio,edge-runtime,logflare,vector,supavisor
PYTHONPATH=. python3 scripts/test_s0_auth_rest_local.py
PYTHONPATH=. python3 scripts/test_s0_cfi01_auth_rest_local.py
PRUMO_CFI01_TRANSACTIONAL_TEST=YES PYTHONPATH=. python3 integration/cfi01/test_restricted_backend.py
supabase stop --no-backup
```

Usar somente stack novo e descartável, CLI 2.84.2 e driver fixado; garantir stop também após falha, como no workflow. Não vincular projeto remoto, usar credenciais reais nem aplicar SQL hospedado. Changelog público Supabase foi tentado, mas proxy retornou 403; documentação atual de sessões/logout consultada por MCP. Nenhum tool de banco hospedado foi chamado.

**Próximo avanço recomendado:** coordenação deve deliberar D1–D4 a partir do contrato e desta matriz. Depois, implementar o binding/lookup aprovado no caminho S0 existente e integrar uma confirmação UI em sandbox autenticado, exigindo estes checks e os vetores do PR #11. Até lá, manter gate UI bloqueado; a biblioteca CFI interna continua funcional. As entregas auxiliares Issue #10 e PR #8 aguardam revisão independente, sem importação antecipada.

Limites remanescentes: helper de sessão ainda é postgres-owned por restrição de auth.sessions; custódia/rotação produtiva, observabilidade, retenção e auditoria durável de recusas continuam pendentes. Isso não autoriza merge, deploy, funções comerciais ou produção.
