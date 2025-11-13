"""main.py — inicialização e loop do jogo (versão comentada para iniciantes)

Este arquivo cria os objetos principais do jogo e executa o loop principal.
Ele NÃO contém regras complexas de jogo — essas ficam em outros módulos:
`Mapa` (tiles), `Player` (movimento/animação) e `HUD` (interface).

Resumo do fluxo:
1. Criar a janela (Window).
2. Construir o mapa (gera tiles e calcula tamanhos).
3. Criar o HUD e o jogador (usa as dimensões do mapa quando necessário).
4. Entrar no loop: ler entradas, atualizar estado (jogador, mapa, HUD) e desenhar.

Comentários no código explicam cada passo de forma simples.
"""

from PPlay.window import Window

from Mapa import Mapa
from Player import Player
from HUD import HUD
import Config
from popup import Popup


# Cria a janela do jogo com as dimensões de `Config` e define o título da janela.
# A janela é a superfície onde tudo será desenhado.
janela = Window(Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
janela.set_title("1001 Rotas")


# --- Inicializar o mapa ---
# O mapa usa a janela para decidir quantos tiles cabem na tela. O método
# `build()` carrega imagens e cria os objetos Tile usados no desenho.
mapa = Mapa(janela)
mapa.build()


# --- Inicializar o HUD ---
# HUD = Heads-Up Display: mostra informações como 'sede' e 'sol'. Recebe a
# janela para posicionar seus elementos corretamente sobre a tela.
hud = HUD(janela)

# Usamos esta variável para contar tempo e atualizar o HUD uma vez por segundo.
tempo_acumulado_hud = 0.0


# --- Inicializar o jogador ---
# Aqui calculamos a posição inicial do jogador em pixels. A posição evita que o
# jogador apareça dentro da área usada pelo HUD (parte superior da tela).
if hasattr(hud, 'slots') and len(hud.slots) > 0:
    altura_slot_hud = hud.slots[0].height
else:
    altura_slot_hud = 0
jogador_x = mapa.tile_width
jogador_y = janela.height - (Config.HUD_HEIGHT_IN_TILES * mapa.tile_height) - max(0, altura_slot_hud)
jogador = Player(jogador_x, jogador_y, janela, mapa, hud=hud)

# Popup: componente para mensagens centrais (ex.: Morte)
popup = Popup(janela)


# --- Loop principal ---
while True:
    # pinta o fundo (cor da areia) antes de desenhar os sprites
    janela.set_background_color((245, 198, 132))  # tom de areia

    # lê entrada e tempo desde o último frame
    teclado = janela.get_keyboard()  # entrada do jogador
    delta_segundos = janela.delta_time()  # tempo desde o último frame

    # Se o popup estiver visível (ex.: mensagem de morte), bloqueamos as
    # atualizações de estado do jogo — o jogo fica "pausado" visualmente.
    if not popup.visible:
        # atualiza estado do jogador (movimento e animação) com base na entrada
        jogador.update(teclado, delta_segundos)

    # --- Atualiza HUD automaticamente: a cada 1 segundo incrementamos os valores ---
    # Acumulamos os segundos em `tempo_acumulado_hud`. Quando atingir >= 1.0
    # aplicamos o número inteiro de segundos acumulados (por segurança se dt for grande).
        tempo_acumulado_hud += delta_segundos
        segundos_completos = int(tempo_acumulado_hud)
        if segundos_completos >= 1:
            # Para cada segundo completo, incrementamos os valores do HUD
            for _ in range(segundos_completos):
                hud.set_values(sede=hud.sede + 4, sol=hud.sol + 2)
            # remove os segundos aplicados, mantendo o restante (fração)
            tempo_acumulado_hud -= segundos_completos

        # Se após o incremento algum valor atingiu 1000 ou mais, mostramos o popup
        # de morte e o jogo ficará bloqueado enquanto o popup estiver visível.
        if (hud.sede >= 1000 or hud.sol >= 1000) and not popup.visible:
            popup.show_death()

    # ação: ao pressionar espaço, inicia escavação (delay de 2s). Durante a escavação
    # não reiniciamos outra escavação. Quando o tempo acabar, tentamos adicionar a overlay
    # e só então aplicamos a recompensa (+4 de sede) se a overlay foi realmente criada.
    # Se apertar Espaço, tenta iniciar escavação no tile onde o jogador está
        if teclado.key_pressed("SPACE"):
            col, row = jogador.get_grid_coords(mapa.tile_width, mapa.tile_height)
            iniciou_escavacao = mapa.start_excavation(col, row)
            # `mapa.start_excavation` já verifica se o tile existe e se já tem overlay.
            if iniciou_escavacao:
                # Player.draw mostrará 'Escavando..' enquanto o mapa reportar escavação
                pass

        # atualiza escavação em Mapa (moved logic)
        # atualiza o estado da escavação (retorna se terminou neste frame, se adicionou overlay, e item encontrado)
        terminou, overlay_adicionada, found_item = mapa.update_excavation(delta_segundos)
        if terminou and overlay_adicionada:
            # recompensa por escavar (somente quando a overlay realmente foi criada)
            # agora adiciona +100 de sede ao escavar
            hud.set_values(sede=hud.sede + 100)
            hud.show_message('sede', '+100', duration=1.5)
            # se encontrou um item (ex.: 'agua') adiciona ao HUD no primeiro slot vazio
            try:
                if found_item == 'agua':
                    hud.add_item_to_slot(Config.ASSETS.get('agua'))
            except Exception:
                pass
            # pós-recompensa: checa também condição de morte
            if (hud.sede >= 1000 or hud.sol >= 1000) and not popup.visible:
                popup.show_death()

        # Ativar slots com teclas numéricas 1..8 (1 = slot mais à esquerda)
        # Se houver 'agua' no slot, aplica redução de sede e remove a água do slot.
        try:
            # só inicia beber se jogador não estiver bebendo e nem escavando
            if not jogador.is_drinking() and not (hasattr(mapa, 'is_excavating') and mapa.is_excavating()):
                for key_num in range(1, min(8, len(hud.slots)) + 1):
                    if teclado.key_pressed(str(key_num)):
                        slot_index = key_num - 1
                        # só inicia beber se houver um overlay (item) no slot
                        try:
                            if getattr(hud, 'slot_overlays', [None])[slot_index] is not None:
                                jogador.start_drink(slot_index, duration=3.0)
                        except Exception:
                            pass
                        break
        except Exception:
            pass

    # desenha o mapa (todos os tiles). A ordem aqui garante que o jogador e o HUD
    # sejam desenhados por cima dos tiles.
    # desenha todos os tiles primeiro
    for tile in mapa.tiles:
        tile.draw()

    # desenha o jogador por cima dos tiles
    jogador.draw()

    # desenha o HUD por cima de tudo
    hud.draw()

    # desenha popup (se visível) por cima de tudo — quando visível o jogo fica bloqueado
    popup.draw()

    # envia o swap-buffer / atualiza a janela para exibir o frame
    janela.update()