# LiberaCred S1-001 — Central de operações (demonstração local)

Primeira interface visual da operação humana da LiberaCred. **Somente dados sintéticos em memória**, sem login, Supabase, Meta, instituição financeira, modelo OpenAI, n8n, API, cookies, armazenamento local ou chamadas de rede.

## Abrir localmente

Requisitos: navegador moderno e Python 3 (somente para servir arquivos locais).

```bash
python3 -m http.server 4173 --directory frontend/s1 --bind 127.0.0.1
```

Abra `http://127.0.0.1:4173` no seu navegador. **Não publicar esse servidor na rede nem hospedar a demo como aplicação autenticada.** Importações ES Modules necessitam servir via HTTP de loopback; abrir `index.html` via `file://` pode falhar.

## Testes automatizados sem dependências

```bash
node --check frontend/s1/domain.mjs
node --check frontend/s1/app.mjs
node --test frontend/s1/tests/*.test.mjs
```

Node 22 recomendado. O workflow `.github/workflows/s1-synthetic-ui.yml` executa a mesma suíte em CI quando os arquivos da S1 mudam.

## Fluxo demonstrável

1. Entre como **Marina Costa · Gestor / Aurora**. Veja apenas os leads fictícios Aurora. Mude para **Paulo Nunes · Gestor / Horizonte** para confirmar que o mesmo telefone em outra concessionária não compartilha histórico, caso ou status.
2. Na Aurora, escolha o lead **A-101** em atendimento pela IA, atribua o caso a **Rafael Lima** ou **Bianca Rocha**; a IA fica suspensa permanentemente após a atribuição humana.
3. Mude o perfil para o operador atribuído: ele vê apenas os próprios casos e pode assumir o atendimento, criar notas internas e simular o encaminhamento de cadastro ao banco, mas não registrar venda/perda ou acessar leads de outros operadores.
4. Como gestor, avance um lead novo A-104 usando **simular primeiro disparo** e **simular triagem IA**. Nenhuma mensagem é enviada.
5. Como gestor, abra **A-105**, que já aparece como cadastro enviado ao banco. Uma venda fictícia só pode ser marcada manualmente com texto de evidência fictícia; não é inferida de callback.
6. Use pesquisa e filtros de status; consulte o histórico e os oito estados comerciais; clique em **Restaurar dados fictícios** para limpar as alterações da sessão de navegador.

## Contrato de segurança e limites

- `domain.mjs` implementa somente **regras de demonstração no navegador**, não uma fronteira de confiança real. Alternar perfis pela interface **não autentica ninguém**.
- Operador só pode consultar casos atualmente atribuídos à própria pessoa e loja; gestor só pode consultar sua loja. As regras são reproduções sintéticas, não substituem RLS, GoTrue, backend ou HMAC.
- Estados comerciais são exatamente oito; tarefas/leases/callbacks são estados **técnicos**, não estados de vendas.
- Atribuição a humano suspende IA automática. A interface não possui função para reativá-la.
- Não existem D3/D4 bancários reais nem campos sensíveis, documentos, valores, CPF ou aprovação bancária.
- Remessas, mensagens, primeiro disparo, triagem IA e venda são **simulações explícitas**. Não há WhatsApp, Graph, banco, OpenAI, importação de clientes, webhook, outbox real ou envio.
- A função `execute` usa checagem de versão para demonstrar concorrência e histórico. Estado é perdido ao atualizar a página; nenhuma persistência.
- Não reutilizar o protótipo como portal operacional sem arquitetura autenticada, autorização server-side, testes RLS/GoTrue, preservação de auditoria e gates de publicação.

Especificação e evidências em `docs/S1_001_JORNADA_HUMANA_VISUAL_2026_10_18.md` e `docs/MAPA_MENTAL.md` na raiz do repositório.


## Evidência automatizada S1-001

[CI S1 #39133454184 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39133454184) no SHA `6bd187148da74da6906493b0e2a97d817ffe84ba`: 18 testes de domínio + 6 testes de montagem usando DOM fictício, todos aprovados em Node 22. **Ainda é necessário abrir a interface em um navegador local para avaliação visual e de acessibilidade** antes de evoluir para S1 integrada.
