"""Gera um Short vertical (1080x1920) a partir de um roteiro JSON.

Uso: python3 gerador/gerar.py roteiros/ocean-sunfish.json [--musica trilha.mp3]

Etapas: narração (edge-tts) -> imagem licenciada por cena (Wikimedia Commons)
-> movimento lento + fundo desfocado -> legendas palavra a palavra -> MP4.
Saída em saida/<slug>/: video.mp4, descricao.txt e creditos.json.
"""
import argparse
import asyncio
import html
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

import edge_tts

RAIZ = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
UA = "canal-shorts/0.1 (https://github.com/allissonronan-max/canal-shorts)"
CA = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
SSL_CTX = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else ssl.create_default_context()
# Só licenças que permitem uso comercial e modificação.
LICENCAS_OK = re.compile(r"^(public domain|pd|cc0|cc by(-sa)? [0-9.]+)", re.I)
FONTE = "Inter Black"


def http_get(url, destino=None, tentativas=6):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for n in range(tentativas):
        try:
            with urllib.request.urlopen(req, context=SSL_CTX, timeout=60) as r:
                dados = r.read()
            break
        except urllib.error.HTTPError as e:
            # A Wikimedia limita o ritmo de requisições; espera e tenta de novo.
            if e.code != 429 or n == tentativas - 1:
                raise
            time.sleep(int(e.headers.get("Retry-After") or 0) or 5 * 2 ** n)
    if destino:
        Path(destino).write_bytes(dados)
    return dados


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duracao(arquivo):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arquivo)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


async def narrar(texto, voz, velocidade, destino):
    edge_tts.communicate._SSL_CTX = SSL_CTX
    com = edge_tts.Communicate(texto, voz, rate=velocidade, boundary="WordBoundary")
    palavras = []
    with open(destino, "wb") as f:
        async for c in com.stream():
            if c["type"] == "audio":
                f.write(c["data"])
            elif c["type"] == "WordBoundary":
                palavras.append({"t": c["offset"] / 1e7, "d": c["duration"] / 1e7, "w": c["text"]})
    return palavras


def buscar_imagem(consultas, usadas, destino):
    """Primeira imagem da Commons com licença aceita que ainda não foi usada no vídeo."""
    for consulta in consultas:
        params = {
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": f"{consulta} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 20,
            "prop": "imageinfo", "iiprop": "url|extmetadata|mime|size", "iiurlwidth": 1600,
        }
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
        paginas = json.loads(http_get(url)).get("query", {}).get("pages", {})
        for p in sorted(paginas.values(), key=lambda p: p["index"]):
            info = p["imageinfo"][0]
            meta = info.get("extmetadata", {})
            licenca = meta.get("LicenseShortName", {}).get("value", "")
            if (p["title"] in usadas or info["mime"] not in ("image/jpeg", "image/png")
                    or info["width"] < 800 or not LICENCAS_OK.match(licenca)):
                continue
            http_get(info["thumburl"], destino)
            usadas.add(p["title"])
            autor = re.sub(r"<[^>]+>", "", html.unescape(meta.get("Artist", {}).get("value", "desconhecido")))
            autor = " ".join(autor.split())
            return {"arquivo": p["title"], "autor": autor, "licenca": licenca,
                    "url": info["descriptionurl"], "w": info["thumbwidth"], "h": info["thumbheight"]}
    raise RuntimeError(f"Nenhuma imagem licenciada encontrada para {consultas}")


def montar_cena(img, info, dur, destino, indice):
    """Fundo desfocado + imagem principal com zoom lento (direção alterna por cena)."""
    frames = int(dur * FPS) + 1
    proporcao = info["h"] / info["w"]
    fg_h = H if proporcao >= 1.2 else max(1000, min(1350, int(W * proporcao))) // 2 * 2
    zoom = "1.0+0.12*on/{n}" if indice % 2 == 0 else "1.12-0.12*on/{n}"
    zoom = zoom.format(n=frames)
    filtro = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=40,eq=brightness=-0.25[bg];"
        f"[0:v]scale={W * 2}:{fg_h * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{fg_h * 2},"
        f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{fg_h}:fps={FPS}[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2-120:shortest=1,format=yuv420p[v]"
    )
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}", "-i", str(img),
         "-filter_complex", filtro, "-map", "[v]", "-t", f"{dur:.3f}", "-r", str(FPS),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(destino)])


