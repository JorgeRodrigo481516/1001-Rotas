"""Mapa - carregar, construir e acessar tiles do cenário.

Responsabilidade:
        - Construir uma grade de tiles que cobre a janela do jogo e expor
            formas simples de acessar um tile por coordenada de grid ou pixel.
"""

from PPlay.sprite import Sprite
import Config
import random


class Tile:
    """Representa uma célula (tile) do mapa.

    Responsabilidade:
        - Manter o sprite base do tile, uma overlay opcional (principal `overlay_sprite`,
          alias `overlay`) e desenhar ambos.

    Contrato (entrada/saída):
        - Entrada: `sprite` (Sprite já carregado), `column` e `row` (inteiros).
        - Saída: métodos `draw()`, `add_overlay(image_path)` e `has_overlay()`.

    Comportamento:
        - `draw()` desenha o sprite base e, se presente, a overlay_sprite (atributo
          principal `overlay_sprite`).
        - `add_overlay()` posiciona a overlay_sprite centralizada no tile.
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
        # guarda o nome
        self.overlay_sprite = overlay_sprite
        self.overlay_path = image_path
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

    def build(self):
        """Construir a grade de tiles que cobre a janela.

        Processo resumido:
        1. Lê `Config.ASSETS['tile_base_pattern']` para obter um exemplo de tile.
        2. Deduz `tile_width`/`tile_height` (se não fornecidos) e armazena em `Config`.
        3. Calcula quantos tiles cabem horizontal/verticalmente.
        4. Para cada célula (coluna, linha) (exceto linhas do HUD) cria um `Tile`.
        """

        base = Config.ASSETS.get('tile_base_pattern')
        if base is None:
            raise RuntimeError('Config.ASSETS["tile_base_pattern"] must be set')

        # carrega um tile de exemplo para obter largura/altura
        sample_sprite = Sprite(base)
        self.tile_width, self.tile_height = sample_sprite.width, sample_sprite.height

        # salva dimensões em Config para outros módulos (ex.: Player)
        Config.TILE_WIDTH, Config.TILE_HEIGHT = self.tile_width, self.tile_height

        num_columns = int(self.janela.width / self.tile_width) + 1
        num_rows = int(self.janela.height / self.tile_height) + 1

        # prepara pattern para arquivos de variação (ex.: …1.png -> …{n}.png)
        # usamos operações de string para obter nome/base e extensão — evita
        # dependência do módulo `os` quando só precisamos dividir filename/ext.
        if '.' in base:
            idx = base.rfind('.')
            base_name = base[:idx]
            ext = base[idx:]
        else:
            base_name = base
            ext = ''
        if '{}' in base:
            filename_pattern = base
        elif base_name.endswith('1'):
            filename_pattern = f"{base_name[:-1]}{{}}{ext}"
        else:
            filename_pattern = f"{base_name}{{}}{ext}"

        # itera linhas e colunas, pulando linhas reservadas ao HUD
        hud_start_row = Config.HUD_HEIGHT_IN_TILES
        pattern_has_placeholder = '{}' in filename_pattern
        for grid_row in range(hud_start_row, num_rows):
            for grid_col in range(num_columns):
                variation_index = random.randint(1, 6)
                tile_path = filename_pattern.format(variation_index) if pattern_has_placeholder else base
                tile_sprite = Sprite(tile_path)
                tile_sprite.x = grid_col * self.tile_width
                tile_sprite.y = grid_row * self.tile_height
                tile_obj = Tile(tile_sprite, grid_col, grid_row)
                self.tiles.append(tile_obj)
                self.tiles_by_coord[(grid_col, grid_row)] = tile_obj

    def get_tile_by_grid(self, col, row):
        """Retorna o objeto Tile na coluna/linha (col, row) ou None se ausente."""
        return self.tiles_by_coord.get((col, row))

    def get_tile_by_pixel(self, px, py):
        """Retorna o Tile que contém o pixel (px, py).

        Lança ValueError se as dimensões do tile não estiverem definidas.
        """
        if not self.tile_width or not self.tile_height:
            raise ValueError('Mapa.tile_width/height must be set')
        return self.get_tile_by_grid(int(px / self.tile_width), int(py / self.tile_height))

    def add_overlay_at(self, col, row, image_path=None):
        """Adiciona uma overlay (overlay_sprite) no tile da posição (col, row).

        Retorna True se adicionou, False caso o tile não exista ou já tenha overlay_sprite.
        """
        tile = self.get_tile_by_grid(col, row)
        if tile:
            return tile.add_overlay(image_path)
        return False
