# FV-UX-01 — Continuidade no Codex, implementação e prévia integral

27/10/2026. Branch própria: `codex/fv-ux-01-comunicacao-20261027`. Base: `8c9498d72cf9551edc50d7f0da8d15c48049e835`, HEAD remoto da branch visual conferido antes do trabalho. A consulta de refs confirmou a mesma base; não havia commits posteriores naquela branch. CI de origem consultado e confirmado SUCCESS: [40477589480](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40477589480). Nenhum módulo foi reconstruído ou excluído.

## Implementado e preservado

- Lista, busca, abas e filtros existentes preservados; filtros avançados e configurações já estavam recolhidos. Reset foi deslocado para Configurações, acessível também no celular. Escape e clique fora fecham esse painel.
- Paleta neutra aplicada a toda a folha existente, inclusive modais gerenciais. A conversão conserva a luminância dos tons anteriores; os gates de contraste continuam obrigatórios. Hierarquia e geometria anteriores foram aproveitadas.
- Conversa com contexto mais curto, aviso único de demonstração e sem badge desnecessário de janela aberta. Janela expirada: “Janela de conversa encerrada”; desconhecida/supervisão/inelegibilidade: “Envio indisponível no momento”. Detalhes, estado comercial, autoria, avisos de transporte incerto e ações elegíveis continuam disponíveis.
- Emoji Unicode discreto, inserção no cursor ou seleção, limite de 500 unidades UTF-16 como no input nativo, setas/Home/End, Enter, Escape, Tab, retorno de foco e rascunho preservado. Escolha não abre prévia nem envia mensagem.
- MediaRecorder solicita microfone por gesto; mostra pedido de permissão, gravação, duração, parada, reprodução nativa, exclusão e confirmação “Anexar só na demo”. Erro, indisponibilidade, ausência de microfone, interrupção e permissão negada não produzem sucesso fictício. Rascunho textual permanece ao excluir/anexar áudio.
- Blob e object URLs ficam somente em memória, sem localStorage/IndexedDB, upload, conversão ou transporte. Limites defensivos da prévia: 120 segundos e 10 MiB, sem impor política produtiva. Tipo capturado é o suportado pelo navegador; WebM não é apresentado como mídia Meta homologada.
- Troca de caso/ator/loja/aba da lista, perda de elegibilidade, conclusão simulada, reset, ocultação/saída da página e navegação móvel que oculta a conversa liberam captura e URLs. Abrir gestão também interrompe áudio. Permissões tardias e callbacks antigos não atravessam gerações. Ao retornar a um anexo descartado, há somente o registro textual local, sem bytes reaproveitados.
- Áudio local mantém `local_demo_not_sent`; não resolve DOT/unread, não confirma resposta humana, não dispara F03, não altera janela ou estado comercial. Texto mantém o fluxo anterior de prévia e autoria.
- Uma base, dois cenários iniciais: `/?perfil=consultor` e `/?perfil=gestor`. Gestor conserva equipe, supervisão, lotes e fila; só pode compor quando titular e elegível. O parâmetro e os seletores são fixtures, nunca autenticação.

## Contratos e checkpoints posteriores consultados, somente leitura

Fontes funcionais: docs 00, 38 (16 critérios FV-22), 88 (checkpoints FVA/FVB/FVC), 95 e 96. Matriz executável `acceptance-matrix.json` ampliada para comunicação, sem marcar critérios homologados.

| Fonte pinada | Conclusão e adaptação futura |
| --- | --- |
| S0/UI CFI-01, `ddec1b80444bfde871d43a02d0ee94b9ed7cde11`, `docs/contratos/ui_cfi01/CONTRATO_UI_S0_CFI01_0_1_CANDIDATE.md` | Proposta 0.1 ainda não ratificada (D1–D4). `expected_case_version` não equivale a ciclo; recheck requer binding do servidor; correlação/contexto devem ser revalidados após await. Não importada nem ativada. |
| S1, `8780b576aa18bd3983c063339e2e42d2452af22c`, I77 e I78 de 27/10 | G1 manual tem prova experimental de compatibilidade; G2/chefia permanece parcial. Fila CAS difere da versão de caso/ciclo. Preservadas pausa de intake, separação de supervisor/titular e ausência de administração de grants pelo Gestor. |
| Meta, `cb7fc3e2eacdaad9b8d47ffca1284759ca3357a3`, `cloud-transport-falhas-pre-homologacao-2026-10-26.md` | Observação Graph é proposta offline; API_ACCEPTED/UNCERTAIN não comprovam envio. Dispatch, recuperação, ACK e locks dependem de META-S0-DISPATCH-01/02, ACK-03 e LOCK-04. Nenhuma chamada ao adaptador. |