def ts(seg):
    h, resto = divmod(seg, 3600)
    m, s = divmod(resto, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def legendas_ass(palavras, destino, por_bloco=3):
    """Blocos de até 3 palavras em caixa alta; a palavra falada fica amarela."""
    cab = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Cap,{FONTE},80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,7,3,2,60,60,520,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    linhas = []
    blocos = [palavras[i:i + por_bloco] for i in range(0, len(palavras), por_bloco)]
    for b, bloco in enumerate(blocos):
        fim_bloco = blocos[b + 1][0]["t"] if b + 1 < len(blocos) else bloco[-1]["t"] + bloco[-1]["d"] + 0.4
        for i, p in enumerate(bloco):
            fim = bloco[i + 1]["t"] if i + 1 < len(bloco) else fim_bloco
            texto = " ".join(
                ("{\\c&H00E5FF&}" + q["w"].upper() + "{\\c&HFFFFFF&}") if j == i else q["w"].upper()
                for j, q in enumerate(bloco)
            )
            linhas.append(f"Dialogue: 0,{ts(p['t'])},{ts(fim)},Cap,,0,0,0,,{texto}")
    Path(destino).write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roteiro")
    ap.add_argument("--musica", help="trilha de fundo licenciada (opcional)")
    args = ap.parse_args()

    rot = json.loads(Path(args.roteiro).read_text(encoding="utf-8"))
    pasta = RAIZ / "saida" / rot["slug"]
    tmp = pasta / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    voz, velocidade = rot.get("voice", "en-US-AndrewNeural"), rot.get("rate", "+5%")
    usadas, creditos, palavras, cenas, t0 = set(), [], [], [], 0.0
    for i, cena in enumerate(rot["scenes"]):
        print(f"cena {i + 1}/{len(rot['scenes'])}: {cena['text'][:50]}…", flush=True)
        audio, img, clipe = tmp / f"{i:02d}.mp3", tmp / f"{i:02d}.jpg", tmp / f"{i:02d}.mp4"
        pals = asyncio.run(narrar(cena["text"], voz, velocidade, audio))
        dur = duracao(audio) + 0.12
        info = buscar_imagem(cena["images"], usadas, img)
        creditos.append(info)
        montar_cena(img, info, dur, clipe, i)
        palavras += [{**p, "t": p["t"] + t0} for p in pals]
        cenas.append((audio, clipe, dur))
        t0 += dur

    lista_v, lista_a = tmp / "v.txt", tmp / "a.txt"
    lista_v.write_text("".join(f"file '{c}'\n" for _, c, _ in cenas))
    # Cada trecho de narração ganha silêncio até a duração exata do clipe, para não dessincronizar.
    audios = []
    for i, (a, _, dur) in enumerate(cenas):
        wav = tmp / f"{i:02d}.wav"
        run(["ffmpeg", "-y", "-i", str(a), "-af", "apad", "-t", f"{dur:.3f}", "-ar", "44100", "-ac", "2", str(wav)])
        audios.append(wav)
    lista_a.write_text("".join(f"file '{a}'\n" for a in audios))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_v), "-c", "copy", str(tmp / "v.mp4")])
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_a), "-c", "copy", str(tmp / "narracao.wav")])

    legendas_ass(palavras, tmp / "legendas.ass")
    entradas = ["-i", str(tmp / "v.mp4"), "-i", str(tmp / "narracao.wav")]
    filtro_a = "[1:a]loudnorm=I=-14:TP=-1.5[a]"
    if args.musica:
        entradas += ["-stream_loop", "-1", "-i", args.musica]
        filtro_a = ("[2:a]volume=0.12[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=0,"
                    "loudnorm=I=-14:TP=-1.5[a]")
    ass = str(tmp / "legendas.ass").replace(":", r"\:")
    run(["ffmpeg", "-y", *entradas, "-filter_complex", f"[0:v]ass='{ass}'[v];{filtro_a}",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(pasta / "video.mp4")])

    (pasta / "creditos.json").write_text(json.dumps(creditos, ensure_ascii=False, indent=2), encoding="utf-8")
    linhas_cred = "\n".join(f"- {c['arquivo'].removeprefix('File:')} — {c['autor']} ({c['licenca']}) {c['url']}"
                            for c in creditos)
    (pasta / "descricao.txt").write_text(
        f"TÍTULO:\n{rot['title']}\n\nDESCRIÇÃO:\n{rot['description']}\n\n{' '.join(rot.get('hashtags', []))}\n\n"
        f"Image credits (Wikimedia Commons):\n{linhas_cred}\n\nNarration: AI voice.\n",
        encoding="utf-8",
    )
    print(f"ok: {pasta / 'video.mp4'} ({t0:.1f}s)")


if __name__ == "__main__":
    sys.exit(main())
