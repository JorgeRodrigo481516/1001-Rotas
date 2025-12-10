"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia o sistema de combate por turnos do jogo, incluindo a lógica de
    batalha, interface gráfica específica e resolução de ações.

RESPONSABILIDADE:
    1. Fluxo de Combate: Gerenciar turnos entre jogador e inimigo.
    2. Ações do Jogador: Processar Ataque, Defesa, Uso de Item e Fuga.
    3. IA do Inimigo: Calcular acertos e danos baseados em RNG.
    4. Integração com HUD: Delegar alterações de estado (Sede/Cura) para a InterfaceUsuario.
    5. Renderização: Desenhar o cenário de combate, sprites e feedback visual (mensagens).
    6. Gatilhos: Determinar probabilidade de início de combate após escavação.

REGRAS DE USO:
    - Instanciar passando a 'janela' e o objeto 'interface' (InterfaceUsuario).
    - Chamar 'verificar_e_iniciar_combate(valor_dado)' após ações de risco no mapa.
    - Chamar 'atualizar(tempo_decorrido, mouse)' no loop principal se 'ativo' for True.
    - Chamar 'desenhar()' após o desenho do mapa/HUD se 'ativo' for True.

NOTAS DE IMPLEMENTAÇÃO:
    - O combate é modal: quando 'ativo' é True, o jogo deve pausar outras atualizações (exceto HUD).
    - Não acessa diretamente 'interface.sede' ou 'interface.sol' para escrita; usa métodos como 'aplicar_dano_combate'.
    - Inimigos ('tempestade', 'serpente') e parâmetros de balanceamento vêm de 'config.py'.
