# Estratégia — Odd Lifeforms

Pesquisa feita em 27/10/2026. A maior parte das fontes é de blogs de ferramentas, então os números são direção, não verdade absoluta. Depois de 2–3 semanas, quem manda são os nossos próprios dados (Metricool / YouTube Analytics).

## O que está funcionando no nicho
- **Duração:** Shorts de fatos rendem melhor com **20–35 s**. Pesquisa da Adobe com 507 criadores (jun/2026): menos de 30 s é o melhor para views, compartilhamentos e salvamentos; 30–60 s empata para ganhar inscritos.
- **Gancho:** a decisão de arrastar ou ficar acontece em **2–3 s**. Começar com a afirmação mais chocante ("This fish lays 300 million eggs"), nunca com "Hey guys" ou com o nome do animal.
- **Retenção:** meta de 70% ou mais em vídeos com menos de 60 s. Trocar de imagem a cada 3–5 s e fazer uma pergunta no meio ("So why does it…?").
- **Formatos fortes:** fatos sobre animais e **comparações** ("X vs Y", "the only animal that…").
- **Horário:** fim de tarde/noite nos EUA (18–20h, horário de Nova York ≈ 19–21h de Cuiabá). Depois ajustamos com o "melhor horário" do Metricool.
- **Volume:** 5–10 por semana na fase de teste, depois 3–5 de alta qualidade por semana.

## Regras para não perder a monetização (política de "conteúdo inautêntico" do YouTube)
- IA pode ser usada, mas **cada vídeo precisa ter contribuição original**: roteiro próprio, pesquisa e edição.
- **Proibido:** reaproveitar vídeo de terceiros, imagem parada com voz por cima, ou o mesmo vídeo trocando só o tema.
- Variar a estrutura dos roteiros, as imagens e os ganchos. Cada fato precisa ser checado.
- Sempre declarar a narração por IA (campo "conteúdo de IA" do YouTube e do TikTok) e creditar as imagens.

## Monetização (expectativa realista)
- **YouTube:** precisa de 1.000 inscritos + 10 milhões de views em Shorts em 90 dias. Uma fonte diz que, a partir de 01/02/2027, novos canais vão precisar de 20 milhões (ainda não confirmado). Shorts pagam pouco por view (centavos de dólar por mil views), então o dinheiro vem do volume.
- **TikTok (Creator Rewards):** 10 mil seguidores, 100 mil views em 30 dias e **vídeos com mais de 1 minuto**. Vale fazer versões de 61–75 s para o TikTok depois que a conta crescer.
- **Facebook/Instagram:** monetização de Reels varia por país e por convite. Por enquanto, usamos essas redes para alcance.
- **Prazo honesto:** a maioria dos canais leva meses para monetizar, e muitos nunca chegam lá. Não há garantia de renda. O plano é testar rápido, medir e dobrar o que funcionar.

## Plano de publicação (primeiros 30 dias)
- **1 Short por dia**, o mesmo vídeo em YouTube Shorts, TikTok, Instagram Reels e Facebook Reels, agendado pelo Metricool às **19h30 (Cuiabá)**.
- Lotes semanais: eu pesquiso, roteirizo, gero e agendo 7 vídeos de uma vez.
- Revisão semanal: quais ganchos e animais seguraram mais a audiência → próximos roteiros seguem o vencedor.
- Aprovação do usuário: só no **primeiro lote** (para validar o estilo). Depois disso, publicação automática, com relatório semanal curto.

## Fluxo de produção (automatizado neste repositório)
1. Pauta: lista de animais/fatos em `roteiros/pauta.md`
2. Roteiro: `roteiros/<slug>.json` (gancho → 3–4 fatos → pergunta → CTA)
3. Vídeo: `python3 gerador/gerar.py roteiros/<slug>.json` → `saida/<slug>/video.mp4` + descrição com créditos
4. Agendamento: Metricool (YouTube, TikTok, Instagram, Facebook)
