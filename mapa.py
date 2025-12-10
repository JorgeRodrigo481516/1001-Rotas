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
    """
    DESCRIÇÃO:
        Representa um tile (quadriculo) do mapa, armazenando sua imagem, sobreposições e estado.

    RESPONSABILIDADE:
        - Desenhar seu próprio sprite e sobreposições.
        - Controlar foco visual e permitir marcação de sobreposições (ex.: escavação, passagem).

    REGRAS DE USO:
        - Criado pelo `Mapa` durante a construção da grade; não deveria ser instanciado diretamente em outro lugar.

    NOTAS DE IMPLEMENTAÇÃO:
        - Contém atributos simples: `imagem_quadriculo`, `imagem_sobreposicao`, `item` e flag `eh_passagem`.
    """
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
    """
    DESCRIÇÃO:
        Gerencia a estrutura de tiles do jogo (grade de `Quadriculo`), geração, escavação e investigação.

    RESPONSABILIDADE:
        - Construir mapas para ambientes (DESERTO, CAVERNA) e distribuir itens e runas.
        - Fornecer métodos para iniciar e atualizar escavação/investigação e desenhar o mapa.

    REGRAS DE USO:
        - Chamar `construir()` após instanciar para popular a grade.
        - Usar `atualizar_escavacao()` e `atualizar_investigacao()` durante o loop de jogo quando ações estiverem ativas.

    NOTAS DE IMPLEMENTAÇÃO:
        - A construção da caverna possui etapas de reserva de espaço e posicionamento de runas/passarens.
    """
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
            item = novo_foco.item if novo_foco.item else 'Nenhum'
            passagem = 'Sim' if novo_foco.eh_passagem else 'Não'
            print(f"Foco ativado em: coluna {coluna}, linha {linha}, item: {item}, passagem: {passagem}")

    def construir(self, tipo='DESERTO', posicao_passagem_anterior=None):
        """
        DESCRIÇÃO:
            Constrói a grade de quadriculos para o tipo de mapa especificado.

        RESPONSABILIDADE:
            - Preparar recursos, inicializar a grade e distribuir itens/runas conforme o tipo.

        REGRAS DE USO:
            - Deve ser chamado após instanciar `Mapa` e antes do uso do mesmo no jogo.

        NOTAS DE IMPLEMENTAÇÃO:
            - Para `CAVERNA`, pode receber `posicao_passagem_anterior` para alinhar passagens entre mapas.
        """
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

        quadriculos_elegiveis = [quadriculo for quadriculo in self.lista_quadriculos if quadriculo.indice_variacao_terreno in (1, 2)] if self.tipo == 'CAVERNA' else list(self.lista_quadriculos)
        random.shuffle(quadriculos_elegiveis)

        self.posicoes_pergaminhos = []
        if self.tipo == 'DESERTO':
            quantidade_pergaminhos = config.JOGABILIDADE.get('quantidade_pergaminhos', 0)
            if quantidade_pergaminhos > 0:
                min_col = min(quadriculo.indice_coluna for quadriculo in self.lista_quadriculos)
                max_col = max(quadriculo.indice_coluna for quadriculo in self.lista_quadriculos)
                min_lin = min(quadriculo.indice_linha for quadriculo in self.lista_quadriculos)
                max_lin = max(quadriculo.indice_linha for quadriculo in self.lista_quadriculos)

                candidatos_pergaminhos = [quadriculo for quadriculo in quadriculos_elegiveis
                                   if (quadriculo.indice_coluna >= (min_col + 2) and quadriculo.indice_coluna <= (max_col - 2)
                                       and quadriculo.indice_linha >= (min_lin + 2) and quadriculo.indice_linha <= (max_lin - 2))]

                if len(candidatos_pergaminhos) < quantidade_pergaminhos:
                    random.shuffle(quadriculos_elegiveis)
                    candidatos_pergaminhos = [quadriculo for quadriculo in quadriculos_elegiveis if quadriculo not in candidatos_pergaminhos]
                    candidatos_pergaminhos = list({quadriculo: None for quadriculo in (candidatos_pergaminhos + quadriculos_elegiveis)}.keys())

                random.shuffle(candidatos_pergaminhos)
                selecionados = candidatos_pergaminhos[:quantidade_pergaminhos]
                for quadriculo in selecionados:
                    quadriculo.item = 'pergaminho'
                    self.posicoes_pergaminhos.append((quadriculo.indice_coluna, quadriculo.indice_linha))


        quadriculos_vazios = [quadriculo for quadriculo in quadriculos_elegiveis if quadriculo.item is None]
        random.shuffle(quadriculos_vazios)
        for indice_item, item in enumerate(lista_itens):
            if indice_item < len(quadriculos_vazios):
                quadriculos_vazios[indice_item].item = item
            else:
                break

        if self.posicoes_pergaminhos:
            print(f"DICA: Pergaminho 1 está em {self.posicoes_pergaminhos[0]}")

    def _definir_passagem_secreta(self, linha_inicio, num_linhas, num_colunas):
        if not self.lista_quadriculos: return
        
        candidatos = [
            quadriculo for quadriculo in self.lista_quadriculos 
            if 0 < quadriculo.indice_coluna < num_colunas - 1 and linha_inicio < quadriculo.indice_linha < num_linhas - 1
        ]
        
        quadriculo_passagem = random.choice(candidatos) if candidatos else random.choice(self.lista_quadriculos)
        quadriculo_passagem.eh_passagem = True

    def _gerar_quadriculos_deserto(self, linha_inicio, num_linhas, num_colunas, padrao_arquivo, usa_marcador, caminho_base):
        for linha in range(linha_inicio, num_linhas):
            for coluna in range(num_colunas):
                indice_variacao = random.randint(1, 6)
                caminho_quadriculo = padrao_arquivo.format(indice_variacao) if usa_marcador else caminho_base
                self._criar_e_adicionar_quadriculo(coluna, linha, caminho_quadriculo, variacao=indice_variacao)

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
                quadriculo = self._criar_e_adicionar_quadriculo(coluna, linha, caminho_quadriculo, variacao=indice)
                
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
            coordenada for coordenada in coordenadas_livres 
            if 0 < coordenada[0] < num_colunas - 1 and linha_inicio < coordenada[1] < num_linhas - 1
        ]
        random.shuffle(candidatos)
        
        posicoes_runas = []
        for _ in range(min(config.JOGABILIDADE['quantidade_runas_caverna'], len(candidatos))):
            coordenada = candidatos.pop()
            if coordenada in coordenadas_livres:
                coordenadas_livres.remove(coordenada)
                mapa_variacoes[coordenada] = config.TIPO_TERRENO_RUNA
                posicoes_runas.append(coordenada)
        
        self.posicao_runa_final = random.choice(posicoes_runas) if posicoes_runas else None

    def _preencher_variacoes_terreno(self, coordenadas_livres, mapa_variacoes, total_quadriculos):
        random.shuffle(coordenadas_livres)
        
        quantidade_variacao_2 = int(total_quadriculos * config.JOGABILIDADE['percentual_variacao_2_caverna'])
        coordenadas_variacao_2 = []
        for _ in range(min(quantidade_variacao_2, len(coordenadas_livres))):
            coordenada = coordenadas_livres.pop()
            mapa_variacoes[coordenada] = 2
            coordenadas_variacao_2.append(coordenada)
            
        quantidade_variacao_3 = int(total_quadriculos * config.JOGABILIDADE['percentual_variacao_3_caverna'])
        conjunto_variacao_2 = set(coordenadas_variacao_2)
        candidatos_variacao_3 = [
            coordenada for coordenada in coordenadas_livres 
            if any((coordenada[0]+deslocamento_x, coordenada[1]+deslocamento_y) in conjunto_variacao_2 for deslocamento_x, deslocamento_y in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)])
        ]
        random.shuffle(candidatos_variacao_3)
        
        contagem = 0
        while contagem < quantidade_variacao_3 and (candidatos_variacao_3 or coordenadas_livres):
            coordenada = candidatos_variacao_3.pop() if candidatos_variacao_3 else coordenadas_livres.pop()
            if coordenada in coordenadas_livres: coordenadas_livres.remove(coordenada) 
            mapa_variacoes[coordenada] = config.TIPO_TERRENO_PAREDE
            contagem += 1

        quantidade_variacao_4 = int(total_quadriculos * config.JOGABILIDADE['percentual_variacao_4_caverna'])
        for _ in range(min(quantidade_variacao_4, len(coordenadas_livres))):
            mapa_variacoes[coordenadas_livres.pop()] = config.TIPO_TERRENO_BURACO

        while coordenadas_livres:
            mapa_variacoes[coordenadas_livres.pop()] = 1

    def _criar_e_adicionar_quadriculo(self, coluna, linha, caminho_arquivo_imagem, variacao=1):
        imagem_quadriculo = Sprite(caminho_arquivo_imagem)
        imagem_quadriculo.x = coluna * self.largura_quadriculo
        imagem_quadriculo.y = linha * self.altura_quadriculo
        novo_quadriculo = Quadriculo(imagem_quadriculo, coluna, linha, indice_variacao_terreno=variacao)
        self.lista_quadriculos.append(novo_quadriculo)
        self.dicionario_quadriculos_por_coordenada[(coluna, linha)] = novo_quadriculo
        return novo_quadriculo

    def transformar_quadriculo_em_inimigo(self, coluna, linha):
        quadriculo = self.obter_quadriculo_por_coordenada(coluna, linha)
        if not quadriculo:
            return

        caminho_base = config.RECURSOS.get('padrao_base_quadriculo_caverna')
        if not caminho_base:
            return
        novo_caminho = caminho_base.replace('1.png', f'{config.TIPO_TERRENO_INIMIGO}.png')

        nova_imagem = Sprite(novo_caminho)
        nova_imagem.x = quadriculo.imagem_quadriculo.x
        nova_imagem.y = quadriculo.imagem_quadriculo.y

        quadriculo.imagem_quadriculo = nova_imagem
        quadriculo.indice_variacao_terreno = config.TIPO_TERRENO_INIMIGO

    def obter_posicao_passagem(self):
        """
        DESCRIÇÃO:
            Retorna a posição (coluna, linha) do quadriculo marcado como passagem, se existir.

        RESPONSABILIDADE:
            - Procurar na lista de quadriculos aquele com a flag `eh_passagem` e retornar suas coordenadas.

        REGRAS DE USO:
            - Retorna uma tupla `(coluna, linha)` ou `None` quando nenhuma passagem estiver definida.

        NOTAS DE IMPLEMENTAÇÃO:
            - Percorre `self.lista_quadriculos` de forma linear; usada por `main.py` para alinhar transições.
        """
        for quadriculo in self.lista_quadriculos:
            if getattr(quadriculo, 'eh_passagem', False):
                return (quadriculo.indice_coluna, quadriculo.indice_linha)
        return None


    def obter_quadriculo_por_coordenada(self, coluna, linha):
        return self.dicionario_quadriculos_por_coordenada.get((coluna, linha))

    def obter_quadriculo_por_posicao_pixel(self, posicao_x, posicao_y):
        return self.obter_quadriculo_por_coordenada(int(posicao_x / self.largura_quadriculo), int(posicao_y / self.altura_quadriculo))

    def marcar_quadriculo_escavado(self, coluna, linha, caminho_arquivo_imagem=None):
        quadriculo = self.obter_quadriculo_por_coordenada(coluna, linha)
        if quadriculo:
            return quadriculo.adicionar_sobreposicao(caminho_arquivo_imagem)
        return False

    def iniciar_escavacao(self, coluna, linha, tem_pa=False):
        """
        DESCRIÇÃO:
            Inicia a ação de escavação no quadriculo indicado se possível.

        RESPONSABILIDADE:
            - Validar se é possível escavar e configurar temporizadores para o processo.

        REGRAS DE USO:
            - Retorna False se já estiver escavando, se o quadriculo não existir ou já tiver sobreposição.

        NOTAS DE IMPLEMENTAÇÃO:
            - Reduz a duração de escavação se `tem_pa` for True.
        """
        if self._escavando:
            return False
        quadriculo = self.obter_quadriculo_por_coordenada(coluna, linha)
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
        """
        DESCRIÇÃO:
            Atualiza o temporizador de escavação e, quando concluída, resolve o resultado (sucesso/item/dado).

        RESPONSABILIDADE:
            - Incrementar o temporizador, verificar conclusão e aplicar resultado de escavação sobre o quadriculo.

        REGRAS DE USO:
            - Retorna uma tupla (concluido, sucesso, item, valor_dado).

        NOTAS DE IMPLEMENTAÇÃO:
            - Usa lógica de probabilidade interna considerando bônus por `pa` e valida duplicatas.
        """
        if not self._escavando:
            return False, False, None, 0
        
        self._temporizador_escavacao += tempo_decorrido
        duracao = getattr(self, '_duracao_atual', self._duracao_escavacao)
        
        if self._temporizador_escavacao < duracao:
            return False, False, None, 0
        
        coluna, linha = self._alvo_escavacao
        quadriculo = self.obter_quadriculo_por_coordenada(coluna, linha)
        
        concluido = True
        sucesso = False
        item = None
        valor_dado = 0

        self._escavando = False
        self._alvo_escavacao = (None, None)
        self._temporizador_escavacao = 0.0

        if quadriculo:
                if (quadriculo.item == 'pa' and tem_pa) or (quadriculo.item == 'faca' and tem_faca):
                    item = f"{quadriculo.item}_duplicada"
                    print(f"Ja tem {quadriculo.item} no inventario")
                    return concluido, sucesso, item, valor_dado

        bonus_dado = config.JOGABILIDADE['bonus_escavacao_pa'] if tem_pa else 0
        dado_bruto = random.randint(0, config.JOGABILIDADE['dado_escavacao'])
        dado = dado_bruto
        
        if (dado_bruto + bonus_dado) > config.JOGABILIDADE['dificuldade_escavacao']:
            sucesso = True
            caminho_imagem = config.RECURSOS['passagem'] if quadriculo and quadriculo.eh_passagem else None
            sobreposicao_adicionada = self.marcar_quadriculo_escavado(coluna, linha, caminho_imagem)

            if sobreposicao_adicionada and quadriculo:
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
                
        valor_dado = dado_bruto
        return concluido, sucesso, item, valor_dado

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

    def _processar_celula_investigacao(self, coluna, linha, nome_posicao, dificuldade):
        quadriculo = self.obter_quadriculo_por_coordenada(coluna, linha)
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

    def iniciar_investigacao(self, coluna, linha):
        """
        DESCRIÇÃO:
            Inicia a sequência de investigação ao redor de uma coordenada central, gerando fila de mensagens.

        RESPONSABILIDADE:
            - Preparar a fila de mensagens que serão exibidas durante a investigação.

        REGRAS DE USO:
            - Retorna False se já estiver investigando ou se coordenada inválida.

        NOTAS DE IMPLEMENTAÇÃO:
            - A dificuldade de cada célula depende de sua posição (centro, ortogonal, diagonal).
        """
        if self._investigando:
            return False

        if (coluna, linha) not in self.dicionario_quadriculos_por_coordenada:
            return False

        direcoes = config.MENSAGENS.get('investigacao_direcoes', {})
        intervalo = config.JOGABILIDADE.get('intervalo_entre_mensagens', 0.3)
        duracao_mensagem = config.JOGABILIDADE.get('tempo_mensagem_investigacao', 2.0)
        atraso_inicial = config.JOGABILIDADE.get('atraso_inicial_investigacao', 1.0)
        atraso_final = config.JOGABILIDADE.get('atraso_final_investigacao', 1.0)

        fila = []
        tempo_atual = atraso_inicial

        for (dx, dy), nome_posicao in direcoes.items():
            dificuldade = config.JOGABILIDADE.get('dificuldade_investigacao_ortogonal', 10)
            if dx == 0 and dy == 0:
                dificuldade = config.JOGABILIDADE.get('dificuldade_investigacao_centro', 5)
            elif abs(dx) == 1 and abs(dy) == 1:
                dificuldade = config.JOGABILIDADE.get('dificuldade_investigacao_diagonal', 15)

            mensagem = self._processar_celula_investigacao(coluna + dx, linha + dy, nome_posicao, dificuldade)
            inicio = tempo_atual
            fim = inicio + duracao_mensagem
            fila.append((inicio, fim, mensagem))
            tempo_atual = fim + intervalo

        duracao_total = tempo_atual + atraso_final

        self._investigando = True
        self._fila_mensagens = fila
        self._tempo_investigacao = 0.0
        self._duracao_total_investigacao = duracao_total
        return True

    def atualizar_investigacao(self, tempo_decorrido):
        """
        DESCRIÇÃO:
            Atualiza o estado da investigação, avança o temporizador e retorna a mensagem atual.

        RESPONSABILIDADE:
            - Retornar (investigando, mensagem_atual).

        REGRAS DE USO:
            - Deve ser chamado a cada frame enquanto `_investigando` for True.

        NOTAS DE IMPLEMENTAÇÃO:
            - Calcula qual mensagem da fila deve ser exibida com base no tempo acumulado.
        """
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
        """
        DESCRIÇÃO:
            Desenha todos os quadriculos que compõem o mapa na ordem de sua lista interna.

        RESPONSABILIDADE:
            - Chamar `desenhar()` de cada `Quadriculo`.

        REGRAS DE USO:
            - Chamado no ciclo de renderização do jogo.

        NOTAS DE IMPLEMENTAÇÃO:
            - A ordem de desenho segue `self.lista_quadriculos`.
        """
        for quadriculo in self.lista_quadriculos:
            quadriculo.desenhar()

    def resetar_estado(self):
        """
        DESCRIÇÃO:
            Limpa estados transitórios do mapa, removendo sobreposições e resetando timers.

        RESPONSABILIDADE:
            - Restaurar o mapa para um estado inicial preservando a geração original.

        REGRAS DE USO:
            - Usado ao reiniciar o jogo para manter distribuição de itens mas limpar o visual.

        NOTAS DE IMPLEMENTAÇÃO:
            - Limpa atributos como `_escavando` e `_investigando` e esvazia filas de mensagens.
        """
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
        quadriculo = self.obter_quadriculo_por_posicao_pixel(x, y)
        if quadriculo and getattr(quadriculo, 'indice_variacao_terreno', 1) == config.TIPO_TERRENO_PAREDE:
            return True
        return False

    def eh_buraco(self, coluna, linha):
        if self.tipo != 'CAVERNA':
            return False
        quadriculo = self.obter_quadriculo_por_coordenada(coluna, linha)
        return quadriculo and getattr(quadriculo, 'indice_variacao_terreno', 1) == config.TIPO_TERRENO_BURACO

    def eh_runa(self, coluna, linha):
        if self.tipo != 'CAVERNA':
            return False
        quadriculo = self.obter_quadriculo_por_coordenada(coluna, linha)
        return quadriculo and getattr(quadriculo, 'indice_variacao_terreno', 1) == config.TIPO_TERRENO_RUNA
