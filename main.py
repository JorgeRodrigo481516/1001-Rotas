"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Ponto de entrada (Entry Point) do jogo "1001 Rotas".

RESPONSABILIDADE:
    1. Inicializar a Janela, o Mapa, o Jogador e a Interface (HUD).
    2. Executar o Game Loop (Loop Principal).
    3. Gerenciar o tempo (delta_time) e inputs globais.
    4. Orquestrar a comunicação entre os módulos.

REGRAS DE USO:
    - Executar este arquivo diretamente para iniciar o jogo.
    - A ordem de inicialização é crítica: Janela -> Mapa -> HUD -> Jogador.

NOTAS DE IMPLEMENTAÇÃO:
    - O jogo roda em loop infinito (while True).
    - Gerencia a condição de vitória/derrota através do PopupFimDeJogo.
-------------------------------------------------------------------
"""
from PPlay.window import Window

from mapa import Mapa
from jogador import Jogador
from interface_usuario import InterfaceUsuario
import config
from popup_fim_de_jogo import PopupFimDeJogo

janela = Window(config.LARGURA_JANELA, config.ALTURA_JANELA)
janela.set_title("1001 Rotas")

mapa = Mapa(janela)
mapa.construir()

hud = InterfaceUsuario(janela)

tempo_acumulado_hud = 0.0

if hasattr(hud, 'espacos') and len(hud.espacos) > 0:
    altura_espaco_hud = hud.espacos[0].height
else:
    altura_espaco_hud = 0
jogador_x = mapa.largura_tile
jogador_y = janela.height - (config.ALTURA_HUD_EM_TILES * mapa.altura_tile) - max(0, altura_espaco_hud)
jogador = Jogador(jogador_x, jogador_y, janela, mapa, hud=hud)

popup = PopupFimDeJogo(janela)

while True:
    janela.set_background_color((245, 198, 132))

    teclado = janela.get_keyboard()
    delta_segundos = janela.delta_time()

    if not popup.esta_visivel:
        jogador.atualizar(teclado, delta_segundos)

        tempo_acumulado_hud += delta_segundos
        segundos_completos = int(tempo_acumulado_hud)
        if segundos_completos >= 1:
            for _ in range(segundos_completos):
                hud.definir_valores(sede=hud.sede + 4, sol=hud.sol + 2)
            tempo_acumulado_hud -= segundos_completos

        if (hud.sede >= 1000 or hud.sol >= 1000) and not popup.esta_visivel:
            popup.exibir_morte()

        if teclado.key_pressed("SPACE"):
            coluna, linha = jogador.obter_coordenadas_grade(mapa.largura_tile, mapa.altura_tile)
            iniciou_escavacao = mapa.iniciar_escavacao(coluna, linha)
            if iniciou_escavacao:
                pass

        terminou, overlay_adicionada, item_encontrado = mapa.atualizar_escavacao(delta_segundos)
        if terminou and overlay_adicionada:
            hud.definir_valores(sede=hud.sede + 100)
            hud.exibir_mensagem('sede', '+100', duration=1.5)
            try:
                if item_encontrado == 'agua':
                    hud.adicionar_item(config.RECURSOS.get('agua'))
            except Exception:
                pass
            if (hud.sede >= 1000 or hud.sol >= 1000) and not popup.esta_visivel:
                popup.exibir_morte()

        try:
            if not jogador.esta_bebendo() and not (hasattr(mapa, 'esta_escavando') and mapa.esta_escavando()):
                for numero_tecla in range(1, min(8, len(hud.espacos)) + 1):
                    if teclado.key_pressed(str(numero_tecla)):
                        indice_espaco = numero_tecla - 1
                        try:
                            if getattr(hud, 'sobreposicoes_espacos', [None])[indice_espaco] is not None:
                                jogador.beber(indice_espaco, duration=3.0)
                        except Exception:
                            pass
                        break
        except Exception:
            pass

    for azulejo in mapa.azulejos:
        azulejo.desenhar()

    jogador.desenhar()

    hud.desenhar()

    popup.desenhar()

    janela.update()