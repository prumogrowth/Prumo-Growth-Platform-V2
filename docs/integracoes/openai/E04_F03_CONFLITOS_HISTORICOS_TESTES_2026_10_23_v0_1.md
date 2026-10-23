# E04 F03 — Detecção independente de conflitos históricos e regressão (23/10/2026)

**Situação:** incremento de código E04 offline autorizado. **Não** é integração física S0, execução de modelo, remessa bancária, atualização de ficha ou homologação dos 70 oráculos SYN. Os esquemas e sinais `s0Verified`, `historyComplete`, `claims.explicit` continuam **fixtures fictícias**, não evidências reais.

## Falha descoberta e correção

O pré-validador F03 anterior validava valores e fontes individualmente, mas **dependia de `proposal.conflicts` fornecido pela própria F03**. Duas fontes explícitas autorizadas podiam afirmar valores diferentes para um mesmo campo do catálogo enquanto a proposta omitisse a divergência. Nessa situação, uma extração poderia ser sinalizada como elegível à rechecagem S0, mesmo sem resolução do conflito.

Atualizado [`f03-commit-gate.mjs`](./e04_offline_lab/f03-commit-gate.mjs) para:
1. Validar a estrutura de **todas** as declarações `claims` retornadas no histórico sintético, inclusive valores não utilizados na proposta; recusar tipos indevidos, `NaN/Infinity`, cadeias vazias e campos desconhecidos no objeto de claim.
2. Examinar, de forma independente do campo `proposal.conflicts`, as declarações **explícitas** `explicit=true`, disponíveis e assinaladas como verificadas pela fixture S0; **comparar por código de campo conhecido no catálogo e valor tipado**.
3. Se um campo tiver valores explícitos diferentes em qualquer fonte elegível da **mesma pessoa/concessionária até o cutoff**, retornar **`HUMAN_REVIEW_REQUIRED`**, mesmo se F03 omitir o conflito. Isso inclui campos opcionais e diferenças entre casos históricos. Não escolher automaticamente a declaração mais recente.
4. Não tratar como certeza declarações hipotéticas (`explicit=false`), fontes indisponíveis ou não verificadas. Valores realmente iguais em diferentes casos permanecem possíveis, sem conflito artificial.
5. Manter **`S0_RECHECK_ONLY`** exclusivamente como candidatura para revalidação final S0, **sem gravação**; `perdido` segue consultivo e `vendido` continua impossível por esta via.

Esta política offline é **deliberadamente conservadora**: uma retificação verdadeira entre atendimentos também requer revisão, enquanto o contrato físico da S0 não aprovar método verificável para resolver conflitos com autoria, tempo, contexto e evidência. Nenhum novo campo de produto foi criado.

## Evidência de testes e arquivos versionados

- Código [`f03-commit-gate.mjs`](./e04_offline_lab/f03-commit-gate.mjs), blob Git SHA: `13b60983b824bcbe145eb708d8b503e10aa45ba9`.
- [`tests/f03-commit-gate.test.mjs`](./e04_offline_lab/tests/f03-commit-gate.test.mjs), blob Git SHA: `b66dedc44edc11d38128447a0abfe23a95d4d375`.
- **15 casos novos F03**, totalizando **57** nesta suíte: conflito omitido, essencial/opcional, mesmo valor, hipotético, falso/zero, fontes inválidas, string vazia, não finito e sugestão de desistência.
- **Node.js 22.16.0 real**, dentro do diretório local de trabalho com 2 suítes disponíveis: `node --test /mnt/data/e04_dev/tests/*.test.mjs` → **110 PASS, 0 FAIL** (**57 F03 + 53 ciclo F02**). Os arquivos F03 locais tinham hashes Git **exatamente iguais** aos publicados.
- **Regressão das 6 suítes atuais recuperadas integralmente do GitHub**, em runtime **V8 isolado com imports `node:test`/`assert` substituídos por equivalentes de teste**: **269 PASS, 0 FAIL** = 50 guardas, 33 transporte, 33 frequência, 53 ciclo F02, 43 jornada, 57 F03. **Não foi execução conjunta Node/CI**.
- O checkout privado **não pôde ser obtido no ambiente Node** por indisponibilidade de resolução de `github.com`; por isso, **não** é correto afirmar `npm test` integral, mesmo com 269 testes aprovados em V8. Registros separados não constituem 269 oráculos SYN.

## Gates físicos ainda abertos

**CFI-01 / issue #4:** manifesto imutável de histórico multi-casos, autorização de consulta, verificabilidade semântica das alegações, conflitos/retificações verdadeiras, versão da ficha independente de ciclo e identidade, execução idempotente e solução de lacunas via Consultor sem edição direta. Receber a evidência de campo não significa receber autorização para aplicá-lo.

**CF-OP-02 / issues #6 e #15:** classificação real Meta, 131049, F02 pós-humano, envio final e C09. Sem mudança nesta rodada.

**Separação de fases:** E04 está autorizada somente offline; E03 credenciais e E05 API paga/dados reais/integração/deploy/merge continuam fora da autorização concedida.
