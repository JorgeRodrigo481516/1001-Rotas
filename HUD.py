"""HUD - visualização de status do jogo.

Responsabilidade:
    - Mostrar ícones, barras e slots no topo da tela.

Contrato (entrada/saída):
    - Entrada: construtor recebe `janela` (com `width` e `height`); valores atualizados via
      `set_values(sede, sol)`.
    - Saída: métodos `set_values(...)` e `draw()`; nenhum retorna valor.

Comportamento:
    - Carrega sprites de `Config.ASSETS`, calcula posições com `calculate_layout()`
      e desenha os sprites em `draw()`.

Regras:
    - Não altera o estado do jogo; `sede` e `sol` ficam limitados a 0..1000.
"""

from PPlay.sprite import Sprite
import Config


class HUD:
    """HUD (Head-Up Display).

    Responsabilidade:
        - Gerenciar a apresentação visual de `sede` e `sol`.

    Contrato (entrada/saída):
        - Entrada: `janela` no construtor.
        - Saída: `set_values` atualiza valores; `draw` desenha o HUD.

    Comportamento:
        - Carrega sprites, calcula layout e desenha os elementos.

    Regras:
        - Valores limitados a 0..1000.
    """

    def __init__(self, janela):
        # Guarda a janela e carrega os sprites usados pelo HUD.
        self.janela = janela
        self.icon_sol = Sprite(Config.ASSETS['hud_sol'])
        self.bar = Sprite(Config.ASSETS['hud_barra'])
        self.icon_sede = Sprite(Config.ASSETS['hud_sede'])
        self.bar2 = Sprite(Config.ASSETS['hud_barra'])

        # Valores mostrados (0..1000). Atualize via set_values().
        self.sede = 10
        self.sol = 10

        # Lista de slots (preenchida em calculate_layout)
        self.slots = []
        self.calculate_layout()

    def calculate_layout(self):
        """Calcular posições dos sprites e criar os slots.

        Responsabilidade:
            - Definir `x`/`y` para ícones, barras e slots.

        Contrato:
            - Entrada: usa sprites carregados e `janela`.
            - Saída: atualiza posições e preenche `self.slots`.

        Comportamento:
            - Usa valores de `Config` quando disponíveis; há fallback simples.

        Regras/Notas:
            - Apenas posiciona; não desenha.
        """

        # 1) Altura do HUD: prefere usar configuração por tile quando disponível.
        tile_h = getattr(Config, 'TILE_HEIGHT', None)
        hud_tiles = getattr(Config, 'HUD_HEIGHT_IN_TILES', None)
        hud_height = (tile_h * hud_tiles) if (tile_h and hud_tiles) else (self.icon_sol.height * 2)

        # posição vertical base
        y = (hud_height - self.icon_sol.height) / 2

        spacing = getattr(Config, 'HUD_ELEMENT_SPACING', 6)
        shift_left = getattr(Config, 'HUD_SHIFT_LEFT', 0)

        total_width = (self.icon_sol.width + self.bar.width + self.icon_sede.width + self.bar2.width) + spacing * 3
        x = ((self.janela.width - total_width) / 2) - shift_left

        # posiciona ícones e barras da esquerda para a direita
        for sprite in (self.icon_sol, self.bar, self.icon_sede, self.bar2):
            sprite.x = x
            sprite.y = y
            x += sprite.width + spacing

        # prepara e posiciona os slots à direita
        tmp = Sprite(Config.ASSETS['slot'])
        slot_w, slot_h = tmp.width, tmp.height
        del tmp

        slots_count = getattr(Config, 'HUD_SLOTS', 8)
        slot_margin_right = getattr(Config, 'HUD_SLOT_RIGHT_MARGIN', 10)
        x_slots = self.janela.width - (slots_count * slot_w) - slot_margin_right
        y_slots = (hud_height - slot_h) / 2

        self.slots = [Sprite(Config.ASSETS['slot']) for _ in range(slots_count)]
        for i, s in enumerate(self.slots):
            s.x = x_slots + i * slot_w
            s.y = y_slots

    def set_values(self, sede=None, sol=None):
        """Atualizar valores mostrados.

        Responsabilidade:
            - Receber `sede` e `sol` e armazená-los (0..1000).

        Contrato:
            - Entrada: `sede` e/ou `sol` (ou `None`).
            - Saída: atualiza atributos internos; não retorna.

        Comportamento:
            - Converte para inteiro e limita a 0..1000.
        """
        if sede is not None:
            # Proteção simples: força número inteiro e limita a 0..1000.
            self.sede = max(0, min(1000, int(sede)))
        if sol is not None:
            self.sol = max(0, min(1000, int(sol)))

    def draw(self):
        """Desenhar o HUD.

        Responsabilidade:
            - Chamar `.draw()` nos sprites na ordem correta.

        Contrato:
            - Entrada: nenhum parâmetro.
            - Saída: desenha na janela; não retorna.

        Comportamento:
            - Desenha elementos principais e depois os slots.
        """
        for sprite in (self.icon_sol, self.bar, self.icon_sede, self.bar2):
            sprite.draw()
        for s in self.slots:
            s.draw()
