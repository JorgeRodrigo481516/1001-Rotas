"""Config - arquivo de configuração do jogo.

Responsabilidade:
        - Armazenar valores simples e constantes usados em todo o projeto (tamanhos,
            caminhos de assets, parâmetros padrão do jogador, ajustes do HUD).

Contrato (entrada/saída):
        - Entrada: nenhum. Este módulo fornece constantes para outros módulos importarem.
        - Saída: variáveis e dicionários (por exemplo `ASSETS`, `WINDOW_WIDTH`) usados
            por `main`, `Mapa`, `HUD`, `Player`, etc.

Comportamento:
        - Não executa lógica. Somente declara valores que podem ser alterados para
            ajustar comportamento/visual do jogo sem tocar em código.

Regras:
        - Mantenha apenas valores simples aqui. Não colocar funções com lógica complexa.
        - Use nomes claros e documente qualquer valor que precise ser ajustado.

Notas:
        - Algumas variáveis (por exemplo `TILE_WIDTH`/`TILE_HEIGHT`) são preenchidas
            em tempo de execução pelo carregamento do mapa e servem como cache global.
"""

# Janela --------------------------------------------------------------------
# Tamanho da janela do jogo em pixels. Alterar aqui muda a resolução usada pelo jogo.
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# HUD (head-up display) ----------------------------------------------------
# Quantas linhas de tiles (em unidades de tile) o HUD ocupa no topo da tela.
HUD_HEIGHT_IN_TILES = 2
# Ajuste horizontal para deslocar o bloco do HUD (pixels, valor positivo desloca para a direita).
HUD_SHIFT_LEFT = 180

# Espaçamento e contagem de slots (ajuste visual)
HUD_ELEMENT_SPACING = 10     # pixels entre ícones/barras centrais
HUD_SLOTS = 8                # número de slots exibidos no canto direito
HUD_SLOT_RIGHT_MARGIN = 20   # margem à direita (pixels)

# Player - parâmetros padrão (unidades simples)
# Velocidade de movimento do jogador em pixels por segundo.
PLAYER_SPEED = 70.0
# Tempo (segundos) por frame de animação do jogador.
PLAYER_ANIM_SPEED = 0.2

# ASSETS: mapeamento de nomes lógicos para caminhos de arquivos de imagem.
# Outros módulos importam `ASSETS['hud_sol']`, por exemplo. Ajuste caminhos se
# mover ou renomear arquivos na pasta `assets/`.
ASSETS = {
    'tile_base_pattern': "assets/Tiles Superfície do Deserto (6 variações)1.png",
    'player_d1': "assets/protagonistaD1.png",
    'player_d2': "assets/protagonistaD2.png",
    'player_e1': "assets/protagonistaE1.png",
    'player_e2': "assets/protagonistaE2.png",
    'hud_sol': "assets/spritesheet HUD sol.png",
    'hud_barra': "assets/spritesheet HUD barra.png",
    'hud_sede': "assets/spritesheet HUD sede.png",
    'slot': "assets/spritesheet HUD slot (1).png",
    'overlay_default': "assets/Escavação da superficie do deserto.png",
}

# TILE_WIDTH / TILE_HEIGHT: preenchidos em runtime pelo módulo `Mapa` após carregar
# o primeiro tile. Servem como cache global para que outros módulos saibam o
# tamanho de um tile sem recarregar imagens.
TILE_WIDTH = TILE_HEIGHT = None
