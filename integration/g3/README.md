# Issue #10 — laboratório auxiliar de catálogo e negativas

Contrato e resultado: `docs/contratos/g3_issue10/RELATORIO_CONTRATO_S0_S1_G3_20261026.md`.

Este pacote não é migration, servidor, contrato aprovado de produto ou integração final. Não modifica outras branches nem contata Supabase hospedado/Meta/Banco/OpenAI. Não instala os PRs em conjunto. Não exige psql, SDK, pip ou segredo real no host; usa somente biblioteca padrão Python, Git e Docker local.

## Reprodução

Em checkout desta auxiliar, com os objetos Git dos SHAs fixados em `run_local.py` e `source_inventory.py` disponíveis. Se o clone for raso, recuperar previamente os refs do relatório. Imagem exata usada:

```sh
docker --host=unix:///var/run/docker.sock pull postgres@sha256:b8faeff7712663c2773a190181e1246e37e364b887611c04658c28b44e2408fe
python3 integration/g3/source_inventory.py --output work/g3-sources.json
python3 integration/g3/run_local.py --output work/g3-pg17
python3 integration/g3/export_evidence.py --input work/g3-pg17 --sources work/g3-sources.json --output work/g3-package
```

O pull é uma preparação separada; o runner exige imagem já presente. O digest identifica a imagem PG17 usada, não é tag flutuante. `run_local.py` fixa socket local, remove seletores Docker remotos, não aceita DSN/endereço/container existente e cria nomes aleatórios `prumo-issue10-*`. Cada perfil usa container próprio `--network none`, sem portas/bind mounts/volumes; dados ficam em tmpfs. `finally` remove o container específico inclusive em falha; falha na remoção é erro. Não remover containers de outras tarefas. Em interrupção abrupta do processo, conferir/remover apenas o nome criado por esta execução.

Bootstrap de `auth.uid()` e `auth.sessions` é **sintético**, explícito e descartável, separado das fontes canônicas. A prova de login CFI abre conexão com `session_user` real do login SQL (socket interno com trust); não é prova GoTrue/JWT/credenciais. Não executar as fixtures diretamente num banco persistente. O runner nunca aceita um projeto/DSN hospedado.

`--profiles s1` restringe execução para diagnóstico. `execution.json` descreve somente os perfis selecionados naquela execução; a evidência entregue foi uma execução final completa dos quatro perfis. Catálogo S1+I63 é capturado dentro de transação revertida; não habilita I64–I74 nem finge que foram implantadas. Perfil F03 instala sete fixtures pertinentes e pré-requisitos, não todas as features do PR #1.

## Ler as evidências

`columns.csv`: colunas/tipos/owner/RLS/SELECT-INSERT-UPDATE efetivos de anon/authenticated. Grants efetivos ainda dependem das policies por linha.

```sh
python3 - <<'PY'
import gzip,json
from pathlib import Path
root=Path('docs/contratos/g3_issue10/evidence')
catalog=json.loads(gzip.decompress((root/'s1-i63-candidate-catalog.json.gz').read_bytes()))
print([(r['schema'],r['name'],r['policies']) for r in catalog['relations'] if r['name']=='mensagens'])
PY
```

Os JSONs de catálogo incluem constraints/policies/colunas/ACL e funções privadas, sem SELECT de linhas comerciais. O índice de fonte lexical inclui comentários e testes: não o interpretar como catálogo implantado. Os hashes são de integridade desta captura; OIDs e metadados de uma nova instalação podem variar. ROLLBACK foi verificado comparando o catálogo antes/depois **no mesmo banco**.

Probes G3 validam controles positivos antes das negativas. PRIVATE testa tabelas que realmente existem e não conta `undefined_table` como negação. URLs antigas e D3/D4 reais sem infraestrutura ficam pendentes. Não criar mock de Storage para declarar esses cenários aprovados.

Esta auxiliar não adiciona workflow nem dispara/registra CI próprio como aprovado. I61–I74 e os CIs #8/#9/#11 continuam evidências das frentes. Sem merge, deploy ou integração automática.
