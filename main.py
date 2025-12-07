"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Ponto de entrada (Entry Point) e orquestrador principal do jogo "1001 Rotas".

RESPONSABILIDADE:
    1. Inicializar a Janela e os subsistemas principais (Mapa, Interface, Jogador, Combate, MecanicasCaverna).
    2. Executar o Game Loop (Loop Principal).
    3. Gerenciar o fluxo global de estados (Jogo, Combate, Game Over).
    4. Coordenar transições entre mapas (Deserto ↔ Caverna) e atualizar referências de subsistemas.
    5. Delegar toda lógica específica para as classes competentes, mantendo papel de orquestrador puro.

REGRAS DE USO:
    - Executar este arquivo diretamente para iniciar o jogo.
    - Atua como controlador central, conectando os eventos de um módulo às ações de outro.

NOTAS DE IMPLEMENTAÇÃO:
    - O jogo roda em loop infinito (while True).
    - Não contém lógica de domínio: escavação processada por Jogador, mecânicas de caverna por MecanicasCaverna.
    - Atualiza referência de mapa em mecanicas_caverna durante transições entre ambientes.
-------------------------------------------------------------------
"""
from PPlay.window import Window

from mapa import Mapa
from jogador import Jogador
from interface_usuario import InterfaceUsuario
import config
from popup_fim_de_jogo import JanelaFimDeJogo
from sistema_combate import SistemaCombate
from mecanicas_caverna import MecanicasCaverna

janela = Window(config.LARGURA_JANELA, config.ALTURA_JANELA)
janela.set_title("1001 Rotas")

janela_fim_jogo = JanelaFimDeJogo(janela)
mouse_entrada = janela.get_mouse()

mapa_deserto = None
mapa_caverna = None
mapa_ativo = None
interface = None
jogador = None
combate = None
controlador_mecanicas_caverna = None

def inicializar_recursos_jogo():
    global mapa_deserto, mapa_caverna, mapa_ativo, interface, jogador, combate, controlador_mecanicas_caverna
    
    if mapa_deserto is None:
        mapa_deserto = Mapa(janela)
        mapa_deserto.construir(tipo='DESERTO')
    else:
        mapa_deserto.resetar_estado()

    if mapa_caverna is not None:
        mapa_caverna.resetar_estado()

    mapa_ativo = mapa_deserto

    interface = InterfaceUsuario(janela, altura_quadriculo=mapa_ativo.altura_quadriculo)
    combate = SistemaCombate(janela, interface)

    jogador = Jogador(None, None, janela, mapa_ativo, interface=interface, sistema_combate=combate)
    
    controlador_mecanicas_caverna = MecanicasCaverna(jogador, mapa_ativo, combate)
    jogador.mecanicas_caverna = controlador_mecanicas_caverna

inicializar_recursos_jogo()
# ---------------------------------------------------------------
print("Jogo iniciado!")
posicao_passagem = mapa_deserto.obter_posicao_passagem()
if posicao_passagem:
    print(f"Passagem em: coluna {posicao_passagem[0]}, linha {posicao_passagem[1]}")
# ---------------------------------------------------------------

while True:
    janela.set_background_color(config.CORES['fundo_janela'])

    teclado = janela.get_keyboard()
    tempo_decorrido = janela.delta_time()

    if janela_fim_jogo.esta_visivel:
        janela_fim_jogo.atualizar(tempo_decorrido)
        if janela_fim_jogo.verificar_clique_reiniciar(mouse_entrada):
            inicializar_recursos_jogo()
            janela_fim_jogo.ocultar()

    if not janela_fim_jogo.esta_visivel:
        interface.atualizar(tempo_decorrido)

        if interface.verificar_se_jogador_morreu() and not janela_fim_jogo.esta_visivel and not combate.combate_ativo:
            janela_fim_jogo.aguardar_clique_apos_morte()
            # ---------------------------------------------------------------
            if interface.sede >= config.JOGABILIDADE['max_sede']:
                print("Morreu de sede!")
            else:
                print("Morreu queimado pelo sol!")
            # ---------------------------------------------------------------

        if combate.combate_ativo:
            combate.atualizar(tempo_decorrido, mouse_entrada)
        else:
            jogador.atualizar(teclado, tempo_decorrido)

            if controlador_mecanicas_caverna.morreu_por_queda and not janela_fim_jogo.esta_visivel:
                janela_fim_jogo.aguardar_clique_apos_morte()

            if controlador_mecanicas_caverna.solicitacao_transicao:
                controlador_mecanicas_caverna.solicitacao_transicao = False
                
                if mapa_ativo == mapa_deserto:
                    if mapa_caverna is None:
                        mapa_caverna = Mapa(janela)
                        posicao_passagem = mapa_deserto.obter_posicao_passagem()
                        mapa_caverna.construir(tipo='CAVERNA', posicao_passagem_anterior=posicao_passagem)
                    
                    mapa_ativo = mapa_caverna
                    interface.definir_multiplicador_custo(config.JOGABILIDADE['multiplicador_custo_caverna'])
                    # ---------------------------------------------------------------
                    print("Entrou na caverna!")
                    # ---------------------------------------------------------------
                else:
                    mapa_ativo = mapa_deserto
                    interface.definir_multiplicador_custo(1.0)
                    # ---------------------------------------------------------------
                    print("Voltou ao deserto!")
                    # ---------------------------------------------------------------
                
                jogador.mapa = mapa_ativo
                controlador_mecanicas_caverna.mapa = mapa_ativo
                posicao_passagem = mapa_ativo.obter_posicao_passagem()
                if posicao_passagem:
                    coluna, linha = posicao_passagem
                    jogador.posicao_pixel_x = coluna * mapa_ativo.largura_quadriculo
                    jogador.posicao_pixel_y = linha * mapa_ativo.altura_quadriculo + config.JOGABILIDADE['ajuste_posicao_inicial_jogador']

            terminou_escavacao, valor_dado = jogador.processar_escavacao(tempo_decorrido)
            investigando_ativo, _ = mapa_ativo.atualizar_investigacao(tempo_decorrido)

            if terminou_escavacao and valor_dado is not None:
                tipo_mapa = getattr(mapa_ativo, 'tipo', 'DESERTO')
                combate.verificar_e_iniciar_combate(valor_dado, tipo_mapa)

                if interface.verificar_se_jogador_morreu() and not janela_fim_jogo.esta_visivel and not combate.combate_ativo:
                    janela_fim_jogo.aguardar_clique_apos_morte()

    mapa_ativo.desenhar()

    jogador.desenhar()

    interface.desenhar()
    
    if combate.combate_ativo:
        combate.desenhar()

    janela_fim_jogo.desenhar()

    janela.update()