Para integrar áudio futuramente, S0/Meta devem pactuar capacidade autorizada de mídia (não inferida de mera leitura ou do `free_text` sintético), autoria em mídia, codecs/transcodificação, upload autorizado, retenção, tamanho/duração, idempotência e projeções de transporte. Na demo, áudio usa a mesma elegibilidade conservadora da composição textual exclusivamente como cenário visual. A rotina de invalidação deverá receber mudanças da identidade/capacidade autenticada; esta entrega não cria transporte, DTO produtivo ou autenticação.

Nenhum arquivo S0/S1, migration, serviço, segredo ou branch de terceiro foi alterado. O workflow visual foi habilitado apenas para a branch nova exata, conservando seus gates; não contém deploy.

## Validação e evidências

Novas suítes `local-audio.test.mjs` e `communication-composer.test.mjs`; todas as suítes anteriores preservadas. `browser.communication.py`, chamado pelo smoke obrigatório, usa ESM por HTTP loopback e MediaRecorder real com dispositivo sintético do Chromium. Seis combinações 320/390/1440 × claro/escuro verificam cursor, limite, teclado, foco, toque, gravação, playback, exclusão, anexo, bloqueio e limpeza. Nove cenários adicionais verificam negativas, permissão tardia, perfis, página oculta/saída, loja, ator e reset. Chamadas externas e persistência são bloqueadas nas jornadas principais; assets HTTP não podem retornar erro.

O gate nativo continua sequencial: revisão/branch limpa e inventário pinado → Python adversarial → todas as suítes Node → Chromium histórico e comunicação. A lista de branches é explícita (origem e esta branch); nenhuma branch arbitrária é aceita. O manifesto identifica a branch efetiva desta entrega. O checkpoint final de commits, CI e artefatos está registrado na seção de fechamento abaixo.

## Prévia integral, sem publicação

- ZIP ESM do runtime autoral, com manifesto de hashes e sem testes/backend/segredos: `build_preview.py`.
- HTML único local: `build_standalone_preview.py` incorpora os mesmos módulos na ordem já exercitada pelo smoke, sem substituir telas ou recursos. É cópia derivada rastreável. Microfone continua dependente de contexto seguro e permissão do navegador; a forma recomendada para o ZIP é HTTP localhost.
- Matriz ampliada de 22 capturas: `collect_visual_review.py` abre a aplicação por HTTP loopback e cobre lista, conversa, emoji, áudio, janela bloqueada, notas, histórico, extração, banco, novo contato, equipe, monitoramento, lotes e fila. Áudio das capturas usa dispositivo fictício do Chromium. `INDEX.html` facilita uma revisão humana consolidada.
- Não foi criado Site, link público, deploy ou novo controle de acesso. Nenhuma prévia foi compartilhada com terceiros.

Para servir a exportação extraída: `python3 -m http.server 4174 --bind 127.0.0.1 --directory CAMINHO_EXTRAIDO`, abrir `http://127.0.0.1:4174/`. Gestor: acrescentar `?perfil=gestor`. Dados são fictícios, nenhuma mensagem é enviada. Não expor esse servidor na rede.

## Pendências

1. Aceite visual consolidado do responsável em celular e desktop; ergonomia, conforto e hierarquia ainda dependem dessa revisão.
2. Verificação em Safari/iOS/Android físicos, teclado virtual e leitor de tela. Chromium e DOM sintético não substituem esses dispositivos ou tecnologias assistivas.
3. Ratificação/interligação S0/S1/Meta, política produtiva de mídia e testes de autenticação/transporte em escopo próprio futuro.
4. Merge, deploy, publicação no Sites e integração operacional continuam fora da autorização desta entrega.

