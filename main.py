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
from popup import TelaMorte, TelaCombate
from sistema_combate import SistemaCombate
from mecanicas_caverna import MecanicasCaverna

janela = Window(config.LARGURA_JANELA, config.ALTURA_JANELA)
janela.set_title("1001 Rotas")

tela_morte = TelaMorte(janela)
mouse_janela = janela.get_mouse()

mapa_deserto = None
mapa_caverna = None
mapa_ativo = None
interface_usuario = None
jogador = None
sistema_combate = None
mecanicas_caverna = None
ja_inicializado = True
investigacao_estava_ativa = False

def inicializar_recursos_do_jogo():
    """
    DESCRIÇÃO:
        Inicializa ou reinicia todos os recursos e subsistemas necessários para rodar o jogo.

    RESPONSABILIDADE:
        1. Criar/Resetar os objetos de `Mapa` (deserto e caverna) e selecionar o `mapa_ativo`.
        2. Inicializar a `InterfaceUsuario`, `Jogador`, `SistemaCombate` e `MecanicasCaverna`.
        3. Garantir que referências cruzadas (ex.: `jogador.mecanicas_caverna`) estejam configuradas.

    REGRAS DE USO:
        - Chamar antes de começar o loop principal ou ao reiniciar o jogo.
        - Pode ser executada múltiplas vezes; deve restaurar o estado para uma partida limpa.

    NOTAS DE IMPLEMENTAÇÃO:
        - A função altera variáveis globais (usa `global`).
        - Se `mapa_deserto` já existir, chama `resetar_estado` para preservar o objeto.
        - Se `mapa_caverna` não existir, será criado apenas quando necessário ao entrar na caverna.
    """
    global ja_inicializado
    global mapa_deserto, mapa_caverna, mapa_ativo, interface_usuario, jogador, sistema_combate, mecanicas_caverna
    
    if mapa_deserto is None:
        mapa_deserto = Mapa(janela)
        mapa_deserto.construir(tipo='DESERTO')
    else:
        mapa_deserto.resetar_estado()
    if mapa_caverna is not None:
        mapa_caverna.resetar_estado()

    mapa_ativo = mapa_deserto

    interface_usuario = InterfaceUsuario(janela, altura_quadriculo=mapa_ativo.altura_quadriculo)
    tela_combate = TelaCombate(janela)
    sistema_combate = SistemaCombate(janela, interface_usuario, tela_combate)

    jogador = Jogador(None, None, janela, mapa_ativo, interface=interface_usuario, sistema_combate=sistema_combate)
    
    mecanicas_caverna = MecanicasCaverna(jogador, mapa_ativo, sistema_combate)
    jogador.mecanicas_caverna = mecanicas_caverna
    


inicializar_recursos_do_jogo()
if hasattr(interface_usuario, 'iniciar_trilha'):
    interface_usuario.iniciar_trilha()

print("Jogo iniciado!")
posicao_passagem = mapa_deserto.obter_posicao_passagem()
if posicao_passagem:
    print(f"Passagem em: coluna {posicao_passagem[0]}, linha {posicao_passagem[1]}")

while True:
    janela.set_background_color(config.CORES['fundo_janela'])

    teclado = janela.get_keyboard()
    tempo_decorrido = janela.delta_time()

    if tela_morte.esta_visivel:
        tela_morte.atualizar(tempo_decorrido)
        if tela_morte.verificar_clique_reiniciar(mouse_janela):
            inicializar_recursos_do_jogo()
            tela_morte.ocultar()

    if not tela_morte.esta_visivel:
        interface_usuario.atualizar(tempo_decorrido)
        resultado_mouse = interface_usuario.processar_input_mouse(mouse_janela)
        if resultado_mouse == 'RESTART':
            inicializar_recursos_do_jogo()
            continue
        if interface_usuario.verificar_se_jogador_morreu() and not sistema_combate.combate_ativo:
            tela_morte.aguardar_clique_apos_morte()
            if interface_usuario.sede >= config.JOGABILIDADE['max_sede']:
                print("Morreu de sede!")
            else:
                print("Morreu queimado pelo sol!")

        if sistema_combate.combate_ativo:
            sistema_combate.atualizar(tempo_decorrido, mouse_janela)
        else:
            jogador.atualizar(teclado, tempo_decorrido)

            if mecanicas_caverna.morreu_por_queda and not tela_morte.esta_visivel:
                tela_morte.aguardar_clique_apos_morte()

            if mecanicas_caverna.pedido_transicao_ambiente:
                mecanicas_caverna.pedido_transicao_ambiente = False
                
                if mapa_ativo == mapa_deserto:
                    if mapa_caverna is None:
                        mapa_caverna = Mapa(janela)
                        posicao_passagem = mapa_deserto.obter_posicao_passagem()
                        mapa_caverna.construir(tipo='CAVERNA', posicao_passagem_anterior=posicao_passagem)
                        if hasattr(mapa_caverna, 'posicao_runa_final') and mapa_caverna.posicao_runa_final is not None:
                            print(f"Runa final em: {mapa_caverna.posicao_runa_final}")
                        else:
                            print("Runa final: desconhecida")
                    
                    mapa_ativo = mapa_caverna
                    if hasattr(mapa_ativo, 'posicao_runa_final') and mapa_ativo.posicao_runa_final is not None:
                        print(f"Entrando na caverna. Runa final em: {mapa_ativo.posicao_runa_final}")
                    else:
                        print("Entrando na caverna. Runa final: desconhecida")
                    interface_usuario.definir_multiplicador_custo(config.JOGABILIDADE['multiplicador_custo_caverna'])
                    print("Entrou na caverna!")
                else:
                    mapa_ativo = mapa_deserto
                    interface_usuario.definir_multiplicador_custo(1.0)
                    print("Voltou ao deserto!")
                
                jogador.mapa = mapa_ativo
                mecanicas_caverna.mapa = mapa_ativo
                posicao_passagem = mapa_ativo.obter_posicao_passagem()
                if posicao_passagem:
                    coluna, linha = posicao_passagem
                    jogador.teleportar_para_passagem(coluna, linha)

            terminou_escavacao, valor_dado = jogador.processar_escavacao(tempo_decorrido)
            investigando_ativo, _ = mapa_ativo.atualizar_investigacao(tempo_decorrido)

            if investigacao_estava_ativa and not investigando_ativo and jogador is not None and interface_usuario is not None:
                interface_usuario.parar_som_investigando(jogador)
            investigacao_estava_ativa = investigando_ativo

            if terminou_escavacao and valor_dado is not None:
                if interface_usuario.verificar_se_jogador_morreu() and not sistema_combate.combate_ativo:
                    tela_morte.aguardar_clique_apos_morte()

    mapa_ativo.desenhar()

    jogador.desenhar()

    interface_usuario.desenhar()
    
    if sistema_combate.combate_ativo:
        sistema_combate.desenhar()

    tela_morte.desenhar()

    janela.update()