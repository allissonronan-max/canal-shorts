"""Cena Blender: a Terra estilo massinha é fatiada e revela as camadas.

Rodar: blender -b --factory-startup --python terra_por_dentro.py -- <tempos.json> <saida/quadro_> <fps>
tempos.json: lista com o início (s) de cada cena da narração + duração total.
Os movimentos de câmera acompanham as cenas: 0 inteira → 1 crosta → 2 manto → 3 núcleo externo
→ 4 núcleo interno → 5 recuo → 6 final.
"""
import json
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
tempos = json.load(open(args[0]))
saida, FPS = args[1], int(args[2])
inicios, total = tempos["inicios"], tempos["total"]
quadro = lambda seg: 1 + round(seg * FPS)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
R = 5.0


def material(nome, cor, rug=0.75, emissao=0.0):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cor, 1)
    b.inputs["Roughness"].default_value = rug
    if emissao:
        b.inputs["Emission Color"].default_value = (*cor, 1)
        b.inputs["Emission Strength"].default_value = emissao
    # Relevo leve de "massinha"
    ruido = nt.nodes.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 18
    relevo = nt.nodes.new("ShaderNodeBump")
    relevo.inputs["Strength"].default_value = 0.08
    nt.links.new(ruido.outputs["Fac"], relevo.inputs["Height"])
    nt.links.new(relevo.outputs["Normal"], b.inputs["Normal"])
    return m, nt, b


def crosta_material():
    """Superfície: oceanos e continentes por ruído. Face cortada: rocha marrom."""
    m, nt, b = material("crosta", (0.55, 0.38, 0.25))
    coord = nt.nodes.new("ShaderNodeTexCoord")
    ruido = nt.nodes.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 0.45
    ruido.inputs["Detail"].default_value = 4
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.interpolation = "CONSTANT"
    rampa.color_ramp.elements[0].color = (0.05, 0.30, 0.85, 1)  # oceano
    rampa.color_ramp.elements[1].position = 0.52
    rampa.color_ramp.elements[1].color = (0.20, 0.62, 0.18, 1)  # terra
    nt.links.new(coord.outputs["Object"], ruido.inputs["Vector"])
    nt.links.new(ruido.outputs["Fac"], rampa.inputs["Fac"])
    dist = nt.nodes.new("ShaderNodeVectorMath")
    dist.operation = "LENGTH"
    nt.links.new(coord.outputs["Object"], dist.inputs[0])
    corte = nt.nodes.new("ShaderNodeMath")
    corte.operation = "GREATER_THAN"
    corte.inputs[1].default_value = R - 0.03
    nt.links.new(dist.outputs["Value"], corte.inputs[0])
    mistura = nt.nodes.new("ShaderNodeMix")
    mistura.data_type = "RGBA"
    mistura.inputs["A"].default_value = (0.55, 0.38, 0.25, 1)
    nt.links.new(corte.outputs["Value"], mistura.inputs["Factor"])
    nt.links.new(rampa.outputs["Color"], mistura.inputs["B"])
    nt.links.new(mistura.outputs["Result"], b.inputs["Base Color"])
    return m


# Faca: cubo que remove um octante; entra de longe e "fatia" a Terra no fim da cena 0.
bpy.ops.mesh.primitive_cube_add(size=2 * R + 2)
faca = bpy.context.object
faca.name = "faca"
for v in faca.data.vertices:
    v.co += Vector((R + 1, -(R + 1), R + 1))
faca.hide_render = True
faca.display_type = "WIRE"
direcao = Vector((1, -1, 1)).normalized()
faca.location = direcao * 14
faca.keyframe_insert("location", frame=quadro(inicios[1] - 1.2))
faca.location = (0, 0, 0)
faca.keyframe_insert("location", frame=quadro(inicios[1] - 0.2))

