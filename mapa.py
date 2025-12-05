"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia a construção do cenário, tiles (azulejos) e mecânica de escavação.

RESPONSABILIDADE:
    1. Gerar o grid de azulejos baseado na configuração.
    2. Gerenciar sobreposições (overlays) nos tiles.
    3. Controlar a lógica e temporização da escavação.
    4. Determinar se itens são encontrados ao escavar.

REGRAS DE USO:
    - 'construir()' deve ser chamado após inicialização.
    - Depende de recursos definidos em config.py.

NOTAS DE IMPLEMENTAÇÃO:
    - Usa sistema de grid (coluna, linha) mapeado para pixels.
    - Escavação é assíncrona (baseada em tempo).
-------------------------------------------------------------------
"""
from PPlay.sprite import Sprite
import config
import random


class Azulejo:
    def __init__(self, sprite, coluna, linha):
        self.sprite = sprite
        self.coluna = coluna
        self.linha = linha
        self.sprite_sobreposicao = None
        self.item = None

    def desenhar(self):
        self.sprite.draw()
        if self.sprite_sobreposicao:
            self.sprite_sobreposicao.draw()

    def tem_sobreposicao(self):
        return self.sprite_sobreposicao is not None

    def adicionar_sobreposicao(self, caminho_imagem=None):
        if self.tem_sobreposicao():
            return False
        if caminho_imagem is None:
            caminho_imagem = config.RECURSOS['overlay_default']
        sprite_sobreposicao = Sprite(caminho_imagem)
        sprite_sobreposicao.x = self.sprite.x + (self.sprite.width - sprite_sobreposicao.width) / 2
        sprite_sobreposicao.y = self.sprite.y + (self.sprite.height - sprite_sobreposicao.height) / 2
        self.sprite_sobreposicao = sprite_sobreposicao
        return True


class Mapa:
    def __init__(self, janela, largura_tile=None, altura_tile=None):
        self.janela = janela
        self.largura_tile = largura_tile
        self.altura_tile = altura_tile
        self.azulejos = []
        self.azulejos_por_coordenada = {}
        self._escavando = False
        self._alvo_escavacao = (None, None)
        self._temporizador_escavacao = 0.0
        self._duracao_escavacao = 2.0

    def construir(self):
        caminho_base = config.RECURSOS.get('tile_base_pattern')
        if caminho_base is None:
            raise RuntimeError('config.RECURSOS["tile_base_pattern"] must be set')

        exemplo = Sprite(caminho_base)
        self.largura_tile = exemplo.width
        self.altura_tile = exemplo.height

        config.LARGURA_TILE = self.largura_tile
        config.ALTURA_TILE = self.altura_tile

        num_colunas = int(self.janela.width / self.largura_tile) + 1
        num_linhas = int(self.janela.height / self.altura_tile) + 1

        if '.' in caminho_base:
            indice = caminho_base.rfind('.')
            nome_base = caminho_base[:indice]
            extensao = caminho_base[indice:]
        else:
            nome_base = caminho_base
            extensao = ''
        if '{}' in caminho_base:
            padrao_arquivo = caminho_base
        elif nome_base.endswith('1'):
            padrao_arquivo = f"{nome_base[:-1]}{{}}{extensao}"
        else:
            padrao_arquivo = f"{nome_base}{{}}{extensao}"

        linha_inicio_hud = config.ALTURA_HUD_EM_TILES
        usa_placeholder = '{}' in padrao_arquivo

        for linha in range(linha_inicio_hud, num_linhas):
            for coluna in range(num_colunas):
                indice_variacao = random.randint(1, 6)
                caminho_azulejo = padrao_arquivo.format(indice_variacao) if usa_placeholder else caminho_base

                sprite_azulejo = Sprite(caminho_azulejo)
                sprite_azulejo.x = coluna * self.largura_tile
                sprite_azulejo.y = linha * self.altura_tile

                novo_azulejo = Azulejo(sprite_azulejo, coluna, linha)
                self.azulejos.append(novo_azulejo)
                self.azulejos_por_coordenada[(coluna, linha)] = novo_azulejo

        total_azulejos = len(self.azulejos)
        qtd_agua = int(total_azulejos * 0.35)
        qtd_pa = int(total_azulejos * 0.05)
        
        itens = ['agua'] * qtd_agua + ['pa'] * qtd_pa + [None] * (total_azulejos - qtd_agua - qtd_pa)
        random.shuffle(itens)
        random.shuffle(itens)
        
        for i, azulejo in enumerate(self.azulejos):
            azulejo.item = itens[i]

    def obter_azulejo_grade(self, coluna, linha):
        return self.azulejos_por_coordenada.get((coluna, linha))

    def obter_azulejo_pixel(self, px, py):
        if not self.largura_tile or not self.altura_tile:
            raise ValueError('Mapa.largura_tile/altura_tile must be set')
        return self.obter_azulejo_grade(int(px / self.largura_tile), int(py / self.altura_tile))

    def adicionar_sobreposicao_em(self, coluna, linha, caminho_imagem=None):
        azulejo = self.obter_azulejo_grade(coluna, linha)
        if azulejo:
            return azulejo.adicionar_sobreposicao(caminho_imagem)
        return False

    def iniciar_escavacao(self, coluna, linha, tem_pa=False):
        if self._escavando:
            return False
        azulejo = self.obter_azulejo_grade(coluna, linha)
        if azulejo is None:
            return False
        if azulejo.tem_sobreposicao():
            return False
        self._escavando = True
        self._alvo_escavacao = (coluna, linha)
        self._temporizador_escavacao = 0.0
        self._duracao_atual = self._duracao_escavacao / 2.0 if tem_pa else self._duracao_escavacao
        return True

    def atualizar_escavacao(self, delta_tempo, bonus_dado=0, tem_pa=False):
        if not self._escavando:
            return (False, False, None, 0)
        self._temporizador_escavacao += delta_tempo
        
        duracao = getattr(self, '_duracao_atual', self._duracao_escavacao)
        if self._temporizador_escavacao < duracao:
            return (False, False, None, 0)
        
        coluna, linha = self._alvo_escavacao
        azulejo = self.obter_azulejo_grade(coluna, linha)

        if azulejo and azulejo.item == 'pa' and tem_pa:
             self._escavando = False
             self._alvo_escavacao = (None, None)
             self._temporizador_escavacao = 0.0
             return (True, False, 'pa_duplicada', 0)
        
        dado = random.randint(0, 20)
        sucesso_escavacao = (dado + bonus_dado) > 12
        
        adicionado = False
        if sucesso_escavacao:
            adicionado = self.adicionar_sobreposicao_em(coluna, linha)
            
        self._escavando = False
        self._alvo_escavacao = (None, None)
        self._temporizador_escavacao = 0.0
        item_encontrado = None
        
        if adicionado and azulejo:
            item_encontrado = azulejo.item
            
        return (True, bool(adicionado), item_encontrado, dado)

    def esta_escavando(self):
        return self._escavando

    def progresso_escavacao(self):
        if not self._escavando:
            return 0.0
        duracao = getattr(self, '_duracao_atual', self._duracao_escavacao)
        return min(1.0, self._temporizador_escavacao / max(1e-6, duracao))
