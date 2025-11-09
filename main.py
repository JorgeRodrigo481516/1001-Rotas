"""main.py

Responsabilidade:
    - Criar a janela do jogo, montar o cenário com tiles e desenhar o HUD + protagonista.

Contrato (entradas/saídas):
    - Entrada: arquivos de imagem em `assets/` (tiles, HUD, protagonista, slots).
    - Saída: exibe uma janela com o cenário desenhado.

Comportamento:
        - Carrega 6 variações de tile e preenche a janela com uma grade (sem margens).
        - Reserva as duas primeiras linhas no topo para o HUD e desenha o HUD ali.
        - Desenha o protagonista sobre os tiles, animação e movimento usam delta time
            (independente do FPS). Também aplica limites para não entrar na área do HUD.

Regras:
    - Os tiles são colocados sem margens entre si.
    - O HUD ocupa a altura de 2 tiles no topo e não é preenchido por tiles.

Notas:
    - Código escrito para ser fácil de entender por iniciantes.
    - Use delta time do `Window` para movimento/ animação consistente.
"""

from PPlay.window import Window
from PPlay.sprite import Sprite
import random


class Tile:
    """Representa uma célula (tile) do cenário.

    Responsabilidade:
        - Guardar o sprite base do tile, suas coordenadas no mapa e a sobreposição
          (overlay), se houver.

    Contrato:
        - Entrada: sprite (Sprite), coord_x (int), coord_y (int)
        - Saída: objeto Tile com métodos para desenhar e gerenciar overlays.

    Comportamento:
        - Desenha o sprite base e, se presente, desenha a overlay centralizada.

    Regras:
        - Coord_x e coord_y representam posições no grid (0,1,2...).
        - A overlay é opcional e, quando adicionada, permanece até ser substituída.
    """

    def __init__(self, sprite, coord_x, coord_y):
        self.sprite = sprite
        self.coord_x = coord_x
        self.coord_y = coord_y

    def draw(self):
        # Desenha o tile base
        self.sprite.draw()

        # Se existir uma sobreposição, desenha por cima do tile
        if hasattr(self, "overlay") and self.overlay is not None:
            self.overlay.draw()

    def has_overlay(self):
        """Retorna True se o tile já tem uma sobreposição (overlay)."""
        return hasattr(self, "overlay") and self.overlay is not None

    def add_overlay(self, image_path=None):
        """Adiciona uma imagem de sobreposição centralizada no tile.

        Responsabilidade:
            - Criar e posicionar um sprite de sobreposição para este tile.

        Contrato:
            - Entrada: image_path (str) opcional, caminho para a imagem da sobreposição.
                       Se None, usa a imagem padrão de escavação.
            - Saída: True se a sobreposição foi adicionada, False se já existia.

        Comportamento:
            - Primeiro verifica se já existe uma sobreposição (otimização).
            - Se não existir, cria um Sprite, centraliza sobre o tile e guarda em self.overlay.
        """
        # Testa se já existe sobreposição - se sim, não faz nada
        if self.has_overlay():
            return False

        # Caminho padrão da sobreposição (pode ser substituído por outro arquivo)
        if image_path is None:
            image_path = "assets/Escavação da superficie do deserto.png"

        # Cria o sprite da sobreposição
        ov = Sprite(image_path)

        # Centraliza a sobreposição sobre o tile
        ov.x = self.sprite.x + (self.sprite.width - ov.width) / 2
        ov.y = self.sprite.y + (self.sprite.height - ov.height) / 2

        # Registra a sobreposição no tile
        self.overlay = ov
        self.overlay_path = image_path
        return True

    def set_overlay(self, image_path):
        """Define (ou substitui) a sobreposição do tile para outra imagem.

        Se já existir uma sobreposição, ela é substituída pela nova.
        """
        # Se já existir, substitui; se não, chama add_overlay
        if self.has_overlay():
            ov = Sprite(image_path)
            ov.x = self.sprite.x + (self.sprite.width - ov.width) / 2
            ov.y = self.sprite.y + (self.sprite.height - ov.height) / 2
            self.overlay = ov
            self.overlay_path = image_path
            return True
        else:
            return self.add_overlay(image_path)

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
# Observação: usamos +1 para garantir cobertura mesmo quando a divisão não é exata
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


