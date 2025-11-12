"""Player - classe do jogador.

Responsabilidade:
    - Representar o jogador: posição, movimento e animação.

Contrato (entrada/saída):
    - Entrada: construtor recebe posição inicial (x, y), `janela` (objeto Window)
      e `mapa` (para informações como altura de HUD). Métodos públicos:
        - `update(teclado, dt)` atualiza posição e animação por frame.
        - `draw()` desenha o sprite atual.
    - Saída: não retorna valores; altera estado interno (posição/frames).

Comportamento:
    - Lê sprites a partir de `Config.ASSETS`.
    - Move o jogador com base nas teclas pressionadas e aplica limites
      (janela e HUD).
    - Alterna frames de animação enquanto o jogador se move.

Regras:
    - Não trata colisões complexas; apenas limites de janela e HUD.
    - `mapa` deve fornecer `tile_height` antes do uso (para calcular limite superior).
"""

from PPlay.sprite import Sprite
import Config


class Player:
    """Classe que controla o jogador: posição, movimento e animação.

    Responsabilidade:
        - Manter posição e estado de animação do jogador.

    Contrato (entrada/saída):
        - Entrada no construtor: x, y (pixels - canto superior esquerdo),
          `janela` (Window), `mapa` (Mapa). Parâmetros opcionais: `speed`, `anim_speed`.
        - Saída: instância pronta para `update()` e `draw()` no loop do jogo.

    Comportamento:
        - Usa sprites definidos em `Config.ASSETS`.
        - Velocidade e tempo de animação usam valores do `Config` quando não passados.

    Regras:
        - `mapa.tile_height` deve estar definido (usado para limitar movimento vertical).

    Notas:
        - Este é um controlador simples; colisões e física devem ser implementadas
          em camadas superiores, se necessário.
    """

    def __init__(self, x, y, janela, mapa, speed=None, anim_speed=None):
        """Inicializa o jogador.

        Parâmetros:
            x, y: posição inicial em pixels (top-left).
            janela: objeto Window (possui width/height).
            mapa: objeto Mapa (deve expor tile_height).
            speed: (opcional) velocidade em px/s; padrão em Config.PLAYER_SPEED.
            anim_speed: (opcional) segundos por frame; padrão em Config.PLAYER_ANIM_SPEED.
        """
        self.janela = janela
        self.mapa = mapa

        # sprites de animação: walk_right_* = andando para a direita,
        # walk_left_* = andando para a esquerda
        self.walk_right_1, self.walk_right_2, self.walk_left_1, self.walk_left_2 = (
            Sprite(Config.ASSETS['player_d1']),
            Sprite(Config.ASSETS['player_d2']),
            Sprite(Config.ASSETS['player_e1']),
            Sprite(Config.ASSETS['player_e2']),
        )

        # posição
        self.x, self.y = x, y

        # estado de animação
        self.last_direction = 'right'
        self.frame_alt = False
        self.animation_timer = 0.0
        self.animation_speed = anim_speed if anim_speed is not None else Config.PLAYER_ANIM_SPEED

        # movimento (px/s)
        self.move_speed = speed if speed is not None else Config.PLAYER_SPEED

    def update(self, teclado, dt):
        """Mover o jogador e atualizar animação.

        Responsabilidade:
            - Atualizar posição com base nas teclas e alternar frames de animação.

        Contrato:
            - teclado: objeto de teclado (ex.: janela.get_keyboard()).
            - dt: delta time em segundos (ex.: janela.delta_time()).
        """

        move_step = self.move_speed * dt

        # movimentos horizontais
        dx = 0
        if teclado.key_pressed("RIGHT"):
            dx = move_step
            self.last_direction = "right"
        elif teclado.key_pressed("LEFT"):
            dx = -move_step

        # movimentos verticais
        dy = 0
        if teclado.key_pressed("UP"):
            dy = -move_step
        elif teclado.key_pressed("DOWN"):
            dy = move_step

        # aplica movimento acumulado
        self.x += dx
        self.y += dy
        moving = bool(dx or dy)

        # animação: alterna frames enquanto se move
        if moving:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer -= self.animation_speed
                self.frame_alt = not self.frame_alt
        else:
            self.frame_alt = False
            self.animation_timer = 0.0

        # limites: não sair da janela nem invadir a área do HUD
        sprite_w, sprite_h = self.walk_right_1.width, self.walk_right_1.height
        min_x, max_x = 0, self.janela.width - sprite_w
        if not getattr(self.mapa, 'tile_height', None):
            raise RuntimeError('Mapa precisa definir tile_height antes de usar Player')
        min_y = Config.HUD_HEIGHT_IN_TILES * self.mapa.tile_height
        max_y = self.janela.height - sprite_h
        # mantém posição dentro dos limites
        self.x = max(min_x, min(self.x, max_x))
        self.y = max(min_y, min(self.y, max_y))

    def draw(self):
        """Desenha o sprite atual do jogador.

        Escolhe o frame com base na direção e no estado de animação.
        """
        if self.last_direction == 'right':
            sprite = self.walk_right_2 if self.frame_alt else self.walk_right_1
        else:
            sprite = self.walk_left_2 if self.frame_alt else self.walk_left_1
        sprite.x, sprite.y = self.x, self.y
        sprite.draw()

    def get_grid_coords(self, tile_width, tile_height):
        """Retorna (coluna, linha) do tile onde o jogador está.

        Contrato:
            - Entrada: `tile_width` e `tile_height` (pixels).
            - Saída: (col, row) inteiros.
        """
        if tile_width is None or tile_height is None:
            raise ValueError('tile_width e tile_height devem estar definidos')
        return int(self.x / tile_width), int(self.y / tile_height)
