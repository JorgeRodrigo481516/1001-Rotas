"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia a Interface de Usuário e centraliza as regras de 
    sobrevivência (Sede, Sol) e gestão de inventário.

RESPONSABILIDADE:
    1. Visualização: Renderizar barras de status, espaços de inventário, mensagens de feedback 
       e barras de progresso genéricas para ações do jogador.
    2. Simulação: Controlar a evolução temporal dos status (taxas de sede/sol por segundo).
    3. Regras de Negócio: Aplicar custos de ações (investigar) e benefícios de itens (beber).
    4. Inventário: Gerenciar adição, remoção e uso de itens nos espaços.
    5. Recompensas: Processar resultados de escavações (recuperar sede, adicionar itens, detectar duplicatas).
    6. Interface de Combate: Fornecer métodos para o sistema de combate aplicar dano/cura e verificar condições.

REGRAS DE USO:
    - 'atualizar(tempo_decorrido)' deve ser chamado a cada frame para processar a simulação.
    - Métodos como 'consumir_bebida', 'aplicar_custo_investigacao' e 'aplicar_dano_combate' encapsulam a lógica de jogo.
    - 'verificar_se_jogador_morreu()' centraliza a checagem de Game Over.
    - 'desenhar_barra_progresso()' pode ser usado por qualquer componente para renderizar progresso visual.

NOTAS DE IMPLEMENTAÇÃO:
    - Centraliza a lógica matemática de sobrevivência para retirar essa carga do 'main.py', 'jogador.py' e 'sistema_combate.py'.
    - Barras de status usam imagens de preenchimento repetidos para visualização dinâmica.
    - Método desenhar_barra_progresso() determina cores automaticamente baseado no texto da ação.
