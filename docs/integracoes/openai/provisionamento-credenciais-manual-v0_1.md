# OAI-02 — Provisionamento MANUAL de credenciais OpenAI | v0.1

**Estado:** procedimento [P], a executar exclusivamente pelo responsável humano; **NÃO executado** em 18/10/2026. Nenhuma credencial criada, lida, armazenada, testada ou copiada pela frente OpenAI.
**Governança do ambiente:** antes de qualquer operação, conferir identidade, organização, `project-ref`, permissões disponíveis para a conta executora e autorização explícita no projeto Supabase exclusivo da Prumo. Conectores, CLI e interfaces são meios admissíveis conforme permissões e autorização de cada conta; nenhum documento presume acesso universal nem limita outros responsáveis autorizados.

## A. Criar e configurar o projeto da OpenAI (responsável)

1. Abrir manualmente https://platform.openai.com/ e conferir ORGANIZAÇÃO correta.
2. Selecionar ou criar projeto API destinado exclusivamente à Prumo; anotar em registro administrativo seguro apenas ID/nome do projeto, pessoa responsável e finalidade. **Não assumir que o projeto existe**.
3. Verificar o faturamento da API separado do ChatGPT, orçamento, alertas, modelos e limites de taxa; nenhuma compra de créditos ou cobrança sem decisão expressa. Configurar alertas/limites compatíveis com a etapa de laboratório.
4. Preferir conta de serviço do projeto para backend quando os controles de acesso permitirem; a decisão e titularidade permanecem com o responsável. A chave de conta de serviço é mostrada na criação e precisa ser guardada naquele momento. Alternativamente, chave de projeto com permissões restritas avaliadas.
5. Gerar a chave secreta no projeto correto com privilégios mínimos compatíveis com o endpoint aprovado. Conferir ajustes de permissões (padrão pode ser amplo). **Não colar a chave em ChatGPT, GitHub, email, planilhas, prompt, testes ou logs.**
6. Preservar a chave apenas em local seguro para o passo B; planejar rotação/revogação. Não compartilhar credencial pessoal entre operadores ou projetos.

## B. Armazenar MANUALMENTE a chave — destino técnico a confirmar

1. Para a alternativa **integração direta via Edge Functions**, o responsável abre https://supabase.com/dashboard e seleciona o projeto exclusivo **Prumo Growth - Platform**, conferindo organização, owner e project-ref antes de salvar. Esta conferência do projeto alvo também se aplica a qualquer outra alteração futura, inclusive quando outro usuário autorizado executá-la.
2. Navegar à área **Edge Function Secrets** (interface pode mudar) se o adaptador for executado na Edge Function. É armazenamento de segredos acessíveis às funções, **não** tabela SQL, coluna pública ou variável de frontend.
3. Nome lógico **proposto** para o segredo: 'OPENAI_API_KEY'. Valor: chave privada emitida no projeto OpenAI apropriado, inserida DIRETAMENTE pelo responsável no Dashboard; nunca registrar valor no GitHub/ChatGPT.
4. Salvar e confirmar somente a PRESENÇA/IDENTIFICADOR do secret. Evitar screenshots que incluam qualquer parte da chave e evitar compartilhar prefixos/sufixos desnecessariamente.
5. Esse armazenamento **não ativa** a API, não cria Edge Function e não prova uma chamada autenticada. Liberar uso futuro é um gate separado. **Se a topologia escolhida usar n8n**, armazenamento no Supabase não disponibiliza automaticamente a chave ao n8n; definir local de secrets/credenciais n8n, responsáveis e autorização separadamente antes de realizar qualquer configuração.

**Separar ambientes:** evitar compartilhar a mesma credencial entre laboratório/produção. A estratégia por ambiente, rotação e contingência permanece [R], assim como a escolha final da topologia (direta ou n8n). O armazenamento manual da chave será confirmado pelo responsável somente depois de definido o alvo técnico.

## C. Evidências seguras para compartilhar depois, sem segredos

- Projeto OpenAI criado? SIM/NÃO (nome ou identificador não secreto, se autorizado).
- Conta de serviço/chave gerada? SIM/NÃO; tipo de permissão e data de criação, sem chave.
- Billing e limites revisados/aprovados? SIM/NÃO; sem informar dados financeiros pessoais.
- Projeto Supabase EXCLUSIVO corretamente identificado para o caminho direto? SIM/NÃO/NÃO APLICÁVEL; se caminho n8n, destino de credencial e acesso aprovados? SIM/NÃO/NÃO APLICÁVEL (sem expor credenciais).
- Secret de runtime aprovado presente? SIM/NÃO/PENDENTE, informado pelo responsável, sem mostrar seu valor (Supabase Edge Functions ou cofre/credential store da alternativa n8n).
- Rotação/revogação e autorização de primeiro teste sintético? PENDENTE/APROVADO EXPRESSAMENTE.

**Jamais pedir que o responsável revele a credencial para validarmos esta fase.**

## C1. Controles de gastos e testes por lote — atualização 18/10/2026

A documentação oficial da OpenAI distingue alertas de orçamento **soft** (não interrompem requisições) e controles de gastos **hard** em projetos/organizações que os disponibilizem. O responsável deve conferir qual controle está efetivamente configurável na sua conta; não presumir que um alerta seja teto. Mesmo limites rígidos podem ter atraso de aplicação e pequeno excedente. Além de alertas/limites, todo lote de testes terá limite técnico interno de chamadas, tokens/duração e retries, preços do momento, estimativa total e **autorização expressa daquele lote**. Como o responsável não fixou um teto global arbitrário, isso não permite uso irrestrito de API.

Ver E03_PREPARACAO_CONTA_CREDENCIAL_GATES_v0_1.md e as fontes oficiais:
- https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform
- https://help.openai.com/en/articles/6614457-troubleshooting-api-usage-and-spend-limits

## D. Custo e autorização

Assinatura ChatGPT não inclui automaticamente API OpenAI; cobrança e consumo da API são separados. O plano de pagamentos da API pode envolver créditos e o saldo não substitui limites em tempo real. Modelo, preço, volume e teto devem ser confirmados pela organização antes de qualquer chamada remunerada.
A decisão de armazenar o segredo não equivale a autorizar chamadas, exposição de dados pessoais, deploy, migrações ou gasto. O mesmo projeto Supabase pode continuar sendo usado por outras frentes com autorização própria, sem que este contrato assuma a titularidade do seu backlog.

## Fontes públicas verificadas em 18/10/2026

OpenAI projetos e contas de serviço: https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform
OpenAI permissões: https://help.openai.com/en/articles/8867743-assign-api-key-permissions
OpenAI proteção de chaves: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
OpenAI faturamento API/ChatGPT: https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform
Supabase Dashboard, Edge Function Secrets: https://supabase.com/docs/guides/functions/secrets
n8n OpenAI credentials: https://docs.n8n.io/integrations/builtin/credentials/openai
n8n OpenAI node: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.openai

**Nenhuma ação realizada nas contas OpenAI ou Supabase por este documento.**
