"""Loop principal e inicialização do jogo.

Responsabilidade:
        - Inicializar os componentes principais do jogo (janela, mapa, HUD, jogador)
            e executar o loop principal responsável por ler entrada, atualizar estado e
            desenhar a cena a cada frame.

Contrato (entrada/saída):
        - Entrada: usa `Config` e módulos (`Mapa`, `Player`, `HUD`) para construir o jogo.
        - Saída: não retorna valores; este módulo inicializa objetos e mantém o loop
            de execução que atualiza a janela até o programa ser finalizado externamente.

Comportamento:
        - A ordem de inicialização é importante: primeiro cria a janela, depois o mapa
            (para conhecer o tamanho dos tiles), o HUD e o jogador. No loop principal,
            o código lê o teclado, atualiza o jogador, aplica ações (ex.: adicionar
            overlay_sprite)
            e redesenha mapa, jogador e HUD na ordem correta.

Regras:
        - Este arquivo deve permanecer uma orquestração simples; a lógica de jogo deve
            ficar nos módulos (`Player`, `Mapa`, `HUD`).

Notas:
        - Os comentários ao longo do código explicam cada etapa para facilitar a
            compreensão.
"""

from PPlay.window import Window

from Mapa import Mapa
from Player import Player
from HUD import HUD
import Config


# Cria a janela do jogo com as dimensões definidas em `Config` e define o título
janela = Window(Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
janela.set_title("1001 Rotas")


# --- Inicializar o mapa ---
# O mapa precisa da referência à janela para calcular quantos tiles cabem.
mapa = Mapa(janela)
mapa.build()  # carrega imagens e monta a lista de tiles


# --- Inicializar o HUD ---
# O HUD desenha informações por cima dos tiles; recebe a janela para saber
# onde posicionar seus elementos.
hud = HUD(janela)


# --- Inicializar o jogador ---
# Calcula a posição inicial do jogador em pixels baseada no tamanho dos tiles
# e na área reservada pelo HUD. `slot.height` protege caso o HUD não tenha slot.
# calcula a altura do slot (caso exista) e a posição inicial do jogador em pixels
slot_height = hud.slot.height if hasattr(hud, 'slot') else 0
player_x = mapa.tile_width
player_y = janela.height - (Config.HUD_HEIGHT_IN_TILES * mapa.tile_height) - max(0, slot_height)
player = Player(player_x, player_y, janela, mapa)


# --- Loop principal ---
while True:
    # pinta o fundo (cor da areia) antes de desenhar os sprites
    janela.set_background_color((245, 198, 132))

    # lê entrada e tempo desde o último frame
    teclado = janela.get_keyboard()
    dt = janela.delta_time()

    # atualiza estado do jogador (movimento e animação) com base na entrada
    player.update(teclado, dt)

    # ação: ao pressionar espaço, adiciona uma overlay (overlay_sprite) no tile atual do jogador
    if teclado.key_pressed("SPACE"):
        col, row = player.get_grid_coords(mapa.tile_width, mapa.tile_height)
        mapa.add_overlay_at(col, row)

    # desenha o mapa (todos os tiles). A ordem aqui garante que o jogador e o HUD
    # sejam desenhados por cima dos tiles.
    for t in mapa.tiles:
        t.draw()

    # desenha o jogador por cima dos tiles
    player.draw()

    # desenha o HUD por cima de tudo
    hud.draw()

    # envia o swap-buffer / atualiza a janela para exibir o frame
    janela.update()