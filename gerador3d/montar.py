"""Monta um Short 3D: narração (Kokoro) -> tempos -> render Blender -> legendas, etiquetas e trilha -> MP4.

Uso: python3 gerador3d/montar.py roteiros3d/terra-por-dentro.json [--previa]
Requer: BLENDER (caminho do executável) e KOKORO_DIR (pasta com kokoro-v1.0.onnx e voices-v1.0.bin).
Saída em saida3d/<slug>/: video.mp4 e descricao.txt.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

RAIZ = Path(__file__).resolve().parent.parent
FPS_RENDER, FPS_FINAL = 12, 30
SR = 24000
FONTE = "Inter Black"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def narrar(cenas, voz, velocidade, pasta):
    """Uma fala por cena, com 0,35 s de pausa entre elas. Devolve o áudio e o início de cada cena."""
    from kokoro_onnx import Kokoro

    k = Kokoro(f"{os.environ['KOKORO_DIR']}/kokoro-v1.0.onnx", f"{os.environ['KOKORO_DIR']}/voices-v1.0.bin")
    partes, inicios, t = [], [], 0.4
    partes.append(np.zeros(int(0.4 * SR), dtype=np.float32))
    for c in cenas:
        audio, _ = k.create(c["text"], voice=voz, speed=velocidade, lang="en-us")
        inicios.append(t)
        partes += [audio.astype(np.float32), np.zeros(int(0.35 * SR), dtype=np.float32)]
        t += len(audio) / SR + 0.35
    total = t + 0.8
    partes.append(np.zeros(int(0.8 * SR), dtype=np.float32))
    sf.write(pasta / "narracao.wav", np.concatenate(partes), SR)
    return inicios, total


def palavras_com_tempo(wav):
    """Tempo de cada palavra falada (faster-whisper), para a legenda acender no ritmo certo."""
    from faster_whisper import WhisperModel

    # O Whisper espera 16 kHz; a Kokoro gera 24 kHz. Sem converter, os tempos saem esticados 1,5x.
    wav16 = Path(wav).with_name("narracao16k.wav")
    run(["ffmpeg", "-y", "-i", str(wav), "-ar", "16000", "-ac", "1", str(wav16)])
    audio, _ = sf.read(wav16, dtype="float32")
    modelo = WhisperModel("base.en", device="cpu", compute_type="int8")
    segs, _ = modelo.transcribe(audio, language="en", word_timestamps=True)
    return [{"t": w.start, "f": w.end, "w": w.word.strip()} for s in segs for w in s.words]


def ts(seg):
    h, resto = divmod(max(seg, 0), 3600)
    m, s = divmod(resto, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def legendas(palavras, cenas, inicios, total, destino):
    cab = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        # Legenda: branca com contorno escuro suave, palavra falada em laranja.
        f"Style: Cap,{FONTE},76,&H00FFFFFF,&H00FFFFFF,&H00201008,&H80000000,0,0,0,0,100,100,0,0,1,9,3,2,70,70,330,1\n"
        # Etiqueta da camada: caixa escura no topo.
        f"Style: Tag,{FONTE},54,&H00FFFFFF,&H00FFFFFF,&H20302018,&H20302018,0,0,0,0,100,100,2,0,3,22,0,8,70,70,240,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    linhas = []
    blocos = [palavras[i:i + 3] for i in range(0, len(palavras), 3)]
    for b, bloco in enumerate(blocos):
        fim_bloco = min(blocos[b + 1][0]["t"], bloco[-1]["f"] + 0.5) if b + 1 < len(blocos) else bloco[-1]["f"] + 0.5
        for i, p in enumerate(bloco):
            fim = bloco[i + 1]["t"] if i + 1 < len(bloco) else fim_bloco
            texto = " ".join(("{\\c&H2A8CFF&}" + q["w"].upper() + "{\\c&HFFFFFF&}") if j == i else q["w"].upper()
                             for j, q in enumerate(bloco))
            linhas.append(f"Dialogue: 0,{ts(p['t'])},{ts(fim)},Cap,,0,0,0,,{{\\fad(60,0)}}{texto}")
    fins = inicios[1:] + [total]
    for c, ini, fim in zip(cenas, inicios, fins):
        if c.get("label"):
            linhas.append(f"Dialogue: 1,{ts(ini + 0.3)},{ts(fim - 0.1)},Tag,,0,0,0,,{{\\fad(200,200)}}{c['label']}")
    Path(destino).write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")


def trilha(total, destino):
    """Pad ambiente gerado por síntese (sem direitos de terceiros): acorde suave com respiração lenta."""
    notas = [110.0, 164.81, 220.0, 261.63, 329.63]
    soma = "+".join(f"0.18*sin(2*PI*{f}*t)*(0.6+0.4*sin(2*PI*{0.07 + i * 0.03:.2f}*t))" for i, f in enumerate(notas))
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"aevalsrc='{soma}':s=44100:d={total:.2f}",
         "-af", f"lowpass=f=1800,afade=t=in:d=1.5,afade=t=out:st={total - 1.5:.2f}:d=1.5,volume=0.5",
         "-ac", "2", str(destino)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roteiro")
    ap.add_argument("--previa", action="store_true")
    args = ap.parse_args()
    rot = json.loads(Path(args.roteiro).read_text(encoding="utf-8"))
    pasta = RAIZ / "saida3d" / rot["slug"]
    quadros = pasta / "quadros"
    quadros.mkdir(parents=True, exist_ok=True)

    if not (pasta / "tempos.json").exists():
        inicios, total = narrar(rot["scenes"], rot.get("voice", "am_michael"), rot.get("speed", 1.05), pasta)
        (pasta / "tempos.json").write_text(json.dumps({"inicios": inicios, "total": total}))
    tempos = json.loads((pasta / "tempos.json").read_text())
    print(f"narração: {tempos['total']:.1f}s", flush=True)

    cena = RAIZ / "gerador3d" / "cenas" / rot["scene_script"]
    cmd = [os.environ["BLENDER"], "-b", "--factory-startup", "--python", str(cena), "--",
           str(pasta / "tempos.json"), str(quadros) + "/", str(FPS_RENDER)]
    if args.previa:
        run(cmd + ["--previa"])
        print(f"prévias em {quadros}")
        return
    if not (pasta / "3d.mp4").exists():
        run(cmd)

    # Fundo em degradê creme -> pêssego atrás da cena; depois suaviza de 12 para 30 quadros/s e amplia.
    run(["ffmpeg", "-y", "-f", "lavfi", "-i",
         "gradients=s=720x1280:c0=0xFBEFE3:c1=0xF2BFA4:x0=360:y0=200:x1=360:y1=1280:d=1:r=1",
         "-frames:v", "1", str(pasta / "fundo.png")])
    if not (pasta / "3d.mp4").exists():
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(pasta / "fundo.png"),
             "-framerate", str(FPS_RENDER), "-i", str(quadros / "%04d.png"),
             "-filter_complex", f"[0:v][1:v]overlay=shortest=1,fps={FPS_RENDER},"
             f"minterpolate=fps={FPS_FINAL}:mi_mode=mci:mc_mode=aobmc:vsbmc=1,scale=1080:1920:flags=lanczos",
             "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(pasta / "3d.mp4")])
    palavras = palavras_com_tempo(pasta / "narracao.wav")
    legendas(palavras, rot["scenes"], tempos["inicios"], tempos["total"], pasta / "legendas.ass")
    trilha(tempos["total"], pasta / "trilha.wav")
    ass = str(pasta / "legendas.ass").replace(":", r"\:")
    run(["ffmpeg", "-y", "-i", str(pasta / "3d.mp4"), "-i", str(pasta / "narracao.wav"), "-i", str(pasta / "trilha.wav"),
         "-filter_complex",
         f"[0:v]ass='{ass}'[v];[1:a]aresample=44100,volume=1.0[n];[2:a]volume=0.22[m];"
         "[n][m]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "19",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(pasta / "video.mp4")])
    (pasta / "descricao.txt").write_text(
        f"TÍTULO:\n{rot['title']}\n\nDESCRIÇÃO:\n{rot['description']}\n\n{' '.join(rot.get('hashtags', []))}\n\n"
        "3D animation made in Blender. Narration: AI voice.\n", encoding="utf-8")
    print(f"ok: {pasta / 'video.mp4'} ({tempos['total']:.1f}s)")


if __name__ == "__main__":
    main()
