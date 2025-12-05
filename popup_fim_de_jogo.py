"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Controla a exibição da tela de "Game Over" ou mensagens modais.

RESPONSABILIDADE:
    1. Renderizar sobreposição escura (dimmer) na tela.
    2. Exibir mensagem de fim de jogo.
    3. Bloquear interação visual quando ativo.

REGRAS DE USO:
    - 'exibir_morte()' ativa o popup.
    - Quando visível, o loop principal geralmente pausa atualizações de jogo.

NOTAS DE IMPLEMENTAÇÃO:
    - Usa PPlay para renderização de texto e primitivas.
-------------------------------------------------------------------
"""
from PPlay.window import Window
from PPlay.gameimage import GameImage
import time

class PopupFimDeJogo:
    def __init__(self, janela: Window):
        self.janela = janela
        self.esta_visivel = False
        self.tempo_inicio_morte = 0
        
        self.bg_morte = GameImage("assets/tela morte.png")
        self.btn_restart = GameImage("assets/botao restart.png")
        
        self._atualizar_posicao()

    def _atualizar_posicao(self):
        self.bg_morte.x = (self.janela.width - self.bg_morte.width) / 2
        self.bg_morte.y = (self.janela.height - self.bg_morte.height) / 2
        
        self.btn_restart.x = (self.janela.width - self.btn_restart.width) / 2
        self.btn_restart.y = self.bg_morte.y + self.bg_morte.height - 70

    def exibir_morte(self):
        self.esta_visivel = True
        self.tempo_inicio_morte = time.time()

    def ocultar(self):
        self.esta_visivel = False

    def verificar_clique(self, mouse):
        if not self.esta_visivel:
            return False

        if time.time() - self.tempo_inicio_morte < 3:
            return False
            
        if mouse.is_button_pressed(1):
            if mouse.is_over_object(self.btn_restart):
                return True
        return False

    def desenhar(self):
        if not self.esta_visivel:
            return

        self.bg_morte.draw()
        self.btn_restart.draw()