# --- Jogador / Protagonista ---
class Player:
    """Representa o protagonista com animação simples.

    Responsabilidade:
        - Gerenciar posição do jogador e escolher quadro de animação.

    Contrato:
        - Entrada: imagens em `assets/` (protagonistaD1/2, protagonistaE1/2)
        - Saída: desenha o jogador com a animação correta.

    Comportamento:
        - Quando o jogador se move, alterna entre duas imagens (frame1/frame2).
        - Mantém a última direção horizontal (direita ou esquerda).

    Regras:
        - Use as imagens: protagonistaD1.png, protagonistaD2.png (direita)
                         protagonistaE1.png, protagonistaE2.png (esquerda)
        - A animação é controlada por tempo (segundos por frame) usando delta time.
    """

    def __init__(self, x, y):
    # Carrega 4 frames de animação (2 para a direita, 2 para a esquerda)
        self.d1 = Sprite("assets/protagonistaD1.png")
        self.d2 = Sprite("assets/protagonistaD2.png")
        self.e1 = Sprite("assets/protagonistaE1.png")
        self.e2 = Sprite("assets/protagonistaE2.png")

        # Posição em pixels (top-left)
        self.x = x
        self.y = y

        # Estado de animação
        self.last_dir = "right"  # 'right' ou 'left'
        self.frame_toggle = False
        # animação baseada em tempo (segundos)
        self.anim_timer = 0.0
        self.anim_speed = 0.2  # segundos por frame

        # velocidade em pixels por segundo
        self.speed = 70.0

    def update(self, teclado, dt):
        """Atualiza posição e estado de animação com base nas teclas.

        Contrato:
            - Entrada: teclado (objeto Keyboard do PPlay)
            - Saída: atualiza x,y e estado interno
        """
        moving = False

        # distância a mover nesta atualização, baseada no delta time (dt em segundos)
        move_amount = self.speed * dt

        # Movimento horizontal
        if teclado.key_pressed("RIGHT"):
            self.x += move_amount
            self.last_dir = "right"
            moving = True
        elif teclado.key_pressed("LEFT"):
            self.x -= move_amount
            self.last_dir = "left"
            moving = True

        # Movimento vertical (não afeta direção horizontal)
        if teclado.key_pressed("UP"):
            self.y -= move_amount
            moving = True
        elif teclado.key_pressed("DOWN"):
            self.y += move_amount
            moving = True

        # Atualiza timer de animação apenas se estiver se movendo
        if moving:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                # decrementa por anim_speed para manter sobra de tempo
                self.anim_timer -= self.anim_speed
                self.frame_toggle = not self.frame_toggle
        else:
            # Se parado, mantenha frame inicial
            self.frame_toggle = False
            self.anim_timer = 0.0

        # --- Limites da tela e da área do HUD ---
        # largura/altura do sprite atual (assumimos mesmas dimensões entre frames)
        sprite_w = self.d1.width
        sprite_h = self.d1.height

        # Limites horizontais
        min_x = 0
        max_x = janela.width - sprite_w

        # Limites verticais: não entrar na área do HUD (altura_hud)
        min_y = altura_hud
        max_y = janela.height - sprite_h

        # Aplica limites
        if self.x < min_x:
            self.x = min_x
        if self.x > max_x:
            self.x = max_x
        if self.y < min_y:
            self.y = min_y
        if self.y > max_y:
            self.y = max_y

    def get_current_sprite(self):
        """Retorna o Sprite atual conforme direção e frame."""
        if self.last_dir == "right":
            return self.d2 if self.frame_toggle else self.d1
        else:
            return self.e2 if self.frame_toggle else self.e1

    def draw(self):
        s = self.get_current_sprite()
        s.x = self.x
        s.y = self.y
        s.draw()


# Cria o jogador e posiciona 1 tile à direita e 2 tiles acima da base
player = Player(1 * largura_tile, janela.height -  (2 * altura_tile) - max(0, slot_altura))


# --- Loop principal ---
while True:
    # Pinta o fundo (cor da areia)
    janela.set_background_color((245, 198, 132))

    # Pega o teclado e o delta time do Window (em segundos)
    teclado = janela.get_keyboard()
    dt = janela.delta_time()

    # Atualiza player (entrada + animação) usando dt (movimento e animação)
    player.update(teclado, dt)

    # Ao pressionar ESPAÇO, tenta adicionar uma sobreposição (escavação)
    # no tile onde o jogador está. Se o tile já tem overlay, não faz nada.
    if teclado.key_pressed("SPACE"):
        # Converte posição do jogador (pixels) para coordenadas do grid (tiles)
        coord_x = int(player.x / largura_tile)
        coord_y = int(player.y / altura_tile)
        t = encontrar_tile(coord_x, coord_y)
        if t is not None:
            # add_overlay retorna False se já existe, True se adicionou
            t.add_overlay()

    # Desenha os tiles do cenário
    for t in todos_os_tiles:
        t.draw()

    # Desenha o protagonista por cima dos tiles
    player.draw()

    # Desenha HUD (itens centrais)
    hud_sol.draw()
    hud_barra1.draw()
    hud_sede.draw()
    hud_barra2.draw()

    # Desenha os slots à direita
    for s in slots:
        s.draw()

    janela.update()