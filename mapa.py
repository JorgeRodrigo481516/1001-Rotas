"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia a construção do cenário, renderização dos tiles (quadriculos) 
    e mecânicas de interação com o terreno (escavação e investigação).

RESPONSABILIDADE:
    1. Geração: Criar o grid de quadriculos e distribuir itens (água, pá, faca) aleatoriamente.
    2. Suporte Multi-Ambiente: Construir mapas DESERTO (6 variações simples) e CAVERNA 
       (variações especiais: parede, buraco, runa, inimigo).
    3. Renderização: Desenhar o cenário e sobreposições (overlays) visuais.
    4. Escavação: Controlar a lógica, temporização e sucesso da busca por itens.
    5. Investigação: Executar a mecânica de radar, calculando probabilidades e 
       gerando mensagens de feedback sobre itens próximos.
    6. Persistência: Permitir resetar o estado visual (escavações) mantendo a 
       distribuição de itens para mecânicas de "conhecimento acumulado" nos reinicios.
    7. Passagens: Gerenciar tiles de passagem que conectam Deserto ↔ Caverna bidirecionalmente.
    8. Detecção de Tiles Especiais: Fornecer métodos para verificar tipo de quadrículo (buraco, runa, parede).

REGRAS DE USO:
    - 'construir()' deve ser chamado uma única vez após a inicialização.
    - 'atualizar_escavacao()' e 'atualizar_investigacao()' devem ser chamados a cada frame.
    - 'desenhar()' deve ser chamado no loop de renderização para exibir o mapa.
    - 'resetar_estado()' deve ser chamado ao reiniciar o jogo para limpar o mapa sem perder a geração.

NOTAS DE IMPLEMENTAÇÃO:
    - Usa sistema de grid (coluna, linha) mapeado para pixels.
    - A investigação implementa um sistema de "alucinação" onde falhas no teste de 
      probabilidade podem gerar informações falsas.
    - Construção de CAVERNA: posiciona runas, reserva espaço ao redor de passagens, distribui paredes/buracos.
    - Métodos eh_buraco(), eh_runa(), verificar_colisao_parede() são usados por MecanicasCaverna.
