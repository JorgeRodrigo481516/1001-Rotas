"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia o HUD (Heads-Up Display), barras de status e inventário.

RESPONSABILIDADE:
    1. Exibir barras de Sede e Sol.
    2. Gerenciar slots de inventário e itens coletados.
    3. Exibir mensagens temporárias na tela.
    4. Calcular layout dinâmico baseado na resolução.

REGRAS DE USO:
    - Deve ser atualizado com 'definir_valores()' para refletir estado do jogo.
    - 'desenhar()' renderiza todos os elementos da interface.

NOTAS DE IMPLEMENTAÇÃO:
    - Barras de status usam sprites de preenchimento repetidos.
    - Slots de inventário suportam sobreposição de itens.
-------------------------------------------------------------------
"""
from PPlay.sprite import Sprite
import config


class InterfaceUsuario:
    def __init__(self, janela):
        self.janela = janela

        self.icone_sol = Sprite(config.RECURSOS['hud_sol'])
        self.barra_sol = Sprite(config.RECURSOS['hud_barra'])
        self.icone_sede = Sprite(config.RECURSOS['hud_sede'])
        self.barra_sede = Sprite(config.RECURSOS['hud_barra'])

        self.sede = 100
        self.sol = 100

        self.espacos = []
        self.calcular_disposicao()

        if not hasattr(config, 'PREENCHIMENTOS_BARRA_HUD'):
            raise RuntimeError('config.PREENCHIMENTOS_BARRA_HUD must be defined (list of image paths)')

        self.sprites_preenchimento = []
        for caminho in config.PREENCHIMENTOS_BARRA_HUD:
            try:
                sprite = Sprite(caminho) if caminho is not None else None
            except Exception:
                sprite = None
            self.sprites_preenchimento.append(sprite)

        self._mensagem_sede = ""
        self._temporizador_mensagem_sede = 0.0
        self._mensagem_sol = ""
        self._temporizador_mensagem_sol = 0.0

    def calcular_disposicao(self):
        altura_tile = getattr(config, 'ALTURA_TILE', None)
        tiles_hud = getattr(config, 'ALTURA_HUD_EM_TILES', None)
        altura_hud = (altura_tile * tiles_hud) if (altura_tile and tiles_hud) else (self.icone_sol.height * 2)

        y = (altura_hud - self.icone_sol.height) / 2

        espaco_entre = getattr(config, 'ESPACAMENTO_ELEMENTOS_HUD', 6)
        deslocamento_esquerda = getattr(config, 'DESLOCAMENTO_ESQUERDA_HUD', 0)

        largura_total = (self.icone_sol.width + self.barra_sol.width + self.icone_sede.width + self.barra_sede.width) + espaco_entre * 3
        pos_x = ((self.janela.width - largura_total) / 2) - deslocamento_esquerda

        for sprite in (self.icone_sol, self.barra_sol, self.icone_sede, self.barra_sede):
            sprite.x = pos_x
            sprite.y = y
            pos_x += sprite.width + espaco_entre

        sprite_temporario = Sprite(config.RECURSOS['slot'])
        largura_espaco, altura_espaco = sprite_temporario.width, sprite_temporario.height
        del sprite_temporario

        contagem_espacos = getattr(config, 'QUANTIDADE_SLOTS_HUD', 8)
        margem_direita_espaco = getattr(config, 'MARGEM_DIREITA_SLOT_HUD', 10)
        x_espacos = self.janela.width - (contagem_espacos * largura_espaco) - margem_direita_espaco
        y_espacos = (altura_hud - altura_espaco) / 2

        self.espacos = [Sprite(config.RECURSOS['slot']) for _ in range(contagem_espacos)]
        for i, s in enumerate(self.espacos):
            s.x = x_espacos + i * largura_espaco
            s.y = y_espacos
        self.sobreposicoes_espacos = [None for _ in range(contagem_espacos)]

    def definir_valores(self, sede=None, sol=None):
        if sede is not None:
            self.sede = max(0, min(1000, int(sede)))
        if sol is not None:
            self.sol = max(0, min(1000, int(sol)))

    def desenhar(self):
        self.icone_sol.draw()
        self.barra_sol.draw()

        self.icone_sede.draw()
        self.barra_sede.draw()

        def desenhar_preenchimento_para(sprite_barra, valor):
            if valor <= 0:
                return

            exemplo_preenchimento = next((p for p in self.sprites_preenchimento if p is not None), None)
            if exemplo_preenchimento is None:
                return

            largura_bloco = int(exemplo_preenchimento.width)
            altura_bloco = int(exemplo_preenchimento.height)

            padding_esq = int(getattr(config, 'PREENCHIMENTO_HUD_PADDING_ESQUERDA', 0))
            padding_dir = int(getattr(config, 'PREENCHIMENTO_HUD_PADDING_DIREITA', 0))
            espaco_entre_blocos = int(getattr(config, 'ESPACAMENTO_PREENCHIMENTO_HUD', 0))

            largura_barra = int(sprite_barra.width)
            largura_util = max(0, largura_barra - padding_esq - padding_dir)

            passo_por_bloco = largura_bloco + espaco_entre_blocos
            if passo_por_bloco <= 0:
                return

            num_blocos = max(1, largura_util // passo_por_bloco)

            blocos_preenchidos = int((valor / 1000.0) * num_blocos)
            blocos_preenchidos = max(0, min(blocos_preenchidos, num_blocos))

            segmentos = max(1, len(self.sprites_preenchimento))
            blocos_por_segmento = max(1, num_blocos // segmentos)

            x_inicio = sprite_barra.x + padding_esq
            y_inicio = sprite_barra.y + (sprite_barra.height - altura_bloco) / 2

            for indice in range(blocos_preenchidos):
                indice_segmento = min(segmentos - 1, indice // blocos_por_segmento)
                sprite_para_desenhar = self.sprites_preenchimento[indice_segmento]
                if sprite_para_desenhar is None:
                    continue

                pos_x = x_inicio + indice * passo_por_bloco
                sprite_para_desenhar.x = pos_x
                sprite_para_desenhar.y = y_inicio
                sprite_para_desenhar.draw()

        desenhar_preenchimento_para(self.barra_sol, self.sol)
        desenhar_preenchimento_para(self.barra_sede, self.sede)

        try:
            delta_tempo = self.janela.delta_time()
        except Exception:
            delta_tempo = 0

        if self._temporizador_mensagem_sede > 0:
            self._temporizador_mensagem_sede -= delta_tempo
            if self._temporizador_mensagem_sede <= 0:
                self._mensagem_sede = ""
                self._temporizador_mensagem_sede = 0.0

        if self._temporizador_mensagem_sol > 0:
            self._temporizador_mensagem_sol -= delta_tempo
            if self._temporizador_mensagem_sol <= 0:
                self._mensagem_sol = ""
                self._temporizador_mensagem_sol = 0.0

        if self._mensagem_sol:
            texto_x = int(self.barra_sol.x + (self.barra_sol.width / 2) - (len(self._mensagem_sol) * 3))
            texto_y = int(self.barra_sol.y + self.barra_sol.height + 4)
            self.janela.draw_text(self._mensagem_sol, texto_x, texto_y, size=14, color=(0,0,0))

        if self._mensagem_sede:
            texto_x = int(self.barra_sede.x + (self.barra_sede.width / 2) - (len(self._mensagem_sede) * 3))
            texto_y = int(self.barra_sede.y + self.barra_sede.height + 4)
            self.janela.draw_text(self._mensagem_sede, texto_x, texto_y, size=14, color=(0,0,0))

        for s in self.espacos:
            s.draw()
        for overlay in getattr(self, 'sobreposicoes_espacos', []):
            if overlay is not None:
                overlay.draw()

    def adicionar_item(self, caminho_imagem):
        for i, ov in enumerate(self.sobreposicoes_espacos):
            if ov is None:
                try:
                    sprite = Sprite(caminho_imagem)
                    espaco = self.espacos[i]
                    sprite.x = espaco.x + (espaco.width - sprite.width) / 2
                    sprite.y = espaco.y + (espaco.height - sprite.height) / 2
                    self.sobreposicoes_espacos[i] = sprite
                    return True
                except Exception:
                    return False
        return False

    def usar_item(self, index):
        if index < 0 or index >= len(self.sobreposicoes_espacos):
            return False
        if self.sobreposicoes_espacos[index] is None:
            return False
        try:
            self.sobreposicoes_espacos[index] = None
            return True
        except Exception:
            return False

    def exibir_mensagem(self, tipo, texto, duration=1.5):
        if tipo == 'sede':
            self._mensagem_sede = str(texto)
            self._temporizador_mensagem_sede = float(duration)
        elif tipo == 'sol':
            self._mensagem_sol = str(texto)
            self._temporizador_mensagem_sol = float(duration)
        else:
            return
