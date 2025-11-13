"""Popup — componente para mensagens centrais (ex.: Morte)

Responsabilidades:
    - Mostrar um popup centralizado cobrindo 80% da janela quando necessário.
    - Expor `show_death()` para ativar o popup de morte e `hide()` para fechá-lo.
    - Fornecer a propriedade `visible` que pode ser consultada pelo loop principal
      para bloquear a atualização do jogo enquanto o popup estiver visível.

Notas:
    - Usa a API de desenho disponível em `janela.get_screen()` e `janela.draw_text()`.
    - Tenta usar `pygame.Surface` com alpha para sobreposição translúcida; caso o
      pygame não esteja disponível, aplica um fallback opaco.
"""

from PPlay.window import Window

class Popup:
    def __init__(self, janela: Window):
        self.janela = janela
        self.visible = False
        self._message = ""

    def show_death(self):
        """Ativa o popup de morte com a mensagem padrão."""
        self._message = "V o c ê  M o r r e u !  F i m   d e   J o g o"
        self.visible = True

    def hide(self):
        """Fecha o popup."""
        self.visible = False

    def draw(self):
        """Desenha o popup se estiver visível.

        Desenha uma sobreposição escura em toda a tela e um painel central
        (80% da largura/altura da janela) com borda e a mensagem centralizada.
        """
        if not self.visible:
            return

        screen = None
        try:
            screen = self.janela.get_screen()
        except Exception:
            # se não pudermos obter a surface, abortamos o desenho
            return

        w, h = int(self.janela.width), int(self.janela.height)

        # 1) desenha overlay translúcida (tenta usar pygame para alpha)
        try:
            import pygame
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
        except Exception:
            # fallback: pintura opaca (mais simples)
            try:
                screen.fill((0, 0, 0), (0, 0, w, h))
            except Exception:
                pass

        # 2) painel central ocupando 80% da janela
        pad_w = int(w * 0.1)
        pad_h = int(h * 0.1)
        panel_x = pad_w
        panel_y = pad_h
        panel_w = w - pad_w * 2
        panel_h = h - pad_h * 2

        # cores do painel — fundo preto pedido pelo usuário
        panel_bg = (0, 0, 0)        # fundo preto
        border = (255, 255, 255)    # borda branca para contraste

        # desenha borda (retângulo maior) e depois fundo (retângulo menor)
        try:
            # borda 4px
            screen.fill(border, (panel_x - 4, panel_y - 4, panel_w + 8, panel_h + 8))
            screen.fill(panel_bg, (panel_x, panel_y, panel_w, panel_h))
        except Exception:
            # se fill falhar, apenas tente desenhar o fundo
            try:
                screen.fill(panel_bg, (panel_x, panel_y, panel_w, panel_h))
            except Exception:
                pass

        # 3) desenha a mensagem centralizada em vermelho e em negrito quando possível
        try:
            text = str(self._message)
            # tenta usar pygame.font para renderizar texto em negrito e centralizado
            try:
                import pygame
                # inicializa o módulo de fontes caso ainda não esteja
                if not pygame.font.get_init():
                    pygame.font.init()
                # tamanho aproximado: 48 para ficar grande no painel
                font = pygame.font.SysFont(None, 48, bold=True)
                text_surf = font.render(text, True, (200, 0, 0))  # vermelho
                # centraliza o texto no painel
                text_rect = text_surf.get_rect(center=(panel_x + panel_w / 2, panel_y + panel_h / 2))
                screen.blit(text_surf, text_rect)
            except Exception:
                # fallback: usar janela.draw_text com cor vermelha e posicionamento aproximado
                est_w = max(1, len(text) * 7)
                est_h = 24
                text_x = int(panel_x + (panel_w - est_w) / 2)
                text_y = int(panel_y + (panel_h - est_h) / 2)
                self.janela.draw_text(text, text_x, text_y, size=32, color=(200, 0, 0))
        except Exception:
            pass