-------------------------------------------------------------------
"""
from PPlay.sprite import Sprite
import config
import random


class Quadriculo:
    def __init__(self, imagem_quadriculo, indice_coluna, indice_linha, indice_variacao_terreno=1):
        self.imagem_quadriculo = imagem_quadriculo
        self.indice_coluna = indice_coluna
        self.indice_linha = indice_linha
        self.indice_variacao_terreno = indice_variacao_terreno
        self.imagem_sobreposicao = None
        self.imagem_foco = None
        self.item = None
        self.eh_passagem = False

    def desenhar(self):
        self.imagem_quadriculo.draw()
        if self.imagem_sobreposicao:
            self.imagem_sobreposicao.draw()
        if self.imagem_foco:
            self.imagem_foco.draw()

    def tem_sobreposicao(self):
        return self.imagem_sobreposicao is not None

    def definir_foco(self, ativo=True):
        if ativo:
            if self.imagem_foco is None:
                self.imagem_foco = Sprite(config.RECURSOS['foco'])
                self.imagem_foco.x = self.imagem_quadriculo.x + (self.imagem_quadriculo.width - self.imagem_foco.width) / 2
                self.imagem_foco.y = self.imagem_quadriculo.y + (self.imagem_quadriculo.height - self.imagem_foco.height) / 2
        else:
            self.imagem_foco = None

    def adicionar_sobreposicao(self, caminho_imagem=None):
        if self.tem_sobreposicao():
            return False
        if caminho_imagem is None:
            caminho_imagem = config.RECURSOS['sobreposicao_padrao']
        imagem_sobreposicao = Sprite(caminho_imagem)
        imagem_sobreposicao.x = self.imagem_quadriculo.x + (self.imagem_quadriculo.width - imagem_sobreposicao.width) / 2
        imagem_sobreposicao.y = self.imagem_quadriculo.y + (self.imagem_quadriculo.height - imagem_sobreposicao.height) / 2
        self.imagem_sobreposicao = imagem_sobreposicao
        return True

class Mapa:
    def __init__(self, janela, largura_quadriculo=None, altura_quadriculo=None):
        self.janela = janela
        self.largura_quadriculo = largura_quadriculo
        self.altura_quadriculo = altura_quadriculo
        self.lista_quadriculos = []
        self.dicionario_quadriculos_por_coordenada = {}
        self._escavando = False
        self._alvo_escavacao = (None, None)
        self._temporizador_escavacao = 0.0
        self._duracao_escavacao = config.JOGABILIDADE['duracao_escavacao']
        
        self._investigando = False
        self._fila_mensagens = []
        self._tempo_investigacao = 0.0
        self._duracao_total_investigacao = 0.0
        
        self.posicao_runa_final = None
        self.quadriculo_focado = None
        self.posicoes_pergaminhos = []

    def remover_foco(self):
        if self.quadriculo_focado:
            self.quadriculo_focado.definir_foco(False)
            self.quadriculo_focado = None

    def atualizar_foco(self, coluna, linha):
        if self.quadriculo_focado and \
           self.quadriculo_focado.indice_coluna == coluna and \
           self.quadriculo_focado.indice_linha == linha:
            return

        if self.quadriculo_focado:
            self.quadriculo_focado.definir_foco(False)
            self.quadriculo_focado = None

        if (coluna, linha) in self.dicionario_quadriculos_por_coordenada:
            novo_foco = self.dicionario_quadriculos_por_coordenada[(coluna, linha)]
            novo_foco.definir_foco(True)
            self.quadriculo_focado = novo_foco
            # ---------------------------------------------------------------
            item = novo_foco.item if novo_foco.item else 'Nenhum'
            passagem = 'Sim' if novo_foco.eh_passagem else 'Não'
            print(f"Foco ativado em: coluna {coluna}, linha {linha}, item: {item}, passagem: {passagem}")
            # ---------------------------------------------------------------

    def construir(self, tipo='DESERTO', posicao_passagem_anterior=None):
        self.tipo = tipo
        caminho_base, multiplicador_itens = self._preparar_recursos(tipo)
        
        self._inicializar_grade(caminho_base)
        
        linha_inicio_painel = config.INTERFACE_USUARIO['altura_painel_em_quadriculos']
        num_linhas = int(self.janela.height / self.altura_quadriculo) + 1
        num_colunas = int(self.janela.width / self.largura_quadriculo) + 1
        
        padrao_arquivo = self._obter_padrao_arquivo(caminho_base)
        usa_marcador = '{}' in padrao_arquivo

        if tipo == 'DESERTO':
            self._gerar_quadriculos_deserto(linha_inicio_painel, num_linhas, num_colunas, padrao_arquivo, usa_marcador, caminho_base)
            self._definir_passagem_secreta(linha_inicio_painel, num_linhas, num_colunas)
        elif tipo == 'CAVERNA':
            self._gerar_quadriculos_caverna(linha_inicio_painel, num_linhas, num_colunas, padrao_arquivo, usa_marcador, caminho_base, posicao_passagem_anterior)

        self._distribuir_itens(multiplicador_itens)

    def _preparar_recursos(self, tipo):
        if tipo == 'CAVERNA':
            return config.RECURSOS.get('padrao_base_quadriculo_caverna'), config.JOGABILIDADE['multiplicador_itens_caverna']
        return config.RECURSOS.get('padrao_base_quadriculo'), 1.0

    def _inicializar_grade(self, caminho_base):
        if caminho_base is None:
            raise RuntimeError(f'padrao_base_quadriculo not set for {self.tipo}')

        exemplo = Sprite(caminho_base)
        self.largura_quadriculo = exemplo.width
        self.altura_quadriculo = exemplo.height
        self.lista_quadriculos = []
        self.dicionario_quadriculos_por_coordenada = {}

    def _obter_padrao_arquivo(self, caminho_base):
        if '{}' in caminho_base: return caminho_base
        
        indice = caminho_base.rfind('.')
        nome_base = caminho_base[:indice]
        extensao = caminho_base[indice:]
        
        if nome_base.endswith('1'):
            return f"{nome_base[:-1]}{{}}{extensao}"
        return f"{nome_base}{{}}{extensao}"

    def _distribuir_itens(self, multiplicador_itens):
        total_quadriculos = len(self.lista_quadriculos)
        quantidade_agua = int(total_quadriculos * config.JOGABILIDADE['distribuicao_itens']['agua'] * multiplicador_itens)
        quantidade_pa = int(total_quadriculos * config.JOGABILIDADE['distribuicao_itens']['pa'] * multiplicador_itens)
        quantidade_faca = int(total_quadriculos * config.JOGABILIDADE['distribuicao_itens']['faca'] * multiplicador_itens)

        lista_itens = ['agua'] * quantidade_agua + ['pa'] * quantidade_pa + ['faca'] * quantidade_faca

        quadriculos_elegiveis = [q for q in self.lista_quadriculos if q.indice_variacao_terreno in (1, 2)] if self.tipo == 'CAVERNA' else list(self.lista_quadriculos)
        random.shuffle(quadriculos_elegiveis)

        self.posicoes_pergaminhos = []
        if self.tipo == 'DESERTO':
            num_perg = config.JOGABILIDADE.get('quantidade_pergaminhos', 0)
            if num_perg > 0:
                min_col = min(q.indice_coluna for q in self.lista_quadriculos)
                max_col = max(q.indice_coluna for q in self.lista_quadriculos)
                min_lin = min(q.indice_linha for q in self.lista_quadriculos)
                max_lin = max(q.indice_linha for q in self.lista_quadriculos)

                candidato_pergs = [q for q in quadriculos_elegiveis
                                   if (q.indice_coluna >= (min_col + 2) and q.indice_coluna <= (max_col - 2)
                                       and q.indice_linha >= (min_lin + 2) and q.indice_linha <= (max_lin - 2))]

                if len(candidato_pergs) < num_perg:
                    random.shuffle(quadriculos_elegiveis)
                    candidato_pergs = [q for q in quadriculos_elegiveis if q not in candidato_pergs]
                    candidato_pergs = list({q: None for q in (candidato_pergs + quadriculos_elegiveis)}.keys())

                random.shuffle(candidato_pergs)
                selecionados = candidato_pergs[:num_perg]
                for q in selecionados:
                    q.item = 'pergaminho'
                    self.posicoes_pergaminhos.append((q.indice_coluna, q.indice_linha))


        quadriculos_vazios = [q for q in quadriculos_elegiveis if q.item is None]
        random.shuffle(quadriculos_vazios)

        for i, item in enumerate(lista_itens):
            if i < len(quadriculos_vazios):
                quadriculos_vazios[i].item = item
            else:
                break

        if self.posicoes_pergaminhos:
            print(f"DICA: Pergaminho 1 está em {self.posicoes_pergaminhos[0]}")

    def _definir_passagem_secreta(self, linha_inicio, num_linhas, num_colunas):
        if not self.lista_quadriculos: return
        
        candidatos = [
            q for q in self.lista_quadriculos 
            if 0 < q.indice_coluna < num_colunas - 1 and linha_inicio < q.indice_linha < num_linhas - 1
        ]
        
        quadriculo_passagem = random.choice(candidatos) if candidatos else random.choice(self.lista_quadriculos)
        quadriculo_passagem.eh_passagem = True

    def _gerar_quadriculos_deserto(self, linha_inicio, num_linhas, num_colunas, padrao_arquivo, usa_marcador, caminho_base):
        for linha in range(linha_inicio, num_linhas):
            for coluna in range(num_colunas):
                indice_variacao = random.randint(1, 6)
                caminho_quadriculo = padrao_arquivo.format(indice_variacao) if usa_marcador else caminho_base
                self._criar_quadriculo_e_adicionar(coluna, linha, caminho_quadriculo, variacao=indice_variacao)

    def _gerar_quadriculos_caverna(self, linha_inicio, num_linhas, num_colunas, padrao_arquivo, usa_marcador, caminho_base, posicao_passagem):
        coordenadas_livres = [(c, l) for l in range(linha_inicio, num_linhas) for c in range(num_colunas)]
        mapa_variacoes = {} 

        self._reservar_espaco_passagem(posicao_passagem, coordenadas_livres, mapa_variacoes)
        self._posicionar_runas(linha_inicio, num_linhas, num_colunas, coordenadas_livres, mapa_variacoes)
        self._preencher_variacoes_terreno(coordenadas_livres, mapa_variacoes, len(self.lista_quadriculos) + len(coordenadas_livres))

        for linha in range(linha_inicio, num_linhas):
            for coluna in range(num_colunas):
                indice = mapa_variacoes.get((coluna, linha), 1)
                caminho_quadriculo = padrao_arquivo.format(indice) if usa_marcador else caminho_base
                quadriculo = self._criar_quadriculo_e_adicionar(coluna, linha, caminho_quadriculo, variacao=indice)
                
                if (coluna, linha) == posicao_passagem:
                    quadriculo.eh_passagem = True
                    quadriculo.adicionar_sobreposicao(config.RECURSOS['passagem'])

    def _reservar_espaco_passagem(self, posicao_passagem, coordenadas_livres, mapa_variacoes):
        if not posicao_passagem: return
        
        if posicao_passagem in coordenadas_livres:
            coordenadas_livres.remove(posicao_passagem)
            mapa_variacoes[posicao_passagem] = 1
        
        posicao_x, posicao_y = posicao_passagem
        for deslocamento_x, deslocamento_y in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
            vizinho = (posicao_x + deslocamento_x, posicao_y + deslocamento_y)
            if vizinho in coordenadas_livres:
                coordenadas_livres.remove(vizinho)
                mapa_variacoes[vizinho] = 1

    def _posicionar_runas(self, linha_inicio, num_linhas, num_colunas, coordenadas_livres, mapa_variacoes):
        candidatos = [
            c for c in coordenadas_livres 
            if 0 < c[0] < num_colunas - 1 and linha_inicio < c[1] < num_linhas - 1
        ]
        random.shuffle(candidatos)
        
        posicoes_runas = []
        for _ in range(min(config.JOGABILIDADE['quantidade_runas_caverna'], len(candidatos))):
            coord = candidatos.pop()
            if coord in coordenadas_livres:
                coordenadas_livres.remove(coord)
                mapa_variacoes[coord] = config.TIPO_TERRENO_RUNA
                posicoes_runas.append(coord)
        
        self.posicao_runa_final = random.choice(posicoes_runas) if posicoes_runas else None

    def _preencher_variacoes_terreno(self, coordenadas_livres, mapa_variacoes, total_quadriculos):
        random.shuffle(coordenadas_livres)
        
        quantidade_variacao_2 = int(total_quadriculos * config.JOGABILIDADE['percentual_variacao_2_caverna'])
        coordenadas_variacao_2 = []
        for _ in range(min(quantidade_variacao_2, len(coordenadas_livres))):
            coord = coordenadas_livres.pop()
            mapa_variacoes[coord] = 2
            coordenadas_variacao_2.append(coord)
            
        quantidade_variacao_3 = int(total_quadriculos * config.JOGABILIDADE['percentual_variacao_3_caverna'])
        conjunto_variacao_2 = set(coordenadas_variacao_2)
        candidatos_variacao_3 = [
            c for c in coordenadas_livres 
            if any((c[0]+deslocamento_x, c[1]+deslocamento_y) in conjunto_variacao_2 for deslocamento_x, deslocamento_y in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)])
        ]
        random.shuffle(candidatos_variacao_3)
        
        contagem = 0
        while contagem < quantidade_variacao_3 and (candidatos_variacao_3 or coordenadas_livres):
            coord = candidatos_variacao_3.pop() if candidatos_variacao_3 else coordenadas_livres.pop()
            if coord in coordenadas_livres: coordenadas_livres.remove(coord) 
            mapa_variacoes[coord] = config.TIPO_TERRENO_PAREDE
            contagem += 1

        quantidade_variacao_4 = int(total_quadriculos * config.JOGABILIDADE['percentual_variacao_4_caverna'])
        for _ in range(min(quantidade_variacao_4, len(coordenadas_livres))):
            mapa_variacoes[coordenadas_livres.pop()] = config.TIPO_TERRENO_BURACO

        while coordenadas_livres:
            mapa_variacoes[coordenadas_livres.pop()] = 1

    def _criar_quadriculo_e_adicionar(self, coluna, linha, caminho_arquivo_imagem, variacao=1):
        imagem_quadriculo = Sprite(caminho_arquivo_imagem)
        imagem_quadriculo.x = coluna * self.largura_quadriculo
        imagem_quadriculo.y = linha * self.altura_quadriculo

        novo_quadriculo = Quadriculo(imagem_quadriculo, coluna, linha, indice_variacao_terreno=variacao)
        self.lista_quadriculos.append(novo_quadriculo)
        self.dicionario_quadriculos_por_coordenada[(coluna, linha)] = novo_quadriculo
        return novo_quadriculo

    def obter_posicao_passagem(self):
        for quadriculo in self.lista_quadriculos:
            if getattr(quadriculo, 'eh_passagem', False):
                return (quadriculo.indice_coluna, quadriculo.indice_linha)
        return None


    def obter_quadriculo_por_coordenada_grade(self, coluna, linha):
        return self.dicionario_quadriculos_por_coordenada.get((coluna, linha))

    def obter_quadriculo_na_posicao_pixel(self, posicao_x, posicao_y):
        return self.obter_quadriculo_por_coordenada_grade(int(posicao_x / self.largura_quadriculo), int(posicao_y / self.altura_quadriculo))

    def marcar_quadriculo_escavado_em(self, coluna, linha, caminho_arquivo_imagem=None):
        quadriculo = self.obter_quadriculo_por_coordenada_grade(coluna, linha)
        if quadriculo:
            return quadriculo.adicionar_sobreposicao(caminho_arquivo_imagem)
        return False

    def iniciar_escavacao(self, coluna, linha, tem_pa=False):
        if self._escavando:
            return False
        quadriculo = self.obter_quadriculo_por_coordenada_grade(coluna, linha)
        if quadriculo is None:
            return False
        if quadriculo.tem_sobreposicao():
            return False
        self._escavando = True
        self._alvo_escavacao = (coluna, linha)
        self._temporizador_escavacao = 0.0
        self._duracao_atual = self._duracao_escavacao / 2.0 if tem_pa else self._duracao_escavacao
        return True

    def atualizar_escavacao(self, tempo_decorrido, tem_pa=False, tem_faca=False):
        if not self._escavando:
            return False, False, None, 0
        
        self._temporizador_escavacao += tempo_decorrido
        duracao = getattr(self, '_duracao_atual', self._duracao_escavacao)
        
        if self._temporizador_escavacao < duracao:
            return False, False, None, 0
        
        coluna, linha = self._alvo_escavacao
        quadriculo = self.obter_quadriculo_por_coordenada_grade(coluna, linha)
        
        concluido = True
        sucesso = False
        item = None
        dado = 0

        self._escavando = False
        self._alvo_escavacao = (None, None)
        self._temporizador_escavacao = 0.0

        if quadriculo:
            if (quadriculo.item == 'pa' and tem_pa) or (quadriculo.item == 'faca' and tem_faca):
                item = f"{quadriculo.item}_duplicada"
                # ---------------------------------------------------------------
                print(f"Ja tem {quadriculo.item} no inventario")
                # ---------------------------------------------------------------S
                return concluido, sucesso, item, dado

        bonus_dado = config.JOGABILIDADE['bonus_escavacao_pa'] if tem_pa else 0
        dado_bruto = random.randint(0, config.JOGABILIDADE['dado_escavacao'])
        dado = dado_bruto
        
        if (dado_bruto + bonus_dado) > config.JOGABILIDADE['dificuldade_escavacao']:
            sucesso = True
            caminho_imagem = config.RECURSOS['passagem'] if quadriculo and quadriculo.eh_passagem else None
            adicionado = self.marcar_quadriculo_escavado_em(coluna, linha, caminho_imagem)

            if adicionado and quadriculo:
                # ---------------------------------------------------------------
                item = quadriculo.item
                item_display = item.upper() if item else "nada"
                print(f"Escavacao conseguiu! Dado: {dado_bruto}+{bonus_dado} vs {config.JOGABILIDADE['dificuldade_escavacao']}")
                print(f"Encontrou: {item_display}")

                if item == 'pergaminho':
                    try:
                        indice = self.posicoes_pergaminhos.index((coluna, linha))
                    except ValueError:
                        indice = None
                    self._imprimir_dica_proximo_pergaminho(coluna, linha)
                    item = ('pergaminho', indice)
                # ---------------------------------------------------------------
                
        return concluido, sucesso, item, dado

    def _imprimir_dica_proximo_pergaminho(self, coluna, linha):
        try:
            indice_atual = self.posicoes_pergaminhos.index((coluna, linha))
            proximo_indice = (indice_atual + 1) % len(self.posicoes_pergaminhos)
            proxima_posicao = self.posicoes_pergaminhos[proximo_indice]
            print(f"DICA: O próximo pergaminho está em {proxima_posicao}")
        except ValueError:
            pass

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
        # ---------------------------------------------------------------
        print(f"Investigando em ({coluna_centro}, {linha_centro})")
        # ---------------------------------------------------------------
        
        ordem_leitura = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0), (0, 0), (1, 0),
            (-1, 1), (0, 1), (1, 1)
        ]

        tempo_acumulado = config.JOGABILIDADE['atraso_inicial_investigacao']
        
        for variacao_x, variacao_y in ordem_leitura:
            nome_posicao = config.MENSAGENS['investigacao_direcoes'].get((variacao_x, variacao_y), "")
            
            if variacao_x == 0 and variacao_y == 0:
                dificuldade = config.JOGABILIDADE['dificuldade_investigacao_centro']
            elif variacao_x == 0 or variacao_y == 0:
                dificuldade = config.JOGABILIDADE['dificuldade_investigacao_ortogonal']
            else:
                dificuldade = config.JOGABILIDADE['dificuldade_investigacao_diagonal']

            coluna = coluna_centro + variacao_x
            linha = linha_centro + variacao_y
            
            mensagem = self._processar_celula_investigacao(coluna, linha, nome_posicao, dificuldade)
            
            inicio = tempo_acumulado
            fim = tempo_acumulado + config.JOGABILIDADE['tempo_mensagem_investigacao']
            self._fila_mensagens.append((inicio, fim, mensagem))
            
            tempo_acumulado = fim + config.JOGABILIDADE['intervalo_entre_mensagens']

        tempo_acumulado -= config.JOGABILIDADE['intervalo_entre_mensagens']
        tempo_acumulado += config.JOGABILIDADE['atraso_final_investigacao']
        
        self._duracao_total_investigacao = tempo_acumulado
        return True

    def _processar_celula_investigacao(self, coluna, linha, nome_posicao, dificuldade):
        quadriculo = self.obter_quadriculo_por_coordenada_grade(coluna, linha)
        item_real = quadriculo.item if quadriculo else None
        
        dado = random.randint(1, 20)
        sucesso = dado > dificuldade
        
        item_mostrado = item_real
        if not sucesso:
            itens_possiveis_investigacao = ['agua', 'pa', 'faca', None]
            itens_falsos_investigacao = [i for i in itens_possiveis_investigacao if i != item_real]
            if not itens_falsos_investigacao:
                itens_falsos_investigacao = [None]
            item_mostrado = random.choice(itens_falsos_investigacao)
        
        nome_item = item_mostrado if item_mostrado else config.MENSAGENS['investigacao_nada']
        nome_item = nome_item.capitalize()
        
        chance = int(((21 - dificuldade) / 20) * 100)
        
        return config.MENSAGENS['investigacao_template'].format(
            posicao=nome_posicao,
            item=nome_item,
            chance=chance
        )

    def atualizar_investigacao(self, tempo_decorrido):
        if not self._investigando:
            return False, ""

        self._tempo_investigacao += tempo_decorrido
        
        if self._tempo_investigacao >= self._duracao_total_investigacao:
            self._investigando = False
            return False, ""
            
        mensagem_atual = ""
        for inicio, fim, mensagem in self._fila_mensagens:
            if inicio <= self._tempo_investigacao < fim:
                mensagem_atual = mensagem
                break
        
        return True, mensagem_atual

    def esta_investigando(self):
        return self._investigando

    def obter_mensagem_investigacao_atual(self):
        if not self._investigando:
            return ""
        for inicio, fim, mensagem in self._fila_mensagens:
            if inicio <= self._tempo_investigacao < fim:
                return mensagem
        return ""

    def progresso_investigacao(self):
        if not self._investigando:
            return 0.0
        return min(1.0, self._tempo_investigacao / max(1e-6, self._duracao_total_investigacao))

    def desenhar(self):
        for quadriculo in self.lista_quadriculos:
            quadriculo.desenhar()

    def resetar_estado(self):
        for quadriculo in self.lista_quadriculos:
            quadriculo.imagem_sobreposicao = None
        
        self._escavando = False
        self._alvo_escavacao = (None, None)
        self._temporizador_escavacao = 0.0
        
        self._investigando = False
        self._fila_mensagens = []
        self._tempo_investigacao = 0.0

    def verificar_colisao_parede(self, x, y):
        if self.tipo != 'CAVERNA':
            return False
        quadriculo = self.obter_quadriculo_na_posicao_pixel(x, y)
        if quadriculo and getattr(quadriculo, 'indice_variacao_terreno', 1) == config.TIPO_TERRENO_PAREDE:
            return True
        return False

    def eh_buraco(self, coluna, linha):
        if self.tipo != 'CAVERNA':
            return False
        quadriculo = self.obter_quadriculo_por_coordenada_grade(coluna, linha)
        return quadriculo and getattr(quadriculo, 'indice_variacao_terreno', 1) == config.TIPO_TERRENO_BURACO

    def eh_runa(self, coluna, linha):
        if self.tipo != 'CAVERNA':
            return False
        quadriculo = self.obter_quadriculo_por_coordenada_grade(coluna, linha)
        return quadriculo and getattr(quadriculo, 'indice_variacao_terreno', 1) == config.TIPO_TERRENO_RUNA
