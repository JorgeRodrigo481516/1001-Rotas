"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Ponto de entrada (Entry Point) e orquestrador principal do jogo "1001 Rotas".

RESPONSABILIDADE:
    1. Inicializar a Janela e os subsistemas principais (Mapa, HUD, Jogador, Combate).
    2. Executar o Game Loop (Loop Principal).
    3. Gerenciar o fluxo global de estados (Jogo, Combate, Game Over).
    4. Delegar a lógica específica para as classes competentes (Mapa, Jogador, etc.).

REGRAS DE USO:
    - Executar este arquivo diretamente para iniciar o jogo.
    - Atua como controlador central, conectando os eventos de um módulo às ações de outro.

NOTAS DE IMPLEMENTAÇÃO:
    - O jogo roda em loop infinito (while True).
    - A lógica de regras de negócio (ex: o que acontece ao achar um item) foi movida
      para as classes de entidade (Jogador, InterfaceUsuario), mantendo este arquivo
      focado apenas na coordenação.
-------------------------------------------------------------------
"""
from PPlay.window import Window

from mapa import Mapa
from jogador import Jogador
from interface_usuario import InterfaceUsuario
import config
from popup_fim_de_jogo import PopupFimDeJogo
from sistema_combate import SistemaCombate

janela = Window(config.LARGURA_JANELA, config.ALTURA_JANELA)
janela.set_title("1001 Rotas")

janela_fim_jogo = PopupFimDeJogo(janela)
mouse_entrada = janela.get_mouse()

mapa = None
interface = None
jogador = None
combate = None

def iniciar_jogo():
    global mapa, interface, jogador, combate
    
    mapa = Mapa(janela)
    mapa.construir()

    interface = InterfaceUsuario(janela)
    combate = SistemaCombate(janela, interface)

    jogador = Jogador(None, None, janela, mapa, interface=interface)

iniciar_jogo()

while True:
    janela.set_background_color(config.CORES['background_janela'])

    teclado = janela.get_keyboard()
    delta_segundos = janela.delta_time()

    if janela_fim_jogo.esta_visivel:
        if janela_fim_jogo.verificar_clique(mouse_entrada):
            iniciar_jogo()
            janela_fim_jogo.ocultar()

    if not janela_fim_jogo.esta_visivel:
        interface.atualizar(delta_segundos)

        if interface.verificar_estado_derrota() and not janela_fim_jogo.esta_visivel and not combate.ativo:
            janela_fim_jogo.exibir_morte()

        mensagem_investigacao = ""
        if combate.ativo:
            combate.atualizar(delta_segundos, mouse_entrada)
        else:
            jogador.atualizar(teclado, delta_segundos)

            tem_pa = interface.tem_item('pa')
            tem_faca = interface.tem_item('faca')
            
            terminou, overlay_adicionada, item_encontrado, valor_dado = mapa.atualizar_escavacao(delta_segundos, tem_pa=tem_pa, tem_faca=tem_faca)
            investigando_ativo, _ = mapa.atualizar_investigacao(delta_segundos)

            if terminou:
                combate.verificar_e_iniciar_combate(valor_dado)
                jogador.processar_recompensa_escavacao(item_encontrado, overlay_adicionada)

                if interface.verificar_estado_derrota() and not janela_fim_jogo.esta_visivel and not combate.ativo:
                    janela_fim_jogo.exibir_morte()

    mapa.desenhar()

    jogador.desenhar()

    interface.desenhar()
    
    if combate.ativo:
        combate.desenhar()

    janela_fim_jogo.desenhar()

    janela.update()