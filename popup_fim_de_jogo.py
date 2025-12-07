"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia a interface gráfica da tela de "Game Over" (Derrota).

RESPONSABILIDADE:
    1. Visualização: Renderizar o background de morte e o botão de reinício.
    2. Interação: Detectar cliques no botão de reinício para resetar o jogo.
    3. Estado Visual: Controlar a visibilidade do popup (exibir/ocultar).

REGRAS DE USO:
    - 'aguardar_clique_apos_morte()' deve ser chamado quando a condição de derrota for confirmada externamente.
    - 'verificar_clique_reiniciar(mouse)' deve ser chamado no loop para processar o reinício.
    - O loop principal deve verificar 'esta_visivel' para pausar a simulação do jogo.

NOTAS DE IMPLEMENTAÇÃO:
    - Atua como uma "View" passiva. Não verifica regras de derrota (Sede/Sol), apenas exibe o resultado.
    - Implementa um delay inicial no clique para evitar reinícios acidentais.
-------------------------------------------------------------------
"""
from PPlay.window import Window
from PPlay.gameimage import GameImage
import config

class JanelaFimDeJogo:
    def __init__(self, janela: Window):
        self.esta_visivel, self.tempo_decorrido_morte = False, 0.0
        
        self.fundo_morte = GameImage(config.RECURSOS['fundo_morte'])
        self.fundo_morte.x = (janela.width - self.fundo_morte.width) / 2
        self.fundo_morte.y = (janela.height - self.fundo_morte.height) / 2

        self.botao_reiniciar = GameImage(config.RECURSOS['botao_reiniciar'])
        self.botao_reiniciar.x = (janela.width - self.botao_reiniciar.width) / 2
        self.botao_reiniciar.y = self.fundo_morte.y + self.fundo_morte.height - config.INTERFACE_USUARIO['deslocamento_y_reiniciar']

    def aguardar_clique_apos_morte(self):
        self.esta_visivel, self.tempo_decorrido_morte = True, 0.0

    def ocultar(self):
        self.esta_visivel = False

    def atualizar(self, tempo_decorrido):
        self.tempo_decorrido_morte += tempo_decorrido

    def verificar_clique_reiniciar(self, mouse):
        return (self.tempo_decorrido_morte >= config.INTERFACE_USUARIO['atraso_clique_morte'] and 
                mouse.is_button_pressed(1) and 
                mouse.is_over_object(self.botao_reiniciar))

    def desenhar(self):
        if self.esta_visivel:
            self.fundo_morte.draw()
            self.botao_reiniciar.draw()
