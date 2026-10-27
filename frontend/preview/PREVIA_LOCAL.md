# Prumo — prévia integral para avaliação

Esta prévia contém o frontend existente completo, com dados fictícios. Nada é enviado pelo WhatsApp e não há conexão operacional com S0/S1, Meta, IA ou banco.

1. Baixe o artefato privado `prumo-demo-visual-zip` do GitHub Actions e extraia-o.
2. Abra `prumo-preview-integral.html` em um navegador para navegar na cópia integral em arquivo único. Conversas, detalhes e todos os módulos gerenciais foram preservados.
3. Para avaliar a exportação ESM original e o microfone em localhost, extraia também `prumo-demo-visual.zip` e execute, na pasta extraída: `python3 -m http.server 4174 --bind 127.0.0.1`. Abra `http://127.0.0.1:4174/`.

Consultor: cenário inicial padrão. Gestor: `?perfil=gestor` no endereço ou escolha o perfil fictício nos três pontos → Configurações. Essa seleção é uma ferramenta da demonstração e não autentica usuários. O tema Claro/Escuro está no mesmo painel.

Para áudio, abra Cliente Exemplo 02 com Rafael. Pressione o microfone, conceda a permissão, grave, pare e ouça. Pode excluir ou usar “Anexar só na demo”. O texto digitado é preservado. Há limite local de 2 minutos / 10 MiB. Navegador, dispositivo e contexto seguro precisam permitir gravação; se o arquivo único não permitir microfone, use localhost. Nada é convertido, carregado para servidor ou persistido. Ao sair do contexto ou ocultar a página, a gravação e a prévia são descartadas.

O artefato `fv-visual-review-screenshots` contém 22 capturas e um `INDEX.html` para comparar lista, conversa, detalhes, emoji, áudio e gestão. As capturas de áudio usam dispositivo sintético de teste.

Observe conforto da lista no celular, leitura em ambos os temas, composição, uso de teclado, retorno de foco e acesso à gestão. Testes automatizados e capturas não equivalem ao seu aceite visual. Dispositivos físicos, Safari/iOS/Android e leitores de tela continuam sujeitos a avaliação específica.

A prévia não foi publicada. O artefato está no repositório privado e tem retenção de 30 dias; o código e os geradores permanecem na branch. Consulte `PROVENIENCIA.json` para commits, arquivos alterados e hashes dos pacotes, e `ENTREGA.md` para implementação e dependências.
