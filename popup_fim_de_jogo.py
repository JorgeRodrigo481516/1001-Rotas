"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia a interface gráfica da tela de "Game Over" (Derrota).

RESPONSABILIDADE:
    1. Visualização: Renderizar o background de morte e o botão de reinício.
    2. Interação: Detectar cliques no botão de reinício para resetar o jogo.
    3. Estado Visual: Controlar a visibilidade do popup (exibir/ocultar).

REGRAS DE USO:
    - 'exibir_morte()' deve ser chamado quando a condição de derrota for confirmada externamente.
    - 'verificar_clique(mouse)' deve ser chamado no loop para processar o reinício.
    - O loop principal deve verificar 'esta_visivel' para pausar a simulação do jogo.

NOTAS DE IMPLEMENTAÇÃO:
    - Atua como uma "View" passiva. Não verifica regras de derrota (Sede/Sol), apenas exibe o resultado.
    - Implementa um delay inicial no clique para evitar reinícios acidentais.
-------------------------------------------------------------------
"""
from PPlay.window import Window
from PPlay.gameimage import GameImage
import time
import config

class PopupFimDeJogo:
    def __init__(self, janela: Window):
        self.janela = janela
        self.esta_visivel = False
        self.tempo_inicio_morte = 0
        
        self.bg_morte = GameImage(config.RECURSOS['bg_morte'])
        self.btn_restart = GameImage(config.RECURSOS['btn_restart'])
        
        self._atualizar_posicao()

    def _atualizar_posicao(self):
        self.bg_morte.x = (self.janela.width - self.bg_morte.width) / 2
        self.bg_morte.y = (self.janela.height - self.bg_morte.height) / 2
        
        self.btn_restart.x = (self.janela.width - self.btn_restart.width) / 2
        self.btn_restart.y = self.bg_morte.y + self.bg_morte.height - config.UI['offset_restart_y']

    def exibir_morte(self):
        self.esta_visivel = True
        self.tempo_inicio_morte = time.time()

    def ocultar(self):
        self.esta_visivel = False

    def verificar_clique(self, mouse):
        if not self.esta_visivel:
            return False

        if time.time() - self.tempo_inicio_morte < config.UI['delay_clique_morte']:
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
