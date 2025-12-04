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
    - Tenta usar Pygame diretamente para transparência (alpha), com fallback.
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

        superficie_tela = None
        try:
            superficie_tela = self.janela.get_screen()
        except Exception:
            return

        largura, altura = int(self.janela.width), int(self.janela.height)

        try:
            import pygame
            superficie_sobreposicao = pygame.Surface((largura, altura), pygame.SRCALPHA)
            superficie_sobreposicao.fill((0, 0, 0, 160))
            superficie_tela.blit(superficie_sobreposicao, (0, 0))
        except Exception:
            try:
                superficie_tela.fill((0, 0, 0), (0, 0, largura, altura))
            except Exception:
                pass

        padding_largura = int(largura * 0.1)
        padding_altura = int(altura * 0.1)
        painel_x = padding_largura
        painel_y = padding_altura
        largura_painel = largura - padding_largura * 2
        altura_painel = altura - padding_altura * 2

        cor_fundo_painel = (0, 0, 0)
        cor_borda = (255, 255, 255)

        try:
            superficie_tela.fill(cor_borda, (painel_x - 4, painel_y - 4, largura_painel + 8, altura_painel + 8))
            superficie_tela.fill(cor_fundo_painel, (painel_x, painel_y, largura_painel, altura_painel))
        except Exception:
            try:
                superficie_tela.fill(cor_fundo_painel, (painel_x, painel_y, largura_painel, altura_painel))
            except Exception:
                pass

        try:
            texto_mensagem = str(self._texto_mensagem)
            try:
                import pygame
                if not pygame.font.get_init():
                    pygame.font.init()
                fonte_pygame = pygame.font.SysFont(None, 48, bold=True)
                superficie_texto = fonte_pygame.render(texto_mensagem, True, (200, 0, 0))
                retangulo_texto = superficie_texto.get_rect(center=(painel_x + largura_painel / 2, painel_y + altura_painel / 2))
                superficie_tela.blit(superficie_texto, retangulo_texto)
            except Exception:
                largura_estimada = max(1, len(texto_mensagem) * 7)
                altura_estimada = 24
                mensagem_x = int(painel_x + (largura_painel - largura_estimada) / 2)
                mensagem_y = int(painel_y + (altura_painel - altura_estimada) / 2)
                self.janela.draw_text(texto_mensagem, mensagem_x, mensagem_y, size=32, color=(200, 0, 0))
        except Exception:
            pass
