"""Mapa - carregar, construir e acessar tiles do cenário.

Responsabilidade:
        - Construir a grade de tiles que cobre a janela do jogo.
        - Fornecer uma API simples para localizar tiles por (col,row) ou por pixel.

Contrato (uso rápido):
        - Impor que `Config.ASSETS['tile_base_pattern']` esteja definido para criar tiles.
        - Depois de `build()` ser chamado: `tiles`, `tiles_by_coord`, `tile_width` e
            `tile_height` estarão disponíveis.

Notas:
        - Um "Tile" é uma célula da grade com um sprite base e opcionalmente uma
            overlay (por exemplo: um item cavado).
        - As funções de escavação foram centralizadas aqui: `start_excavation`,
            `update_excavation`, `is_excavating` e `excavation_progress`.
"""

from PPlay.sprite import Sprite
import Config
import random


class Tile:
    """Representa uma célula (tile) do mapa.

    Responsabilidade:
        - Guardar o `sprite` base do tile, posição na grade (`column`, `row`) e
          uma `overlay_sprite` opcional (por exemplo: item cavado).

    Contrato (entrada/saída):
        - __init__(sprite, column, row): recebe um `Sprite` já carregado e
          inteiros para coluna/linha.
        - Métodos públicos: `draw()`, `add_overlay(image_path)`, `has_overlay()`.

    Comportamento:
        - `draw()` sempre desenha o sprite base; se `overlay_sprite` existir,
          ela é desenhada por cima, centralizada.

    Regras/Notas:
        - `add_overlay()` retorna False se já existir overlay (evita duplicatas).
        - A overlay é posicionada centralmente dentro dos limites do tile.
    """

    def __init__(self, sprite, column, row):
        # sprite que representa o tile
        self.sprite = sprite
        # nomes mais descritivos: coluna e linha na grade
        self.column = column
        self.row = row
        # overlay principal (pode ser None)
        self.overlay_sprite = None

    def draw(self):
        """Desenha a imagem base e, se houver, desenha a overlay por cima."""
        self.sprite.draw()
        if self.overlay_sprite:
            self.overlay_sprite.draw()

    def has_overlay(self):
        """Retorna True se o tile tem uma overlay_sprite, False caso contrário."""
        return self.overlay_sprite is not None

    def add_overlay(self, image_path=None):
        """Adiciona uma overlay (overlay_sprite) no centro do tile.

        Retorna True se adicionou, False se já existia.
        """
        if self.has_overlay():
            return False
        if image_path is None:
            image_path = Config.ASSETS['overlay_default']
        # cria o sprite da overlay (overlay_sprite) e centraliza dentro do tile
        overlay_sprite = Sprite(image_path)
        overlay_sprite.x = self.sprite.x + (self.sprite.width - overlay_sprite.width) / 2
        overlay_sprite.y = self.sprite.y + (self.sprite.height - overlay_sprite.height) / 2
        # guarda o sprite da overlay no tile
        self.overlay_sprite = overlay_sprite
        return True


