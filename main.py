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
from sistema_combate import SistemaCombate
import random

janela = Window(config.LARGURA_JANELA, config.ALTURA_JANELA)
janela.set_title("1001 Rotas")

popup = PopupFimDeJogo(janela)
mouse = janela.get_mouse()

mapa = None
hud = None
jogador = None
combate = None
tempo_acumulado_hud = 0.0

def iniciar_jogo():
    global mapa, hud, jogador, combate, tempo_acumulado_hud
    
    mapa = Mapa(janela)
    mapa.construir()

    hud = InterfaceUsuario(janela)
    combate = SistemaCombate(janela, hud)

    tempo_acumulado_hud = 0.0

    if len(hud.espacos) > 0:
        altura_espaco_hud = hud.espacos[0].height
    else:
        altura_espaco_hud = 0
    jogador_x = mapa.largura_tile
    jogador_y = janela.height - (config.ALTURA_HUD_EM_TILES * mapa.altura_tile) - max(0, altura_espaco_hud)
    jogador = Jogador(jogador_x, jogador_y, janela, mapa, hud=hud)

iniciar_jogo()

while True:
    janela.set_background_color((245, 198, 132))

    teclado = janela.get_keyboard()
    delta_segundos = janela.delta_time()

    if popup.esta_visivel:
        if popup.verificar_clique(mouse):
            iniciar_jogo()
            popup.ocultar()

    if not popup.esta_visivel:
        tempo_acumulado_hud += delta_segundos
        segundos_completos = int(tempo_acumulado_hud)
        if segundos_completos >= 1:
            hud.definir_valores(sede=hud.sede + (4 * segundos_completos), sol=hud.sol + (2 * segundos_completos))
            tempo_acumulado_hud -= segundos_completos

        if (hud.sede >= 1000 or hud.sol >= 1000) and not popup.esta_visivel and not combate.ativo:
            popup.exibir_morte()

        if combate.ativo:
            combate.atualizar(delta_segundos, mouse)
        else:
            jogador.atualizar(teclado, delta_segundos)

            tem_pa = hud.tem_item('pa')
            bonus_escavacao = 3 if tem_pa else 0

            if teclado.key_pressed("SPACE") and not jogador.tem_mensagem_cabeca():
                coluna, linha = jogador.obter_coordenadas_grade(mapa.largura_tile, mapa.altura_tile)
                mapa.iniciar_escavacao(coluna, linha, tem_pa=tem_pa)
            
            terminou, overlay_adicionada, item_encontrado, valor_dado = mapa.atualizar_escavacao(delta_segundos, bonus_dado=bonus_escavacao, tem_pa=tem_pa)
            if terminou:
                chance_combate = (20 - valor_dado) * 5
                if chance_combate > 0:
                    if (1000 - hud.sede) >= 20:
                        roll_combate = random.randint(1, 100)
                        if roll_combate <= chance_combate:
                            combate.iniciar_combate()

                if item_encontrado == 'pa_duplicada':
                     jogador.exibir_mensagem_cabeca("Só posso carregar uma pá...", duration=3.0)
                else:
                    hud.definir_valores(sede=hud.sede + 100)
                    hud.exibir_mensagem('sede', '+100', duration=1.5)
                    
                    if overlay_adicionada:
                        if item_encontrado == 'agua':
                            hud.adicionar_item(config.RECURSOS.get('agua'), 'agua')
                        elif item_encontrado == 'pa':
                            hud.adicionar_item(config.RECURSOS.get('pa'), 'pa')
                    else:
                        jogador.exibir_mensagem_cabeca("Não consegui...", duration=2.0)

                if (hud.sede >= 1000 or hud.sol >= 1000) and not popup.esta_visivel and not combate.ativo:
                    popup.exibir_morte()

            if not jogador.esta_bebendo() and not mapa.esta_escavando():
                for numero_tecla in range(1, min(8, len(hud.espacos)) + 1):
                    if teclado.key_pressed(str(numero_tecla)):
                        indice_espaco = numero_tecla - 1
                        if hud.sobreposicoes_espacos[indice_espaco] is not None:
                            jogador.beber(indice_espaco, duration=3.0)
                        break

    for azulejo in mapa.azulejos:
        azulejo.desenhar()

    jogador.desenhar()

    hud.desenhar()
    
    if combate.ativo:
        combate.desenhar()

    popup.desenhar()

    janela.update()