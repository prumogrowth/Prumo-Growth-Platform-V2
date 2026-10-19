# FV-UI-008 — Auditoria da tela O4 (remessa e retorno do banco)

**Data:** 19/10/2026. **Branch exclusiva:** `feat/frontend-plataforma-visual`. **Status:** demonstração visual com dados totalmente fictícios, **sem operações bancárias ou integrações reais**.

## Alinhamento normativo

Caderno 24, tela **O4**; FV-01 §3/4/6; oito estados comerciais; D41; separação de competência da S0 e responsabilidade humana sobre remessa e desfecho. A UI exibe uma leitura fictícia, **não cria comandos C15–C18**, não informa que o banco aprovou/recusou por silêncio, não emite evidência e não altera estado do caso. O produto LiberaCred pertence à instituição financeira; a Prumo emprega operadores e gestores; lojas são escopos, não empregadoras.

## Incremento implementado

- `frontend/visual/bank-view.mjs`: projeção mínima de acompanhamento bancário; só informa **remessa confirmada** em cenário com versão não vazia, prova marcada como verificada e ação humana representada. **Retorno confirmado** exige, além disso, prova e registro humano próprios.
- Nova aba **Banco** no painel existente (desktop/mobile): destaca estado comercial canônico separadamente do estado técnico de remessa/retorno; não fornece botões de remessa, recusa, venda ou upload.
- Fixture `A-105`: apenas remessa sintética verificada e **retorno pendente**, nunca aprovado/vendido/recusado por inferência. Nenhum dado bancário real, identificador de cliente, documento ou prova bruta.
- Gestor em supervisão na loja concedida recebe **resumo operacional sem versão, prova, conteúdo ou detalhes D4**. Profissional atribuído vê apenas os rótulos minimizados da fixture; contexto inválido/suspenso não lê nada.
- Scripts de teste de interface e roteiro Chromium atualizados para cenário O4. Não modificadas S0, S1-002, OpenAI, Meta, Supabase, `main` ou outras branches.

## Verificação executada

Arquivos mais recentes foram recuperados **diretamente do GitHub** e submetidos a harness de asserções JavaScript V8, adaptando os imports e o ambiente DOM sintético:
- **46/46** testes de regras e projeções passaram (incluindo **9 novos testes O4**).
- **21/21** testes de interação DOM passaram (incluindo **2 de interface O4**).
- **10/10** inspeções estáticas passaram (incluindo **2 novas inspeções O4**).
- **77/77** verificações sintéticas passaram; não foram detectados erros na análise de sintaxe dos módulos examinados.

**Limitação:** essa evidência **não é execução literal de Node, Chromium ou Playwright**, não demonstra responsividade física, leitor de tela, isolamento real via backend, autorização, política bancária ou entrega HTTP. O navegador local está instalado, mas **o checkout atual do repositório privado não está disponível no ambiente de execução**; por isso, o roteiro Chromium atualizado não foi executado. Não há **GO** funcional, bancário ou de produção.

## Itens seguintes

O5 (novo contato humano após marco, preservando ciclo anterior) e as vistas G2–G4 ainda carecem de representação visual completa; a S0 deve definir contratos físicos de prova bancária, registro humano, versionamento e leitura minimizada. Antes de revisão final pelo responsável, executar teste com checkout GitHub autorizado em Node/Chromium e revisar acessibilidade. Sem mudança automática do progresso auditado (doc.19F = **69/100**).

**Resultado:** tela O4 **coerente como simulação testada**, não homologada como funcionalidade bancária real.
