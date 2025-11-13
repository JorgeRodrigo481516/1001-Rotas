"""HUD - visualização de status do jogo.

Responsabilidade:
    - Mostrar os ícones, barras de status e slots no topo da tela.

Contrato (entrada/saída):
    - Entrada: construtor recebe `janela` (objeto Window com `width`/`height`).
    - Saída: métodos públicos `set_values(...)`, `draw()` e `show_message(...)`.

Comportamento:
    - Carrega sprites a partir de `Config.ASSETS` e `Config.HUD_BAR_FILLS`.
    - Calcula posições dos elementos com `calculate_layout()` e desenha tudo em `draw()`.
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

        # ícones e barras: sol (esquerda) e sede (direita)
        self.icon_sol = Sprite(Config.ASSETS['hud_sol'])
        self.barra_sol = Sprite(Config.ASSETS['hud_barra'])
        self.icon_sede = Sprite(Config.ASSETS['hud_sede'])
        self.barra_sede = Sprite(Config.ASSETS['hud_barra'])

        # Valores mostrados (0..1000). Atualize via set_values().
        self.sede = 100
        self.sol = 100

        # Lista de slots (preenchida em calculate_layout)
        self.slots = []
        self.calculate_layout()

        # Carrega sprites de preenchimento a partir de `Config.HUD_BAR_FILLS`.
        if not hasattr(Config, 'HUD_BAR_FILLS'):
            raise RuntimeError('Config.HUD_BAR_FILLS must be defined (list of image paths)')

        self.fill_sprites = []
        for path in Config.HUD_BAR_FILLS:
            try:
                sprite = Sprite(path) if path is not None else None
            except Exception:
                # Em caso de falha ao carregar, registramos None e o HUD
                # continuará funcionando (cores ausentes serão puladas).
                sprite = None
            self.fill_sprites.append(sprite)

        # Mensagens temporárias exibidas abaixo das barras (texto e timer em segundos)
        self._message_sede = ""
        self._message_sede_timer = 0.0
        self._message_sol = ""
        self._message_sol_timer = 0.0

    def calculate_layout(self):
        """Calcular posições dos sprites e criar os slots.

        Responsabilidade:
            - Definir as coordenadas (x, y) de ícones, barras e slots do HUD.

        Contrato:
            - Entrada: usa os sprites carregados e tamanho da `janela`.
            - Saída: modifica atributos `.x` e `.y` dos sprites e preenche `self.slots`.

        Comportamento:
            - Centraliza os elementos na largura da janela, aplica espaçamentos e
              calcula onde os slots (ícones à direita) devem ficar.

        Regras/Notas:
            - Não desenha nada; apenas posiciona. Deve ser chamado após carregar sprites.
        """

        # 1) Altura do HUD: prefere usar configuração por tile quando disponível.
        tile_h = getattr(Config, 'TILE_HEIGHT', None)
        hud_tiles = getattr(Config, 'HUD_HEIGHT_IN_TILES', None)
        hud_height = (tile_h * hud_tiles) if (tile_h and hud_tiles) else (self.icon_sol.height * 2)

        # posição vertical base
        y = (hud_height - self.icon_sol.height) / 2

        espaco_entre = getattr(Config, 'HUD_ELEMENT_SPACING', 6)
        deslocamento_esquerda = getattr(Config, 'HUD_SHIFT_LEFT', 0)

        largura_total = (self.icon_sol.width + self.barra_sol.width + self.icon_sede.width + self.barra_sede.width) + espaco_entre * 3
        pos_x = ((self.janela.width - largura_total) / 2) - deslocamento_esquerda

        # posiciona ícones e barras da esquerda para a direita
        for sprite in (self.icon_sol, self.barra_sol, self.icon_sede, self.barra_sede):
            sprite.x = pos_x
            sprite.y = y
            pos_x += sprite.width + espaco_entre

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
        # overlays que podem aparecer sobre os slots (por exemplo: água)
        # cada entrada será um Sprite ou None, alinhado ao slot correspondente
        self.slot_overlays = [None for _ in range(slots_count)]

    def set_values(self, sede=None, sol=None):
        """Atualizar valores mostrados.

        Responsabilidade:
            - Receber novos valores para `sede` e `sol` e armazená-los no HUD.

        Contrato:
            - Entrada: `sede` e/ou `sol` (números) ou `None` para manter o valor atual.
            - Saída: atualiza `self.sede` e/ou `self.sol` (sem retorno).

        Comportamento:
            - Converte entradas para inteiro e limita valores ao intervalo 0..1000.
        """
        if sede is not None:
            # Proteção simples: força número inteiro e limita a 0..1000.
            self.sede = max(0, min(1000, int(sede)))
        if sol is not None:
            self.sol = max(0, min(1000, int(sol)))

    def draw(self):
        """Desenhar o HUD na tela.

        Responsabilidade:
            - Renderizar ícones, barras, preenchimentos e mensagens do HUD.

        Contrato:
            - Entrada: nenhum parâmetro.
            - Saída: desenha diretamente na janela (sem retorno).

        Comportamento:
            - Desenha, nesta ordem: ícones/barras de fundo, preenchimento das barras,
              mensagens temporárias e slots.
        """
        # Desenha ícones e barras de fundo (ordem: ícone, barra, ícone, barra)
        # Primeiro desenha as barras de fundo para que o preenchimento seja sobreposto.
        self.icon_sol.draw()
        self.barra_sol.draw()

        self.icon_sede.draw()
        self.barra_sede.draw()

        # Desenha preenchimento interno baseado nos valores (sol e sede)
        # A função auxiliar abaixo faz esse trabalho para uma barra qualquer.
        def draw_fill_for(bar_sprite, value):
            """Desenha o preenchimento interno da barra.

            Explicação simples:
            - A barra é composta por blocos (imagens em `self.fill_sprites`).
            - Calculamos quantos blocos cabem na barra e quantos devem ser desenhados
              com base no valor (0..1000).
            - Cada bloco recebe uma imagem (cor) que muda por 'segmentos'.
            """
            # se o valor for zero ou negativo, nada a desenhar
            if value <= 0:
                return

            # encontra um exemplo de sprite de preenchimento para ler largura/altura
            exemplo_preenchimento = next((p for p in self.fill_sprites if p is not None), None)
            if exemplo_preenchimento is None:
                return

            largura_bloco = int(exemplo_preenchimento.width)
            altura_bloco = int(exemplo_preenchimento.height)

            # configurações de espaçamento/padding com fallback
            padding_esq = int(getattr(Config, 'HUD_FILL_PADDING_LEFT', 0))
            padding_dir = int(getattr(Config, 'HUD_FILL_PADDING_RIGHT', 0))
            espaco_entre_blocos = int(getattr(Config, 'HUD_FILL_SPACING', 0))

            largura_barra = int(bar_sprite.width)
            largura_util = max(0, largura_barra - padding_esq - padding_dir)

            passo_por_bloco = largura_bloco + espaco_entre_blocos
            if passo_por_bloco <= 0:
                return

            num_blocos = max(1, largura_util // passo_por_bloco)

            # blocos a desenhar proporcional ao valor (0..1000)
            blocos_preenchidos = int((value / 1000.0) * num_blocos)
            blocos_preenchidos = max(0, min(blocos_preenchidos, num_blocos))

            # quantos blocos correspondem a cada segmento de cor (baseado no número de imagens)
            segmentos = max(1, len(self.fill_sprites))
            blocos_por_segmento = max(1, num_blocos // segmentos)

            # posição inicial (esquerda) e vertical (centraliza o bloco na altura da barra)
            x_inicio = bar_sprite.x + padding_esq
            y_inicio = bar_sprite.y + (bar_sprite.height - altura_bloco) / 2

            # desenha blocos da esquerda para a direita
            for indice in range(blocos_preenchidos):
                idx_segmento = min(segmentos - 1, indice // blocos_por_segmento)
                sprite_para_desenhar = self.fill_sprites[idx_segmento]
                if sprite_para_desenhar is None:
                    continue

                pos_x = x_inicio + indice * passo_por_bloco
                sprite_para_desenhar.x = pos_x
                sprite_para_desenhar.y = y_inicio
                sprite_para_desenhar.draw()
        # Desenha preenchimento para o sol (na primeira barra)
        draw_fill_for(self.barra_sol, self.sol)
        # Desenha preenchimento para a sede (na segunda barra)
        draw_fill_for(self.barra_sede, self.sede)

        # atualiza timers de mensagens (usa delta_time da janela)
        try:
            dt = self.janela.delta_time()
        except Exception:
            dt = 0

        if self._message_sede_timer > 0:
            self._message_sede_timer -= dt
            if self._message_sede_timer <= 0:
                self._message_sede = ""
                self._message_sede_timer = 0.0

        if self._message_sol_timer > 0:
            self._message_sol_timer -= dt
            if self._message_sol_timer <= 0:
                self._message_sol = ""
                self._message_sol_timer = 0.0

        # desenha mensagens se existirem (posicionadas abaixo das respectivas barras)
        if self._message_sol:
            # posiciona texto abaixo da primeira barra (sol)
            text_x = int(self.barra_sol.x + (self.barra_sol.width / 2) - (len(self._message_sol) * 3))
            text_y = int(self.barra_sol.y + self.barra_sol.height + 4)
            self.janela.draw_text(self._message_sol, text_x, text_y, size=14, color=(0,0,0))

        if self._message_sede:
            # posiciona texto abaixo da segunda barra (sede)
            text_x = int(self.barra_sede.x + (self.barra_sede.width / 2) - (len(self._message_sede) * 3))
            text_y = int(self.barra_sede.y + self.barra_sede.height + 4)
            self.janela.draw_text(self._message_sede, text_x, text_y, size=14, color=(0,0,0))

        # desenha os slots à direita
        for s in self.slots:
            s.draw()
        # desenha overlays dos slots (se existirem) por cima dos slots
        for overlay in getattr(self, 'slot_overlays', []):
            if overlay is not None:
                overlay.draw()

    def add_item_to_slot(self, image_path):
        """Adiciona uma imagem sobrepondo no primeiro slot vazio (esquerda->direita).

        Retorna True se adicionou com sucesso, False se não houver slot vazio.
        """
        # encontra o primeiro slot vazio
        for i, ov in enumerate(self.slot_overlays):
            if ov is None:
                try:
                    sprite = Sprite(image_path)
                    slot = self.slots[i]
                    # centraliza a overlay sobre o slot
                    sprite.x = slot.x + (slot.width - sprite.width) / 2
                    sprite.y = slot.y + (slot.height - sprite.height) / 2
                    self.slot_overlays[i] = sprite
                    return True
                except Exception:
                    return False
        return False

    def use_slot(self, index):
        """Usa o item no slot `index` (0-based). Se houver um overlay, remove-o
        e retorna True; caso contrário retorna False.
        """
        if index < 0 or index >= len(self.slot_overlays):
            return False
        if self.slot_overlays[index] is None:
            return False
        # remove a overlay do slot
        try:
            self.slot_overlays[index] = None
            return True
        except Exception:
            return False

    def show_message(self, tipo, texto, duration=1.5):
        """Mostrar uma mensagem temporária abaixo da barra especificada.

        tipo: 'sede' ou 'sol'
        texto: string a mostrar
        duration: tempo em segundos para exibir
        """
        if tipo == 'sede':
            self._message_sede = str(texto)
            self._message_sede_timer = float(duration)
        elif tipo == 'sol':
            self._message_sol = str(texto)
            self._message_sol_timer = float(duration)
        else:
            # ignore tipos desconhecidos
            return
