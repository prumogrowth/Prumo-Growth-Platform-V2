# FV-UX-01 — Continuidade no Codex, implementação e prévia integral

27/10/2026. Branch própria: `codex/fv-ux-01-comunicacao-20261027`. Base: `8c9498d72cf9551edc50d7f0da8d15c48049e835`, HEAD remoto da branch visual conferido antes do trabalho. A consulta de refs confirmou a mesma base; não havia commits posteriores naquela branch. CI de origem informado: [40477589480](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40477589480). Nenhum módulo foi reconstruído ou excluído.

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

O gate nativo continua sequencial: revisão/branch limpa e inventário pinado → Python adversarial → todas as suítes Node → Chromium histórico e comunicação. A lista de branches é explícita (origem e esta branch); nenhuma branch arbitrária é aceita. O manifesto identifica a branch efetiva desta entrega. O checkpoint final de commits e CI será registrado ao concluir o gate.

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
