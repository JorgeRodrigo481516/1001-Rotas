import random
from PPlay.gameimage import GameImage
from PPlay.window import Window

class SistemaCombate:
    def __init__(self, janela: Window, hud):
        self.janela = janela
        self.hud = hud
        self.ativo = False
        
        self.bg_combate = GameImage("assets/tela combate.png")
        self.protagonista = GameImage("assets/protagonista1.png")
        
        self.btn_attack = GameImage("assets/botao attack.png")
        self.btn_defend = GameImage("assets/botao defend.png")
        self.btn_item = GameImage("assets/botao item.png")
        self.btn_run = GameImage("assets/botao run.png")
        
        self.img_tempestade = GameImage("assets/inimigo tempestade.png")
        self.img_serpente = GameImage("assets/inimigo serpente.png")
        
        self.inimigo_atual = None
        self.imune_turnos = 0
        self.mensagem_combate = ""
        self.timer_mensagem = 0
        self.clique_processado = False
        
        self.dados_inimigos = {
            'tempestade': {'img': self.img_tempestade, 'dano_base': 100},
            'serpente': {'img': self.img_serpente, 'dano_base': 130}
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

    def iniciar_combate(self):
        self.ativo = True
        tipo_inimigo = random.choice(['tempestade', 'serpente'])
        self.inimigo_atual = self.dados_inimigos[tipo_inimigo].copy()
        self.imune_turnos = 0
        self.mensagens = [] 
        self.timer_mensagem = 6.0
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
        dado = random.randint(1, 20)
        self.mensagens = [] 
        if dado > 18:
            self.mensagens.append((f"Crítico! Inimigo derrotado!", (255, 215, 0))) # Dourado
            self.timer_mensagem = 6.0
            self.encerrando_combate = True
            self.timer_encerramento = 3.0 
        elif dado > 9:
            self.mensagens.append((f"Sucesso Parcial. Dano INIMIGO reduzido NESTE COMBATE!", (255, 165, 0))) # Laranja
            self.timer_mensagem = 4.5
            self.inimigo_atual['dano_base'] = int(self.inimigo_atual['dano_base'] / 2)
        else:
            self.mensagens.append((f"Errou o ataque...", (200, 200, 200))) # Cinza
            self.timer_mensagem = 4.5

    def _acao_defender(self):
        dado = random.randint(1, 20)
        self.mensagens = []
        if dado > 11:
            self.imune_turnos = 2
            self.mensagens.append((f"Defesa Perfeita! Imune por 2 turnos!", (0, 255, 0))) # Verde
        else:
            self.mensagens.append((f"Falha na defesa...", (200, 200, 200))) # Cinza
        self.timer_mensagem = 4.5

    def _acao_item(self):
        self.mensagens = []
        if not self.hud.tem_item('agua'):
            self.mensagens.append(("Não tem agua...", (255, 0, 0))) # Vermelho
            self.timer_mensagem = 6.0
            return False 
        
        dado = random.randint(1, 20)
        if dado > 9:
            self.hud.definir_valores(sede=max(0, self.hud.sede - 200))
            self.hud.remover_item('agua')
            self.mensagens.append((f"Bebeu água!", (0, 191, 255))) # Azul DeepSkyBlue
        else:
            self.mensagens.append((f"Derrubou a água...", (255, 100, 100))) # Vermelho claro
            self.hud.remover_item('agua')
        
        self.timer_mensagem = 4.5
        return True

    def _acao_fugir(self):
        dado = random.randint(1, 20)
        self.mensagens = []
        if dado > 14:
            self.mensagens.append((f"Fugiu com sucesso!", (255, 255, 0))) # Amarelo
            self.timer_mensagem = 6.0
            self.encerrando_combate = True
            self.timer_encerramento = 2.0
        else:
            self.mensagens.append((f"Falha ao fugir...", (200, 200, 200))) # Cinza
            self.timer_mensagem = 4.5

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
            
            self.hud.definir_valores(sede=self.hud.sede + dano_final)
            
            if self.hud.sede >= 1000:
                self.encerrando_combate = True
                self.timer_encerramento = 3.0
            
            self.mensagens.append((f"| Inimigo atacou! +{dano_final} Sede", (255, 50, 50))) # Vermelho
            self.timer_mensagem = 6.0
        else:
            self.mensagens.append((f"| Inimigo errou!", (150, 255, 150))) # Verde claro
            self.timer_mensagem = 6.0

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
                    size=10, 
                    color=cor, 
                    font_name="Arial", 
                    bold=True
                )
                largura_estimada = len(texto) * 6
                x_atual += largura_estimada