camadas = [  # raio externo, espessura, material (crosta exagerada para aparecer)
    (R, 0.28, crosta_material()),
    (R - 0.28, R - 0.28 - 2.73, material("manto", (0.85, 0.22, 0.06))[0]),
    (2.73, 2.73 - 0.96, material("nucleo_externo", (1.0, 0.55, 0.05), emissao=0.25)[0]),
]
for raio, esp, mat in camadas:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=raio, segments=96, ring_count=48)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    s = o.modifiers.new("casca", "SOLIDIFY")
    s.thickness = esp
    s.offset = -1
    bo = o.modifiers.new("corte", "BOOLEAN")
    bo.object = faca
    bo.solver = "EXACT"
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.96, segments=64, ring_count=32)
nucleo = bpy.context.object
bpy.ops.object.shade_smooth()
nucleo.data.materials.append(material("nucleo_interno", (1.0, 0.85, 0.20), emissao=0.6)[0])
bo = nucleo.modifiers.new("corte", "BOOLEAN")
bo.object = faca
bo.solver = "EXACT"

# Luz suave de estúdio + fundo pastel
bpy.ops.object.light_add(type="AREA", location=(8, -10, 12))
luz = bpy.context.object
luz.data.energy = 1600
luz.data.size = 12
luz.rotation_euler = (math.radians(45), 0, math.radians(40))
bpy.ops.object.light_add(type="AREA", location=(-12, -4, 4))
bpy.context.object.data.energy = 300
bpy.context.object.data.size = 10
bpy.context.object.rotation_euler = (math.radians(80), 0, math.radians(-70))
mundo = bpy.data.worlds.new("mundo")
sc.world = mundo
mundo.use_nodes = True
mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.98, 0.80, 0.72, 1)
mundo.node_tree.nodes["Background"].inputs[1].default_value = 0.35

# Câmera: gira em volta (pivô) e aponta para um alvo que caminha até o núcleo.
bpy.ops.object.empty_add(location=(0, 0, 0))
pivo = bpy.context.object
bpy.ops.object.empty_add(location=(0, 0, 0))
alvo = bpy.context.object
bpy.ops.object.camera_add()
cam = bpy.context.object
cam.parent = pivo
cam.data.lens = 50
sc.camera = cam
mira = cam.constraints.new("TRACK_TO")
mira.target = alvo
mira.track_axis = "TRACK_NEGATIVE_Z"
mira.up_axis = "UP_Y"

olhar = Vector((1, -1, 0.75)).normalized()
roteiro = [  # (distância, alvo ao longo da diagonal do corte, giro do pivô em graus)
    (34, 0.0, -70), (24, 2.2, -8), (22, 1.2, -4), (17, 0.6, 2), (12.5, 0.15, 6), (30, 0.0, 14), (34, 0.0, 22),
]
marcas = [quadro(t) for t in inicios] + [quadro(total)]
for i, (dist, al, giro) in enumerate(roteiro):
    for f in (marcas[i] + (0 if i == 0 else round(0.6 * FPS)), marcas[i + 1]):
        cam.location = olhar * dist
        cam.keyframe_insert("location", frame=f)
        alvo.location = direcao * al
        alvo.keyframe_insert("location", frame=f)
        pivo.rotation_euler = (0, 0, math.radians(giro + (4 if f == marcas[i + 1] else 0)))
        pivo.keyframe_insert("rotation_euler", frame=f)
for obj in (cam, alvo, pivo, faca):
    if obj.animation_data:
        for fc in obj.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = "BEZIER"
                k.easing = "EASE_IN_OUT"

sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 10
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy"
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, marcas[-1]
sc.render.image_settings.file_format = "PNG"
sc.render.film_transparent = True  # o fundo em degradê entra na montagem
sc.render.image_settings.color_mode = "RGBA"
sc.render.filepath = saida
if "--previa" in args:
    # Um quadro do meio de cada cena, pequeno e rápido, para conferir o enquadramento.
    sc.render.resolution_percentage = 50
    sc.cycles.samples = 4
    for i in range(len(marcas) - 1):
        sc.frame_set((marcas[i] + marcas[i + 1]) // 2)
        sc.render.filepath = f"{saida}previa_{i}.png"
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
