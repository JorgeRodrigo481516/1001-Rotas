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

class PopupFimDeJogo:
    def __init__(self, janela: Window):
        self.janela = janela
        self.esta_visivel = False
        self._texto_mensagem = ""

    def exibir_morte(self):
        self._texto_mensagem = "V o c ê  M o r r e u !  F i m   d e   J o g o"
        self.esta_visivel = True

    def ocultar(self):
        self.esta_visivel = False

    def desenhar(self):
        if not self.esta_visivel:
            return

        largura, altura = int(self.janela.width), int(self.janela.height)

        padding_largura = int(largura * 0.1)
        padding_altura = int(altura * 0.1)
        painel_x = padding_largura
        painel_y = padding_altura
        largura_painel = largura - padding_largura * 2
        altura_painel = altura - padding_altura * 2

        cor_fundo_painel = (0, 0, 0)
        cor_borda = (255, 255, 255)

        tela = self.janela.get_screen()
        tela.fill(cor_borda, (painel_x - 4, painel_y - 4, largura_painel + 8, altura_painel + 8))
        tela.fill(cor_fundo_painel, (painel_x, painel_y, largura_painel, altura_painel))

        texto_mensagem = str(self._texto_mensagem)
        tamanho_fonte = 28
        largura_estimada = len(texto_mensagem) * (tamanho_fonte * 0.4) 
        altura_estimada = tamanho_fonte
        
        mensagem_x = int(painel_x + (largura_painel - largura_estimada) / 2)
        mensagem_y = int(painel_y + (altura_painel - altura_estimada) / 8)
        
        self.janela.draw_text(texto_mensagem, mensagem_x, mensagem_y, size=tamanho_fonte, color=(200, 0, 0), bold=True)
