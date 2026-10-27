# FV-UX-01 — Conversa em primeiro lugar, voz e emojis (decisões de alinhamento)

**Data:** 26/10/2026. **Projeto:** Prumo Growth / LiberaCred. **Frente:** frontend visual. **Situação:** diretriz autoral aprovada para orientar incrementos subsequentes; **NÃO equivale à implementação da gravação ou transmissão real**.

## 1. Contexto e intenção do autor

Após abrir a versão integral do frontend no ChatGPT Sites pelo celular, o responsável concluiu que a interface está funcional e com direção visual aproveitável, porém **densa demais**: métricas, chips, badges, explicações técnicas e seletores de teste ocupam a parte superior e empurram a lista de conversas para baixo. As cores foram interpretadas em tons verdes/azulados, embora a intenção fosse uma base principalmente **branca, preta e cinza**, em ambos os temas.

O WhatsApp é **referência de hierarquia e de ergonomia conversacional**, não de marca, paleta, implementação ou catálogo de funções. O frontend atual já possui vários recursos úteis, logo o objetivo é **reorganizar e aproveitar**, não apagar/reconstruir do zero.

## 2. Regra de hierarquia e contexto de perfis

- **Consultor:** entrada principal deve mostrar conversas no primeiro viewport do celular. Prioridades: buscar, abrir conversa, responder, acompanhar casos; informações de negócio aprofundadas sob ação deliberada.
- **Gestor:** experiência de gestão própria: equipe, monitoramento, filas, lotes, acompanhamento permitido. Usar os módulos de gestão já existentes. Pode haver **dois Sites temporários**, um para cada visão, derivados de **uma única base visual**; não duplicar código nem implementar dois aplicativos permanentes.
- Escolha de ator fictício não é uma função da plataforma operacional autenticada. Durante avaliação, usar **perfil demonstrativo fixo por Site/cenário** e, quando necessário, ferramentas de teste num painel discreto e rotulado como tal, **sem sugerir autenticação real**.
- O filtro de concessionária continua sujeito ao escopo projetado; não vira seletor de autorização ou concessões.
- **Menu secundário / três pontos / painel lateral de configurações** recebe escolha de tema, configurações da demonstração, reset, opções menos frequentes e informações técnicas. A escolha de tema mantém teclado e acessibilidade.
- **Filtros avançados**, estado comercial e indicadores continuam acessíveis, mas recolhidos por padrão; não remover recursos úteis para a gestão. Busca e lista de atendimentos ficam imediatamente visíveis.
- Deixar indicação não intrusiva de demonstração (ex.: legenda discreta ou ponto de informação); dispensar repetição de `demo/fictício/beta` em todo badge, mas **não esconder o fato de que não há envios reais** quando o usuário tentar enviar.

## 3. Direção estética e composição

Paleta principal **neutra** (branco/gelo/cinza/preto/grafite), contrastes legíveis em claro/escuro e uma única cor de acento discreta onde necessário. Não importar o verde institucional do WhatsApp. Reduzir superfície colorida, bordas decorativas, densidade de etiquetas e ornamentos; melhorar altura útil e legibilidade da fila. Estados importantes continuam visíveis em contexto (erro, pendência, envio não confirmado), sem virar repetição textual. Ícones com rótulos acessíveis, áreas clicáveis compatíveis com toque.

**Referência trazida pelo autor:** no WhatsApp, conversas aparecem cedo no viewport; na prévia da Prumo, controles de perfil, loja, filtros, indicadores e badges empurravam a lista para baixo. Corrigir hierarquia antes de adicionar mais cards.

## 4. Comunicação — funcionalidades prioritárias

### 4.1 Texto, emoji e ações essenciais

- Campo de composição **sempre localizado no rodapé** da conversa elegível; entrada disponível somente com permissão/ciclo/janela operacional autorizados. Enviar texto mantém prévia/autoria e estado conservador de envio já implementados; `api_accepted` não significa `sent_confirmed`.
- Emoji: **botão discreto próximo ao campo** para inserir no cursor do rascunho, com picker compacto em desktop; em celular aproveitar o teclado nativo e oferecer acesso complementar se útil. Usar caracteres Unicode, respeitando limite do texto e acessibilidade; **nunca enviar automaticamente** ao escolher emoji. Reações às mensagens podem ficar em avaliação posterior; não exigir cópia completa do WhatsApp.
- Áudio: botão de microfone é **necessário para o Consultor** na conversa elegível. O estado visual deve permitir solicitar microfone com gesto de usuário, iniciar/parar, ver duração, reproduzir prévia, excluir e confirmar o rascunho, com resposta acessível a erro/permissão negada. Não gravar automaticamente nem persistir bytes em storage.
- Para a **prévia sintética do Sites**, gravar e reproduzir áudio **somente no navegador** se a plataforma, o dispositivo, HTTPS e a permissão permitirem; representar "anexado apenas nesta demonstração" ao confirmar; **sem upload, sem Meta, sem envio e sem payload real**. Se `MediaRecorder` não estiver disponível, exibir indisponibilidade discreta e segura, sem falso sucesso.
- **Para o produto real**, a interface pode registrar uma intenção autenticada de envio. Codec, transcodificação para formato permitido, upload, limites, validação, autorização S0, estado de transporte e reprocessamento idempotente pertencem ao núcleo/integração; não definir isso exclusivamente no browser.
- Meta Cloud API oferece `type=audio`; mensagens de voz envolvem OGG/Opus e parâmetros de áudio. **Não equiparar Blob WebM gravado pelo navegador a áudio imediatamente aceito pela Meta**.

