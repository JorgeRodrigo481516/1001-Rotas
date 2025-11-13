"""Player - classe do jogador.

Responsabilidade:
        - Representar o jogador: posição, movimento, animação e pequenas
            informações de interface (ex.: desenhar barra de progresso durante escavação).

Contrato (entrada/saída):
        - Entrada: construtor recebe posição inicial (x, y), `janela` (objeto Window)
            e `mapa` (para informações como altura de HUD e estado de escavação).
        - Métodos públicos principais:
                - `update(teclado, dt)` atualiza posição e animação por frame.
                - `draw()` desenha o sprite atual e elementos relacionados (texto/barra).
        - Saída: não retorna valores; altera estado interno (posição/frames).

Comportamento:
        - Lê sprites a partir de `Config.ASSETS`.
        - Move o jogador com base nas teclas pressionadas e aplica limites
            (janela e HUD).
        - Alterna frames de animação enquanto o jogador se move.

Regras/Notas:
        - `mapa` deve expor `tile_height` antes do uso (usado para calcular limite
            superior de movimento) e idealmente fornecer `is_excavating()` e
            `excavation_progress()` para suporte à mecânica de escavação.
        - Este módulo não implementa física avançada ou colisões; é um
            controlador simples adequado para jogos em grade.
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

    def __init__(self, x, y, janela, mapa, speed=None, anim_speed=None, hud=None):
        """Inicializa o jogador.

        Parâmetros:
            x, y: posição inicial em pixels (top-left).
            janela: objeto Window (possui width/height).
            mapa: objeto Mapa (deve expor tile_height).
            speed: (opcional) velocidade em px/s; padrão em Config.PLAYER_SPEED.
            anim_speed: (opcional) segundos por frame; padrão em Config.PLAYER_ANIM_SPEED.

        Contrato/Notas:
            - Espera `janela` com atributos `width` e `height`.
            - `mapa` deve ter `tile_height` disponível se você pretende usar
              limites verticais corretamente.
            - `speed` e `anim_speed` podem ser omitidos para usar valores em
              `Config`.
        """
        self.janela = janela
        self.mapa = mapa
        # referência ao HUD para aplicar efeitos (ex.: consumir água após beber)
        self.hud = hud

        # sprites de animação: walk_right_* = andando para a direita,
        # walk_left_* = andando para a esquerda
        self.andar_direita_1, self.andar_direita_2, self.andar_esquerda_1, self.andar_esquerda_2 = (
            Sprite(Config.ASSETS['player_d1']),
            Sprite(Config.ASSETS['player_d2']),
            Sprite(Config.ASSETS['player_e1']),
            Sprite(Config.ASSETS['player_e2']),
        )

        # posição
        self.x, self.y = x, y

        # estado de animação
        self.ultima_direcao = 'right'
        self.quadro_alternativo = False
        self.tempo_animacao = 0.0
        self.velocidade_animacao = anim_speed if anim_speed is not None else Config.PLAYER_ANIM_SPEED

        # movimento (px/s)
        self.velocidade_movimento = speed if speed is not None else Config.PLAYER_SPEED

        # estado de beber: quando o jogador inicia beber a água de um slot
        self._drinking = False
        self._drink_timer = 0.0
        self._drink_duration = 3.0  # segundos a beber
        self._drink_slot_index = None

    def update(self, teclado, dt):
        """Mover o jogador e atualizar animação.

        Responsabilidade:
            - Atualizar posição com base nas teclas e alternar frames de animação.

        Contrato:
            - teclado: objeto de teclado (ex.: janela.get_keyboard()).
            - dt: delta time em segundos (ex.: janela.delta_time()).

        Regras/Notas:
            - Se `mapa` fornecer `is_excavating()`, o jogador ficará imobilizado enquanto
              a escavação estiver em andamento. Este método assume que `mapa` é confiável
              quanto a essa API; use verificações com hasattr/callable quando chamar externamente.
        """

        # Se o mapa está em escavação, o jogador não pode se mover
        if (hasattr(self.mapa, 'is_excavating') and callable(self.mapa.is_excavating) and self.mapa.is_excavating()) or self._drinking:
            # bloqueia movimento e reseta animação
            esta_movendo = False
            self.quadro_alternativo = False
            self.tempo_animacao = 0.0
            # se estiver bebendo, decrementar o timer e aplicar o efeito quando terminar
            if self._drinking:
                self._drink_timer += dt
                if self._drink_timer >= self._drink_duration:
                    # terminou de beber: consumir o item do HUD e aplicar efeito
                    slot_idx = self._drink_slot_index
                    try:
                        if self.hud is not None:
                            # remove a água do slot
                            removed = self.hud.use_slot(slot_idx)
                            if removed:
                                # aplica efeito: reduzir sede em 200 e mostrar mensagem
                                self.hud.set_values(sede=self.hud.sede - 200)
                                self.hud.show_message('sede', '-200', duration=1.5)
                    except Exception:
                        pass
                    # reset estado de beber
                    self._drinking = False
                    self._drink_timer = 0.0
                    self._drink_slot_index = None
        else:
            passo = self.velocidade_movimento * dt

            # movimentos horizontais
            delta_x = 0
            if teclado.key_pressed("RIGHT"):
                delta_x = passo
                self.ultima_direcao = "right"
            elif teclado.key_pressed("LEFT"):
                delta_x = -passo
                self.ultima_direcao = "left"

            # movimentos verticais
            delta_y = 0
            if teclado.key_pressed("UP"):
                delta_y = -passo
            elif teclado.key_pressed("DOWN"):
                delta_y = passo

            # aplica movimento acumulado
            self.x += delta_x
            self.y += delta_y
            esta_movendo = (delta_x != 0) or (delta_y != 0)

        # animação: alterna frames enquanto se move
        if esta_movendo:
            self.tempo_animacao += dt
            if self.tempo_animacao >= self.velocidade_animacao:
                self.tempo_animacao -= self.velocidade_animacao
                self.quadro_alternativo = not self.quadro_alternativo
        else:
            self.quadro_alternativo = False
            self.tempo_animacao = 0.0

        # limites: não sair da janela nem invadir a área do HUD
        sprite_w, sprite_h = self.andar_direita_1.width, self.andar_direita_1.height
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

        Contrato/Notas:
            - Desenha o sprite atual na posição (`self.x`, `self.y`).
            - Se `mapa.is_excavating()` for True, desenha também um texto "Escavando.."
              e uma barra de progresso acima do sprite. Para desenhar texto utiliza
              `janela.draw_text()` quando disponível e para a barra usa a superfície
              retornada por `janela.get_screen()`.
            - Todo o desenho adicional é protegido por try/except para evitar que
              falhas gráficas quebrem o loop do jogo.
        """
        if self.ultima_direcao == 'right':
            current_sprite = self.andar_direita_2 if self.quadro_alternativo else self.andar_direita_1
        else:
            current_sprite = self.andar_esquerda_2 if self.quadro_alternativo else self.andar_esquerda_1
        current_sprite.x, current_sprite.y = self.x, self.y
        current_sprite.draw()
        # Se o mapa está escavando, mostramos 'Escavando..' acima da cabeça do jogador
        try:
            excavating = hasattr(self.mapa, 'is_excavating') and callable(self.mapa.is_excavating) and self.mapa.is_excavating()
        except Exception:
            excavating = False
        if excavating:
            text = "Escavando.."
            # posiciona texto centrado acima do sprite
            text_x = int(self.x + (current_sprite.width / 2) - (len(text) * 3))
            text_y = int(self.y - 18)
            # usa janela para desenhar texto
            try:
                self.janela.draw_text(text, text_x, text_y, size=14, color=(0,0,0))
            except Exception:
                pass
            # Desenha uma pequena barra de progresso acima do jogador (sem importar pygame,
            # usando apenas a API do PPlay: Window.get_screen().fill(rect))
            try:
                # progresso 0.0..1.0 fornecido por Mapa.excavation_progress()
                if hasattr(self.mapa, 'excavation_progress') and callable(self.mapa.excavation_progress):
                    progress = self.mapa.excavation_progress()
                else:
                    progress = 0.0
                # dimensões da barra (proporcional ao sprite)
                bar_w = int(current_sprite.width * 0.7)
                bar_h = 6
                # posiciona o texto primeiro, depois a barra acima do texto (pedido do usuário)
                text = "Escavando.."
                text_x = int(self.x + (current_sprite.width / 2) - (len(text) * 3))
                text_y = int(self.y - 18)
                bar_x = int(self.x + (current_sprite.width - bar_w) / 2)
                bar_y = int(text_y - bar_h - 4)
                # cores
                # cores em tom deserto: contorno mais escuro, fundo areia clara, preenchimento terracota
                border_color = (120, 90, 60)    # contorno (marrom escuro)
                back_color = (237, 201, 175)   # fundo da barra (areia clara)
                fill_color = (194, 117, 30)     # preenchimento (terracota / laranja quente)

                screen = self.janela.get_screen()
                # desenha contorno (retângulo maior)
                screen.fill(border_color, (bar_x-1, bar_y-1, bar_w+2, bar_h+2))
                # desenha fundo da barra
                screen.fill(back_color, (bar_x, bar_y, bar_w, bar_h))
                # desenha preenchimento conforme progresso
                fill_w = max(0, min(bar_w, int(bar_w * float(progress))))
                if fill_w > 0:
                    screen.fill(fill_color, (bar_x, bar_y, fill_w, bar_h))
            except Exception:
                # segurança: se algo falhar, não quebrar o jogo
                pass

        # Se o jogador está bebendo (iniciado por um slot), mostramos 'Bebendo..' e uma barra azul
        try:
            if self._drinking:
                text = "Bebendo.."
                # posiciona texto centrado acima do sprite
                text_x = int(self.x + (current_sprite.width / 2) - (len(text) * 3))
                text_y = int(self.y - 18)
                try:
                    self.janela.draw_text(text, text_x, text_y, size=14, color=(255,255,255))
                except Exception:
                    pass

                # barra de progresso azul
                try:
                    progress = min(1.0, self._drink_timer / max(1e-6, self._drink_duration))
                    bar_w = int(current_sprite.width * 0.7)
                    bar_h = 6
                    bar_x = int(self.x + (current_sprite.width - bar_w) / 2)
                    bar_y = int(text_y - bar_h - 4)
                    border_color = (30, 60, 120)
                    back_color = (40, 80, 140)
                    fill_color = (80, 160, 240)  # azul claro
                    screen = self.janela.get_screen()
                    screen.fill(border_color, (bar_x-1, bar_y-1, bar_w+2, bar_h+2))
                    screen.fill(back_color, (bar_x, bar_y, bar_w, bar_h))
                    fill_w = max(0, min(bar_w, int(bar_w * float(progress))))
                    if fill_w > 0:
                        screen.fill(fill_color, (bar_x, bar_y, fill_w, bar_h))
                except Exception:
                    pass
        except Exception:
            pass

    def start_drink(self, slot_index, duration=3.0):
        """Inicia a ação de beber a água do slot `slot_index`.

        A ação bloqueia movimento por `duration` segundos e ao terminar
        remove o item do HUD e aplica o efeito (reduzir sede em 200).
        """
        # não iniciar se já estiver bebendo
        if self._drinking:
            return False
        self._drinking = True
        self._drink_timer = 0.0
        self._drink_duration = float(duration)
        self._drink_slot_index = int(slot_index)
        return True

    def is_drinking(self):
        return bool(self._drinking)

    def get_grid_coords(self, tile_width, tile_height):
        """Retorna (coluna, linha) do tile onde o jogador está.

        Contrato:
            - Entrada: `tile_width` e `tile_height` (pixels).
            - Saída: (col, row) inteiros.
        """
        if tile_width is None or tile_height is None:
            raise ValueError('tile_width e tile_height devem estar definidos')
        return int(self.x / tile_width), int(self.y / tile_height)
