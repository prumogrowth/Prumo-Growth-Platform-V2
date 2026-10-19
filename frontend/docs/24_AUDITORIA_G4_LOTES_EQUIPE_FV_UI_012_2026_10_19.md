# FV-UI-012 — Auditoria G4: consulta de importações e lotes por equipe

**Data:** 19/10/2026. **Branch:** `feat/frontend-plataforma-visual`. **Escopo:** apenas `frontend/`. **Estado:** implementação de UI **inteiramente sintética e somente leitura**.

## Objetivo e critérios

G4, segundo `frontend/docs/02_MAPA_DE_TELAS_E_JORNADAS.md`: acompanhar lotes autorizados, qualidade e situação operacional **sem implementar o motor de importação**. Aplicar a decisão [D] de que o gestor acompanha **operadores da própria equipe**, não todas as concessionárias, e não pode decidir as lojas A/B/C concedidas pelo responsável. S0/S1-002 mantém autoridade para ingestão, validação, distribuição, permissões e redistribuição.

## Entrega

- `batch-monitor.mjs`: **quatro lotes fictícios**, distribuídos em equipes Marina e Daniel, mesmo compartilhando concessionárias, com isolamento de observações e IDs por `managerId` e pelo escopo de loja permitido. Os rótulos `received`, `under_review`, `validated_partial` e `distribution_blocked` são **fases técnicas de lotes**, não estados comerciais.
- Somente apresentar números de linhas/qualidade se a fixture trouxer confirmação, referência de versão não vazia e contagens matematicamente coerentes. Caso contrário, mostrar **“Contagens não confirmadas”**, sem inventar zero ou conclusão.
- Terceira aba **Lotes** no painel da equipe, ao lado de **Operadores** (G2) e **Monitoramento** (G3), em desktop e mobile. Projeções exibem a concessionária de origem e observação sintética. **Não existe** campo de upload, seleção de CSV, ação de distribuição, aceite de registros, formulário bancário ou edição de lojas.
- Troca de gestor fecha o diálogo e limpa o conteúdo do gestor anterior, inclusive lotes, evitando que a demonstração mantenha projeções alheias no DOM.
- `browser.smoke.py` atualizado para carregar `batch-monitor.mjs` e conferir troca de aba com o cenário G4. Esse roteiro **não foi executado em Chromium** nesta sessão.

## Conciliação prévia do G3 (FV-UI-011)

Como dependência, foram reconciliadas duas implementações simultâneas de G3, preservando indicadores agregados, os oito estados comerciais em quadro próprio e sinais técnicos projetados. Corrigidos ID `team-monitor` duplicado e roteiro Chromium que carregava módulo incompleto/tentava ler aba oculta. A [auditoria G3](23_AUDITORIA_G3_MONITORAMENTO_UNIFICADO_FV_UI_011_2026_10_19.md) registra regressão específica.

## Verificação executada após integração G2/G3/G4

Arquivos recuperados da **branch remota GitHub** e avaliados em harness JavaScript V8 com imports/asserções adaptados e DOM sintético:

- **110/110** testes de regras, sendo 11 novos testes G4 de isolamento de lotes, validação de contagens, versão, escopo e ausência de efeitos.
- **45/45** testes de interação com DOM simulado, incluindo novos cenários G4 em desktop/mobile, navegação entre abas, privacidade e limpeza na troca de gestor.
- **25/25** inspeções estáticas de fonte, documentação estrutural, navegação e roteiro Chromium.
- **180/180 verificações sintéticas PASS**.

**Não comprova:** execução nativa `node --test`, Playwright/Chromium da revisão atual, responsividade real, acessibilidade com leitor de tela, autorização no backend, importação, ingestão de CSV, análise de dados pessoais, concessões ou distribuição no S0/S1. **NÃO autoriza produção**.

## Pendências para integrações futuras

1. Definir projeções S0 autorizadas e minimizadas para lotes por equipe e loja, revisão de LGPD e prova técnica de isolamento de tenant e gestor.
2. Contratos reais de validação, proveniência, duplicidade, quarentena de linhas, etapas e idempotência; somente o responsável define concessões e a equipe S0/S1 processa a elegibilidade.
3. Resolver divergência [S1-002/I10 e gestão por operadores, issue #9](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/9). Sem criar comportamento unilateral da UI.
4. Testes Node e Chromium reais sobre checkout autorizado, mobile, acessibilidade e homologação interfrentes, antes da avaliação visual final.
5. Sem merge, deploy, Supabase, Meta, pagamento de API ou mudança do índice auditado 19F (**69/100**).

**Veredito:** G4 implementado como visualização **fictícia e somente leitura**, com regressão sintética aprovada; nenhuma integração funcional ou homologação real reivindicada.