### 4.2 Janela conversacional e estados

- Quando a capacidade de texto/áudio estiver **comprovadamente disponível**, mostrar controles ativos; **não precisa colocar badge "Janela Meta aberta"** na composição.
- Quando o núcleo/fixture informar **`expired`**, desabilitar composição e exibir nota pequena e clara `Janela de conversa encerrada` no lugar apropriado. Não fingir que o texto/áudio pode enviar. Templates elegíveis continuam ação separada, preferivelmente em menu de ação contextual, não card gigante.
- Se a janela **não estiver confirmada/for desconhecida**, mostrar `Envio indisponível no momento` ou equivalente neutro, **não rotular falsamente como "fechada"**. Os detalhes técnicos e `asOf` ficam no painel de informações para quando forem relevantes.
- Observação do autor: os profissionais são capacitados; evitar tutoriais incessantes, mas conservar mensagens de erro e incerteza decisivas para evitar ações incorretas.
- Supervisão não equivale a autoria de Consultor; controles de áudio/texto não ficam ativos com base somente em permissão de leitura.
- Mensagem sonora e reação não devem limpar unread/pendência, marcar leitura, disparar F03, mudar status comercial nem liberar janela por conta própria.

## 5. Separação entre UI demonstrativa e S0/Meta

| Função | Demonstração visual | Produto com S0/Meta |
| --- | --- | --- |
| Texto | prévia + inserção local claramente não enviada | comando autenticado, retorno de transporte |
| Emojis no texto | inserção no rascunho local | texto Unicode no comando validado |
| Áudio | microfone/gravador/preview em memória, sem upload | comando autenticado, conversão de mídia, envio e confirmação por integrações autorizadas |
| Janela | estado ilustrativo projetado pela fixture, conservador | projeção autenticada de política Meta e permissões |
| Perfil e loja | cenário fixado por prévia e filtros em escopo | identidade/roles/grants do serviço |
| Ajustes | menu recolhido com ações de demonstração | configurações autorizadas por perfil |

No caso de permissão de microfone negada, fechar janela, trocar ator/loja/caso, reset ou sair da página, **descartar a prévia de áudio e interromper tracks ativas**. Não reutilizar áudio entre clientes ou identidades. Não salvar rascunhos de voz em localStorage/IndexedDB na demo.

## 6. Ordem de execução e gates (sem reconstrução)

1. Reorganizar layout mobile e desktop com **lista primeiro**, esconder indicadores/controles de teste em zonas secundárias; definir tema neutro. Conservar ids/ações/contratos e atualizar testes de foco, toque e responsividade.
2. Acrescentar emoji no composer e cobrir inserção, cursor, limite, troca de contexto, janela bloqueada e teclado.
3. Acrescentar captura local de áudio com controles de gravação e preview; testar indisponibilidade de MediaRecorder, permissão negada, cleanup, confirmação fictícia e nenhuma chamada externa. **Não declarar envio real**.
4. Ajustar apresentação da janela (aberta/expirada/desconhecida) sem violar decisão S0. Testes visuais dos dois perfis e duas cores em 320px, 390px e desktop.
5. Atualizar snapshots/manifesto e executar o gate nativo **Python + Node + Chromium**, todos obrigatórios. Validar no ChatGPT Sites e, por fim, colher uma avaliação consolidada dos usuários, sem uma aprovação por componente.
6. Preparar duas **experiências/projeções temporárias** para o Sites, se for mais simples para avaliar Consultor vs Gestor, com **mesma fonte autoral, sem criar dois produtos**. Confirmar viabilidade com Work antes de publicar.

Não iniciar novos módulos (chamadas, status do WhatsApp, stories, figurinhas completas, feed, etc.) só porque aparecem no WhatsApp.

## 7. Referências externas verificadas em 26/10/2026

**WhatsApp oficial:** gravação, pausa/prévia e cancelamento de voz
https://faq.whatsapp.com/657157755756612/?cms_platform=web
e https://faq.whatsapp.com/1044960269529733/

**WhatsApp oficial:** reações com emoji, gesto contextual
https://faq.whatsapp.com/424198503229937/?cms_platform=web&locale=pt_BR

**Meta — coleção oficial da API:** formato e contrato de áudio por `type=audio`, com campo `audio.voice` e OGG/Opus
https://www.postman.com/meta/whatsapp-business-platform/request/juzqcg2/send-audio-message-by-url

**MDN:** navegador exige permissão para microfone via `getUserMedia()` e captura com `MediaRecorder`.
https://developer.mozilla.org/en-US/docs/Web/API/MediaStream_Recording_API/Using_the_MediaStream_Recording_API
https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia

**Janela de 24h:** preservar o conceito de período permitido para mensagens livres; jamais tratar template ou ACK como prova automática de envio.
https://www.twilio.com/docs/whatsapp/key-concepts

## 8. Autoridade e estado

**Fonte autoral:** feedback do responsável e imagens de 26/10/2026. **Pesquisa externa:** links da seção anterior. **Proposta de desenho/interação:** organização dos §§2–6, a ser executada incrementalmente sob testes. Esta decisão passa a guiar a lapidação visual e substitui a hipótese de que a prévia será aceita esteticamente só por passar nos testes.

**Persistido aqui:** contrato de UI e obrigações futuras, **sem mudança de runtime**, sem revisão do manifesto, sem deploy, sem modificação em main ou S0. A preparação anterior de entrega no ChatGPT Sites deve aguardar a lapidação desta UX antes da próxima rodada de avaliação.