-------------------------------------------------------------------
"""
from PPlay.sprite import Sprite
import config


class InterfaceUsuario:
    def __init__(self, janela, altura_quadriculo=None):
        self.janela = janela
        self.altura_quadriculo = altura_quadriculo

        self.icone_sol = Sprite(config.RECURSOS['painel_sol'])
        self.barra_sol = Sprite(config.RECURSOS['painel_barra'])
        self.icone_sede = Sprite(config.RECURSOS['painel_sede'])
        self.barra_sede = Sprite(config.RECURSOS['painel_barra'])

        self.sede = config.JOGABILIDADE['sede_inicial']
        self.sol = config.JOGABILIDADE['sol_inicial']
        self._tempo_acumulado = 0.0

        self.espacos_inventario = []
        self.calcular_disposicao()

        imagens_preenchimento = config.INTERFACE_USUARIO.get('imagens_preenchimento_barra', [])
        if not imagens_preenchimento:
            raise RuntimeError('config.INTERFACE_USUARIO["imagens_preenchimento_barra"] must be defined')

        self.imagens_preenchimento = []
        for caminho in imagens_preenchimento:
            try:
                imagem = Sprite(caminho) if caminho is not None else None
            except Exception:
                imagem = None
            self.imagens_preenchimento.append(imagem)

        self._mensagem_sede = ""
        self._temporizador_mensagem_sede = 0.0
        self._mensagem_sol = ""
        self._temporizador_mensagem_sol = 0.0
        
        self.multiplicador_custo = 1.0

    def calcular_disposicao(self):
        quadriculos_painel = config.INTERFACE_USUARIO.get('altura_painel_em_quadriculos', 2)
        
        if self.altura_quadriculo and quadriculos_painel:
            altura_painel = self.altura_quadriculo * quadriculos_painel
        else:
            altura_painel = self.icone_sol.height * 2

        posicao_y = (altura_painel - self.icone_sol.height) / 2

        espaco_entre = config.INTERFACE_USUARIO.get('espacamento_elementos_painel', 6)
        deslocamento_esquerda = config.INTERFACE_USUARIO.get('deslocamento_esquerda_painel', 0)

        largura_total = (self.icone_sol.width + self.barra_sol.width + self.icone_sede.width + self.barra_sede.width) + espaco_entre * 3
        posicao_x = ((self.janela.width - largura_total) / 2) - deslocamento_esquerda

        for imagem in (self.icone_sol, self.barra_sol, self.icone_sede, self.barra_sede):
            imagem.x = posicao_x
            imagem.y = posicao_y
            posicao_x += imagem.width + espaco_entre

        imagem_temporaria = Sprite(config.RECURSOS['espaco_inventario'])
        largura_espaco, altura_espaco = imagem_temporaria.width, imagem_temporaria.height
        del imagem_temporaria

        contagem_espacos = config.INTERFACE_USUARIO.get('quantidade_espacos_painel', 8)
        margem_direita_espaco = config.INTERFACE_USUARIO.get('margem_direita_espaco_painel', 10)
        x_espacos = self.janela.width - (contagem_espacos * largura_espaco) - margem_direita_espaco
        y_espacos = (altura_painel - altura_espaco) / 2

        self.espacos_inventario = [Sprite(config.RECURSOS['espaco_inventario']) for _ in range(contagem_espacos)]
        for i, espaco_atual in enumerate(self.espacos_inventario):
            espaco_atual.x = x_espacos + i * largura_espaco
            espaco_atual.y = y_espacos
        self.sobreposicoes_espacos = [None for _ in range(contagem_espacos)]
        self.nomes_itens = [None for _ in range(contagem_espacos)]

    def definir_valores(self, sede=None, sol=None):
        if sede is not None:
            self.sede = max(0, min(config.JOGABILIDADE['max_sede'], int(sede)))
        if sol is not None:
            self.sol = max(0, min(config.JOGABILIDADE['max_sol'], int(sol)))

    def atualizar(self, tempo_decorrido):
        self._tempo_acumulado += tempo_decorrido
        segundos_completos = int(self._tempo_acumulado)
        
        if segundos_completos >= 1:
            nova_sede = self.sede + (config.JOGABILIDADE['taxa_sede_segundo'] * segundos_completos * self.multiplicador_custo)
            novo_sol = self.sol + (config.JOGABILIDADE['taxa_sol_segundo'] * segundos_completos * self.multiplicador_custo)
            self.definir_valores(sede=nova_sede, sol=novo_sol)
            self._tempo_acumulado -= segundos_completos

        if self._temporizador_mensagem_sede > 0:
            self._temporizador_mensagem_sede -= tempo_decorrido
            if self._temporizador_mensagem_sede <= 0:
                self._mensagem_sede = ""
                self._temporizador_mensagem_sede = 0.0

        if self._temporizador_mensagem_sol > 0:
            self._temporizador_mensagem_sol -= tempo_decorrido
            if self._temporizador_mensagem_sol <= 0:
                self._mensagem_sol = ""
                self._temporizador_mensagem_sol = 0.0

    def desenhar(self):
        self.icone_sol.draw()
        self.barra_sol.draw()

        self.icone_sede.draw()
        self.barra_sede.draw()

        self._desenhar_barras_sede_e_sol(self.barra_sol, self.sol)
        self._desenhar_barras_sede_e_sol(self.barra_sede, self.sede)

        if self._mensagem_sol:
            texto_x = int(self.barra_sol.x + (self.barra_sol.width / 2) - (len(self._mensagem_sol) * 3))
            texto_y = int(self.barra_sol.y + self.barra_sol.height + 4)
            self.janela.draw_text(self._mensagem_sol, texto_x, texto_y, size=config.INTERFACE_USUARIO['tamanho_fonte_padrao'], color=config.CORES['preto'])

        if self._mensagem_sede:
            texto_x = int(self.barra_sede.x + (self.barra_sede.width / 2) - (len(self._mensagem_sede) * 3))
            texto_y = int(self.barra_sede.y + self.barra_sede.height + 4)
            self.janela.draw_text(self._mensagem_sede, texto_x, texto_y, size=config.INTERFACE_USUARIO['tamanho_fonte_padrao'], color=config.CORES['preto'])

        for espaco_atual in self.espacos_inventario:
            espaco_atual.draw()
        for sobreposicao in self.sobreposicoes_espacos:
            if sobreposicao is not None:
                sobreposicao.draw()

    def _desenhar_barras_sede_e_sol(self, imagem_barra, valor):
        if valor <= 0:
            return

        exemplo_preenchimento = next((p for p in self.imagens_preenchimento if p is not None), None)
        if exemplo_preenchimento is None:
            return

        largura_bloco = int(exemplo_preenchimento.width)
        altura_bloco = int(exemplo_preenchimento.height)

        margem_interna_esq = int(config.INTERFACE_USUARIO.get('margem_interna_esquerda_painel', 0))
        margem_interna_dir = int(config.INTERFACE_USUARIO.get('margem_interna_direita_painel', 0))
        espaco_entre_blocos = int(config.INTERFACE_USUARIO.get('espacamento_interno_painel', 0))

        largura_barra = int(imagem_barra.width)
        largura_util = max(0, largura_barra - margem_interna_esq - margem_interna_dir)

        passo_por_bloco = largura_bloco + espaco_entre_blocos
        if passo_por_bloco <= 0:
            return

        num_blocos = max(1, largura_util // passo_por_bloco)

        blocos_preenchidos = int((valor / float(config.JOGABILIDADE['max_sede'])) * num_blocos)
        blocos_preenchidos = max(0, min(blocos_preenchidos, num_blocos))

        segmentos = max(1, len(self.imagens_preenchimento))
        blocos_por_segmento = max(1, num_blocos // segmentos)

        x_inicio = imagem_barra.x + margem_interna_esq
        y_inicio = imagem_barra.y + (imagem_barra.height - altura_bloco) / 2

        for indice in range(blocos_preenchidos):
            indice_segmento = min(segmentos - 1, indice // blocos_por_segmento)
            imagem_para_desenhar = self.imagens_preenchimento[indice_segmento]
            if imagem_para_desenhar is None:
                continue

            posicao_x = x_inicio + indice * passo_por_bloco
            imagem_para_desenhar.x = posicao_x
            imagem_para_desenhar.y = y_inicio
            imagem_para_desenhar.draw()

    def definir_multiplicador_custo(self, valor):
        self.multiplicador_custo = valor

    def processar_item_encontrado(self, nome_item):
        if not nome_item:
            return False
            
        caminho_imagem = config.RECURSOS.get(nome_item)
        if caminho_imagem:
            return self.adicionar_item(caminho_imagem, nome_item)
        return False

    def adicionar_item(self, caminho_imagem, nome_item=None):
        for i, sobreposicao in enumerate(self.sobreposicoes_espacos):
            if sobreposicao is None:
                imagem = Sprite(caminho_imagem)
                espaco = self.espacos_inventario[i]
                imagem.x = espaco.x + (espaco.width - imagem.width) / 2
                imagem.y = espaco.y + (espaco.height - imagem.height) / 2
                self.sobreposicoes_espacos[i] = imagem
                self.nomes_itens[i] = nome_item
                # ---------------------------------------------------------------
                item_nome = nome_item.upper() if nome_item else "item"
                print(f"Pegou: {item_nome}")
                # ---------------------------------------------------------------
                return True
        return False

    def usar_item(self, indice):
        if indice < 0 or indice >= len(self.sobreposicoes_espacos):
            return False
        if self.sobreposicoes_espacos[indice] is None:
            return False
        self.sobreposicoes_espacos[indice] = None
        self.nomes_itens[indice] = None
        return True

    def tem_item(self, nome_item):
        return nome_item in self.nomes_itens

    def remover_item(self, nome_item):
        try:
            indice = self.nomes_itens.index(nome_item)
            self.sobreposicoes_espacos[indice] = None
            self.nomes_itens[indice] = None
            return True
        except ValueError:
            return False

    def recuperar_sede_escavacao(self):
        # Aumentar a sede é custo/punição (quanto maior, pior para o jogador)
        custo_sede = config.JOGABILIDADE['recuperacao_sede_item']
        self.definir_valores(sede=self.sede + custo_sede)
        self.exibir_mensagem('sede', f'+{custo_sede}', duracao=config.INTERFACE_USUARIO['duracao_mensagem_feedback'])
        print(f"Custo da escavacao: sede +{custo_sede}")

    def consumir_bebida(self, indice_espaco):
        if self.usar_item(indice_espaco):
            recuperacao = config.JOGABILIDADE['recuperacao_sede_beber']
            self.definir_valores(sede=self.sede - recuperacao)
            self.exibir_mensagem('sede', f"-{recuperacao}", duracao=config.INTERFACE_USUARIO['duracao_mensagem_feedback'])
            # ---------------------------------------------------------------
            print(f"Bebeu agua!")
            # ---------------------------------------------------------------
            return True
        return False

    def aplicar_custo_investigacao(self):
        custo_sede = config.JOGABILIDADE['custo_investigacao_sede']
        custo_sol = config.JOGABILIDADE['custo_investigacao_sol']
        
        self.definir_valores(sede=self.sede + custo_sede, sol=self.sol + custo_sol)
        self.exibir_mensagem('sede', f'+{custo_sede}', duracao=config.INTERFACE_USUARIO['duracao_mensagem_feedback'])
        self.exibir_mensagem('sol', f'+{custo_sol}', duracao=config.INTERFACE_USUARIO['duracao_mensagem_feedback'])
        # ---------------------------------------------------------------
        print(f"Investigando... Sede {self.sede}, Sol {self.sol}")
        # ---------------------------------------------------------------
    def verificar_se_jogador_morreu(self):
        return self.sede >= config.JOGABILIDADE['max_sede'] or self.sol >= config.JOGABILIDADE['max_sol']

    def aplicar_dano_combate(self, valor):
        self.definir_valores(sede=self.sede + valor)

    def aplicar_cura_combate(self, valor):
        self.definir_valores(sede=self.sede - valor)

    def possui_condicao_para_combate(self):
        vida_restante = config.JOGABILIDADE['max_sede'] - self.sede
        return vida_restante >= config.JOGABILIDADE['limiar_sede_combate']

    def exibir_mensagem(self, tipo, texto, duracao=1.5):
        if tipo == 'sede':
            self._mensagem_sede = str(texto)
            self._temporizador_mensagem_sede = float(duracao)
        elif tipo == 'sol':
            self._mensagem_sol = str(texto)
            self._temporizador_mensagem_sol = float(duracao)
        else:
            return

    def obter_indice_item_acionado(self, teclado):
        for numero_tecla in range(1, min(8, len(self.espacos_inventario)) + 1):
            if teclado.key_pressed(str(numero_tecla)):
                indice_espaco = numero_tecla - 1
                if self.sobreposicoes_espacos[indice_espaco] is not None:
                    return indice_espaco
        return None

    def desenhar_barra_progresso(self, x_referencia, y_referencia, largura_referencia, texto, progresso, cor_preenchimento):
        if "Escavando" in texto:
            cor_borda = config.CORES['barra_escavacao_borda']
            cor_fundo = config.CORES['barra_escavacao_fundo']
            cor_texto = config.CORES['preto']
        elif "Bebendo" in texto:
            cor_borda = config.CORES['barra_bebendo_borda']
            cor_fundo = config.CORES['barra_bebendo_fundo']
            cor_texto = config.CORES['azul_escuro']
        elif "Caindo" in texto:
            cor_borda = config.CORES['preto']
            cor_fundo = config.CORES['branco']
            cor_texto = config.CORES['vermelho']
        elif "Investigando" in texto:
            cor_borda = config.CORES['barra_investigando_borda']
            cor_fundo = config.CORES['barra_investigando_fundo']
            cor_texto = config.CORES['texto_investigacao']
        elif "Ativando" in texto:
            cor_borda = config.CORES['barra_investigando_borda']
            cor_fundo = config.CORES['barra_investigando_fundo']
            cor_texto = config.CORES['texto_ativando']
        elif "Entrando" in texto or "Saindo" in texto:
            cor_borda = config.CORES['barra_entrando_borda']
            cor_fundo = config.CORES['barra_entrando_fundo']
            cor_texto = config.CORES['preto']
        else:
            cor_borda = config.CORES['preto']
            cor_fundo = config.CORES['branco']
            cor_texto = config.CORES['preto']

        texto_x = int(x_referencia + (largura_referencia / 2) - (len(texto) * 3))
        if "Investigando" in texto:
            texto_x += 10
        texto_y = int(y_referencia - 18)
        self.janela.draw_text(texto, texto_x, texto_y, size=config.INTERFACE_USUARIO['tamanho_fonte_padrao'], color=cor_texto, bold=True)

        largura_barra = int(largura_referencia * 1) + 35
        altura_barra = 6
        barra_x = int(x_referencia + (largura_referencia - largura_barra) / 2)
        barra_y = int(texto_y - altura_barra - 4)

        tela = self.janela.get_screen()
        tela.fill(cor_borda, (barra_x-1, barra_y-1, largura_barra+2, altura_barra+2))
        tela.fill(cor_fundo, (barra_x, barra_y, largura_barra, altura_barra))
        
        largura_preenchimento = max(0, min(largura_barra, int(largura_barra * float(progresso))))
        if largura_preenchimento > 0:
            tela.fill(cor_preenchimento, (barra_x, barra_y, largura_preenchimento, altura_barra))

    def processar_recompensa_escavacao(self, item_encontrado, sobreposicao_adicionada):
        if item_encontrado in ['pa_duplicada', 'faca_duplicada']:
            return item_encontrado 
        
        self.recuperar_sede_escavacao()
        
        if sobreposicao_adicionada and item_encontrado:
            self.processar_item_encontrado(item_encontrado)
            return 'sucesso'
        elif sobreposicao_adicionada:
            return 'sucesso_sem_item'
        else:
            return 'falha'
