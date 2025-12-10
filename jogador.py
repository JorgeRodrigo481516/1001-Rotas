"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Define a entidade Jogador, controlando a movimentação, animação e 
    interação do protagonista com o mundo.

RESPONSABILIDADE:
    1. Gerenciar posição (x, y) e renderização das imagens do personagem.
    2. Processar input de teclado para movimentação e iniciar ações (beber, escavar, investigar).
    3. Controlar estados de animação e bloqueio de movimento durante ações.
    4. Validar colisão com bordas da janela, área da Interface e paredes (caverna).
    5. Delegar a aplicação de regras de negócio (custos, recuperação) para InterfaceUsuario.
    6. Coordenar processamento de escavação: verificar itens, chamar mapa e processar recompensas.
    7. Integrar com MecanicasCaverna para atualizar mecânicas específicas da caverna quando aplicável.

REGRAS DE USO:
    - Exige instâncias válidas de 'Janela', 'Mapa' e opcionalmente 'InterfaceUsuario'.
    - Requer instância de 'MecanicasCaverna' atribuída via atributo 'mecanicas_caverna'.
    - Se x/y não forem fornecidos na instanciação, calcula posição inicial automaticamente.
    - 'atualizar()' deve ser chamado a cada frame do loop principal.

NOTAS DE IMPLEMENTAÇÃO:
    - Não implementa lógica de queda, runas ou passagens - delegada para MecanicasCaverna.
    - Não desenha barras de progresso diretamente - delega para interface.desenhar_barra_progresso().
    - Método processar_escavacao() encapsula: verificar itens → atualizar mapa → processar recompensa.
    - Mantém estado interno de 'bebendo' para bloquear input durante a animação.
