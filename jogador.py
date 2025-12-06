"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Define a entidade Jogador, controlando sua movimentação e ações.

RESPONSABILIDADE:
    1. Gerenciar posição e renderização do sprite do protagonista.
    2. Processar input de teclado para movimentação.
    3. Controlar estados de ação (andando, bebendo).
    4. Validar limites de movimento (colisão com bordas/HUD).

REGRAS DE USO:
    - Exige instâncias válidas de 'Mapa' e 'Janela'.
    - 'atualizar()' deve ser chamado a cada frame.

NOTAS DE IMPLEMENTAÇÃO:
    - Animação alterna entre sprites baseada no tempo.
    - Ação de beber bloqueia movimentação.
-------------------------------------------------------------------
"""
from PPlay.sprite import Sprite
import config


class Jogador:
    def __init__(self, x, y, janela, mapa, velocidade=None, velocidade_animacao=None, hud=None):
        self.janela = janela
        self.mapa = mapa
        self.hud = hud

        self.andar_direita_1, self.andar_direita_2, self.andar_esquerda_1, self.andar_esquerda_2 = (
            Sprite(config.RECURSOS['player_d1']),
            Sprite(config.RECURSOS['player_d2']),
            Sprite(config.RECURSOS['player_e1']),
            Sprite(config.RECURSOS['player_e2']),
        )

        self.x, self.y = x, y

        self.ultima_direcao = 'right'
        self.quadro_alternativo = False
        self.tempo_animacao = 0.0
        self.velocidade_animacao = velocidade_animacao if velocidade_animacao is not None else config.VELOCIDADE_ANIMACAO_JOGADOR

        self.velocidade_movimento = velocidade if velocidade is not None else config.VELOCIDADE_JOGADOR

        self._bebendo = False
        self._temporizador_bebida = 0.0
        self._duracao_bebida = 3.0
        self._indice_espaco_bebida = None

        self._mensagem_cabeca = ""
        self._temporizador_mensagem_cabeca = 0.0

    def atualizar(self, teclado, delta_tempo):
        if self._temporizador_mensagem_cabeca > 0:
            self._temporizador_mensagem_cabeca -= delta_tempo
            if self._temporizador_mensagem_cabeca <= 0:
                self._mensagem_cabeca = ""
                self._temporizador_mensagem_cabeca = 0.0

        if self.mapa.esta_escavando() or self.mapa.esta_investigando() or self._bebendo:
            esta_movendo = False
            self.quadro_alternativo = False
            self.tempo_animacao = 0.0
            if self._bebendo:
                self._temporizador_bebida += delta_tempo
                if self._temporizador_bebida >= self._duracao_bebida:
                    indice_espaco = self._indice_espaco_bebida
                    if self.hud is not None:
                        removido = self.hud.usar_item(indice_espaco)
                        if removido:
                            self.hud.definir_valores(sede=self.hud.sede - 200)
                            self.hud.exibir_mensagem('sede', '-200', duration=1.5)
                    self._bebendo = False
                    self._temporizador_bebida = 0.0
                    self._indice_espaco_bebida = None
        else:
            passo = self.velocidade_movimento * delta_tempo

            delta_x = 0
            if teclado.key_pressed("RIGHT"):
                delta_x = passo
                self.ultima_direcao = "right"
            elif teclado.key_pressed("LEFT"):
                delta_x = -passo
                self.ultima_direcao = "left"

            delta_y = 0
            if teclado.key_pressed("UP"):
                delta_y = -passo
            elif teclado.key_pressed("DOWN"):
                delta_y = passo

            self.x += delta_x
            self.y += delta_y
            esta_movendo = (delta_x != 0) or (delta_y != 0)

        if esta_movendo:
            self.tempo_animacao += delta_tempo
            if self.tempo_animacao >= self.velocidade_animacao:
                self.tempo_animacao -= self.velocidade_animacao
                self.quadro_alternativo = not self.quadro_alternativo
        else:
            self.quadro_alternativo = False
            self.tempo_animacao = 0.0

        largura_sprite, altura_sprite = self.andar_direita_1.width, self.andar_direita_1.height
        min_x, max_x = 0, self.janela.width - largura_sprite
        if not self.mapa.altura_tile:
            raise RuntimeError('Mapa precisa definir altura_tile antes de usar Jogador')
        min_y = config.ALTURA_HUD_EM_TILES * self.mapa.altura_tile
        max_y = self.janela.height - altura_sprite
        self.x = max(min_x, min(self.x, max_x))
        self.y = max(min_y, min(self.y, max_y))

    def desenhar(self):
        if self.ultima_direcao == 'right':
            sprite_atual = self.andar_direita_2 if self.quadro_alternativo else self.andar_direita_1
        else:
            sprite_atual = self.andar_esquerda_2 if self.quadro_alternativo else self.andar_esquerda_1
        sprite_atual.x, sprite_atual.y = self.x, self.y
        sprite_atual.draw()

        if self._mensagem_cabeca:
            texto_x = int(self.x + (sprite_atual.width / 2) - (len(self._mensagem_cabeca) * 3))
            texto_y = int(self.y - 25)
            self.janela.draw_text(self._mensagem_cabeca, texto_x, texto_y, size=14, color=(255, 0, 0))

        if self.mapa.esta_escavando():
            self._desenhar_barra_progresso(sprite_atual, "Escavando..", self.mapa.progresso_escavacao(), (194, 117, 30))

        if self.mapa.esta_investigando():
            self._desenhar_barra_progresso(sprite_atual, "Investigando...", self.mapa.progresso_investigacao(), (138, 43, 226))
            msg = self.mapa.obter_mensagem_investigacao_atual()
            if msg:
                texto_x = int(self.x + (sprite_atual.width / 2) - (len(msg) * 3))
                texto_y = int(self.y - 55)
                self.janela.draw_text(msg, texto_x, texto_y, size=14, color=(50, 0, 100))

        if self._bebendo:
            progresso = min(1.0, self._temporizador_bebida / max(1e-6, self._duracao_bebida))
            self._desenhar_barra_progresso(sprite_atual, "Bebendo..", progresso, (65, 105, 225))

    def _desenhar_barra_progresso(self, sprite_referencia, texto, progresso, cor_preenchimento):
        if "Escavando" in texto:
            cor_borda = (101, 67, 33)
            cor_fundo = (245, 222, 179)
            cor_texto = (0, 0, 0)
        elif "Bebendo" in texto:
            cor_borda = (0, 0, 128)
            cor_fundo = (224, 255, 255)
            cor_texto = (0, 0, 128)
        elif "Investigando" in texto:
            cor_borda = (75, 0, 130)
            cor_fundo = (230, 230, 250)
            cor_texto = (50, 0, 100)
        else:
            cor_borda = (0, 0, 0)
            cor_fundo = (255, 255, 255)
            cor_texto = (0, 0, 0)

        texto_x = int(self.x + (sprite_referencia.width / 2) - (len(texto) * 3))
        if "Investigando" in texto:
            texto_x += 10
        texto_y = int(self.y - 18)
        self.janela.draw_text(texto, texto_x, texto_y, size=14, color=cor_texto)

        largura_barra = int(sprite_referencia.width * 1) + 35
        altura_barra = 6
        barra_x = int(self.x + (sprite_referencia.width - largura_barra) / 2)
        barra_y = int(texto_y - altura_barra - 4)

        tela = self.janela.get_screen()
        tela.fill(cor_borda, (barra_x-1, barra_y-1, largura_barra+2, altura_barra+2))
        tela.fill(cor_fundo, (barra_x, barra_y, largura_barra, altura_barra))
        
        largura_preenchimento = max(0, min(largura_barra, int(largura_barra * float(progresso))))
        if largura_preenchimento > 0:
            tela.fill(cor_preenchimento, (barra_x, barra_y, largura_preenchimento, altura_barra))

    def beber(self, indice_espaco, duration=3.0):
        if self._bebendo:
            return False
        self._bebendo = True
        self._temporizador_bebida = 0.0
        self._duracao_bebida = float(duration)
        self._indice_espaco_bebida = int(indice_espaco)
        return True

    def exibir_mensagem_cabeca(self, texto, duration=2.0):
        self._mensagem_cabeca = texto
        self._temporizador_mensagem_cabeca = float(duration)

    def tem_mensagem_cabeca(self):
        return self._temporizador_mensagem_cabeca > 0

    def esta_bebendo(self):
        return bool(self._bebendo)

    def obter_coordenadas_grade(self, largura_tile, altura_tile):
        if largura_tile is None or altura_tile is None:
            raise ValueError('largura_tile e altura_tile devem estar definidos')
        return int(self.x / largura_tile), int(self.y / altura_tile)
