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
from PPlay.sound import Sound
from popup import TelaLeitura
import config


class InterfaceUsuario:
    """
    DESCRIÇÃO:
        Classe responsável pela apresentação e lógica de interface do jogo (HUD, inventário, mensagens).

    RESPONSABILIDADE:
        1. Renderizar barras de status (sede, sol) e inventário.
        2. Gerenciar a evolução temporal de recursos do jogador (taxas de sede/sol).
        3. Controlar sons relacionados à interface (escavar, investigando, trilha).
        4. Fornecer métodos para adicionar/usar/remover itens do inventário.

    REGRAS DE USO:
        - Instanciar passando a `janela` do jogo e opcionalmente `altura_quadriculo`.
        - Chamar `atualizar(tempo_decorrido)` a cada frame e `desenhar()` após as atualizações.

    NOTAS DE IMPLEMENTAÇÃO:
        - Muitos métodos operam diretamente sobre sprites e componentes de áudio; falhas ao carregar assets são tratadas silenciosamente.
        - Usa configurações definidas em `config` para valores de gameplay e recursos.
    """
    def __init__(self, janela, altura_quadriculo=None):
        """
        DESCRIÇÃO:
            Inicializa a interface de usuário com sprites, sons e estados iniciais.

        RESPONSABILIDADE:
            - Configurar sprites de HUD, carregar imagens de preenchimento e preparar slots de inventário.

        REGRAS DE USO:
            - Recebe a `janela` como objeto PPlay.Window e opcional `altura_quadriculo` para dimensionamento.

        NOTAS DE IMPLEMENTAÇÃO:
            - Sons opcionais são carregados com tratamento de exceção para permitir execução sem áudio.
        """
        self.janela = janela
        self.altura_quadriculo = altura_quadriculo

        self.icone_sol = Sprite(config.RECURSOS['painel_sol'])
        self.barra_sol = Sprite(config.RECURSOS['painel_barra'])
        self.icone_sede = Sprite(config.RECURSOS['painel_sede'])
        self.barra_sede = Sprite(config.RECURSOS['painel_barra'])

        self.sede = config.JOGABILIDADE['sede_inicial']
        self.sol = config.JOGABILIDADE['sol_inicial']
        self._tempo_acumulado = 0.0

        self.slots_inventario = []
        self.calcular_disposicao()

        imagens_preenchimento = config.INTERFACE_USUARIO.get('imagens_preenchimento_barra', [])
        if not imagens_preenchimento:
            raise RuntimeError('config.INTERFACE_USUARIO["imagens_preenchimento_barra"] must be defined')

        self.imagens_preenchimento = []
        for caminho in imagens_preenchimento:
            imagem = self._carregar_sprite_segura(caminho)
            self.imagens_preenchimento.append(imagem)

        self._mensagem_sede = ""
        self._temporizador_mensagem_sede = 0.0
        self._mensagem_sol = ""
        self._temporizador_mensagem_sol = 0.0
        
        self.multiplicador_custo = 1.0

        self.pergaminhos_coletados = []
        self.modo_inventario = 'padrao' 
        self.lendo_pergaminho = False
        self.indice_leitura_atual = None
        self.leitura_referencia = False
        
        self.tela_leitura = TelaLeitura(self.janela)
        try:
            self.som_bebendo = Sound("assets/bebendo.ogg")
        except Exception:
            self.som_bebendo = None
        try:
            self.som_escavando = Sound("assets/escavando.ogg")
        except Exception:
            self.som_escavando = None
        try:
            self.som_investigando = Sound("assets/investigando.ogg")
        except Exception:
            self.som_investigando = None

        self.trilha_sonora = None

    def iniciar_trilha(self, caminho="assets/trilha.ogg", volume=5):
        """
        DESCRIÇÃO:
            Inicia a trilha sonora do jogo, carregando o arquivo e configurando repetição/volume.

        RESPONSABILIDADE:
            - Criar o objeto `Sound`, configurar repetição e volume, e iniciar a reprodução.

        REGRAS DE USO:
            - Chamado opcionalmente logo após a inicialização dos recursos do jogo.
            - Não reinicia a trilha se já estiver ativa.

        NOTAS DE IMPLEMENTAÇÃO:
            - Falhas no carregamento são tratadas silenciosamente para permitir execução sem áudio.
        """
        if getattr(self, 'trilha_sonora', None) is not None:
            return
        try:
            self.trilha_sonora = Sound(caminho)
            self.trilha_sonora.set_repeat(True)
            self.trilha_sonora.set_volume(volume)
            self.trilha_sonora.play()
        except Exception:
            pass

    def iniciar_som_escavando(self, jogador=None):
        try:
            if getattr(self, 'som_escavando', None):
                self.som_escavando.set_repeat(True)
                self.som_escavando.play()
                if jogador is not None:
                    jogador._tocando_som_escavando = True
        except Exception:
            pass

    def parar_som_escavando(self, jogador=None):
        try:
            if getattr(self, 'som_escavando', None):
                self.som_escavando.set_repeat(False)
                self.som_escavando.stop()
                if jogador is not None:
                    jogador._tocando_som_escavando = False
        except Exception:
            pass

    def iniciar_som_investigando(self, jogador=None):
        """
        DESCRIÇÃO:
            Começa a reprodução do som de investigação em loop, marcando o jogador como tocando o som.

        RESPONSABILIDADE:
            - Iniciar `som_investigando` e marcar `jogador._tocando_som_investigando` quando aplicável.

        REGRAS DE USO:
            - Usar apenas quando a investigação começar; falhas no áudio são ignoradas.

        NOTAS DE IMPLEMENTAÇÃO:
            - Protegido por `getattr` para cenários sem suporte a áudio.
        """
        try:
            if getattr(self, 'som_investigando', None):
                self.som_investigando.set_repeat(True)
                self.som_investigando.play()
                if jogador is not None:
                    jogador._tocando_som_investigando = True
        except Exception:
            pass

    def parar_som_investigando(self, jogador=None):
        """
        DESCRIÇÃO:
            Para a reprodução do som de investigação e remove a marcação no jogador.

        RESPONSABILIDADE:
            - Parar `som_investigando` e limpar `jogador._tocando_som_investigando` quando aplicável.

        REGRAS DE USO:
            - Deve ser chamado quando a investigação terminar ou for cancelada.

        NOTAS DE IMPLEMENTAÇÃO:
            - Trata exceções silenciosamente para rodar sem dependência de áudio.
        """
        try:
            if getattr(self, 'som_investigando', None):
                self.som_investigando.set_repeat(False)
                self.som_investigando.stop()
                if jogador is not None:
                    jogador._tocando_som_investigando = False
        except Exception:
            pass

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

        self.slots_inventario = [Sprite(config.RECURSOS['espaco_inventario']) for _ in range(contagem_espacos)]
        for indice_espaco, espaco_atual in enumerate(self.slots_inventario):
            espaco_atual.x = x_espacos + indice_espaco * largura_espaco
            espaco_atual.y = y_espacos
        self.imagens_sobreposicao_slots = [None for _ in range(contagem_espacos)]
        self.nomes_itens = [None for _ in range(contagem_espacos)]
        self.usos_restantes_por_slot = [None for _ in range(contagem_espacos)]

    def _carregar_sprite_segura(self, caminho):
        if not caminho:
            return None
        try:
            return Sprite(caminho)
        except Exception:
            return None

    def definir_status_sede_sol(self, sede=None, sol=None):
        if sede is not None:
            self.sede = max(0, min(config.JOGABILIDADE['max_sede'], int(sede)))
        if sol is not None:
            self.sol = max(0, min(config.JOGABILIDADE['max_sol'], int(sol)))

    def atualizar(self, tempo_decorrido):
        """
        DESCRIÇÃO:
            Atualiza timers e aplica variações de sede/sol baseadas em `tempo_decorrido`.

        RESPONSABILIDADE:
            - Incrementar recursos do jogador de acordo com taxas configuradas.
            - Atualizar temporizadores de mensagens visuais.

        REGRAS DE USO:
            - Deve ser chamado a cada frame antes de `desenhar()`.

        NOTAS DE IMPLEMENTAÇÃO:
            - Acumula tempo em `_tempo_acumulado` para calcular segundos completos.
        """
        self._tempo_acumulado += tempo_decorrido
        segundos_completos = int(self._tempo_acumulado)
        
        if segundos_completos >= 1:
            nova_sede = self.sede + (config.JOGABILIDADE['taxa_sede_segundo'] * segundos_completos * self.multiplicador_custo)
            novo_sol = self.sol + (config.JOGABILIDADE['taxa_sol_segundo'] * segundos_completos * self.multiplicador_custo)
            self.definir_status_sede_sol(sede=nova_sede, sol=novo_sol)
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
        """
        DESCRIÇÃO:
            Renderiza elementos visuais da interface: ícones, barras de status, inventário e leitura de pergaminhos.

        RESPONSABILIDADE:
            - Desenhar sprites e textos relacionados ao HUD e inventário.

        REGRAS DE USO:
            - Chamado no ciclo de renderização do jogo após atualizações.

        NOTAS DE IMPLEMENTAÇÃO:
            - Usa `self.imagens_preenchimento` para compor barras de progresso preenchidas.
        """
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

        if self.modo_inventario == 'padrao':
            for espaco_atual in self.slots_inventario:
                espaco_atual.draw()
            for sobreposicao in self.imagens_sobreposicao_slots:
                if sobreposicao is not None:
                    sobreposicao.draw()
        elif self.modo_inventario == 'pergaminhos':
            self.desenhar_inventario_pergaminhos()

        if self.lendo_pergaminho:
            self.tela_leitura.desenhar(self.pergaminhos_coletados, self.indice_leitura_atual, self.lendo_pergaminho, referencia=self.leitura_referencia)

    def desenhar_inventario_pergaminhos(self):
        imagem_pergaminho = getattr(self.tela_leitura, 'imagem_pergaminho_fragmento', None)
        for indice_espaco, espaco_atual in enumerate(self.slots_inventario):
            espaco_atual.draw()
            if indice_espaco in self.pergaminhos_coletados and imagem_pergaminho is not None:
                imagem_pergaminho.x = espaco_atual.x + (espaco_atual.width - imagem_pergaminho.width) / 2
                imagem_pergaminho.y = espaco_atual.y + (espaco_atual.height - imagem_pergaminho.height) / 2
                imagem_pergaminho.draw()

    def alternar_modo_inventario(self, modo):
        self.modo_inventario = modo
        if modo == 'padrao':
            self.fechar_leitura()

    def abrir_leitura(self, indice, referencia=False):
        self.lendo_pergaminho = True
        self.indice_leitura_atual = indice
        self.leitura_referencia = bool(referencia)

    def processar_input_mouse(self, dispositivo_mouse):
        """
        DESCRIÇÃO:
            Processa eventos do mouse relacionados à interface (principalmente leitura de pergaminhos).

        RESPONSABILIDADE:
            - Encaminhar eventos à `TelaLeitura` quando em modo de leitura e retornar ações especiais.

        REGRAS DE USO:
            - Retorna `None` quando não há ação, ou `'RESTART'` quando o usuário acionou reinício via UI.

        NOTAS DE IMPLEMENTAÇÃO:
            - Quando `tela_leitura` retorna um índice, atualiza `indice_leitura_atual` e retorna None.
        """
        if not self.lendo_pergaminho:
            return None

        resultado = self.tela_leitura.processar_evento(dispositivo_mouse, self.pergaminhos_coletados, self.indice_leitura_atual, referencia=self.leitura_referencia)
        if resultado is not None and resultado != 'RESTART':
            self.indice_leitura_atual = resultado
            return None
        return resultado

    def fechar_leitura(self):
        self.lendo_pergaminho = False
        self.indice_leitura_atual = None
        self.leitura_referencia = False

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
        """
        DESCRIÇÃO:
            Define o multiplicador de custo aplicado às taxas de sede/sol e outras ações da interface.

        RESPONSABILIDADE:
            - Ajustar `multiplicador_custo` para refletir diferenças de custo entre ambientes (ex.: caverna).

        REGRAS DE USO:
            - Recebe um valor numérico (float) e substitui o multiplicador atual.

        NOTAS DE IMPLEMENTAÇÃO:
            - Usado por `main.py` para reduzir custos ao entrar na caverna.
        """
        self.multiplicador_custo = valor

    def processar_item_encontrado(self, nome_item):
        if not nome_item:
            return False
            
        caminho_imagem = config.RECURSOS.get(nome_item)
        if caminho_imagem:
            return self.adicionar_item(caminho_imagem, nome_item)
        return False

    def adicionar_item(self, caminho_imagem, nome_item=None):
        """
        DESCRIÇÃO:
            Tenta adicionar uma sobreposição de imagem representando um item no primeiro slot livre.

        RESPONSABILIDADE:
            - Inserir sprite do item no inventário e registrar usos caso aplicável.

        REGRAS DE USO:
            - Recebe o caminho da imagem e (opcional) o nome lógico do item.
            - Retorna True se item foi adicionado, False caso não haja slot livre.

        NOTAS DE IMPLEMENTAÇÃO:
            - Define usos iniciais para itens como 'pa' ou 'faca' usando `config.JOGABILIDADE`.
        """
        for indice_slot, sobreposicao in enumerate(self.imagens_sobreposicao_slots):
            if sobreposicao is None:
                imagem = Sprite(caminho_imagem)
                espaco = self.slots_inventario[indice_slot]
                imagem.x = espaco.x + (espaco.width - imagem.width) / 2
                imagem.y = espaco.y + (espaco.height - imagem.height) / 2
                self.imagens_sobreposicao_slots[indice_slot] = imagem
                self.nomes_itens[indice_slot] = nome_item
                if nome_item == 'pa':
                    self.usos_restantes_por_slot[indice_slot] = config.JOGABILIDADE.get('usos_pa', None)
                elif nome_item == 'faca':
                    self.usos_restantes_por_slot[indice_slot] = config.JOGABILIDADE.get('usos_faca', None)
                else:
                    self.usos_restantes_por_slot[indice_slot] = None
                item_nome = nome_item.upper() if nome_item else "item"
                print(f"Pegou: {item_nome}")
                return True
        return False

    def usar_item(self, indice_slot):
        """
        DESCRIÇÃO:
            Usa o item presente no `indice_slot` do inventário e atualiza usos/removendo-o quando esgotado.

        RESPONSABILIDADE:
            - Diminuir contador de usos para ferramentas ou remover consumíveis.

        REGRAS DE USO:
            - Recebe índice do slot; retorna False para índices inválidos ou slot vazio.
            - Retorna True quando a operação foi bem-sucedida.

        NOTAS DE IMPLEMENTAÇÃO:
            - Atualiza listas internas: `imagens_sobreposicao_slots`, `nomes_itens`, `usos_restantes_por_slot`.
        """
        if indice_slot < 0 or indice_slot >= len(self.imagens_sobreposicao_slots):
            return False
        if self.imagens_sobreposicao_slots[indice_slot] is None:
            return False
        nome = self.nomes_itens[indice_slot]
        if nome in ('pa', 'faca') and self.usos_restantes_por_slot[indice_slot] is not None:
            usos_restantes = self.usos_restantes_por_slot[indice_slot]
            if usos_restantes > 1:
                self.usos_restantes_por_slot[indice_slot] = usos_restantes - 1
                print(f"Usou {nome}. Usos restantes: {self.usos_restantes_por_slot[indice_slot]}")
                return True
            else:
                self.usos_restantes_por_slot[indice_slot] = None
                self.imagens_sobreposicao_slots[indice_slot] = None
                self.nomes_itens[indice_slot] = None
                print(f"{nome.upper()} quebrou/acabou e foi removida do inventário.")
                return True

        self.imagens_sobreposicao_slots[indice_slot] = None
        self.nomes_itens[indice_slot] = None
        self.usos_restantes_por_slot[indice_slot] = None
        return True

    def tem_item(self, nome_item):
        return nome_item in self.nomes_itens

    def consumir_uso_por_nome(self, nome_item):
        try:
            indice_encontrado = self.nomes_itens.index(nome_item)
        except ValueError:
            return False

        usos = self.usos_restantes_por_slot[indice_encontrado]
        if usos is None:
            self.imagens_sobreposicao_slots[indice_encontrado] = None
            self.nomes_itens[indice_encontrado] = None
            self.usos_restantes_por_slot[indice_encontrado] = None
            return True

        if usos > 1:
            self.usos_restantes_por_slot[indice_encontrado] = usos - 1
            print(f"Consumiu uso de {nome_item}. Usos restantes: {self.usos_restantes_por_slot[indice_encontrado]}")
            return True
        else:
            self.imagens_sobreposicao_slots[indice_encontrado] = None
            self.nomes_itens[indice_encontrado] = None
            self.usos_restantes_por_slot[indice_encontrado] = None
            print(f"{nome_item.upper()} quebrou/acabou e foi removida do inventário.")
            return True

    def remover_item(self, nome_item):
        try:
            indice_encontrado = self.nomes_itens.index(nome_item)
            self.imagens_sobreposicao_slots[indice_encontrado] = None
            self.nomes_itens[indice_encontrado] = None
            return True
        except ValueError:
            return False

    def recuperar_sede_escavacao(self):
        custo_sede = config.JOGABILIDADE['recuperacao_sede_item']
        self.definir_status_sede_sol(sede=self.sede + custo_sede)
        self.exibir_mensagem('sede', f'+{custo_sede}', duracao=config.INTERFACE_USUARIO['duracao_mensagem_feedback'])
        print(f"Custo da escavacao: sede +{custo_sede}")

    def consumir_bebida(self, indice_espaco):
        if self.usar_item(indice_espaco):
            recuperacao = config.JOGABILIDADE['recuperacao_sede_beber']
            self.definir_status_sede_sol(sede=self.sede - recuperacao)
            self.exibir_mensagem('sede', f"-{recuperacao}", duracao=config.INTERFACE_USUARIO['duracao_mensagem_feedback'])
            print(f"Bebeu agua!")
            return True
        return False

    def aplicar_custo_investigacao(self):
        custo_sede = config.JOGABILIDADE['custo_investigacao_sede']
        custo_sol = config.JOGABILIDADE['custo_investigacao_sol']
        
        self.definir_status_sede_sol(sede=self.sede + custo_sede, sol=self.sol + custo_sol)
        self.exibir_mensagem('sede', f'+{custo_sede}', duracao=config.INTERFACE_USUARIO['duracao_mensagem_feedback'])
        self.exibir_mensagem('sol', f'+{custo_sol}', duracao=config.INTERFACE_USUARIO['duracao_mensagem_feedback'])
        print(f"Investigando... Sede {self.sede}, Sol {self.sol}")
    def verificar_se_jogador_morreu(self):
        """
        DESCRIÇÃO:
            Verifica se os status de `sede` ou `sol` atingiram os limites de Game Over.

        RESPONSABILIDADE:
            - Retornar True quando qualquer dos status atingir ou ultrapassar seus máximos configurados.

        REGRAS DE USO:
            - Chamado pelo loop principal para checar condição de morte do jogador.

        NOTAS DE IMPLEMENTAÇÃO:
            - Compara `self.sede` e `self.sol` com os valores em `config.JOGABILIDADE`.
        """
        return self.sede >= config.JOGABILIDADE['max_sede'] or self.sol >= config.JOGABILIDADE['max_sol']

    def aplicar_dano_combate(self, valor):
        self.definir_status_sede_sol(sede=self.sede + valor)

    def aplicar_cura_combate(self, valor):
        self.definir_status_sede_sol(sede=self.sede - valor)

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
        if self.modo_inventario != 'padrao' or self.lendo_pergaminho:
            return None

        for numero_tecla in range(1, min(8, len(self.slots_inventario)) + 1):
            if teclado.key_pressed(str(numero_tecla)):
                indice_espaco = numero_tecla - 1
                if self.imagens_sobreposicao_slots[indice_espaco] is not None:
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
        """
        DESCRIÇÃO:
            Processa a recompensa resultante de uma escavação: aplica efeitos de sede e adiciona itens/pergaminhos.

        RESPONSABILIDADE:
            - Recuperar sede do jogador e tratar itens especiais (pergaminhos, duplicatas).
            - Integrar com inventário quando houver sobreposição adicionada.

        REGRAS DE USO:
            - Recebe `item_encontrado` (string ou tupla para pergaminhos) e `sobreposicao_adicionada` (bool).
            - Retorna um código representando o resultado ('sucesso', 'pergaminho_encontrado', 'falha', etc.).

        NOTAS DE IMPLEMENTAÇÃO:
            - Se `item_encontrado` for duplicado, retorna código apropriado sem adicionar ao inventário.
        """
        if item_encontrado in ['pa_duplicada', 'faca_duplicada']:
            return item_encontrado 
        
        self.recuperar_sede_escavacao()
        
        if isinstance(item_encontrado, tuple) and item_encontrado[0] == 'pergaminho':
            indice_pergaminho = item_encontrado[1]
            if indice_pergaminho is None:
                if len(self.pergaminhos_coletados) < config.JOGABILIDADE['quantidade_pergaminhos']:
                    novo_id = len(self.pergaminhos_coletados)
                    self.pergaminhos_coletados.append(novo_id)
                    print(f"Pergaminho #{novo_id + 1} encontrado!")
                    self.alternar_modo_inventario('pergaminhos')
                    return 'pergaminho_encontrado'
                else:
                    return 'sucesso_sem_item'

            if 0 <= indice_pergaminho < config.JOGABILIDADE['quantidade_pergaminhos']:
                if indice_pergaminho not in self.pergaminhos_coletados:
                    self.pergaminhos_coletados.append(indice_pergaminho)
                    print(f"Pergaminho #{indice_pergaminho + 1} encontrado! (slot fixo)")
                    self.alternar_modo_inventario('pergaminhos')
                    return 'pergaminho_encontrado'
                else:
                    return 'sucesso_sem_item'

        if item_encontrado == 'pergaminho':
            if len(self.pergaminhos_coletados) < config.JOGABILIDADE['quantidade_pergaminhos']:
                novo_id = len(self.pergaminhos_coletados)
                self.pergaminhos_coletados.append(novo_id)
                print(f"Pergaminho #{novo_id + 1} encontrado!")
                self.alternar_modo_inventario('pergaminhos')
                return 'pergaminho_encontrado'
            else:
                return 'sucesso_sem_item'

        if sobreposicao_adicionada and item_encontrado:
            self.processar_item_encontrado(item_encontrado)
            self.alternar_modo_inventario('padrao')
            return 'sucesso'
        elif sobreposicao_adicionada:
            return 'sucesso_sem_item'
        else:
            return 'falha'