-------------------------------------------------------------------
"""
from PPlay.sprite import Sprite
import config


class Jogador:
    """
    DESCRIÇÃO:
        Representa o protagonista controlável pelo jogador, incluindo movimento, animações e interações.

    RESPONSABILIDADE:
        1. Processar entrada do jogador e movimentação no mundo.
        2. Gerenciar estados de ação (escavar, beber, ativar runa, cair).
        3. Encaminhar/receber efeitos via `InterfaceUsuario` e `MecanicasCaverna`.

    REGRAS DE USO:
        - Instanciar com referência a `janela` e `mapa` válidos.
        - Chamar `atualizar(teclado, tempo_decorrido)` a cada frame e `desenhar()` na fase de render.

    NOTAS DE IMPLEMENTAÇÃO:
        - Muitos métodos dependem de atributos de `mapa` estarem previamente inicializados (ex.: `altura_quadriculo`).
    """
    def __init__(self, posicao_pixel_x, posicao_pixel_y, janela, mapa, velocidade_movimento=None, velocidade_animacao=None, interface=None, interface_usuario=None, sistema_combate=None):
        """
        DESCRIÇÃO:
            Inicializa o jogador configurando sprites, posições e estados iniciais.

        RESPONSABILIDADE:
            - Preparar sprites de animação, estado de inventário e referências a subsistemas.

        REGRAS DE USO:
            - `posicao_pixel_x` e `posicao_pixel_y` podem ser None para uso da posição inicial por padrão.

        NOTAS DE IMPLEMENTAÇÃO:
            - Aceita `interface` ou `interface_usuario` (compatibilidade); prefere `interface_usuario` se fornecido.
        """
        self.janela = janela
        self.mapa = mapa
        # Prefer explicit `interface_usuario` if fornecido; manter `self.interface` como alias por compatibilidade.
        iface = interface_usuario if interface_usuario is not None else interface
        self.interface_usuario = iface
        self.sistema_combate = sistema_combate

        self.sprite_andar_direita_1, self.sprite_andar_direita_2, self.sprite_andar_esquerda_1, self.sprite_andar_esquerda_2 = (
            Sprite(config.RECURSOS['jogador_direita_1']),
            Sprite(config.RECURSOS['jogador_direita_2']),
            Sprite(config.RECURSOS['jogador_esquerda_1']),
            Sprite(config.RECURSOS['jogador_esquerda_2']),
        )

        if posicao_pixel_x is None or posicao_pixel_y is None:
            self.definir_posicao_inicial()
        else:
            self.posicao_pixel_x, self.posicao_pixel_y = posicao_pixel_x, posicao_pixel_y

        self.ultima_direcao = 'direita'
        self.frame_alternativo = False
        self.tempo_animacao = 0.0
        self.velocidade_animacao = velocidade_animacao if velocidade_animacao is not None else config.JOGABILIDADE['velocidade_animacao_jogador']

        self.velocidade_movimento = velocidade_movimento if velocidade_movimento is not None else config.JOGABILIDADE['velocidade_jogador']

        self._bebendo = False
        self._temporizador_bebida = 0.0
        self._duracao_bebida = config.JOGABILIDADE['duracao_beber']
        self._indice_slot_bebida = None

        self._mensagem_acima = ""
        self._temporizador_mensagem_acima = 0.0
        
        self._caindo = False
        self._temporizador_queda = 0.0
        self._ativando_runa = False
        self._temporizador_ativacao = 0.0
        
        self._tempo_parado = 0.0
        self._tempo_para_ativar_foco = config.JOGABILIDADE.get('tempo_para_ativar_foco', 0.5)
        
        self.sistema_foco_ativo = False
        self.tecla_f_pressionada = False

        self.mecanicas_caverna = None
        self._tocando_som_escavando = False
        self._tocando_som_investigando = False

    def atualizar(self, teclado, tempo_decorrido):
        """
        DESCRIÇÃO:
            Processa entrada do jogador, atualiza animações, aplica limites de movimento e chama mecânicas relacionadas.

        RESPONSABILIDADE:
            - Ler teclado, mover o jogador se permitido, atualizar animação e temporizadores de ação.
            - Propagar atualização para `MecanicasCaverna` quando presentes.

        REGRAS DE USO:
            - Deve ser chamado a cada frame; recebe objeto `teclado` e `tempo_decorrido` em segundos.

        NOTAS DE IMPLEMENTAÇÃO:
            - Valida movimento com `movimento_valido_para` antes de alterar posição.
        """
        self.processar_comandos(teclado)

        if self._temporizador_mensagem_acima > 0:
            self._temporizador_mensagem_acima -= tempo_decorrido
            if self._temporizador_mensagem_acima <= 0:
                self._mensagem_acima = ""
                self._temporizador_mensagem_acima = 0.0

        if self._esta_em_acao():
            esta_movendo = False
            self.frame_alternativo = False
            self.tempo_animacao = 0.0
            if self._bebendo:
                self._temporizador_bebida += tempo_decorrido
                if self._temporizador_bebida >= self._duracao_bebida:
                    indice_espaco = self._indice_slot_bebida
                    if self.interface_usuario is not None:
                        self.interface_usuario.consumir_bebida(indice_espaco)
                    self._bebendo = False
                    self._temporizador_bebida = 0.0
                    self._indice_slot_bebida = None
        else:
            passo = self.velocidade_movimento * tempo_decorrido

            deslocamento_x = 0
            if teclado.key_pressed("RIGHT"):
                deslocamento_x = passo
                self.ultima_direcao = "direita"
            elif teclado.key_pressed("LEFT"):
                deslocamento_x = -passo
                self.ultima_direcao = "esquerda"

            deslocamento_y = 0
            if teclado.key_pressed("UP"):
                deslocamento_y = -passo
            elif teclado.key_pressed("DOWN"):
                deslocamento_y = passo

            posicao_x_antiga, posicao_y_antiga = self.posicao_pixel_x, self.posicao_pixel_y
            
            if deslocamento_x != 0 and self.movimento_valido_para(self.posicao_pixel_x + deslocamento_x, self.posicao_pixel_y):
                self.posicao_pixel_x += deslocamento_x
                
            if deslocamento_y != 0 and self.movimento_valido_para(self.posicao_pixel_x, self.posicao_pixel_y + deslocamento_y):
                self.posicao_pixel_y += deslocamento_y

            esta_movendo = (self.posicao_pixel_x != posicao_x_antiga) or (self.posicao_pixel_y != posicao_y_antiga)

        if esta_movendo:
            self._caindo = False
            self._temporizador_queda = 0.0
            
            self._ativando_runa = False
            self._temporizador_ativacao = 0.0
            if self._mensagem_acima == "Ativando...":
                self._mensagem_acima = ""

            self.tempo_animacao += tempo_decorrido
            if self.tempo_animacao >= self.velocidade_animacao:
                self.tempo_animacao -= self.velocidade_animacao
                self.frame_alternativo = not self.frame_alternativo
        else:
            self.frame_alternativo = False
            self.tempo_animacao = 0.0

        if self.mecanicas_caverna:
            self.mecanicas_caverna.atualizar(tempo_decorrido, esta_movendo)

        largura_sprite, altura_sprite = self.sprite_andar_direita_1.width, self.sprite_andar_direita_1.height
        min_x, max_x = 0, self.janela.width - largura_sprite
        if not self.mapa.altura_quadriculo:
            raise RuntimeError('Mapa precisa definir altura_quadriculo antes de usar Jogador')
        min_y = config.INTERFACE_USUARIO['altura_painel_em_quadriculos'] * self.mapa.altura_quadriculo
        max_y = self.janela.height - altura_sprite
        self.posicao_pixel_x = max(min_x, min(self.posicao_pixel_x, max_x))
        self.posicao_pixel_y = max(min_y, min(self.posicao_pixel_y, max_y))

        if self.sistema_foco_ativo:
            if esta_movendo:
                self._tempo_parado = 0.0
                if self.mapa:
                    self.mapa.remover_foco()
            else:
                self._tempo_parado += tempo_decorrido
                if self._tempo_parado >= self._tempo_para_ativar_foco:
                    try:
                        coluna_foco, linha_foco = self.obter_coordenadas_grade(self.mapa.largura_quadriculo, self.mapa.altura_quadriculo)
                        self.mapa.atualizar_foco(coluna_foco, linha_foco)
                    except:
                        pass
                else:
                    if self.mapa:
                        self.mapa.remover_foco()
        else:
            self._tempo_parado = 0.0
            if self.mapa:
                self.mapa.remover_foco()

    def processar_comandos(self, teclado):
        """
        DESCRIÇÃO:
            Interpreta comandos discretos do teclado (ativar foco, alternar inventário, iniciar investigação/escavação).

        RESPONSABILIDADE:
            - Lidar com teclas de atalho (F, P, I, X, SPACE, X) e atalhos numéricos para itens.

        REGRAS DE USO:
            - Chamado internamente por `atualizar` antes do processamento de movimento.

        NOTAS DE IMPLEMENTAÇÃO:
            - Respeita estados que bloqueiam input (ex.: lendo pergaminho ou em ação).
        """
        if self.interface_usuario and self.interface_usuario.lendo_pergaminho:
            if teclado.key_pressed("I"):
                self.interface_usuario.alternar_modo_inventario('padrao')
            return

        if self.tem_mensagem_acima() or self._esta_em_acao():
            return

        if teclado.key_pressed("F"):
            if not self.tecla_f_pressionada:
                self.sistema_foco_ativo = not self.sistema_foco_ativo
                self.tecla_f_pressionada = True
                estado = "ATIVADO" if self.sistema_foco_ativo else "DESATIVADO"
                print(f"Sistema de foco: {estado}")
        else:
            self.tecla_f_pressionada = False

        if teclado.key_pressed("P"):
            if self.interface_usuario:
                self.interface_usuario.alternar_modo_inventario('pergaminhos')
        
        if teclado.key_pressed("I"):
            if self.interface_usuario:
                self.interface_usuario.alternar_modo_inventario('padrao')

        if self.interface_usuario and self.interface_usuario.modo_inventario == 'pergaminhos':
             for i in range(8):
                 if teclado.key_pressed(str(i+1)):
                     if i in self.interface_usuario.pergaminhos_coletados:
                        self.interface_usuario.abrir_leitura(i)
                        return

        if teclado.key_pressed("X"):
             if getattr(self.mapa, 'tipo', 'DESERTO') != 'CAVERNA':
                 coluna, linha = self.obter_coordenadas_grade(self.mapa.largura_quadriculo, self.mapa.altura_quadriculo)
                 if self.mapa.iniciar_investigacao(coluna, linha):
                     if self.interface_usuario:
                        self.interface_usuario.aplicar_custo_investigacao()
                     try:
                         if self.interface_usuario:
                             self.interface_usuario.iniciar_som_investigando(self)
                     except Exception:
                         pass

        if teclado.key_pressed("SPACE"):
            coluna, linha = self.obter_coordenadas_grade(self.mapa.largura_quadriculo, self.mapa.altura_quadriculo)
            possui_pa = self.interface_usuario.tem_item('pa') if self.interface_usuario else False
            if possui_pa and self.interface_usuario:
                self.interface_usuario.consumir_uso_por_nome('pa')
            iniciou = self.mapa.iniciar_escavacao(coluna, linha, tem_pa=possui_pa)
            if iniciou:
                try:
                    if self.interface_usuario:
                        self.interface_usuario.iniciar_som_escavando(self)
                except Exception:
                    pass

        if self.interface_usuario:
            indice_acionado = self.interface_usuario.obter_indice_item_acionado(teclado)
            if indice_acionado is not None:
                nome_item = self.interface_usuario.nomes_itens[indice_acionado]
                if nome_item == 'agua':
                    self.beber(indice_acionado, duracao=config.JOGABILIDADE['duracao_beber'])
                else:
                    print(f"Atalho numérico: item no slot {indice_acionado+1} ('{nome_item}') não é ativável por número.")

    def desenhar(self):
        """
        DESCRIÇÃO:
            Renderiza o sprite do jogador e textos/indicadores acima do personagem.

        RESPONSABILIDADE:
            - Selecionar frame correto de animação e desenhar barras de progresso quando em ações.

        REGRAS DE USO:
            - Chamado durante a fase de renderização do frame.

        NOTAS DE IMPLEMENTAÇÃO:
            - Depende de `interface_usuario` para desenhar barras de progresso associadas a ações.
        """
        if self.ultima_direcao == 'direita':
            imagem_atual = self.sprite_andar_direita_2 if self.frame_alternativo else self.sprite_andar_direita_1
        else:
            imagem_atual = self.sprite_andar_esquerda_2 if self.frame_alternativo else self.sprite_andar_esquerda_1
        imagem_atual.x, imagem_atual.y = self.posicao_pixel_x, self.posicao_pixel_y
        imagem_atual.draw()

        if self._mensagem_acima:
            texto_x = int(self.posicao_pixel_x + (imagem_atual.width / 2) - (len(self._mensagem_acima) * 3))
            texto_y = int(self.posicao_pixel_y - 25)
            self.janela.draw_text(self._mensagem_acima, texto_x, texto_y, size=config.INTERFACE_USUARIO['tamanho_fonte_padrao'], color=config.CORES['vermelho'], bold=True)

        if self.mapa.esta_escavando():
            if self.interface_usuario:
                self.interface_usuario.desenhar_barra_progresso(self.posicao_pixel_x, self.posicao_pixel_y, imagem_atual.width, 
                    "Escavando..", self.mapa.progresso_escavacao(), config.CORES['barra_escavacao_preenchimento'])

        if self.mapa.esta_investigando():
            if self.interface_usuario:
                self.interface_usuario.desenhar_barra_progresso(self.posicao_pixel_x, self.posicao_pixel_y, imagem_atual.width,
                    "Investigando...", self.mapa.progresso_investigacao(), config.CORES['barra_investigando_preenchimento'])
            mensagem = self.mapa.obter_mensagem_investigacao_atual()
            if mensagem:
                texto_x = int(self.posicao_pixel_x + (imagem_atual.width / 2) - (len(mensagem) * 3))
                texto_y = int(self.posicao_pixel_y - 55)
                self.janela.draw_text(mensagem, texto_x, texto_y, size=config.INTERFACE_USUARIO['tamanho_fonte_padrao'], color=config.CORES['texto_investigacao'], bold=True)

        if self._bebendo:
            progresso = min(1.0, self._temporizador_bebida / max(1e-6, self._duracao_bebida))
            if self.interface_usuario:
                self.interface_usuario.desenhar_barra_progresso(self.posicao_pixel_x, self.posicao_pixel_y, imagem_atual.width,
                    "Bebendo..", progresso, config.CORES['azul_real'])

        if self.mecanicas_caverna and self.mecanicas_caverna.esta_entrando_passagem():
            progresso = self.mecanicas_caverna.progresso_entrada()
            texto_acao = "Saindo..." if getattr(self.mapa, 'tipo', 'DESERTO') == 'CAVERNA' else "Entrando..."
            if self.interface_usuario:
                self.interface_usuario.desenhar_barra_progresso(self.posicao_pixel_x, self.posicao_pixel_y, imagem_atual.width,
                    texto_acao, progresso, config.CORES['barra_entrando_preenchimento'])

        if self.mecanicas_caverna and self.mecanicas_caverna.esta_ativando_runa():
            progresso = self.mecanicas_caverna.progresso_ativacao()
            if self.interface_usuario:
                self.interface_usuario.desenhar_barra_progresso(self.posicao_pixel_x, self.posicao_pixel_y, imagem_atual.width,
                    "Ativando...", progresso, config.CORES['barra_ativando_preenchimento'])

        if self.mecanicas_caverna and self.mecanicas_caverna.esta_caindo():
            progresso = self.mecanicas_caverna.progresso_queda()
            if self.interface_usuario:
                self.interface_usuario.desenhar_barra_progresso(self.posicao_pixel_x, self.posicao_pixel_y, imagem_atual.width,
                    "Caindo...", progresso, config.CORES['vermelho'])

    def beber(self, indice_espaco, duracao=3.0):
        """
        DESCRIÇÃO:
            Inicia a ação de beber de um item em um slot do inventário, bloqueando outras ações até concluir.

        RESPONSABILIDADE:
            - Marcar estado `_bebendo` e reproduzir som associado se disponível.

        REGRAS DE USO:
            - Recebe índice de slot contendo a bebida; retorna False se já estiver bebendo.

        NOTAS DE IMPLEMENTAÇÃO:
            - Define `_duracao_bebida` com o valor passado e toca `som_bebendo` via `interface_usuario`.
        """
        if self._bebendo:
            return False
        self._bebendo = True
        self._temporizador_bebida = 0.0
        self._duracao_bebida = float(duracao)
        self._indice_slot_bebida = int(indice_espaco)
        
        if self.interface_usuario and getattr(self.interface_usuario, 'som_bebendo', None):
            self.interface_usuario.som_bebendo.play()
        
        return True

    def exibir_mensagem_acima(self, texto, duracao=2.0):
        self._mensagem_acima = texto
        self._temporizador_mensagem_acima = float(duracao)

    def tem_mensagem_acima(self):
        return self._temporizador_mensagem_acima > 0

    def esta_bebendo(self):
        return bool(self._bebendo)

    def obter_coordenadas_grade(self, largura_quadriculo, altura_quadriculo):
        if largura_quadriculo is None or altura_quadriculo is None:
            raise ValueError('largura_quadriculo e altura_quadriculo devem estar definidos')
        return int(self.posicao_pixel_x / largura_quadriculo), int(self.posicao_pixel_y / altura_quadriculo)

    def definir_posicao_inicial(self):
        if self.interface_usuario and len(self.interface_usuario.slots_inventario) > 0:
            altura_espaco_painel = self.interface_usuario.slots_inventario[0].height
        else:
            altura_espaco_painel = 0
        
        self.posicao_pixel_x = self.mapa.largura_quadriculo
        self.posicao_pixel_y = self.janela.height - (config.INTERFACE_USUARIO['altura_painel_em_quadriculos'] * self.mapa.altura_quadriculo) - max(0, altura_espaco_painel)

    def teleportar_para_passagem(self, coluna, linha):
        """
        DESCRIÇÃO:
            Teleporta o jogador para a posição da passagem indicada e marca visualmente o tile como passagem.

        RESPONSABILIDADE:
            - Atualizar as coordenadas em pixels (`posicao_pixel_x`, `posicao_pixel_y`) baseado na grade.
            - Adicionar sobreposição de passagem no quadriculo se aplicável.

        REGRAS DE USO:
            - `coluna` e `linha` devem ser coordenadas válidas dentro do mapa.

        NOTAS DE IMPLEMENTAÇÃO:
            - Usa `config.JOGABILIDADE['ajuste_posicao_inicial_jogador']` para ajustar a posição vertical.
            - Silencia exceções para evitar travar o jogo em caso de inconsistências de mapa.
        """
        self.posicao_pixel_x = coluna * self.mapa.largura_quadriculo
        self.posicao_pixel_y = linha * self.mapa.altura_quadriculo + config.JOGABILIDADE['ajuste_posicao_inicial_jogador']
        try:
            quad = self.mapa.obter_quadriculo_por_coordenada(coluna, linha)
            if quad and getattr(quad, 'eh_passagem', False) and not quad.tem_sobreposicao():
                quad.adicionar_sobreposicao(config.RECURSOS['passagem'])
        except Exception:
            pass

    def processar_escavacao(self, tempo_decorrido):
        """
        DESCRIÇÃO:
            Coordena o ciclo de escavação: atualiza progresso, finaliza ação e processa recompensas.

        RESPONSABILIDADE:
            - Consultar `mapa` para progresso de escavação e delegar o processamento de recompensa para `InterfaceUsuario`.

        REGRAS DE USO:
            - Chamado periodicamente pelo loop principal quando a ação de escavar está em curso.

        NOTAS DE IMPLEMENTAÇÃO:
            - Pode disparar combates com base no `valor_dado` retornado pelo mapa.
        """
        if not self.interface_usuario:
            return False, None
        try:
            if not self.mapa.esta_escavando() and self.interface_usuario:
                self.interface_usuario.parar_som_escavando(self)
        except Exception:
            pass
        
        tem_pa = self.interface_usuario.tem_item('pa')
        tem_faca = self.interface_usuario.tem_item('faca')
        
        terminou, sobreposicao_adicionada, item_encontrado, valor_dado = self.mapa.atualizar_escavacao(
            tempo_decorrido, tem_pa=tem_pa, tem_faca=tem_faca
        )
        
        if terminou:
            resultado = self.interface_usuario.processar_recompensa_escavacao(item_encontrado, sobreposicao_adicionada)
            
            if resultado == 'pergaminho_encontrado':
                 self.exibir_mensagem_acima("Fragmento de Historia!", 
                    duracao=config.INTERFACE_USUARIO['duracao_msg_cabeca_padrao'])
            elif resultado == 'pa_duplicada':
                self.exibir_mensagem_acima(config.MENSAGENS['erro_pa_duplicada'], 
                    duracao=config.INTERFACE_USUARIO['duracao_msg_cabeca_erro'])
            elif resultado == 'faca_duplicada':
                self.exibir_mensagem_acima(config.MENSAGENS['erro_faca_duplicada'], 
                    duracao=config.INTERFACE_USUARIO['duracao_msg_cabeca_erro'])
            elif resultado == 'falha':
                self.exibir_mensagem_acima(config.MENSAGENS['erro_escavacao_falha'], 
                    duracao=config.INTERFACE_USUARIO['duracao_msg_cabeca_padrao'])
            try:
                if self.interface_usuario:
                    self.interface_usuario.parar_som_escavando(self)
            except Exception:
                pass
            try:
                if self.interface_usuario and getattr(self.mapa, 'esta_investigando', None):
                    if not self.mapa.esta_investigando():
                        self.interface_usuario.parar_som_investigando(self)
            except Exception:
                pass
            try:
                if valor_dado is not None and getattr(self, 'sistema_combate', None):
                    tipo_mapa = getattr(self.mapa, 'tipo', 'DESERTO')
                    self.sistema_combate.verificar_e_iniciar_combate(valor_dado, tipo_mapa)
            except Exception:
                pass
            return True, valor_dado
        
        return False, None

    def movimento_valido_para(self, x, y):
        largura = self.sprite_andar_direita_1.width
        altura = self.sprite_andar_direita_1.height
        
        margem_x = 15
        margem_y_topo = altura * 0.6 
        margem_y_fundo = 5
        
        pontos_verificacao = [
            (x + margem_x, y + margem_y_topo), 
            (x + largura - margem_x, y + margem_y_topo),
            (x + margem_x, y + altura - margem_y_fundo), 
            (x + largura - margem_x, y + altura - margem_y_fundo) 
        ]
        
        for ponto_x, ponto_y in pontos_verificacao:
            if self.mapa.verificar_colisao_parede(ponto_x, ponto_y):
                return False
                
        return True

    def _esta_em_acao(self):
        caindo = self.mecanicas_caverna.esta_caindo() if self.mecanicas_caverna else False
        lendo = self.interface_usuario.lendo_pergaminho if self.interface_usuario else False
        return self.mapa.esta_escavando() or self.mapa.esta_investigando() or self._bebendo or caindo or lendo

