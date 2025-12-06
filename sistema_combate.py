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
    - Chamar 'atualizar(delta_time, mouse)' no loop principal se 'ativo' for True.
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
    def __init__(self, janela: Window, interface):
        self.janela = janela
        self.interface = interface
        self.ativo = False
        
        self.fundo_combate = GameImage(config.RECURSOS['fundo_combate'])
        self.protagonista = GameImage(config.RECURSOS['protagonista_combate'])
        
        self.botao_atacar = GameImage(config.RECURSOS['botao_atacar'])
        self.botao_defender = GameImage(config.RECURSOS['botao_defender'])
        self.botao_item = GameImage(config.RECURSOS['botao_item'])
        self.botao_fugir = GameImage(config.RECURSOS['botao_fugir'])
        
        self.imagem_tempestade = GameImage(config.RECURSOS['inimigo_tempestade'])
        self.imagem_serpente = GameImage(config.RECURSOS['inimigo_serpente'])
        
        self.inimigo_atual = None
        self.turnos_imunidade = 0
        self.mensagem_combate = ""
        self.temporizador_mensagem = 0
        self.clique_processado = False
        
        self.dados_inimigos = {
            'tempestade': {'imagem': self.imagem_tempestade, 'dano_base': config.COMBATE['dano_base_tempestade']},
            'serpente': {'imagem': self.imagem_serpente, 'dano_base': config.COMBATE['dano_base_serpente']}
        }
        
        self._posicionar_elementos()

    def _posicionar_elementos(self):
        self.fundo_combate.x = (self.janela.width - self.fundo_combate.width) / 2
        self.fundo_combate.y = (self.janela.height - self.fundo_combate.height) / 2 + 20
        
        centro_x = self.fundo_combate.x + self.fundo_combate.width / 2
        centro_y = self.fundo_combate.y + self.fundo_combate.height / 2
        
        self.protagonista.x = centro_x - self.protagonista.width - 50
        self.protagonista.y = centro_y - self.protagonista.height / 2 - 30
        
        self.imagem_tempestade.x = centro_x + 50
        self.imagem_tempestade.y = centro_y - self.imagem_tempestade.height / 2 - 30
        
        self.imagem_serpente.x = centro_x + 50
        self.imagem_serpente.y = centro_y - self.imagem_serpente.height / 2 - 30
        
        espacamento = 20
        largura_total_botoes = (self.botao_atacar.width + self.botao_defender.width + 
                               self.botao_item.width + self.botao_fugir.width + espacamento * 3)
        
        inicio_x = self.fundo_combate.x + (self.fundo_combate.width - largura_total_botoes) / 2
        y_botoes = self.fundo_combate.y + self.fundo_combate.height - self.botao_atacar.height - 30 - 15
        
        self.botao_atacar.x = inicio_x
        self.botao_atacar.y = y_botoes
        
        self.botao_defender.x = self.botao_atacar.x + self.botao_atacar.width + espacamento
        self.botao_defender.y = y_botoes
        
        self.botao_item.x = self.botao_defender.x + self.botao_defender.width + espacamento
        self.botao_item.y = y_botoes
        
        self.botao_fugir.x = self.botao_item.x + self.botao_item.width + espacamento
        self.botao_fugir.y = y_botoes

    def verificar_e_iniciar_combate(self, valor_dado_escavacao):
        chance_combate = (config.JOGABILIDADE['dado_escavacao'] - valor_dado_escavacao) * 5
        
        if chance_combate > 0:
            if self.interface.possui_condicao_para_combate():
                roll_combate = random.randint(1, 100)
                if roll_combate <= chance_combate:
                    self.iniciar_combate()
                    return True
        return False

    def iniciar_combate(self):
        self.ativo = True
        tipo_inimigo = random.choice(['tempestade', 'serpente'])
        self.inimigo_atual = self.dados_inimigos[tipo_inimigo].copy()
        self.turnos_imunidade = 0
        
        nome_inimigo = tipo_inimigo.capitalize()
        self.mensagens = [(f"Uma {nome_inimigo} apareceu...", config.CORES['branco'])]
        self.temporizador_mensagem = config.COMBATE['tempo_mensagem_curto']
        
        self.clique_processado = False
        self.encerrando_combate = False
        self.timer_encerramento = 0.0

    def atualizar(self, delta_time, mouse):
        if not self.ativo:
            return

        if self.temporizador_mensagem > 0:
            self.temporizador_mensagem -= delta_time
            if self.temporizador_mensagem <= 0:
                self.mensagens = []

        if self.encerrando_combate:
            self.timer_encerramento -= delta_time
            if self.timer_encerramento <= 0:
                self.ativo = False
                self.encerrando_combate = False
            return

        if mouse.is_button_pressed(1):
            if not self.clique_processado:
                self.clique_processado = True
                acao_realizada = False
                
                if mouse.is_over_object(self.botao_atacar):
                    self._acao_atacar()
                    acao_realizada = True
                elif mouse.is_over_object(self.botao_defender):
                    self._acao_defender()
                    acao_realizada = True
                elif mouse.is_over_object(self.botao_item):
                    if self._acao_item():
                        acao_realizada = True
                elif mouse.is_over_object(self.botao_fugir):
                    self._acao_fugir()
                    if not self.ativo:
                        return
                    acao_realizada = True
                
                if acao_realizada and self.ativo:
                    self._turno_inimigo()
        else:
            self.clique_processado = False

    def _acao_atacar(self):
        bonus = config.JOGABILIDADE['bonus_combate_faca'] if self.interface.tem_item('faca') else 0
        dado = random.randint(1, 20) + bonus
        self.mensagens = [] 
        if dado > config.COMBATE['limiar_critico']:
            self.mensagens.append((f"Crítico! Inimigo derrotado!", config.CORES['dourado'])) # Dourado
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']
            self.encerrando_combate = True
            self.timer_encerramento = 3.0 
        elif dado > config.COMBATE['limiar_sucesso_parcial']:
            self.mensagens.append((f"Sucesso Parcial. Dano INIMIGO reduzido NESTE COMBATE!", config.CORES['laranja'])) # Laranja
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']
            self.inimigo_atual['dano_base'] = int(self.inimigo_atual['dano_base'] / 2)
        else:
            self.mensagens.append((f"Errou o ataque...", config.CORES['cinza'])) # Cinza
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']

    def _acao_defender(self):
        bonus = config.JOGABILIDADE['bonus_combate_faca'] if self.interface.tem_item('faca') else 0
        dado = random.randint(1, 20) + bonus
        self.mensagens = []
        if dado > config.COMBATE['limiar_defesa']:
            self.turnos_imunidade = config.COMBATE['turnos_imunidade']
            self.mensagens.append((f"Defesa Perfeita! Imune por {config.COMBATE['turnos_imunidade']} turnos!", config.CORES['verde'])) # Verde
        else:
            self.mensagens.append((f"Falha na defesa...", config.CORES['cinza'])) # Cinza
        self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']

    def _acao_item(self):
        self.mensagens = []
        if not self.interface.tem_item('agua'):
            self.mensagens.append(("Não tem agua...", config.CORES['vermelho'])) # Vermelho
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']
            return False 
        
        dado = random.randint(1, 20)
        if dado > 9:
            self.interface.aplicar_cura_combate(config.JOGABILIDADE['recuperacao_sede_beber'])
            self.interface.remover_item('agua')
            self.mensagens.append((f"Bebeu água!", config.CORES['azul_deepskyblue'])) # Azul DeepSkyBlue
        else:
            self.mensagens.append((f"Derrubou a água...", config.CORES['vermelho_agua'])) # Vermelho claro
            self.interface.remover_item('agua')
        
        self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']
        return True

    def _acao_fugir(self):
        bonus = config.JOGABILIDADE['bonus_combate_faca'] if self.interface.tem_item('faca') else 0
        dado = random.randint(1, 20) + bonus
        self.mensagens = []
        if dado > config.COMBATE['limiar_fuga']:
            self.mensagens.append((f"Fugiu com sucesso!", config.CORES['amarelo'])) # Amarelo
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']
            self.encerrando_combate = True
            self.timer_encerramento = 2.0
        else:
            self.mensagens.append((f"Falha ao fugir...", config.CORES['cinza'])) # Cinza
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_padrao']

    def _turno_inimigo(self):
        if self.turnos_imunidade > 0:
            self.turnos_imunidade -= 1
            return 

        dado = random.randint(1, 20)
        
        if dado >= 10:
            porcentagem = (dado - 9) * 10
            if dado == 20:
                porcentagem = 200
            
            dano_base = self.inimigo_atual['dano_base']
            
            dano_final = int(dano_base * (porcentagem / 100.0))
            
            self.interface.aplicar_dano_combate(dano_final)
            
            if self.interface.verificar_estado_derrota():
                self.encerrando_combate = True
                self.timer_encerramento = 3.0
            
            self.mensagens.append((f"| Inimigo atacou! +{dano_final} Sede", config.CORES['vermelho_claro'])) # Vermelho
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']
        else:
            self.mensagens.append((f"| Inimigo errou!", config.CORES['verde_claro'])) # Verde claro
            self.temporizador_mensagem = config.COMBATE['tempo_mensagem_critico']

    def desenhar(self):
        if not self.ativo:
            return

        self.fundo_combate.draw()
        self.protagonista.draw()
        self.inimigo_atual['imagem'].draw()
        
        self.botao_atacar.draw()
        self.botao_defender.draw()
        self.botao_item.draw()
        self.botao_fugir.draw()
        
        if self.mensagens:
            x_atual = self.fundo_combate.x + 40 + 10
            y_texto = self.fundo_combate.y + 40
            
            for texto, cor in self.mensagens:
                self.janela.draw_text(
                    texto, 
                    x_atual, 
                    y_texto, 
                    size=config.INTERFACE_USUARIO['tamanho_fonte_combate'], 
                    color=cor, 
                    font_name="Arial", 
                    bold=True
                )
                largura_estimada = len(texto) * 6
                x_atual += largura_estimada
