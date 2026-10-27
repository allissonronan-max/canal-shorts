# Referências salvas — vídeos do X

Salvos em 27/10/2026 a pedido do usuário. Conteúdo analisado a partir do texto do post, dos quadros do vídeo e da transcrição automática do áudio.
Números de faturamento citados nos posts são **alegações dos autores, não verificadas**.

---

## 1. Fluxo de Shorts "faceless" com Claude — @heyliccia
- Link: https://x.com/heyliccia/status/2114745638957056073/video/1
- Data: 26/10/2026 · ~14,5 mil views · vídeo vertical, 34 s, só música (sem narração)
- Alegação do post: "US$ 10.188/mês" (não verificado)

**Passo a passo mostrado na tela**
1. Entrar em YouTube Shorts e achar um vídeo viral (exemplo: peixe-lua / ocean sunfish).
2. Abrir o viewmax.io → ferramenta "Caption Remover" → remover as legendas do vídeo original.
3. Pedir ao Claude um roteiro de narração no estilo documentário sobre o tema.
4. Colar o roteiro no gerador de voz/vídeo do Viewmax e gerar a narração.
5. Soltar o vídeo, gerar legendas novas e publicar.
6. Acompanhar no YouTube Analytics (a tela mostra um Short com 54,2 M de views).
7. CTA final: "comente 'Secret' que eu mando o tutorial no DM" (isca de engajamento).

**Avaliação para o nosso canal**
- ⚠️ Reaproveitar vídeo de terceiros só tirando a legenda **infringe direito autoral** e o YouTube costuma recusar a monetização de "conteúdo reutilizado". O próprio post faz esse alerta. **Não usar desse jeito.**
- ✅ O que vale aproveitar: o formato (fato curioso + narração documental + legenda grande + 30–60 s) e o uso do Claude para escrever roteiros, aplicando isso a **imagens próprias, licenciadas ou de bancos gratuitos** (Pexels, Pixabay) ou geradas por IA.
- Para o OrçaLucro: mesmo formato com temas de precificação e orçamento para autônomos ("quanto cobrar por…", "o erro que faz você trabalhar de graça").

## 2. "Como fazer US$ 100 mil/mês com YT Shorts" — @DevenSeenath
- Link: https://x.com/DevenSeenath/status/2098303171546448234/video/1
- Data: 11/09/2026 · ~280 mil views · 3 min 13 s, horizontal
- Formato: trecho de uma call de mentoria/venda (o autor, com placas do YouTube ao fundo, conversando com um aluno).

**O que é dito (resumo da transcrição)**
- O objetivo seria "liberdade de tempo, de lugar e financeira".
- O aluno quer chegar a US$ 5 mil/mês; o mentor diz que a meta é pequena e que metas maiores "comprimem o prazo".
- Menciona que o aluno "acabou de gastar 4 mil" na mentoria; o mentor diz faturar US$ 300 mil.
- **Não ensina nenhum método prático de Shorts.** É conteúdo de mentalidade e venda de mentoria.

**Avaliação**: baixo valor prático. Serve só como exemplo de gancho ("como fazer X por mês") e de formato "trecho de call". Não replicar a promessa de renda, porque vai contra a regra do projeto de não prometer enriquecimento.

## 3. Workshop da Anthropic sobre como escrever prompts para o Claude — @dravenip
- Link: https://x.com/dravenip/status/2114399052259287226/video/1
- Data: 25/10/2026 · ~1,6 M views · ~28 min, com legendas em inglês e espanhol
- Post: workshop gratuito "dado por quem construiu o Claude".

**O que o vídeo é de fato (pela transcrição):** não é um workshop genérico sobre prompts. É a palestra de **Boris, criador do Claude Code**, com dicas práticas de uso do **Claude Code** (o assistente de programação no terminal). Parece ser a palestra do evento "Code with Claude" de 2025 republicada; o post exagera o título.

**Principais dicas**
1. **Comece fazendo perguntas, não editando.** Pergunte ao Claude sobre o projeto ("como isso funciona?", "por que isto está assim?", e ele consulta o histórico do git). Na Anthropic, isso reduziu a integração de novos engenheiros de 2–3 semanas para 2–3 dias.
2. **Peça um plano antes de executar.** "Antes de escrever código, faça um plano e me peça aprovação." Isso evita que ele construa a coisa errada.
3. **Dê um jeito de ele conferir o próprio trabalho** (testes, screenshots, mockups). Com 2–3 rodadas de iteração, o resultado chega perto do perfeito.
4. **CLAUDE.md:** um arquivo na raiz do projeto que é lido no início de toda sessão, com comandos, regras, arquivos importantes e estilo. Deve ser curto. Também dá para ter versões pessoais e por pasta.
5. **Conecte as ferramentas da equipe** (CLIs, servidores MCP) e explique ao Claude como usá-las.
6. **Atalhos:** Shift+Tab aceita as edições automaticamente · `#` salva algo na memória · `!` roda um comando · Esc interrompe sem quebrar nada · Esc Esc volta no histórico · `--resume`/`--continue` retomam a sessão.
7. **Modo programático** (`claude -p "prompt"`, com saída JSON) para automações e pipelines.
8. **Usuários avançados** rodam várias sessões do Claude em paralelo.
9. Aceita imagens: dá para arrastar um mockup e pedir para implementar.

**Aplicação aqui**
- Criar um `CLAUDE.md` neste repositório com as regras do canal (português, sem depoimentos falsos, sem promessa de renda, aprovação antes de publicar ou gastar). Isso já tinha sido sugerido ao analisar o pacote de migração.
- Fluxo de trabalho: pedir um plano → aprovar → produzir roteiros → revisar.
