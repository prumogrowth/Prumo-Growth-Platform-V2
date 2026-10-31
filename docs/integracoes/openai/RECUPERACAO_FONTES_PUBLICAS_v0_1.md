# OAI-OFF-01 — fontes públicas e preflight offline v0.1

31/10/2026, America/Sao_Paulo. Repositório oficial:
`prumogrowth/Prumo-Growth-Platform-V2`. Implementação isolada sobre
`1747cb0fee2a95322dc768044bafe9817d8cc540`, na branch
`feat/oai-off01-source-preflight-20261031`. OAI-RET-01 fornece o diagnóstico;
a autorização OAI-OFF-01 permite somente as quatro adições desta entrega.

## Resultado e autoridade

O único resultado positivo é **SOURCE_INTEGRITY_VERIFIED**: os arquivos
selecionados dos checkouts informados correspondem ao manifesto versionado,
à identidade de origem local observável, ao commit, à árvore, aos blobs e aos
bytes esperados. Não é integração, homologação, prova de qualidade do modelo,
autorização S0, execução E02 ou recuperação A38. Nenhum módulo das fontes é
importado ou executado. Nenhum comando operacional é produzido.

Sempre permanecem falsos `integration_homologated`, `s0_authorized`,
`semantic_validation`, `e02_homologated` e `a38_recovered`. Erros não revelam
URLs de origem, caminhos absolutos, conteúdos, stderr Git ou credenciais.
Não existe resultado LAB_CLOSED nem parâmetro para aprovar integração.

## Fontes fixadas e seleção

O inventário executável é [source-manifest.json](./e04_offline_lab/source-manifest.json).
Cada entrada declara repositório, branch informativa, commit, árvore e caminhos
relativos. Branch não seleciona versão durante a inspeção: somente o SHA exato.

| ID | Commit | Árvore | Arquivos | Exigência padrão |
| --- | --- | --- | ---: | --- |
| s2 | `1747cb0fee2a95322dc768044bafe9817d8cc540` | `3522e49b45d4b6dce23d46a56c81c0f6035668cf` | 15 | Obrigatória |
| f03 | `dc8554db2e625accbf95cf922fdff8446be56f00` | `aae2ef09c05eb045a4ff9ee4b55f69301b83119f` | 23 | Obrigatória |
| s0 | `7d3232f59aab35265c3aa7fb5ab5ab2f06d5d047` | `574c69e6c232c7ebb1e8719721fb8283c439dbbe` | 16 | Opcional; `--require s0` exige |
| i86 | `a0c4eaf2720bd6cf2bd756544498f8f185f005fc` | `977c4ed302b9dd14e459575abbbc718eaa8ca920` | 6 | Opcional; `--require i86` exige |

S2 corresponde à branch `feat/s2-openai-adapter-sintetico`; F03 à
`feat/oai-s0-f03-history-port-20261023`; S0 à
`exp/s0-s1-ops02-evidence-contract-20261030`; I86 à
`exp/s1-i86-manual-director-20261028`. Todos pertencem ao repositório oficial.

A seleção é deliberadamente limitada:

- **S2:** seis módulos E04, package.json e seis testes originais, contrato E01
  tipado v0.4 e caderno E02 de 70 oráculos. Não inclui os arquivos OFF-01.
- **F03:** dez módulos de histórico/selo/conteúdo/HMAC/reserva/contratos/
  ponte/evidência/aplicação/mídia; três módulos puros F02 compartilhados;
  ponte e executor atômico CFI; consumidor S2 multirrota, recuperação A38,
  CLI JS pinada e runner PG17; schema F02 pinado, documento A38 e duas ADRs.
- **S0:** schema e contrato candidato de revisão F02, três módulos F02
  compartilhados, ponte/executor CFI, contrato/decisões OPS-02 e gramática
  administrativa declarativa; seis arquivos protegidos I86 também comparados.
- **I86:** decisão/manifesto CM-01, contrato manual v2, checker I86 e dois
  manifestos de dependências. Essa leitura não executa o checker ou SQL.

Os 60 registros são seleções por snapshot; arquivos compartilhados aparecem
nas duas fontes por serem verificações independentes. Não é inventário de todo
o backend, nem prova de completude de dependências para executar F03/A38.

## Bytes versus objetos Git

Para cada arquivo, `sha256` é SHA-256 dos bytes brutos, sem normalização de
newlines/Unicode. `git_blob` é o OID Git SHA-1 de
`UTF8("blob " + comprimento + NUL) || bytes`, no formato de objetos deste
repositório. Não são intercambiáveis. `byte_length` e `mode` também são conferidos.

