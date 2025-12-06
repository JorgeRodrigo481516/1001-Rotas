"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Define a entidade Jogador, controlando a movimentação, animação e 
    interação do protagonista com o mundo.

RESPONSABILIDADE:
    1. Gerenciar posição (x, y) e renderização dos sprites do personagem.
    2. Processar input de teclado para movimentação e iniciar ações (beber, escavar, investigar).
    3. Controlar estados de animação e bloqueio de movimento durante ações.
    4. Validar colisão com bordas da janela e área do HUD.
    5. Delegar a aplicação de regras de negócio (custos, recuperação de status) para a InterfaceUsuario.

REGRAS DE USO:
    - Exige instâncias válidas de 'Janela', 'Mapa' e opcionalmente 'InterfaceUsuario' (HUD).
    - Se x/y não forem fornecidos na instanciação, calcula posição inicial automaticamente.
    - 'atualizar()' deve ser chamado a cada frame do loop principal.

NOTAS DE IMPLEMENTAÇÃO:
    - A lógica de "o que acontece quando bebe" ou "custo de investigar" reside no HUD,
      o Jogador apenas solicita a execução dessas regras.
    - Mantém estado interno de 'bebendo' para bloquear input durante a animação.
-------------------------------------------------------------------
"""
from PPlay.sprite import Sprite
import config


class Jogador:
    def __init__(self, posicao_x, posicao_y, janela, mapa, velocidade=None, velocidade_animacao=None, interface=None):
        self.janela = janela
        self.mapa = mapa
        self.interface = interface

        self.andar_direita_1, self.andar_direita_2, self.andar_esquerda_1, self.andar_esquerda_2 = (
            Sprite(config.RECURSOS['jogador_direita_1']),
            Sprite(config.RECURSOS['jogador_direita_2']),
            Sprite(config.RECURSOS['jogador_esquerda_1']),
            Sprite(config.RECURSOS['jogador_esquerda_2']),
        )

        if posicao_x is None or posicao_y is None:
            self.definir_posicao_inicial()
        else:
            self.x, self.y = posicao_x, posicao_y

        self.ultima_direcao = 'right'
        self.quadro_alternativo = False
        self.tempo_animacao = 0.0
        self.velocidade_animacao = velocidade_animacao if velocidade_animacao is not None else config.VELOCIDADE_ANIMACAO_JOGADOR

        self.velocidade_movimento = velocidade if velocidade is not None else config.VELOCIDADE_JOGADOR

        self._bebendo = False
        self._temporizador_bebida = 0.0
        self._duracao_bebida = config.JOGABILIDADE['duracao_beber']
        self._indice_espaco_bebida = None

        self._mensagem_cabeca = ""
        self._temporizador_mensagem_cabeca = 0.0

    def atualizar(self, teclado, tempo_decorrido_segundos):
        self.processar_input_acoes(teclado)

        if self._temporizador_mensagem_cabeca > 0:
            self._temporizador_mensagem_cabeca -= tempo_decorrido_segundos
            if self._temporizador_mensagem_cabeca <= 0:
                self._mensagem_cabeca = ""
                self._temporizador_mensagem_cabeca = 0.0

        if self.mapa.esta_escavando() or self.mapa.esta_investigando() or self._bebendo:
            esta_movendo = False
            self.quadro_alternativo = False
            self.tempo_animacao = 0.0
            if self._bebendo:
                self._temporizador_bebida += tempo_decorrido_segundos
                if self._temporizador_bebida >= self._duracao_bebida:
                    indice_espaco = self._indice_espaco_bebida
                    if self.interface is not None:
                        self.interface.consumir_bebida(indice_espaco)
                    self._bebendo = False
                    self._temporizador_bebida = 0.0
                    self._indice_espaco_bebida = None
        else:
            passo = self.velocidade_movimento * tempo_decorrido_segundos

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
            self.tempo_animacao += tempo_decorrido_segundos
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

    def processar_input_acoes(self, teclado):
        if self.tem_mensagem_cabeca() or self.mapa.esta_escavando() or self.mapa.esta_investigando() or self.esta_bebendo():
            return

        if teclado.key_pressed("X"):
             coluna, linha = self.obter_coordenadas_grade(self.mapa.largura_tile, self.mapa.altura_tile)
             if self.mapa.iniciar_investigacao(coluna, linha):
                 if self.interface:
                    self.interface.aplicar_custo_investigacao()

        if teclado.key_pressed("SPACE"):
            coluna, linha = self.obter_coordenadas_grade(self.mapa.largura_tile, self.mapa.altura_tile)
            tem_pa = self.interface.tem_item('pa') if self.interface else False
            self.mapa.iniciar_escavacao(coluna, linha, tem_pa=tem_pa)

        if self.interface:
            for numero_tecla in range(1, min(8, len(self.interface.slots_inventario)) + 1):
                if teclado.key_pressed(str(numero_tecla)):
                    indice_espaco = numero_tecla - 1
                    if self.interface.sobreposicoes_slots[indice_espaco] is not None:
                        self.beber(indice_espaco, duration=config.JOGABILIDADE['duracao_beber'])
                    break

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
            self.janela.draw_text(self._mensagem_cabeca, texto_x, texto_y, size=config.INTERFACE_USUARIO['tamanho_fonte_padrao'], color=config.CORES['vermelho'])

        if self.mapa.esta_escavando():
            self._desenhar_barra_progresso(sprite_atual, "Escavando..", self.mapa.progresso_escavacao(), config.CORES['barra_escavacao_preenchimento'])

        if self.mapa.esta_investigando():
            self._desenhar_barra_progresso(sprite_atual, "Investigando...", self.mapa.progresso_investigacao(), config.CORES['barra_investigando_preenchimento'])
            msg = self.mapa.obter_mensagem_investigacao_atual()
            if msg:
                texto_x = int(self.x + (sprite_atual.width / 2) - (len(msg) * 3))
                texto_y = int(self.y - 55)
                self.janela.draw_text(msg, texto_x, texto_y, size=config.INTERFACE_USUARIO['tamanho_fonte_padrao'], color=config.CORES['texto_investigacao'])

        if self._bebendo:
            progresso = min(1.0, self._temporizador_bebida / max(1e-6, self._duracao_bebida))
            self._desenhar_barra_progresso(sprite_atual, "Bebendo..", progresso, config.CORES['azul_royal'])

    def _desenhar_barra_progresso(self, sprite_referencia, texto, progresso, cor_preenchimento):
        if "Escavando" in texto:
            cor_borda = config.CORES['barra_escavacao_borda']
            cor_fundo = config.CORES['barra_escavacao_fundo']
            cor_texto = config.CORES['preto']
        elif "Bebendo" in texto:
            cor_borda = config.CORES['barra_bebendo_borda']
            cor_fundo = config.CORES['barra_bebendo_fundo']
            cor_texto = config.CORES['azul_escuro']
        elif "Investigando" in texto:
            cor_borda = config.CORES['barra_investigando_borda']
            cor_fundo = config.CORES['barra_investigando_fundo']
            cor_texto = config.CORES['texto_investigacao']
        else:
            cor_borda = config.CORES['preto']
            cor_fundo = config.CORES['branco']
            cor_texto = config.CORES['preto']

        texto_x = int(self.x + (sprite_referencia.width / 2) - (len(texto) * 3))
        if "Investigando" in texto:
            texto_x += 10
        texto_y = int(self.y - 18)
        self.janela.draw_text(texto, texto_x, texto_y, size=config.INTERFACE_USUARIO['tamanho_fonte_padrao'], color=cor_texto)

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

    def definir_posicao_inicial(self):
        if self.interface and len(self.interface.slots_inventario) > 0:
            altura_espaco_hud = self.interface.slots_inventario[0].height
        else:
            altura_espaco_hud = 0
        
        self.x = self.mapa.largura_tile
        self.y = self.janela.height - (config.ALTURA_HUD_EM_TILES * self.mapa.altura_tile) - max(0, altura_espaco_hud)

    def processar_recompensa_escavacao(self, item_encontrado, overlay_adicionada):
        if item_encontrado == 'pa_duplicada':
             self.exibir_mensagem_cabeca("Só posso carregar uma pá...", duration=config.INTERFACE_USUARIO['duracao_msg_cabeca_erro'])
        elif item_encontrado == 'faca_duplicada':
             self.exibir_mensagem_cabeca("Só posso carregar uma faca...", duration=config.INTERFACE_USUARIO['duracao_msg_cabeca_erro'])
        else:
            if self.interface:
                self.interface.recuperar_sede_escavacao()
            
            if overlay_adicionada:
                if self.interface:
                    self.interface.processar_item_encontrado(item_encontrado)
            else:
                self.exibir_mensagem_cabeca("Não consegui...", duration=config.INTERFACE_USUARIO['duracao_msg_cabeca_padrao'])