class Mapa:
    """Constrói e fornece acesso à grade de tiles do mapa.

    Responsabilidade:
        - Gerar os objetos `Tile` que cobrem a janela e permitir busca por
          coordenadas de grid ou pixel.

    Contrato (entrada/saída):
        - Entrada no construtor: `janela`, `tile_width`/`tile_height` opcionais.
        - Saída: atributos `tiles`, `tiles_by_coord`, `tile_width`, `tile_height`.
    """

    def __init__(self, janela, tile_width=None, tile_height=None):
        """Inicializa o mapa com referência à janela e dimensões dos tiles."""
        self.janela = janela
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.tiles = []
        self.tiles_by_coord = {}
        # estado de escavação (um único processo de escavação por vez)
        # target: tupla (col, row) ou (None, None)
        self._excavating = False
        self._excav_target = (None, None)
        self._excav_timer = 0.0
        self._excav_duration = 2.0  # segundos necessários para escavar

    def build(self):
        """Construir a grade de tiles que cobre a janela.

        Processo resumido:
        1. Lê `Config.ASSETS['tile_base_pattern']` para obter um exemplo de tile.
        2. Deduz `tile_width`/`tile_height` (se não fornecidos) e armazena em `Config`.
        3. Calcula quantos tiles cabem horizontal/verticalmente.
        4. Para cada célula (coluna, linha) (exceto linhas do HUD) cria um `Tile`.
        """

        caminho_base = Config.ASSETS.get('tile_base_pattern')
        if caminho_base is None:
            raise RuntimeError('Config.ASSETS["tile_base_pattern"] must be set')

        # Carrega um sprite de exemplo para determinar a largura/altura do tile
        exemplo = Sprite(caminho_base)
        self.tile_width = exemplo.width
        self.tile_height = exemplo.height

        # Guarda as dimensões em Config para outros módulos (por exemplo Player)
        Config.TILE_WIDTH = self.tile_width
        Config.TILE_HEIGHT = self.tile_height

        # Quantos tiles cabem horizontal e verticalmente (adicionamos +1 para cobrir bordas)
        num_colunas = int(self.janela.width / self.tile_width) + 1
        num_linhas = int(self.janela.height / self.tile_height) + 1

        # Prepara um padrão de filename para variações (ex.: 'tile{} .png')
        # usando operações de string para manter o código portátil e claro.
        if '.' in caminho_base:
            idx = caminho_base.rfind('.')
            base_name = caminho_base[:idx]
            ext = caminho_base[idx:]
        else:
            base_name = caminho_base
            ext = ''
        # Se o caminho original contiver '{}', mantemos esse padrão
        if '{}' in caminho_base:
            padrao_arquivo = caminho_base
        elif base_name.endswith('1'):
            # transforma 'tile1.png' em 'tile{} .png'
            padrao_arquivo = f"{base_name[:-1]}{{}}{ext}"
        else:
            padrao_arquivo = f"{base_name}{{}}{ext}"

        # Itera pelas linhas/colunas, pulando as linhas reservadas ao HUD
        linha_inicio_hud = Config.HUD_HEIGHT_IN_TILES
        usa_placeholder = '{}' in padrao_arquivo

        for linha in range(linha_inicio_hud, num_linhas):
            for coluna in range(num_colunas):
                indice_variacao = random.randint(1, 6)
                caminho_tile = padrao_arquivo.format(indice_variacao) if usa_placeholder else caminho_base

                sprite_tile = Sprite(caminho_tile)
                sprite_tile.x = coluna * self.tile_width
                sprite_tile.y = linha * self.tile_height

                novo_tile = Tile(sprite_tile, coluna, linha)
                self.tiles.append(novo_tile)
                self.tiles_by_coord[(coluna, linha)] = novo_tile

    def get_tile_by_grid(self, col, row):
        """Retorna o objeto Tile na coluna/linha (col, row) ou None se ausente.

        Contrato:
            - Entrada: `col`, `row` inteiros.
            - Saída: `Tile` ou `None`.
        """
        return self.tiles_by_coord.get((col, row))

    def get_tile_by_pixel(self, px, py):
        """Retorna o Tile que contém o pixel (px, py).

        Contrato:
            - Entrada: `px`, `py` coordenadas em pixels.
            - Saída: `Tile` ou `None`.

        Regras:
            - Lança ValueError se `tile_width`/`tile_height` não estiverem definidos
              (necessário para converter pixels → grid).
        """
        if not self.tile_width or not self.tile_height:
            raise ValueError('Mapa.tile_width/height must be set')
        return self.get_tile_by_grid(int(px / self.tile_width), int(py / self.tile_height))

    def add_overlay_at(self, col, row, image_path=None):
        """Adiciona uma overlay (overlay_sprite) no tile da posição (col, row).

        Comportamento:
            - Se o tile existir e não tiver overlay, cria a overlay e retorna True.
            - Caso contrário retorna False (tile ausente ou já tem overlay).
        """
        tile = self.get_tile_by_grid(col, row)
        if tile:
            return tile.add_overlay(image_path)
        return False

    # --- Escavação (moved logic) ---------------------------------------
    def start_excavation(self, col, row):
        """Inicia um processo de escavação no tile (col,row).

        Contrato:
            - Entrada: `col`, `row` inteiros indicando o tile alvo.
            - Saída: True se a escavação começou, False caso contrário.

        Regras / Comportamento:
            - Só é possível iniciar uma escavação se não houver outra em andamento
              e se o tile existir e não tiver overlay.
            - Ao iniciar, o estado interno `_excavating` é marcado como True e o
              timer (`_excav_timer`) é zerado.
        """
        if self._excavating:
            return False
        tile = self.get_tile_by_grid(col, row)
        if tile is None:
            return False
        if tile.has_overlay():
            return False
        # iniciar escavação
        self._excavating = True
        self._excav_target = (col, row)
        self._excav_timer = 0.0
        return True

    def update_excavation(self, dt):
        """Atualiza o timer de escavação. Deve ser chamado a cada frame com dt.

        Contrato:
            - Entrada: `dt` (float) tempo em segundos desde o último frame.
            - Saída: tupla `(finished, added)`:
                * finished (bool): True se o processo terminou neste passo.
                * added (bool): True se uma overlay foi efetivamente adicionada.

        Notas:
            - Retorna (False, False) imediatamente se não houver escavação em andamento.
            - Quando o timer atinge `_excav_duration` a overlay é tentada e o
              estado de escavação é resetado.
        """
        if not self._excavating:
            return (False, False, None)
        self._excav_timer += dt
        if self._excav_timer < self._excav_duration:
            return (False, False, None)
        # tempo atingido: tenta adicionar overlay no tile alvo
        col, row = self._excav_target
        added = self.add_overlay_at(col, row)
        # reset estado
        self._excavating = False
        self._excav_target = (None, None)
        self._excav_timer = 0.0
        # Decide se o jogador encontrou um item (ex.: água) — 20% de chance quando adicionou overlay
        found_item = None
        try:
            # 70% chance de encontrar água quando a overlay foi adicionada
            if added and random.random() < 0.70:
                found_item = 'agua'
        except Exception:
            found_item = None
        return (True, bool(added), found_item)

    def is_excavating(self):
        """Retorna True se houver uma escavação em andamento.

        Uso: chamado por outras partes do jogo (ex.: `Player.draw()`) para bloquear
        movimento ou para desenhar barra de progresso.
        """
        return self._excavating

    def excavation_progress(self):
        """Retorna progresso da escavação (float 0.0..1.0).

        Comportamento:
            - Se não houver escavação retorna 0.0.
            - Se houver, divide `_excav_timer` por `_excav_duration` e limita em 1.0.
        """
        if not self._excavating:
            return 0.0
        return min(1.0, self._excav_timer / max(1e-6, self._excav_duration))