O preflight rederiva os OIDs de commit, árvore raiz e blobs lidos, compara a
entrada `ls-tree`, verifica o índice selecionado e só então confere os bytes
do worktree. O manifesto contém hashes calculados dos snapshots recuperados;
não contém caminhos locais, dados de cliente, secrets ou um hash inventado
para o commit histórico ausente.

## Uso local explícito

Requer Linux/POSIX, Node.js 22+ e Git com suporte a `GIT_NO_LAZY_FETCH`
(ambiente desta missão: Git 2.52.0). Sem pacotes npm ou configuração de serviço.
As fontes precisam já estar disponíveis em checkouts separados, exatamente
nos commits da tabela. A criação desses checkouts é preparação externa ao
preflight; ele nunca clona, baixa, busca, instala ou troca HEAD.

Defina `OFF01_S2`, `OFF01_F03`, `OFF01_S0` e `OFF01_I86` como raízes absolutas
dos respectivos checkouts. A partir da raiz da branch OFF-01:

```sh
node docs/integracoes/openai/e04_offline_lab/source-preflight.mjs \
  --source "s2=$OFF01_S2" --source "f03=$OFF01_F03" \
  --source "s0=$OFF01_S0" --source "i86=$OFF01_I86" \
  --require s0 --require i86
```

O checker é executado a partir da branch OFF-01, mas **s2 deve apontar ao
checkout base preservado**, não à branch que contém o novo commit OFF-01.
O commit novo tem outro HEAD e será corretamente recusado como fonte s2.

Sem as fontes opcionais, omita seus argumentos. A saída as classifica
`OPTIONAL_NOT_PROVIDED`; comparações que dependem delas ficam
`NOT_EVALUATED_SOURCE_NOT_VERIFIED`. Isso não equivale a verificá-las.
Uma fonte opcional informada incorretamente produz falha. `--require` torna
obrigatória sua presença. Não há descoberta automática de raízes.

`--manifest /caminho/explicito.json` permite escolher um manifesto revisado
na mesma versão. Ele é parte da base de confiança: não é assinado e não
ratifica novas fontes. A substituição do manifesto e do verificador por um
adversário exige controle externo de versão/revisão, não pode ser autenticada
pelo próprio programa. Os testes protegem os quatro pins públicos desta versão.

API ESM: `verifySources({manifest, roots, requireSources?, operation?})`;
`readManifest(path)` faz leitura estrita; `validateManifest` e `parseManifest`
recusam gramática/versão/campos desconhecidos, duplicatas JSON e paths inseguros.
Importar o módulo não lê o manifesto ou checkouts implicitamente.

## Resultados e falha fechada

CLI escreve JSON determinístico em stdout, sem timestamps nem raízes locais.
Exit **0** somente para SOURCE_INTEGRITY_VERIFIED; exit **2** para falha tratada.
Falha fatal de processo/SO não é aprovação. Ordem de fontes/comparações é estável.

| Família | Códigos principais |
| --- | --- |
| Manifesto/argumentos | INVALID_MANIFEST, MANIFEST_VERSION_UNSUPPORTED, UNEXPECTED_FIELD, INVALID_OPTIONS, UNSAFE_PATH |
| Checkout/proveniência | CHECKOUT_REQUIRED, CHECKOUT_ABSENT, CHECKOUT_ROOT_MISMATCH, REPOSITORY_UNOBSERVABLE, REPOSITORY_MISMATCH |
| Objetos/bytes | COMMIT_MISMATCH, TREE_MISMATCH, GIT_OBJECT_MISMATCH, FILE_MISSING, INDEX_MISMATCH, BLOB_MISMATCH, HASH_MISMATCH, CONTENT_MISMATCH, MODE_MISMATCH |
| Leitura defensiva | SYMLINK_OR_ESCAPE, NOT_REGULAR_FILE, SOURCE_CHANGED, PARTIAL_CLONE_UNSUPPORTED, GIT_INSPECTION_FAILED |
| Comparações/dependências | COMPARISON_MISMATCH, ANCESTRY_MISMATCH, HISTORICAL_SUBSTITUTION_FORBIDDEN, HISTORICAL_SOURCE_UNRECOVERED |