-------------------------------------------------------------------
"""
from PPlay.gameimage import GameImage
from PPlay.window import Window
import config
import random

class SistemaCombate:
    """
    DESCRIÇÃO:
        Implementa um sistema de combate por turnos, com seleção de ações do jogador e resposta do inimigo.

    RESPONSABILIDADE:
        - Gerenciar o fluxo do combate, interpretar cliques em botões e calcular resultados de ações.
        - Integrar com `InterfaceUsuario` para aplicar dano/curas e exibir mensagens.

    REGRAS DE USO:
        - Instanciar com `janela`, `interface` (InterfaceUsuario) e `tela_combate` (popup.TelaCombate).
        - Chamar `verificar_e_iniciar_combate(valor_dado)` após eventos de risco (ex.: escavação).
        - Enquanto `combate_ativo` for True, chamar `atualizar(dt, mouse)` e `desenhar()` no loop principal.

    NOTAS DE IMPLEMENTAÇÃO:
        - Métodos internos lidam com resolução de ações e RNG; mensagens de feedback são mantidas em `self.mensagens`.
    """
    def __init__(self, janela: Window, interface, tela_combate):
        self.janela = janela
        # Store as `interface_usuario` and keep `interface` as alias for compatibility
        self.interface_usuario = interface
        self.combate_ativo = False
        self.tela_combate = tela_combate

        self.tela_combate.atualizar_posicoes()
        self.fundo_combate = self.tela_combate.fundo_combate
        self.protagonista = self.tela_combate.protagonista

        self.botao_atacar = self.tela_combate.botao_atacar
        self.botao_defender = self.tela_combate.botao_defender
        self.botao_item = self.tela_combate.botao_item
        self.botao_fugir = self.tela_combate.botao_fugir

        self.imagem_tempestade = self.tela_combate.imagem_tempestade
        self.imagem_serpente = self.tela_combate.imagem_serpente
        self.imagem_golem = self.tela_combate.imagem_golem

        self.inimigo_atual = None
        self.turnos_imunidade = 0
        self.temporizador_mensagem = 0
        self.clique_processado = False

        self.dados_inimigos = {
            'tempestade': {'imagem': self.imagem_tempestade, 'dano_base': config.COMBATE['dano_base_tempestade']},
            'serpente': {'imagem': self.imagem_serpente, 'dano_base': config.COMBATE['dano_base_serpente']},
            'golem': {'imagem': self.imagem_golem, 'dano_base': config.COMBATE['dano_base_golem']}
        }

        # Posicionamento agora é responsabilidade de `TelaCombate` (popup.py)

    def verificar_e_iniciar_combate(self, valor_dado_escavacao, tipo_mapa='DESERTO'):
        """
        DESCRIÇÃO:
            Calcula a chance de início de combate baseado em `valor_dado_escavacao` e tenta iniciar.

        RESPONSABILIDADE:
            - Verificar se o jogador possui condição para combate e rolar chance; iniciar combate se sorte favorável.

        REGRAS DE USO:
            - Retorna True se o combate foi iniciado, False caso contrário.

        NOTAS DE IMPLEMENTAÇÃO:
            - Utiliza `config.COMBATE['multiplicador_chance_combate']` para ajustar probabilidade.
        """
        chance_combate = (config.JOGABILIDADE['dado_escavacao'] - valor_dado_escavacao) * config.COMBATE['multiplicador_chance_combate']
        
        if chance_combate > 0:
            if self.interface_usuario.possui_condicao_para_combate():
                rolagem_combate = random.randint(1, 100)
                if rolagem_combate <= chance_combate:
                    self.iniciar_combate(tipo_mapa)
                    return True
        return False

    def iniciar_combate(self, tipo_mapa='DESERTO', nome_inimigo=None):
        """
        DESCRIÇÃO:
            Configura estado interno para iniciar um combate com inimigo selecionado/aleatório.

        RESPONSABILIDADE:
            - Escolher inimigo, preparar mensagens iniciais e sinalizar `combate_ativo`.

        REGRAS DE USO:
            - Pode receber `nome_inimigo` explícito ou escolher baseado em `tipo_mapa`.

        NOTAS DE IMPLEMENTAÇÃO:
            - Inicializa `tela_combate` para exibir a interface modal de combate.
        """
        self.combate_ativo = True
        
        if nome_inimigo:
            tipo_inimigo = nome_inimigo
        elif tipo_mapa == 'CAVERNA':
            tipo_inimigo = 'serpente'
        else:
            tipo_inimigo = random.choice(['tempestade', 'serpente'])
            
        self.inimigo_atual = self.dados_inimigos[tipo_inimigo].copy()
        self.inimigo_atual['nome'] = tipo_inimigo
        self.turnos_imunidade = 0
        
        nome_exibicao = tipo_inimigo.capitalize()
        self.mensagens = [(f"Um {nome_exibicao} apareceu...", config.CORES['branco'])]
        self.temporizador_mensagem = config.COMBATE['tempo_mensagem_curto']
        print(f"Apareceu um inimigo! {nome_exibicao}")
        
        self.clique_processado = False
        self.encerrando_combate = False
        self.temporizador_encerramento = 0.0
        self.tela_combate.iniciar_combate(self.inimigo_atual, None, callback_resultado=None)

    def atualizar(self, tempo_decorrido, dispositivo_mouse):
        """
        DESCRIÇÃO:
            Lida com entrada do mouse na UI de combate e atualiza temporizadores/mensagens do combate.

        RESPONSABILIDADE:
            - Processar cliques em botões de ação e acionar consequências (ataque, defesa, item, fugir).

        REGRAS DE USO:
            - Chamado cada frame quando `combate_ativo` for True; recebe `dispositivo_mouse` para detectar cliques.

        NOTAS DE IMPLEMENTAÇÃO:
            - Implementa proteção contra cliques repetidos com `clique_processado`.
        """
        if not self.combate_ativo:
            return

        if self.temporizador_mensagem > 0:
            self.temporizador_mensagem -= tempo_decorrido
            if self.temporizador_mensagem <= 0:
                self.mensagens = []

        if self.encerrando_combate:
            self.temporizador_encerramento -= tempo_decorrido
            if self.temporizador_encerramento <= 0:
                self.combate_ativo = False
                self.encerrando_combate = False
                self.tela_combate.ocultar()
            return

        if dispositivo_mouse.is_button_pressed(1):
            if not self.clique_processado:
                self.clique_processado = True
                acao_realizada = False
                
                if dispositivo_mouse.is_over_object(self.botao_atacar):
                    self._acao_atacar()
                    acao_realizada = True
                elif dispositivo_mouse.is_over_object(self.botao_defender):
                    self._acao_defender()
                    acao_realizada = True
                elif dispositivo_mouse.is_over_object(self.botao_item):
                    if self._acao_item():
                        acao_realizada = True
                elif dispositivo_mouse.is_over_object(self.botao_fugir):
                    self._acao_fugir()
                    if not self.combate_ativo:
                        return
                    acao_realizada = True
                
                if acao_realizada and self.combate_ativo:
                    self._turno_inimigo()
        else:
            self.clique_processado = False

    def _calcular_resultado_dado(self, usar_faca=True):
        bonus_faca_combate = config.JOGABILIDADE['bonus_combate_faca'] if (usar_faca and self.interface_usuario.tem_item('faca')) else 0
        penalidade_por_inimigo_golem = config.COMBATE['penalidade_golem'] if self.inimigo_atual.get('nome') == 'golem' else 0
        
        valor_sorteado_dado = random.randint(1, 20)
        total = valor_sorteado_dado + bonus_faca_combate + penalidade_por_inimigo_golem
        
        return total

    def _acao_atacar(self):
        resultado_lancamento_dado = self._calcular_resultado_dado(usar_faca=True)

        self.mensagens = []
        if resultado_lancamento_dado > config.COMBATE['limiar_critico']:
            self.mensagens.append((f"Crítico! Inimigo derrotado!", config.CORES['dourado'])) # Dourado
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']
            self.encerrando_combate = True
            self.temporizador_encerramento = 3.0 
        elif resultado_lancamento_dado > config.COMBATE['limiar_sucesso_parcial']:
            self.mensagens.append((f"Sucesso Parcial. Dano INIMIGO reduzido NESTE COMBATE!", config.CORES['laranja'])) # Laranja
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']
            self.inimigo_atual['dano_base'] = int(self.inimigo_atual['dano_base'] / 2)
        else:
            self.mensagens.append((f"Errou o ataque...", config.CORES['cinza'])) # Cinza
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']
            if self.interface_usuario:
                self.interface_usuario.consumir_uso_por_nome('faca')

    def _acao_defender(self):
        resultado_lancamento_dado = self._calcular_resultado_dado(usar_faca=True)

        self.mensagens = []
        if resultado_lancamento_dado > config.COMBATE['limiar_defesa']:
            self.turnos_imunidade = config.COMBATE['turnos_imunidade']
            self.mensagens.append((f"Defesa Perfeita! Imune por {config.COMBATE['turnos_imunidade']} turnos!", config.CORES['verde'])) # Verde
        else:
            self.mensagens.append((f"Falha na defesa...", config.CORES['cinza'])) # Cinza
        self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']

    def _acao_item(self):
        self.mensagens = []
        if not self.interface_usuario.tem_item('agua'):
            self.mensagens.append(("Não tem agua...", config.CORES['vermelho'])) # Vermelho
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']
            return False 
        
        valor_sorteado_dado = self._calcular_resultado_dado(usar_faca=False)

        if valor_sorteado_dado > config.COMBATE['limiar_sucesso_item']:
            self.interface_usuario.aplicar_cura_combate(config.JOGABILIDADE['recuperacao_sede_beber'])
            self.interface_usuario.remover_item('agua')
            self.mensagens.append((f"Bebeu água!", config.CORES['azul_ceu_profundo'])) # Azul DeepSkyBlue
        else:
            self.mensagens.append((f"Derrubou a água...", config.CORES['vermelho_agua'])) # Vermelho claro
            self.interface_usuario.remover_item('agua')
        
        self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']
        return True

    def _acao_fugir(self):
        resultado_lancamento_dado = self._calcular_resultado_dado(usar_faca=True)

        self.mensagens = []
        if resultado_lancamento_dado > config.COMBATE['limiar_fuga']:
            self.mensagens.append((f"Fugiu com sucesso!", config.CORES['amarelo'])) # Amarelo
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']
            self.encerrando_combate = True
            self.temporizador_encerramento = 2.0
        else:
            self.mensagens.append((f"Falha ao fugir...", config.CORES['cinza'])) # Cinza
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']

    def _turno_inimigo(self):
        if self.turnos_imunidade > 0:
            self.turnos_imunidade -= 1
            return 

        valor_dado_rolado = random.randint(1, 20)
        
        if valor_dado_rolado >= config.COMBATE['limiar_acerto_inimigo']:
            porcentagem = (valor_dado_rolado - (config.COMBATE['limiar_acerto_inimigo'] - 1)) * 10
            if valor_dado_rolado == 20:
                porcentagem = config.COMBATE['multiplicador_critico_inimigo']
            
            dano_base = self.inimigo_atual['dano_base']
            
            dano_final = int(dano_base * (porcentagem / 100.0))
            
            self.interface_usuario.aplicar_dano_combate(dano_final)
            
            if self.interface_usuario.verificar_se_jogador_morreu():
                self.encerrando_combate = True
                self.temporizador_encerramento = 3.0
            
            self.mensagens.append((f"| Inimigo atacou! +{dano_final} Sede", config.CORES['vermelho_claro'])) # Vermelho
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']
        else:
            self.mensagens.append((f"| Inimigo errou!", config.CORES['verde_claro'])) # Verde claro
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']

    def desenhar(self):
        """
        DESCRIÇÃO:
            Encaminha a renderização para `tela_combate` quando o combate está ativo.

        RESPONSABILIDADE:
            - Mostrar painel de combate, inimigo atual e mensagens de feedback.

        REGRAS DE USO:
            - Chamado no ciclo de desenho do jogo enquanto `combate_ativo` for True.

        NOTAS DE IMPLEMENTAÇÃO:
            - Depende de `tela_combate.desenhar(inimigo_atual, mensagens)` para a renderização real.
        """
        if not self.combate_ativo:
            return
        self.tela_combate.desenhar(inimigo_atual=self.inimigo_atual, mensagens=getattr(self, 'mensagens', None))
