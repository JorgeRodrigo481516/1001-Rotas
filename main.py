"""main.py

Responsabilidade:
    - Criar a janela do jogo, montar o cenário com tiles e desenhar o HUD + protagonista.

Contrato (entradas/saídas):
    - Entrada: arquivos de imagem em `assets/` (tiles, HUD, protagonista, slots).
    - Saída: exibe uma janela com o cenário desenhado.

Comportamento:
    - Carrega 6 variações de tile e preenche a janela com uma grade.
    - Reserva as duas primeiras linhas no topo para o HUD.
    - Desenha o protagonista sobre os tiles e mostra HUD (ícones + barras + slots).

Regras:
    - Os tiles são colocados sem margens entre si.
    - O HUD ocupa a altura de 2 tiles no topo e não é preenchido por tiles.

Notas:
    - Nomes e comentários simples.
"""

from PPlay.window import Window
from PPlay.sprite import Sprite
import random


class Tile:
    """Representa uma célula (tile) do cenário.

    Responsabilidade:
        - Guardar o sprite e as coordenadas do tile no mapa.

    Contrato:
        - Entrada: sprite (Sprite), coord_x (int), coord_y (int)
        - Saída: objeto Tile com métodos simples.

    Comportamento:
        - Pode desenhar o seu sprite na tela e informar suas coordenadas.

    Regras:
        - Coord_x e coord_y representam posições no grid (0,1,2...).
    """

    def __init__(self, sprite, coord_x, coord_y):
        self.sprite = sprite
        self.coord_x = coord_x
        self.coord_y = coord_y

    def draw(self):
        self.sprite.draw()

    def get_position(self):
        return (self.coord_x, self.coord_y)


# --- Janela ---
janela = Window(800, 600)
janela.set_title("1001 Rotas")


# --- Tiles (cenário) ---
# Carrega um tile só para saber o tamanho (assume-se que todas as variações têm o mesmo tamanho)
primeiro_tile = Sprite("assets/Tiles Superfície do Deserto (6 variações)1.png")
largura_tile = primeiro_tile.width
altura_tile = primeiro_tile.height

# Quantos tiles precisamos (adiciona +1 para cobrir possíveis bordas)
tiles_horizontais = int(janela.width / largura_tile) + 1
tiles_verticais = int(janela.height / altura_tile) + 1

# Guarda os tiles do cenário e permite busca por coordenada
todos_os_tiles = []
mapa_tiles = {}


# --- HUD ---
# Carrega elementos do HUD
hud_sol = Sprite("assets/spritesheet HUD sol.png")
hud_barra1 = Sprite("assets/spritesheet HUD barra.png")
hud_sede = Sprite("assets/spritesheet HUD sede.png")
hud_barra2 = Sprite("assets/spritesheet HUD barra.png")

# Espaço reservado no topo (2 tiles de altura)
altura_hud = altura_tile * 2

# Calcula posição Y central para os elementos do HUD
hud_y = (altura_hud - hud_sol.height) / 2

# Largura total dos itens centrais do HUD (sol + barra + sede + barra)
espaco_entre_elementos = 10
largura_total_hud = (
    hud_sol.width + hud_barra1.width + hud_sede.width + hud_barra2.width
)
largura_total_com_espacos = largura_total_hud + (espaco_entre_elementos * 3)

# Move o HUD um pouco para a esquerda do centro para ajuste visual
hud_shift_left = 180
x_inicial_hud = ((janela.width - largura_total_com_espacos) / 2) - hud_shift_left

# Posiciona os itens centrais do HUD
hud_sol.x = x_inicial_hud
hud_sol.y = hud_y
hud_barra1.x = hud_sol.x + hud_sol.width + espaco_entre_elementos
hud_barra1.y = hud_y
hud_sede.x = hud_barra1.x + hud_barra1.width + espaco_entre_elementos
hud_sede.y = hud_y
hud_barra2.x = hud_sede.x + hud_sede.width + espaco_entre_elementos
hud_barra2.y = hud_y


# --- Slots (direita do HUD) ---
# Cria 8 slots alinhados à direita e centralizados verticalmente no espaço do HUD
slots = []
slot_exemplo = Sprite("assets/spritesheet HUD slot (1).png")
slot_largura = slot_exemplo.width
slot_altura = slot_exemplo.height

margem_direita = 20
x_slots = janela.width - (8 * slot_largura) - margem_direita
y_slots = (altura_hud - slot_altura) / 2

for i in range(8):
    s = Sprite("assets/spritesheet HUD slot (1).png")
    s.x = x_slots + (i * slot_largura)
    s.y = y_slots
    slots.append(s)


# --- Monta a grade de tiles, pulando as duas primeiras linhas (HUD) ---
for linha in range(tiles_verticais):
    if linha < 2:
        # Não desenhar tiles nas duas primeiras linhas (espaço do HUD)
        continue

    for coluna in range(tiles_horizontais):
        numero = random.randint(1, 6)
        sprite = Sprite(f"assets/Tiles Superfície do Deserto (6 variações){numero}.png")
        sprite.x = coluna * largura_tile
        sprite.y = linha * altura_tile
        tile = Tile(sprite, coluna, linha)
        todos_os_tiles.append(tile)
        mapa_tiles[(coluna, linha)] = tile


def encontrar_tile(coord_x, coord_y):
    """Retorna o Tile nas coordenadas do grid ou None.

    Contrato:
        - Entrada: coord_x (int), coord_y (int)
        - Saída: Tile | None

    Comportamento:
        - Busca no dicionário `mapa_tiles` pela chave (coord_x, coord_y).
    """

    return mapa_tiles.get((coord_x, coord_y))


# --- Protagonista ---
protagonista = Sprite("assets/protagonista1.png")
# Posiciona 1 tile à direita e 2 tiles acima da base
protagonista.x = 1 * largura_tile
protagonista.y = janela.height - protagonista.height - (2 * altura_tile)


# --- Loop principal ---
while True:
    janela.set_background_color((245, 198, 132))

    # Desenha os tiles do cenário
    for t in todos_os_tiles:
        t.draw()

    # Desenha o protagonista por cima dos tiles
    protagonista.draw()

    # Desenha HUD (itens centrais)
    hud_sol.draw()
    hud_barra1.draw()
    hud_sede.draw()
    hud_barra2.draw()

    # Desenha os slots à direita
    for s in slots:
        s.draw()

    janela.update()