# FV-GATE-01 — Critério de apresentação ao responsável | 18/10/2026

**Direção expressa do responsável:** continuar o desenvolvimento visual da plataforma na branch própria, seguindo as funcionalidades e limites já previstos na documentação. **Não solicitar avaliação visual incremental a cada versão.** O responsável pretende examinar a plataforma no GitHub somente quando a experiência estiver **substancialmente completa, verificada e bem aprovada tecnicamente**, reservando sua participação principalmente a **aparência, disposição de botões e eventuais ajustes finais de experiência**.

## Processo proposto para esta frente [P]

- Implementar interface, navegação, responsividade, estados de erro/carregamento/pendência e componentes com **somente dados sintéticos**, preservando as decisões de negócio.
- Conferir critérios funcionalmente simuláveis por teste de unidade, testes de navegador em múltiplas larguras e checagens de acessibilidade; registrar fatos executados e o que ficou por verificar.
- Conferir continuamente a propriedade de cada frente: autorização, estados de domínio, S0, Supabase, OpenAI, Meta e Banco **não são implementações da FV**.
- Conectar serviços apenas após contratos interfrentes homologados e autorizações explícitas; não confundir protótipo bem testado com portal operacional aprovado.
- Consolidar pendências técnicas em documentos/Issues do GitHub em vez de transferir decisões já documentadas ao responsável. **Pedir decisão somente quando houver bloqueio real e matéria ainda não resolvida pelo acervo normativo.**
- Preparar uma **revisão única de UX/estética** quando houver navegação integral em desktop/mobile, fluxos visuais completos conforme o escopo aprovado, testes e auditoria. Não declarar pronto para essa revisão enquanto restarem pendências funcionais críticas.

## Limites

Esse critério de apresentação **não substitui aceites técnicos por S0/OpenAI, revisão de segurança/privacidade ou decisão sobre publicação**. Não significa autorização para hospedar, comprar domínio, consumir APIs pagas, trabalhar com dados reais, abrir PR para merge na main ou alterar infraestrutura. A pendência contratual existente está no [issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4). O andamento da frente FV não altera automaticamente a régua 19F.
