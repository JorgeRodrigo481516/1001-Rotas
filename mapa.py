"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia a construção do cenário, renderização dos tiles (azulejos) 
    e mecânicas de interação com o terreno (escavação e investigação).

RESPONSABILIDADE:
    1. Geração: Criar o grid de azulejos e distribuir itens (água, pá, faca) aleatoriamente.
    2. Renderização: Desenhar o cenário e sobreposições (overlays) visuais.
    3. Escavação: Controlar a lógica, temporização e sucesso da busca por itens.
    4. Investigação: Executar a mecânica de radar, calculando probabilidades e 
       gerando mensagens de feedback sobre itens próximos.

REGRAS DE USO:
    - 'construir()' deve ser chamado uma única vez após a inicialização.
    - 'atualizar_escavacao()' e 'atualizar_investigacao()' devem ser chamados a cada frame.
    - 'desenhar()' deve ser chamado no loop de renderização para exibir o mapa.

NOTAS DE IMPLEMENTAÇÃO:
    - Usa sistema de grid (coluna, linha) mapeado para pixels.
    - A investigação implementa um sistema de "alucinação" onde falhas no teste de 
      probabilidade podem gerar informações falsas.
-------------------------------------------------------------------
"""
from PPlay.sprite import Sprite
import config
import random


class Azulejo:
    def __init__(self, imagem_azulejo, coluna, linha):
        self.imagem_azulejo = imagem_azulejo
        self.coluna = coluna
        self.linha = linha
        self.sprite_sobreposicao = None
        self.item = None

    def desenhar(self):
        self.imagem_azulejo.draw()
        if self.sprite_sobreposicao:
            self.sprite_sobreposicao.draw()

    def tem_sobreposicao(self):
        return self.sprite_sobreposicao is not None

    def adicionar_sobreposicao(self, caminho_imagem=None):
        if self.tem_sobreposicao():
            return False
        if caminho_imagem is None:
            caminho_imagem = config.RECURSOS['sobreposicao_padrao']
        sprite_sobreposicao = Sprite(caminho_imagem)
        sprite_sobreposicao.x = self.imagem_azulejo.x + (self.imagem_azulejo.width - sprite_sobreposicao.width) / 2
        sprite_sobreposicao.y = self.imagem_azulejo.y + (self.imagem_azulejo.height - sprite_sobreposicao.height) / 2
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
        self._duracao_escavacao = config.JOGABILIDADE['duracao_escavacao']
        
        self._investigando = False
        self._fila_mensagens = []
        self._tempo_investigacao = 0.0
        self._duracao_total_investigacao = 0.0

    def construir(self):
        caminho_base = config.RECURSOS.get('padrao_base_azulejo')
        if caminho_base is None:
            raise RuntimeError('config.RECURSOS["padrao_base_azulejo"] must be set')

        exemplo = Sprite(caminho_base)
        self.largura_tile = exemplo.width
        self.altura_tile = exemplo.height

        config.LARGURA_TILE = self.largura_tile
        config.ALTURA_TILE = self.altura_tile

        numero_colunas = int(self.janela.width / self.largura_tile) + 1
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
            for coluna in range(numero_colunas):
                indice_variacao = random.randint(1, 6)
                caminho_azulejo = padrao_arquivo.format(indice_variacao) if usa_placeholder else caminho_base

                sprite_azulejo = Sprite(caminho_azulejo)
                sprite_azulejo.x = coluna * self.largura_tile
                sprite_azulejo.y = linha * self.altura_tile

                novo_azulejo = Azulejo(sprite_azulejo, coluna, linha)
                self.azulejos.append(novo_azulejo)
                self.azulejos_por_coordenada[(coluna, linha)] = novo_azulejo

        total_azulejos = len(self.azulejos)
        qtd_agua = int(total_azulejos * config.JOGABILIDADE['distribuicao_itens']['agua'])
        qtd_pa = int(total_azulejos * config.JOGABILIDADE['distribuicao_itens']['pa'])
        qtd_faca = int(total_azulejos * config.JOGABILIDADE['distribuicao_itens']['faca'])
        
        itens = ['agua'] * qtd_agua + ['pa'] * qtd_pa + ['faca'] * qtd_faca + [None] * (total_azulejos - qtd_agua - qtd_pa - qtd_faca)
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

    def atualizar_escavacao(self, delta_tempo, tem_pa=False, tem_faca=False):
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

        if azulejo and azulejo.item == 'faca' and tem_faca:
             self._escavando = False
             self._alvo_escavacao = (None, None)
             self._temporizador_escavacao = 0.0
             return (True, False, 'faca_duplicada', 0)
        
        bonus_dado = config.JOGABILIDADE['bonus_escavacao_pa'] if tem_pa else 0
        dado = random.randint(0, config.JOGABILIDADE['dado_escavacao'])
        sucesso_escavacao = (dado + bonus_dado) > config.JOGABILIDADE['dificuldade_escavacao']
        
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

    def iniciar_investigacao(self, coluna_centro, linha_centro):
        if self._escavando or self._investigando:
            return False
        
        self._investigando = True
        self._tempo_investigacao = 0.0
        self._fila_mensagens = []
        
        grid_info = [
            (-1, -1, "Superior Esquerda", config.DIFICULDADE_INVESTIGACAO_DIAGONAL),
            (0, -1, "Superior Centro", config.DIFICULDADE_INVESTIGACAO_ORTOGONAL),
            (1, -1, "Superior Direita", config.DIFICULDADE_INVESTIGACAO_DIAGONAL),
            (-1, 0, "Meio Esquerda", config.DIFICULDADE_INVESTIGACAO_ORTOGONAL),
            (0, 0, "Centro", config.DIFICULDADE_INVESTIGACAO_CENTRO),
            (1, 0, "Meio Direita", config.DIFICULDADE_INVESTIGACAO_ORTOGONAL),
            (-1, 1, "Inferior Esquerda", config.DIFICULDADE_INVESTIGACAO_DIAGONAL),
            (0, 1, "Inferior Centro", config.DIFICULDADE_INVESTIGACAO_ORTOGONAL),
            (1, 1, "Inferior Direita", config.DIFICULDADE_INVESTIGACAO_DIAGONAL),
        ]

        tempo_acumulado = config.DELAY_INICIAL_INVESTIGACAO
        
        for dx, dy, nome_pos, dificuldade in grid_info:
            col = coluna_centro + dx
            lin = linha_centro + dy
            
            mensagem = self._processar_celula_investigacao(col, lin, nome_pos, dificuldade)
            
            inicio = tempo_acumulado
            fim = tempo_acumulado + config.TEMPO_MENSAGEM_INVESTIGACAO
            self._fila_mensagens.append((inicio, fim, mensagem))
            
            tempo_acumulado = fim + config.DELAY_ENTRE_MENSAGENS

        tempo_acumulado -= config.DELAY_ENTRE_MENSAGENS
        tempo_acumulado += config.DELAY_FINAL_INVESTIGACAO
        
        self._duracao_total_investigacao = tempo_acumulado
        return True

    def _processar_celula_investigacao(self, col, lin, nome_pos, dificuldade):
        azulejo = self.obter_azulejo_grade(col, lin)
        item_real = azulejo.item if azulejo else None
        
        dado = random.randint(1, 20)
        sucesso = dado > dificuldade
        
        item_mostrado = item_real
        if not sucesso:
            possiveis_itens = ['agua', 'pa', 'faca', None]
            opcoes_erradas = [i for i in possiveis_itens if i != item_real]
            if not opcoes_erradas:
                opcoes_erradas = [None]
            item_mostrado = random.choice(opcoes_erradas)
        
        nome_item = item_mostrado if item_mostrado else "Nada"
        nome_item = nome_item.capitalize()
        
        chance = int(((21 - dificuldade) / 20) * 100)
        
        return f"{nome_pos}: {nome_item} {chance}%"

    def atualizar_investigacao(self, delta_tempo):
        if not self._investigando:
            return False, ""

        self._tempo_investigacao += delta_tempo
        
        if self._tempo_investigacao >= self._duracao_total_investigacao:
            self._investigando = False
            return False, ""
            
        mensagem_atual = ""
        for inicio, fim, msg in self._fila_mensagens:
            if inicio <= self._tempo_investigacao < fim:
                mensagem_atual = msg
                break
        
        return True, mensagem_atual

    def esta_investigando(self):
        return self._investigando

    def obter_mensagem_investigacao_atual(self):
        if not self._investigando:
            return ""
        for inicio, fim, msg in self._fila_mensagens:
            if inicio <= self._tempo_investigacao < fim:
                return msg
        return ""

    def progresso_investigacao(self):
        if not self._investigando:
            return 0.0
        return min(1.0, self._tempo_investigacao / max(1e-6, self._duracao_total_investigacao))

    def desenhar(self):
        for azulejo in self.azulejos:
            azulejo.desenhar()
