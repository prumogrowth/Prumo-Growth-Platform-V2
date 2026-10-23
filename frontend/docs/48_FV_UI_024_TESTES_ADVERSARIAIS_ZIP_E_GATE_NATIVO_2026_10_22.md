# FV-UI-024 — Testes adversariais do ZIP e gates nativos obrigatórios
**Data:** 22/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Estado:** implementação do Frontend/testes, **não homologada**.

**Precedência:** [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md), [FV-UI-023](./47_FV_UI_023_MANIFESTO_ZIP_OFFLINE_NATIVO_2026_10_22.md). Não altera S0/S1, Meta, F01/F02/F03, Supabase, banco, credenciais ou produção.

## Problema identificado

O verificador de ZIP do FV-UI-023 validava hashes, caminhos e inventário, mas o comportamento de rejeição de pacotes adulterados **não tinha suíte de regressão Python executável**. Uma simples inspeção estática dos hashes não prova que o script bloqueie efetivamente duplicatas, caminhos inseguros, versões trocadas ou entradas grandes quando recebe um ZIP.

## Implementação

- `frontend/visual/tests/test_offline_export.py`: **15 cenários adversariais e positivo**, `unittest` padrão do Python e arquivos ZIP totalmente sintéticos, sem rede. Cobertura: ZIP correto com verificador original, blob modificado, blob adulterado com mesmo tamanho, arquivo extra, arquivo necessário ausente, arquivo duplicado, verificador trocado, diretório `..`, caminho absoluto, symlink, múltiplas raízes de Frontend, raiz ausente, arquivo não ZIP, digest Git diferente de SHA bruto e limite agregado de descompressão.
- `verify_offline_export.py`: limite adicional de **25 MB descompactados no total para `frontend/visual`** e execução obrigatória de `python -m unittest discover -p test_offline_export.py` no snapshot validado, antes de considerar o diagnóstico nativo como aprovado. O mesmo processo deve passar nos testes **Node + Chromium**; isso nunca marca `full_acceptance` como verdadeiro para um ZIP sem checkout autenticado.
- `run_acceptance.py`: inclui o arquivo Python no inventário e exige a regressão adversarial no checkout Git já validado antes de considerar o aceite local completo.
- `offline-export-manifest.test.mjs`: teste nativo Node de segunda ordem confirma que os dois runners incluem a suíte adversarial, que o limite de tamanho está ativo e que há pelo menos 15 cenários positivos/negativos.
- `acceptance-matrix.json`: mantém os critérios FV-22-01..16; a suíte de teste Node do manifesto continua associada a FV-22-16. **Nenhuma mudança de status de homologação**.

## Como executar

**Checkout Git verificado** — o gate integral continua exigindo SHA completo e branch limpa:
```bash
python3 frontend/visual/tests/run_acceptance.py --expected-head <SHA_COMPLETO> \
  --json-report /tmp/fv24-checkout.json
```

**ZIP da branch exportado no GitHub** — apenas diagnóstico offline autenticado por Git blob SHA e comparação do verificador:
```bash
python3 frontend/visual/tests/verify_offline_export.py \
  --archive /caminho/zip_da_branch.zip --run-native \
  --json-report /tmp/fv24-zip.json
```

**Somente testes do verificador**, sem GitHub ou browser:
```bash
python3 -m unittest discover -s frontend/visual/tests \
  -p test_offline_export.py -v
```

## Evidência disponível nesta rodada

- O código e a suíte Python foram incluídos na branch; leitura direta do GitHub confirmou a presença dos **15 métodos `test_*`**, das verificações de hash, symlink, caminhos, limite de descompressão e dos novos comandos de gate.
- O ambiente desta conversa tem Node e Chromium, mas **não tem acesso ao checkout privado nem ao ZIP do código**. Portanto **não foi executada a suíte Python do repositório em tempo de execução, tampouco Node/Chromium do projeto**. Verificar presença das proteções no código não equivale a afirmar que os testes passaram.
- O manifesto pinado no verificador deve ser **atualizado depois de finalizar todas as alterações em `frontend/visual`**. A própria cópia do verificador segue comparada byte a byte com a incluída no ZIP, evitando autopinagem circular. O `source_head` representa a revisão dos arquivos pinados, não substitui o HEAD do pacote exportado.
- Não há autorização para atualizar avaliação 19F, percentual de conclusão ou declarar homologação FV-UI-013.

**Próximo gate:** usar ZIP privado efetivo ou checkout Git autorizado para rodar o Python/Node/Chromium de ponta a ponta; registrar logs e corrigir falhas reais, inclusive em foco/zoom/leitor de tela.
