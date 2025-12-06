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
    - Instanciar passando a 'janela' e o objeto 'hud' (InterfaceUsuario).
    - Chamar 'verificar_e_iniciar_combate(valor_dado)' após ações de risco no mapa.
    - Chamar 'atualizar(delta_time, mouse)' no loop principal se 'ativo' for True.
    - Chamar 'desenhar()' após o desenho do mapa/HUD se 'ativo' for True.

NOTAS DE IMPLEMENTAÇÃO:
    - O combate é modal: quando 'ativo' é True, o jogo deve pausar outras atualizações (exceto HUD).
    - Não acessa diretamente 'hud.sede' ou 'hud.sol' para escrita; usa métodos como 'aplicar_dano_combate'.
    - Inimigos ('tempestade', 'serpente') e parâmetros de balanceamento vêm de 'config.py'.
-------------------------------------------------------------------
"""
from PPlay.gameimage import GameImage
from PPlay.window import Window
import config
import random

class SistemaCombate:
    def __init__(self, janela: Window, hud):
        self.janela = janela
        self.hud = hud
        self.ativo = False
        
        self.bg_combate = GameImage(config.RECURSOS['bg_combate'])
        self.protagonista = GameImage(config.RECURSOS['protagonista_combate'])
        
        self.btn_attack = GameImage(config.RECURSOS['btn_attack'])
        self.btn_defend = GameImage(config.RECURSOS['btn_defend'])
        self.btn_item = GameImage(config.RECURSOS['btn_item'])
        self.btn_run = GameImage(config.RECURSOS['btn_run'])
        
        self.img_tempestade = GameImage(config.RECURSOS['inimigo_tempestade'])
        self.img_serpente = GameImage(config.RECURSOS['inimigo_serpente'])
        
        self.inimigo_atual = None
        self.imune_turnos = 0
        self.mensagem_combate = ""
        self.timer_mensagem = 0
        self.clique_processado = False
        
        self.dados_inimigos = {
            'tempestade': {'img': self.img_tempestade, 'dano_base': config.COMBATE['dano_base_tempestade']},
            'serpente': {'img': self.img_serpente, 'dano_base': config.COMBATE['dano_base_serpente']}
        }
        
        self._posicionar_elementos()

    def _posicionar_elementos(self):
        self.bg_combate.x = (self.janela.width - self.bg_combate.width) / 2
        self.bg_combate.y = (self.janela.height - self.bg_combate.height) / 2 + 20
        
        centro_x = self.bg_combate.x + self.bg_combate.width / 2
        centro_y = self.bg_combate.y + self.bg_combate.height / 2
        
        self.protagonista.x = centro_x - self.protagonista.width - 50
        self.protagonista.y = centro_y - self.protagonista.height / 2 - 30
        
        self.img_tempestade.x = centro_x + 50
        self.img_tempestade.y = centro_y - self.img_tempestade.height / 2 - 30
        
        self.img_serpente.x = centro_x + 50
        self.img_serpente.y = centro_y - self.img_serpente.height / 2 - 30
        
        espacamento = 20
        largura_total_botoes = (self.btn_attack.width + self.btn_defend.width + 
                               self.btn_item.width + self.btn_run.width + espacamento * 3)
        
        inicio_x = self.bg_combate.x + (self.bg_combate.width - largura_total_botoes) / 2
        y_botoes = self.bg_combate.y + self.bg_combate.height - self.btn_attack.height - 30 - 15
        
        self.btn_attack.x = inicio_x
        self.btn_attack.y = y_botoes
        
        self.btn_defend.x = self.btn_attack.x + self.btn_attack.width + espacamento
        self.btn_defend.y = y_botoes
        
        self.btn_item.x = self.btn_defend.x + self.btn_defend.width + espacamento
        self.btn_item.y = y_botoes
        
        self.btn_run.x = self.btn_item.x + self.btn_item.width + espacamento
        self.btn_run.y = y_botoes

    def verificar_e_iniciar_combate(self, valor_dado_escavacao):
        """Verifica se um combate deve ocorrer baseado no resultado da escavação."""
        chance_combate = (config.GAMEPLAY['dado_escavacao'] - valor_dado_escavacao) * 5
        
        if chance_combate > 0:
            # Só inicia combate se o jogador tiver "vida" (sede) suficiente para sobreviver ao menos um pouco
            if self.hud.possui_condicao_para_combate():
                roll_combate = random.randint(1, 100)
                if roll_combate <= chance_combate:
                    self.iniciar_combate()
                    return True
        return False

    def iniciar_combate(self):
        self.ativo = True
        tipo_inimigo = random.choice(['tempestade', 'serpente'])
        self.inimigo_atual = self.dados_inimigos[tipo_inimigo].copy()
        self.imune_turnos = 0
        
        nome_inimigo = tipo_inimigo.capitalize()
        self.mensagens = [(f"Uma {nome_inimigo} apareceu...", config.CORES['branco'])]
        self.timer_mensagem = config.COMBATE['timer_mensagem_curto']
        
        self.clique_processado = False
        self.encerrando_combate = False
        self.timer_encerramento = 0.0

    def atualizar(self, delta_time, mouse):
        if not self.ativo:
            return

        if self.timer_mensagem > 0:
            self.timer_mensagem -= delta_time
            if self.timer_mensagem <= 0:
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
                
                if mouse.is_over_object(self.btn_attack):
                    self._acao_atacar()
                    acao_realizada = True
                elif mouse.is_over_object(self.btn_defend):
                    self._acao_defender()
                    acao_realizada = True
                elif mouse.is_over_object(self.btn_item):
                    if self._acao_item():
                        acao_realizada = True
                elif mouse.is_over_object(self.btn_run):
                    self._acao_fugir()
                    if not self.ativo:
                        return
                    acao_realizada = True
                
                if acao_realizada and self.ativo:
                    self._turno_inimigo()
        else:
            self.clique_processado = False

    def _acao_atacar(self):
        bonus = config.GAMEPLAY['bonus_combate_faca'] if self.hud.tem_item('faca') else 0
        dado = random.randint(1, 20) + bonus
        self.mensagens = [] 
        if dado > config.COMBATE['limiar_critico']:
            self.mensagens.append((f"Crítico! Inimigo derrotado!", config.CORES['dourado'])) # Dourado
            self.timer_mensagem = config.COMBATE['timer_mensagem_critico']
            self.encerrando_combate = True
            self.timer_encerramento = 3.0 
        elif dado > config.COMBATE['limiar_sucesso_parcial']:
            self.mensagens.append((f"Sucesso Parcial. Dano INIMIGO reduzido NESTE COMBATE!", config.CORES['laranja'])) # Laranja
            self.timer_mensagem = config.COMBATE['timer_mensagem_padrao']
            self.inimigo_atual['dano_base'] = int(self.inimigo_atual['dano_base'] / 2)
        else:
            self.mensagens.append((f"Errou o ataque...", config.CORES['cinza'])) # Cinza
            self.timer_mensagem = config.COMBATE['timer_mensagem_padrao']

    def _acao_defender(self):
        bonus = config.GAMEPLAY['bonus_combate_faca'] if self.hud.tem_item('faca') else 0
        dado = random.randint(1, 20) + bonus
        self.mensagens = []
        if dado > config.COMBATE['limiar_defesa']:
            self.imune_turnos = config.COMBATE['turnos_imunidade']
            self.mensagens.append((f"Defesa Perfeita! Imune por {config.COMBATE['turnos_imunidade']} turnos!", config.CORES['verde'])) # Verde
        else:
            self.mensagens.append((f"Falha na defesa...", config.CORES['cinza'])) # Cinza
        self.timer_mensagem = config.COMBATE['timer_mensagem_padrao']

    def _acao_item(self):
        self.mensagens = []
        if not self.hud.tem_item('agua'):
            self.mensagens.append(("Não tem agua...", config.CORES['vermelho'])) # Vermelho
            self.timer_mensagem = config.COMBATE['timer_mensagem_critico']
            return False 
        
        dado = random.randint(1, 20)
        if dado > 9:
            self.hud.aplicar_cura_combate(config.GAMEPLAY['recuperacao_sede_beber'])
            self.hud.remover_item('agua')
            self.mensagens.append((f"Bebeu água!", config.CORES['azul_deepskyblue'])) # Azul DeepSkyBlue
        else:
            self.mensagens.append((f"Derrubou a água...", config.CORES['vermelho_agua'])) # Vermelho claro
            self.hud.remover_item('agua')
        
        self.timer_mensagem = config.COMBATE['timer_mensagem_padrao']
        return True

    def _acao_fugir(self):
        bonus = config.GAMEPLAY['bonus_combate_faca'] if self.hud.tem_item('faca') else 0
        dado = random.randint(1, 20) + bonus
        self.mensagens = []
        if dado > config.COMBATE['limiar_fuga']:
            self.mensagens.append((f"Fugiu com sucesso!", config.CORES['amarelo'])) # Amarelo
            self.timer_mensagem = config.COMBATE['timer_mensagem_critico']
            self.encerrando_combate = True
            self.timer_encerramento = 2.0
        else:
            self.mensagens.append((f"Falha ao fugir...", config.CORES['cinza'])) # Cinza
            self.timer_mensagem = config.COMBATE['timer_mensagem_padrao']

    def _turno_inimigo(self):
        if self.imune_turnos > 0:
            self.imune_turnos -= 1
            return 

        dado = random.randint(1, 20)
        
        if dado >= 10:
            porcentagem = (dado - 9) * 10
            if dado == 20:
                porcentagem = 200
            
            dano_base = self.inimigo_atual['dano_base']
            
            dano_final = int(dano_base * (porcentagem / 100.0))
            
            self.hud.aplicar_dano_combate(dano_final)
            
            if self.hud.verificar_estado_derrota():
                self.encerrando_combate = True
                self.timer_encerramento = 3.0
            
            self.mensagens.append((f"| Inimigo atacou! +{dano_final} Sede", config.CORES['vermelho_claro'])) # Vermelho
            self.timer_mensagem = config.COMBATE['timer_mensagem_critico']
        else:
            self.mensagens.append((f"| Inimigo errou!", config.CORES['verde_claro'])) # Verde claro
            self.timer_mensagem = config.COMBATE['timer_mensagem_critico']

    def desenhar(self):
        if not self.ativo:
            return

        self.bg_combate.draw()
        self.protagonista.draw()
        self.inimigo_atual['img'].draw()
        
        self.btn_attack.draw()
        self.btn_defend.draw()
        self.btn_item.draw()
        self.btn_run.draw()
        
        if self.mensagens:
            x_atual = self.bg_combate.x + 40 + 10
            y_texto = self.bg_combate.y + 40
            
            for texto, cor in self.mensagens:
                self.janela.draw_text(
                    texto, 
                    x_atual, 
                    y_texto, 
                    size=config.UI['tamanho_fonte_combate'], 
                    color=cor, 
                    font_name="Arial", 
                    bold=True
                )
                largura_estimada = len(texto) * 6
                x_atual += largura_estimada
