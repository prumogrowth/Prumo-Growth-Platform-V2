# OAI-02 — Provisionamento MANUAL de credenciais OpenAI | v0.1

**Estado:** procedimento [P], a executar exclusivamente pelo responsável humano; **NÃO executado** em 18/10/2026. Nenhuma credencial criada, lida, armazenada, testada ou copiada pela frente OpenAI.
**Isolamento expresso:** o plugin Supabase conectado ao ChatGPT pertence a outro projeto. É proibido consultá-lo, inspecionar projetos ou usá-lo nesta frente. O destino futuro será selecionado e confirmado MANUALMENTE pelo responsável no dashboard do Supabase EXCLUSIVO da Prumo.

## A. Criar e configurar o projeto da OpenAI (responsável)

1. Abrir manualmente https://platform.openai.com/ e conferir ORGANIZAÇÃO correta.
2. Selecionar ou criar projeto API destinado exclusivamente à Prumo; anotar em registro administrativo seguro apenas ID/nome do projeto, pessoa responsável e finalidade. **Não assumir que o projeto existe**.
3. Verificar o faturamento da API separado do ChatGPT, orçamento, alertas, modelos e limites de taxa; nenhuma compra de créditos ou cobrança sem decisão expressa. Configurar alertas/limites compatíveis com a etapa de laboratório.
4. Preferir conta de serviço do projeto para backend quando os controles de acesso permitirem; a decisão e titularidade permanecem com o responsável. A chave de conta de serviço é mostrada na criação e precisa ser guardada naquele momento. Alternativamente, chave de projeto com permissões restritas avaliadas.
5. Gerar a chave secreta no projeto correto com privilégios mínimos compatíveis com o endpoint aprovado. Conferir ajustes de permissões (padrão pode ser amplo). **Não colar a chave em ChatGPT, GitHub, email, planilhas, prompt, testes ou logs.**
6. Preservar a chave apenas em local seguro para o passo B; planejar rotação/revogação. Não compartilhar credencial pessoal entre operadores ou projetos.

## B. Guardar manualmente no Supabase CORRETO, sem consultas automáticas

1. O responsável abre manualmente https://supabase.com/dashboard e seleciona o projeto exclusivo **Prumo Growth - Platform** após conferir owner/project-ref pela própria interface. **Não confundir com o projeto Supabase conectado como plugin.**
2. Navegar no dashboard à área **Edge Function Secrets** (interface pode mudar). É armazenamento de segredos acessíveis às Edge Functions, **não** uma linha de tabela SQL, coluna pública ou variável de frontend.
3. Nome lógico **proposto** para o segredo: 'OPENAI_API_KEY'. Valor: chave privada emitida no projeto OpenAI apropriado, inserida DIRETAMENTE pelo responsável no Dashboard; nunca registrar valor no GitHub/ChatGPT.
4. Salvar e confirmar somente a PRESENÇA/IDENTIFICADOR do secret. Evitar screenshots que incluam qualquer parte da chave e evitar compartilhar prefixos/sufixos desnecessariamente.
5. Esse armazenamento **não ativa** a API, não cria Edge Function e não prova uma chamada autenticada. Liberar o uso futuro é um gate separado.

**Separar ambientes:** um único segredo compartilhado entre laboratório/produção não é recomendado. A estratégia por ambiente, rotação e contingência permanece [R], assim como a escolha final de onde o adaptador roda. Caso o adaptador não seja executado em Edge Functions, revisar o local correto de secrets antes de salvar.

## C. Evidências seguras para compartilhar depois, sem segredos

- Projeto OpenAI criado? SIM/NÃO (nome ou identificador não secreto, se autorizado).
- Conta de serviço/chave gerada? SIM/NÃO; tipo de permissão e data de criação, sem chave.
- Billing e limites revisados/aprovados? SIM/NÃO; sem informar dados financeiros pessoais.
- Projeto SUPABASE EXCLUSIVO conferido manualmente? SIM/NÃO (sem expor credenciais).
- Secret 'OPENAI_API_KEY' presente? SIM/NÃO, informado pelo responsável, sem mostrar seu valor.
- Rotação/revogação e autorização de primeiro teste sintético? PENDENTE/APROVADO EXPRESSAMENTE.

**Jamais pedir que o responsável revele a credencial para validarmos esta fase.**

## D. Custo e autorização

Assinatura ChatGPT não inclui automaticamente API OpenAI; cobrança e consumo da API são separados. O plano de pagamentos da API pode envolver créditos e o saldo não substitui limites em tempo real. Modelo, preço, volume e teto devem ser confirmados pela organização antes de qualquer chamada remunerada.
A decisão de armazenar o segredo não equivale a autorizar chamadas, exposição de dados pessoais, deploy, migrações ou gasto.

## Fontes públicas verificadas em 18/10/2026

OpenAI projetos e contas de serviço: https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform
OpenAI permissões: https://help.openai.com/en/articles/8867743-assign-api-key-permissions
OpenAI proteção de chaves: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
OpenAI faturamento API/ChatGPT: https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform
Supabase Dashboard, Edge Function Secrets: https://supabase.com/docs/guides/functions/secrets

**Nenhuma ação realizada nas contas OpenAI ou Supabase por este documento.**