Sem origem `origin` local observável, a fonte é recusada. São reconhecidas
somente formas GitHub HTTPS e SSH sem credencial embutida. A observação da URL
local **não autentica o servidor GitHub**: sua autenticidade depende da obtenção
externa/revisão dos pins. Não há consulta ao remoto durante a verificação.

## Compatibilidade demonstrada e precedência

As doze comparações previstas são:

1. Schema F02 pinado na F03 versus resultado S0: bytes idênticos, blob
   `61598ba702dc03f9f715673118c88f9359e64113`.
2. `f02_reconciled_human_authorization_handoff.py`: bytes idênticos.
3. `f02_reconciled_review_lifecycle.py`: bytes idênticos.
4. `f02_reconciled_review_recovery.py`: bytes idênticos.
5. `s0_cfi01_f03_receipt_bridge_local.py`: bytes diferentes.
6. `s0_cfi01_atomic_commands_local.py`: bytes diferentes.
7–12. Os seis arquivos I86 selecionados: bytes preservados em OPS-02.

Diferença declarada e confirmada é informação de integridade, não um erro
automático. Não autoriza substituir módulos. A S0 posterior copia o payload
antes do trabalho externo, vincula `expected_receipt` e valida antes do COMMIT.
Esses reparos não devem ser apagados pela importação da ponte F03 antiga.
A ancestralidade I86 → OPS-02 é verificada quando ambos são fornecidos.

I86/CM-01 é o checkpoint técnico-laboratorial protegido. O contrato OPS-02
registra fechamento pela orquestração nesse alcance, após a run 41087043183;
documentos anteriores LAB_BLOCKED são snapshots históricos preservados.
OFF-01 verifica os bytes desses registros, sem reexecutar os quatro jobs,
reabrir CM-01, certificar operador humano ou atribuir autoridade ao OPS-02.
OPS-02 trata declarações formais não confiáveis, sem aprovar ações.

E01/OAI e o resultado `prumo.s0.f02.review.result/0.1-candidate` continuam
contratos candidatos nas fronteiras descritas. Código físico local ou arquivos
iguais não equivalem a contrato interfrentes ratificado. OAI-RET-01 é diagnóstico,
não homologação produtiva. A ADR de governança de 27/10 supera a antiga premissa
de S0 sem frente própria; nenhuma mudança S0 foi executada aqui.

Permanecem pendentes: tradução de versões/cutoff, recibo F03 final, quatro provas
F02, recuperação do binding, ratificação humana distinta e disposição Meta.
O gate F03 independente não passa a integrar automaticamente journey.mjs.
O laboratório S2 não contém cliente OpenAI operacional.

## Âncora histórica e A38

`ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c` está separado em `historical`, com
origens documentais selecionadas na F03, dependência `a38`, recuperação registrada
`NOT_RECOVERED_IN_OAI_RET_01` e `replacement:null`. O 422 registrado na missão
anterior não prova exclusão definitiva. OFF-01 não refaz consulta GitHub.

O comando abaixo **não executa A38**: verifica as fontes fornecidas e solicita
o gate dessa dependência, que termina em HISTORICAL_SOURCE_UNRECOVERED, exit 2:

```sh
node docs/integracoes/openai/e04_offline_lab/source-preflight.mjs \
  --source "s2=$OFF01_S2" --source "f03=$OFF01_F03" --operation a38
```

A ausência histórica não impede verificar os snapshots públicos atuais. Porém,
um SOURCE_INTEGRITY_VERIFIED nunca converte A38 em aprovada. Alterar o pin,
declarar recuperação, informar uma raiz extra ou apontar a dependência para
s2 atual é recusado nesta versão. Recuperar a fonte exata ou ratificar uma nova
base exige missão/revisão próprias, sem equivalência histórica inventada.

## E02 e testes desta entrega

O caderno E02 selecionado preserva **70 SYN, 65 P0 e 5 P1**, com oráculos
documentais. Nenhum SYN foi homologado nesta missão. Resultados históricos de
133 testes F03, 83 F02 e 1/39 A38 são referências OAI-RET-01, não execuções OFF-01.

Reprodução separada dos seis arquivos originais S2, na pasta do laboratório:

```sh
node --test tests/offline.test.mjs tests/journey.test.mjs \
  tests/f03-commit-gate.test.mjs tests/plan-lifecycle.test.mjs \
  tests/template-frequency.test.mjs tests/transport-evidence.test.mjs
node --test tests/source-preflight.test.mjs
npm test
```

