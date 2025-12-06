"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Repositório central de dados estáticos, constantes de configuração 
    e caminhos de recursos (assets).

RESPONSABILIDADE:
    1. Parâmetros Globais: Resolução, taxas de atualização e dimensões fixas.
    2. Gerenciamento de Assets: Mapeamento centralizado de caminhos de imagens.
    3. Balanceamento: Definição de valores de gameplay (dano, recuperação, chances).
    4. Estilização: Paleta de cores e configurações de UI.

REGRAS DE USO:
    - Este arquivo deve conter APENAS definições de dados (constantes, dicionários).
    - Nenhuma lógica de execução ou classes deve ser implementada aqui.
    - Importado globalmente para garantir consistência de valores.

NOTAS DE IMPLEMENTAÇÃO:
    - 'LARGURA_TILE' e 'ALTURA_TILE' são exceções: inicializados como None, 
      são definidos em tempo de execução pelo módulo Mapa.
    - Configurações agrupadas semanticamente: CORES, JOGABILIDADE, COMBATE, INTERFACE_USUARIO.
-------------------------------------------------------------------
"""

LARGURA_JANELA = 800
ALTURA_JANELA = 600

ALTURA_HUD_EM_TILES = 2
DESLOCAMENTO_ESQUERDA_HUD = 180

ESPACAMENTO_ELEMENTOS_HUD = 10
QUANTIDADE_SLOTS_HUD = 8
MARGEM_DIREITA_SLOT_HUD = 20

PREENCHIMENTO_HUD_PADDING_ESQUERDA = 7
PREENCHIMENTO_HUD_PADDING_DIREITA = 4
ESPACAMENTO_PREENCHIMENTO_HUD = 0

VELOCIDADE_JOGADOR = 70.0
VELOCIDADE_ANIMACAO_JOGADOR = 0.2

RECURSOS = {
    'padrao_base_azulejo': "assets/Tiles Superfície do Deserto (6 variações)1.png",
    'jogador_direita_1': "assets/protagonistaD1.png",
    'jogador_direita_2': "assets/protagonistaD2.png",
    'jogador_esquerda_1': "assets/protagonistaE1.png",
    'jogador_esquerda_2': "assets/protagonistaE2.png",
    'painel_sol': "assets/spritesheet HUD sol.png",
    'painel_barra': "assets/spritesheet HUD barra.png",
    'painel_sede': "assets/spritesheet HUD sede.png",
    'slot': "assets/spritesheet HUD slot (1).png",
    'sobreposicao_padrao': "assets/escavação da superficie do deserto.png",
    'agua': "assets/agua.png",
    'pa': "assets/pa.png",
    'faca': "assets/faca.png",
    'fundo_combate': "assets/tela combate.png",
    'protagonista_combate': "assets/protagonista1.png",
    'botao_atacar': "assets/botao attack.png",
    'botao_defender': "assets/botao defend.png",
    'botao_item': "assets/botao item.png",
    'botao_fugir': "assets/botao run.png",
    'inimigo_tempestade': "assets/inimigo tempestade.png",
    'inimigo_serpente': "assets/inimigo serpente.png",
    'fundo_morte': "assets/tela morte.png",
    'botao_reiniciar': "assets/botao restart.png",
}

IMAGENS_PREENCHIMENTO_BARRA = [
    "assets/barra cor 1.png",
    "assets/barra cor 2.png",
    "assets/barra cor 3.png",
    "assets/barra cor 4.png",
    "assets/barra cor 5.png",
    "assets/barra cor 6.png",
    "assets/barra cor 7.png",
    "assets/barra cor 8.png",
]

LARGURA_TILE = ALTURA_TILE = None

CUSTO_INVESTIGACAO_SEDE = 30
CUSTO_INVESTIGACAO_SOL = 30

DIFICULDADE_INVESTIGACAO_DIAGONAL = 15
DIFICULDADE_INVESTIGACAO_ORTOGONAL = 10
DIFICULDADE_INVESTIGACAO_CENTRO = 5

TEMPO_MENSAGEM_INVESTIGACAO = 2.0
DELAY_ENTRE_MENSAGENS = 0.3
DELAY_INICIAL_INVESTIGACAO = 1.0
DELAY_FINAL_INVESTIGACAO = 1.0

CORES = {
    'branco': (255, 255, 255),
    'preto': (0, 0, 0),
    'vermelho': (255, 0, 0),
    'vermelho_claro': (255, 50, 50),
    'vermelho_agua': (255, 100, 100),
    'verde': (0, 255, 0),
    'verde_claro': (150, 255, 150),
    'azul_deepskyblue': (0, 191, 255),
    'azul_royal': (65, 105, 225),
    'azul_escuro': (0, 0, 128),
    'amarelo': (255, 255, 0),
    'dourado': (255, 215, 0),
    'laranja': (255, 165, 0),
    'cinza': (200, 200, 200),
    'background_janela': (245, 198, 132),
    'texto_investigacao': (50, 0, 100),
    'barra_escavacao_borda': (101, 67, 33),
    'barra_escavacao_fundo': (245, 222, 179),
    'barra_escavacao_preenchimento': (194, 117, 30),
    'barra_bebendo_borda': (0, 0, 128),
    'barra_bebendo_fundo': (224, 255, 255),
    'barra_investigando_borda': (75, 0, 130),
    'barra_investigando_fundo': (230, 230, 250),
    'barra_investigando_preenchimento': (138, 43, 226),
}

JOGABILIDADE = {
    'max_sede': 1000,
    'max_sol': 1000,
    'sede_inicial': 100,
    'sol_inicial': 100,
    'taxa_sede_segundo': 4,
    'taxa_sol_segundo': 2,
    'recuperacao_sede_item': 100,
    'recuperacao_sede_beber': 200,
    'bonus_escavacao_pa': 3,
    'bonus_combate_faca': 3,
    'limiar_sede_combate': 20,
    'duracao_beber': 3.0,
    'duracao_escavacao': 2.0,
    'dificuldade_escavacao': 12,
    'dado_escavacao': 20,
    'distribuicao_itens': {'agua': 0.35, 'pa': 0.05, 'faca': 0.05},
}

COMBATE = {
    'dano_base_tempestade': 100,
    'dano_base_serpente': 130,
    'limiar_critico': 18,
    'limiar_sucesso_parcial': 9,
    'limiar_defesa': 11,
    'limiar_fuga': 14,
    'turnos_imunidade': 2,
    'tempo_mensagem_critico': 6.0,
    'tempo_mensagem_padrao': 4.5,
    'tempo_mensagem_curto': 3.0,
}

INTERFACE_USUARIO = {
    'tamanho_fonte_padrao': 14,
    'tamanho_fonte_combate': 10,
    'duracao_msg_cabeca_padrao': 2.0,
    'duracao_msg_cabeca_erro': 3.0,
    'deslocamento_y_reiniciar': 70,
    'delay_clique_morte': 3,
}
