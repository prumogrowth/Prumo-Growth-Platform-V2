# CM-01 — decisão de confiança pública para o laboratório I86

30/10/2026, America/Sao_Paulo. Repositório oficial:
https://github.com/prumogrowth/Prumo-Growth-Platform-V2

## Autorização e limites

Autorização expressa do responsável nesta sessão: “Autorização CM-01 —
Reconciliação pública S0/S1”. Autoriza os nove arquivos da proposta, a transição
extraordinária dos dois manifestos nos conteúdos/digests apresentados, commit
atômico, push seguro na branch específica e quatro jobs descartáveis, após
testes de integridade e verificação independente. Não autoriza merge, deploy,
produção, Supabase hospedado, Diretores reais, autenticação operacional ou
ampliação da autoridade de IA/MCP. Qualquer divergência de pai, conteúdo
protegido, testes ou escopo interrompe a execução e retorna à orquestração.

O estado de certificação neste documento é **LAB_BLOCKED / execução pendente**.
A autorização da reconciliação não é certificação física. Resultados posteriores
devem ser conferidos nos runs/artifacts e no relatório da orquestração, usando o
SHA e a árvore efetivamente testados; não há autorreferência ao SHA deste commit.

## Novo marco, sem equivalência histórica privada

O novo marco público é ae4bb16ac12086ad64509eff1c200b282fbd2f9f, árvore
3385f06bb477007c7d682f621227da422cf6fc5c. O inventário Git `ls-tree -rz`
contém 382 arquivos 100644; SHA-256 do inventário:
ea2eba6648f83f6f6d2656a111422105ef3b7687bda567d44279e3290b66daf0.

Esse marco substitui a âncora executável ausente dbf49ab19b73766d60678c4ce6f7dea56cd66c9b
e a árvore 9d2f54b8753d4afadf5175ee5b332510890f1772 para esta jornada.
**Não se declara equivalência integral entre as árvores privada e pública.**
Não se recupera histórico privado nem conteúdo removido na sanitização.

O marco é ancestral do pai da migração, 89513a82c7fe00fd22ffb71384aef3636a143e42,
árvore 3f4608e01a374583ce5c14b837ab4cd0da7af003. Entre ambos há exatamente
4b50171b95b1a120bf668cf60d1c73e15f8200ac e 89513a82c7fe00fd22ffb71384aef3636a143e42.
Foram examinados os 25 registros de alteração em 21 caminhos distintos: todos
na allowlist I86, apenas adições 000000→100644 e modificações 100644→100644.
I85 permanece em af84fed5b6535405a44ab5bffb7536c24377bb86, ancestral preservado.

## Fonte S1 e dependências

S1 fixada em 0b0930778c29204904c1c1358a9a7ae9e3fff10b, árvore
e18d4d1c0b75f6a2ed9fa4d7c904737500fe3e0b. Inventário: 476 arquivos 100644;
SHA-256 c65823e7e143b6c2ee35a0e8c29c663f12e212c3bee245bfdeaaa2719cd85de9.
Conferem os 34 digests publicados, as 35 migrations sobrepostas e a referência
038. Os 27 arquivos instaláveis e seus digests permanecem idênticos.

Cadeia: workflow → sandbox → Operator.init/prepare → environment.checkout →
bootstrap.install → manifesto G1 → verify_sources → SQL herdado/I79/I83.
verify_sources, checkout e bootstrap permanecem byte a byte intactos. Somente
o ref do manifesto G1, o s1_ref declarativo e seu digest dependente mudam.
O campo base=df7ea64ea9490f70f553f5a02149dbfe96aacf76 das dependências é
proveniência histórica, não é consumido como gate nessa cadeia e fica intacto.

O default integration/history/s1_sources.json, com ref d3e9f0a..., pertence à
jornada histórica. O bootstrap I84 fornece explicitamente o manifesto G1.
Workflows históricos, rótulos de proveniência I81 e relatórios anteriores
permanecem intactos. Esta reconciliação não recupera todas as outras jornadas.

## Exceção única, sem ampliar a allowlist ordinária

O commit de migração deve ter um único pai exatamente 89513a82c7fe00fd22ffb71384aef3636a143e42.
Os dois arquivos protegidos devem mudar juntos, em um único commit e com modo
100644. Seus blobs antes/depois e SHA-256 constam no manifesto CM-01 e são
fixados no checker. Não há parâmetro CLI, variável de ambiente ou documento
mutável que autorize uma transição diferente. permitted() continua recusando
esses caminhos como permissões ordinárias.

O checker examina cada commit e o diff agregado, exige os estados antes/depois,
índice e bytes locais exatos. Reedições, inclusive edit/revert posterior,
alterações pendentes, renomes, remoções, symlinks e gitlinks são recusados.
Ancestralidade, árvore, branch, linearidade, outros caminhos protegidos,
ignorados e exportação de código confirmado permanecem fiscalizados.

## Arquivos autorizados

- integration/i86/scope.py
- integration/i86/test_scope.py
- integration/i86/sandbox.py
- .github/workflows/exp-s1-i86-manual-director.yml
- docs/contratos/i86_authority/manual/CHECKPOINT.md
- docs/contratos/i86_authority/manual/CM01_DECISAO_CONFIANCA_PUBLICA.md
- docs/contratos/i86_authority/manual/CM01_MANIFESTO_PUBLICO.json
- integration/g1/s1_sources.json
- local_admin/dependencies.json

Os dois últimos são exceções extraordinárias exatas, não novos prefixos da
allowlist. Nenhum SQL, código funcional I85/S0/S1, contrato de autoridade,
backend, migration, frontend ou integração comercial é modificado.

## Validação e rollback

Antes do commit: testes adversariais, fontes, digests e regressões, mais
comparação independente do delta e dos bytes protegidos. O gate real ainda deve
recusar a transição pendente. Após o commit atômico: gate oficial PASS, relatório
antes/depois, rechecagem do remoto e push seguro do mesmo commit.

Na CI: quatro jobs; jornada I85 (13 pontos/seis comandos), 22 casos do
observador e 31 manuais sem skips; PG17/GoTrue/SQL/Edge reais; logs/artifacts,
catálogo/ACL/RLS, CAS, concorrência, SIGKILL, COMMIT, sessões e descarte de cada
stack. Falta de artifact, caso obrigatório ou descarte impede fechamento.

Rollback somente por revert normal do commit completo, sem reescrever histórico.
Restaurar as âncoras antigas retorna ao bloqueio conhecido. A exceção não admite
automaticamente uma transição inversa mantendo o gate verde.

Presença humana não é comprovada por simulação privilegiada. Operador nominal,
custódia, evidência externa e continuidade continuam decisões humanas pendentes.
Não se inventam quórum, segundo aprovador, prazo ou limite de Diretores.
