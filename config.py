"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Arquivo central de configurações, constantes e caminhos de recursos.

RESPONSABILIDADE:
    1. Definir resolução e parâmetros da janela.
    2. Mapear caminhos de arquivos de imagem (assets).
    3. Definir constantes de gameplay (velocidade, dimensões).

REGRAS DE USO:
    - Importado por quase todos os módulos.
    - Alterações aqui afetam o comportamento global do jogo.

NOTAS DE IMPLEMENTAÇÃO:
    - Dicionário RECURSOS centraliza paths de assets.
-------------------------------------------------------------------
"""

LARGURA_JANELA = 800
ALTURA_JANELA = 600

ALTURA_HUD_EM_TILES = 2
DESLOCAMENTO_ESQUERDA_HUD = 180

ESPACAMENTO_ELEMENTOS_HUD = 10
QUANTIDADE_SLOTS_HUD = 8
MARGEM_DIREITA_SLOT_HUD = 20

PREENCHIMENTO_HUD_PADDING_ESQUERDA = 7
PREENCHIMENTO_HUD_PADDING_DIREITA = 4
ESPACAMENTO_PREENCHIMENTO_HUD = 0

VELOCIDADE_JOGADOR = 70.0
VELOCIDADE_ANIMACAO_JOGADOR = 0.2

RECURSOS = {
    'tile_base_pattern': "assets/Tiles Superfície do Deserto (6 variações)1.png",
    'player_d1': "assets/protagonistaD1.png",
    'player_d2': "assets/protagonistaD2.png",
    'player_e1': "assets/protagonistaE1.png",
    'player_e2': "assets/protagonistaE2.png",
    'hud_sol': "assets/spritesheet HUD sol.png",
    'hud_barra': "assets/spritesheet HUD barra.png",
    'hud_sede': "assets/spritesheet HUD sede.png",
    'slot': "assets/spritesheet HUD slot (1).png",
    'overlay_default': "assets/escavação da superficie do deserto.png",
    'agua': "assets/agua.png",
    'pa': "assets/pa.png",
    'faca': "assets/faca.png",
}

PREENCHIMENTOS_BARRA_HUD = [
    "assets/barra cor 1.png",
    "assets/barra cor 2.png",
    "assets/barra cor 3.png",
    "assets/barra cor 4.png",
    "assets/barra cor 5.png",
    "assets/barra cor 6.png",
    "assets/barra cor 7.png",
    "assets/barra cor 8.png",
]

LARGURA_TILE = ALTURA_TILE = None

CUSTO_INVESTIGACAO_SEDE = 30
CUSTO_INVESTIGACAO_SOL = 30

DIFICULDADE_INVESTIGACAO_DIAGONAL = 15
DIFICULDADE_INVESTIGACAO_ORTOGONAL = 10
DIFICULDADE_INVESTIGACAO_CENTRO = 5

TEMPO_MENSAGEM_INVESTIGACAO = 2.0
DELAY_ENTRE_MENSAGENS = 0.3
DELAY_INICIAL_INVESTIGACAO = 1.0
DELAY_FINAL_INVESTIGACAO = 1.0