## Fechamento técnico executado

Código e testes no commit `d9c1bb8fc90d394c6738070d2c647b0b735d9182`; primeiro manifesto `cfcb0a63be7720f40d71e408f6a9b9b3a5e11590`; alinhamento da expectativa de aviso curto e pacote integral em `ddb9f93f1eb66fe4fa0931168b6bbd82c3407268`; manifesto final e **HEAD técnico validado** `b770ccd2551586bbb2164aa4d01a7fccdda5a304`. Os quatro commits foram enviados somente à branch própria.

Gate local em checkout limpo: **PASS**, 64 arquivos conferidos no inventário Git, 30 suítes Node com **393/393 testes**, Python adversarial **27/27**, Chromium histórico completo mais seis jornadas de comunicação e nove cenários adicionais **PASS**. Os **2/2** testes do exportador também passaram. O HTML integral foi servido por localhost e exercitado com os dois perfis, emoji, áudio e fila; sem dependências externas. A navegação direta `file://` não foi certificada porque o Chromium gerenciado bloqueia esse protocolo por política; o caminho localhost foi validado. Matriz final: **22/22 capturas geradas**, sem erro de script ou overflow horizontal.

CI independente no GitHub: **[40485648685](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40485648685) — completed/SUCCESS**, SHA `b770ccd2551586bbb2164aa4d01a7fccdda5a304`, job `122126648766`. Logs conferidos: preflight 64 arquivos, 27/27 Python, 393/393 Node22, `FULL LOCAL ACCEPTANCE: PASS`, exportação com 24 arquivos de runtime e matriz de 22 capturas..

Artefatos privados (retenção de 30 dias): [prévia integral HTML + ZIP + instruções + proveniência, ID 12723914613](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40485648685/artifacts/12723914613) e [22 capturas e índice, ID 12725007932](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40485648685/artifacts/12725007932). A prévia inclui `LEIA-ME.md`, `ENTREGA.md`, HTML único, ZIP ESM e `PROVENIENCIA.json` com branch/HEAD, lista de alterações e hashes SHA-256. Não há publicação, compartilhamento com terceiros, merge ou integração operacional.

O checkpoint documental de fechamento posterior preserva a árvore `frontend/visual/` certificada acima; não declara um novo teste de código por editar documentação.

### Arquivos alterados em relação à base

```text
.github/workflows/frontend-visual-validation.yml
frontend/docs/00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md
frontend/docs/96_FV_UX_01_COMUNICACAO_LIMPEZA_AUDIO_EMOJI_2026_10_26.md
frontend/docs/97_FV_UX_01_CODEX_IMPLEMENTACAO_E_PREVIA_2026_10_27.md
frontend/preview/PREVIA_LOCAL.md
frontend/preview/build_preview.py
frontend/preview/build_standalone_preview.py
frontend/preview/collect_visual_review.py
frontend/visual/README.md
frontend/visual/app.mjs
frontend/visual/communication-composer.mjs
frontend/visual/index.html
frontend/visual/local-audio.mjs
frontend/visual/styles.css
frontend/visual/tests/acceptance-matrix.json
frontend/visual/tests/browser.communication.py
frontend/visual/tests/browser.smoke.py
frontend/visual/tests/communication-composer.test.mjs
frontend/visual/tests/dom-fixture.mjs
frontend/visual/tests/local-audio.test.mjs
frontend/visual/tests/offline-export-manifest.test.mjs
frontend/visual/tests/run_acceptance.py
frontend/visual/tests/source-contract.test.mjs
frontend/visual/tests/source-module-graph.test.mjs
frontend/visual/tests/test_offline_export.py
frontend/visual/tests/validation-layers.json
frontend/visual/tests/verify_offline_export.py
```

O `ENTREGA.md` dentro do artefato é o retrato documental do SHA técnico usado no CI; esta seção online acrescenta o resultado final do próprio CI e os IDs dos artefatos após sua conclusão.