package.json permanece intacto: `npm test` usa `tests/*.test.mjs` e inclui o novo
arquivo automaticamente. Assim, o total agregado desse comando inclui OFF-01;
os 269 testes herdados são apresentados separadamente. Os testes novos criam
repositórios sintéticos descartáveis em diretório temporário, com commits e
arquivos fictícios; não usam o histórico ausente ou credenciais. Essas escritas
de setup de teste não são capacidades do preflight. Tripwires recusam rede,
escritas e comandos Git fora da lista de inspeção durante sua execução; um
inventário antes/depois compara os bytes Git e de trabalho das fixtures.

Resultados locais efetivamente executados em 31/10/2026, Node 24.19.0,
npm 11.9.0 e Git 2.52.0:

| Execução | Resultado | Limite |
| --- | --- | --- |
| Seis arquivos S2 originais, comando explícito acima | 269/269, zero falhas/skips | Regressão de guardas sintéticas |
| source-preflight.test.mjs isolado | 73/73, zero falhas/skips | Fixtures locais e contratos OFF-01 |
| npm test original | 342/342, zero falhas/skips | Inclui 269 herdados e os mesmos 73 OFF-01; não somar novamente |
| CLI real com s2/f03/s0/i86 e ambas opcionais exigidas | SOURCE_INTEGRITY_VERIFIED, exit 0 | 60 registros, dez igualdades, duas diferenças e uma ancestralidade |
| Repetição da CLI real com argumentos reordenados | JSON byte a byte idêntico | Determinismo nesta entrada |
| Gate --operation a38 com s2/f03 atuais | HISTORICAL_SOURCE_UNRECOVERED, exit 2 | Negativa esperada, tests_executed=false |

A rodada inicial de desenvolvimento tinha uma falha no setup de um teste:
sobrescrita de objetos Git somente leitura ao montar a fixture de ancestralidade.
O setup novo passou a copiar somente objetos ainda ausentes. Nenhum arquivo
herdado foi alterado para obter PASS. A rodada final isolada e o npm test
posterior passaram integralmente. Não foram reexecutados os 133 F03, 83 F02,
A38, PG17/GoTrue ou os 70 SYN nesta missão.

Contagens não constituem homologação E02 nem fechamento independente do laboratório.
Não há certificação autoatribuída ou autorreferência ao futuro commit.

## Limites e próximo passo

Somente arquivos selecionados são conferidos; alterações em arquivos não
selecionados não tornam o checkout inteiro certificado. O índice selecionado
é comparado mesmo se flags Git ocultarem alterações. Hashes não provam qualidade
semântica, completude do backend, direitos de dados ou autorização de negócio.

As leituras recusam symlinks observáveis nos pais/raiz/arquivos, hardlinks,
dispositivos, FIFO e diretórios; usam O_NOFOLLOW/O_NONBLOCK e verificam mudanças
observáveis no arquivo aberto. Há limites de tamanho/tempo e rechecagem de HEAD.
Isso não é snapshot atômico de múltiplos repositórios nem sandbox contra troca
hostil simultânea de diretórios/configuração ou contra um executável Git adulterado.
Git utiliza sua área administrativa de worktree compartilhada, que pode estar
fora da raiz; apenas os paths de conteúdo selecionados ficam restritos à raiz.

Comandos executados pelo utilitário: rev-parse, config sem includes, cat-file,
ls-tree, ls-files e merge-base. Sem shell, fetch/pull/clone, hooks de commit,
textconv, imports das fontes, SQL ou SDK. Configurações globais/sistema,
seletores Git herdados, substituição de objetos, locks opcionais e lazy fetch
são desabilitados; clones parciais/promisor são recusados antes de ler objetos.
O ambiente/local config/Git são parte do host de confiança, não prova de origem.

S0/S1 preserva identidade, permissões, estado, versões, rechecks e persistência;
OpenAI continua responsável por F01/F02/F03; Meta prova transporte; Frontend
exibe projeções autorizadas. Futuras chamadas permanecem servidor-servidor pelo
backend Supabase autorizado conforme ADR. Não há IA otimizadora, executor MCP,
administração de Diretores, secret, dado real ou efeito comercial nesta entrega.

**Próxima etapa proposta, não iniciada:** fronteira tipada offline da Etapa B,
reutilizando módulos existentes com validação estrita, separação do envelope
privado/payload e falhas tipadas. Não modificar S0/Meta/Frontend nem implementar
cliente real, chamadas pagas ou E05 sem autorização separada.
