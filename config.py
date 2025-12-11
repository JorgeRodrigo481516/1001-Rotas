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
    - 'LARGURA_QUADRICULO' e 'ALTURA_QUADRICULO' são exceções: inicializados como None, 
      são definidos em tempo de execução pelo módulo Mapa.
    - Configurações agrupadas semanticamente: CORES, JOGABILIDADE, COMBATE, INTERFACE_USUARIO.
-------------------------------------------------------------------
"""

LARGURA_JANELA = 800
ALTURA_JANELA = 728



RECURSOS = {
    'padrao_base_quadriculo': "assets/Tiles Superfície do Deserto (6 variações)1.png",
    'padrao_base_quadriculo_caverna': "assets/Tiles Superfície do Caverna(6 variações)1.png",
    'jogador_direita_1': "assets/protagonistaD1.png",
    'jogador_direita_2': "assets/protagonistaD2.png",
    'jogador_esquerda_1': "assets/protagonistaE1.png",
    'jogador_esquerda_2': "assets/protagonistaE2.png",
    'passagem': "assets/passagem.png",
    'painel_sol': "assets/spritesheet HUD sol.png",
    'painel_barra': "assets/spritesheet HUD barra.png",
    'painel_sede': "assets/spritesheet HUD sede.png",
    'espaco_inventario': "assets/spritesheet HUD slot (1).png",
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
    'botao_back': "assets/botao back.png",
    'botao_next': "assets/botao next.png",
    'inimigo_tempestade': "assets/inimigo tempestade.png",
    'inimigo_serpente': "assets/inimigo serpente.png",
    'inimigo_golem': "assets/inimigo golem.png",
    'fundo_morte': "assets/tela morte.png",
    'botao_reiniciar': "assets/botao restart.png",
    'foco': "assets/foco.png",
    'pergaminho': "assets/pergaminho.png",
    'fundo_leitura': "assets/tela combate.png",
}



CORES = {
    'branco': (255, 255, 255),
    'preto': (0, 0, 0),
    'vermelho': (255, 0, 0),
    'vermelho_claro': (255, 50, 50),
    'vermelho_agua': (255, 100, 100),
    'verde': (0, 255, 0),
    'verde_claro': (150, 255, 150),
    'azul_ceu_profundo': (0, 191, 255),
    'azul_real': (65, 105, 225),
    'azul_escuro': (0, 0, 128),
    'amarelo': (255, 255, 0),
    'dourado': (255, 215, 0),
    'laranja': (255, 165, 0),
    'cinza': (200, 200, 200),
    'fundo_janela': (245, 198, 132),
    'texto_investigacao': (0, 100, 200),
    'barra_escavacao_borda': (101, 67, 33),
    'barra_escavacao_fundo': (245, 222, 179),
    'barra_escavacao_preenchimento': (194, 117, 30),
    'barra_bebendo_borda': (0, 0, 128),
    'barra_bebendo_fundo': (224, 255, 255),
    'barra_investigando_borda': (0, 50, 150),
    'barra_investigando_fundo': (180, 220, 240),
    'barra_investigando_preenchimento': (0, 100, 200),
    'barra_entrando_borda': (0, 0, 0),
    'barra_entrando_fundo': (200, 200, 200),
    'barra_entrando_preenchimento': (100, 255, 100),
    'barra_ativando_preenchimento': (148, 0, 211),
    'texto_ativando': (148, 0, 211),
    'azul_runico': (0, 255, 255),
}

JOGABILIDADE = {
    'velocidade_jogador': 70.0,
    'velocidade_animacao_jogador': 0.2,
    'ajuste_posicao_inicial_jogador': 20,
    
    'max_sede': 1000,
    'max_sol': 1000,
    'sede_inicial': 100,
    'sol_inicial': 100,
    'taxa_sede_segundo': 2,
    'taxa_sol_segundo': 1,
    'recuperacao_sede_item': 40,
    'recuperacao_sede_beber': 200,
    'bonus_escavacao_pa': 3,
    'bonus_combate_faca': 3,
    'limiar_sede_combate': 20,
    'duracao_beber': 3.0,
    'duracao_entrada_passagem': 3.0,
    'duracao_escavacao': 2.0,
    'dificuldade_escavacao': 12,
    'dado_escavacao': 20,
    'usos_pa': 6,
    'usos_faca': 9,
    'distribuicao_itens': {'agua': 0.45, 'pa': 0.10, 'faca': 0.10},
    
    'custo_investigacao_sede': 30,
    'custo_investigacao_sol': 30,
    'multiplicador_custo_caverna': 0.5,
    'multiplicador_itens_caverna': 1.0,
    
    'dificuldade_investigacao_diagonal': 15,
    'dificuldade_investigacao_ortogonal': 10,
    'dificuldade_investigacao_centro': 5,
    
    'tempo_mensagem_investigacao': 2.0,
    'intervalo_entre_mensagens': 0.3,
    'atraso_inicial_investigacao': 1.0,
    'atraso_final_investigacao': 1.0,
    'percentual_variacao_2_caverna': 0.15,
    'percentual_variacao_3_caverna': 0.15,
    'percentual_variacao_4_caverna': 0.05,
    'quantidade_runas_caverna': 7,
    'quantidade_pergaminhos': 8,
}

JOGABILIDADE.update({
    'tempo_para_ativar_foco': 0.5,
    'duracao_queda_buraco': 0.5,
    'duracao_ativacao_runa': 6.0,
    'limiar_distancia_centro_buraco': 10,
    'limiar_distancia_centro_runa': 15,
    'num_variacoes_superficie': 6,
})

COMBATE = {
    'dano_base_tempestade': 100,
    'dano_base_serpente': 130,
    'dano_base_golem': 180,
    'limiar_critico': 18,
    'limiar_sucesso_parcial': 9,
    'limiar_defesa': 11,
    'limiar_fuga': 14,
    'limiar_sucesso_item': 9,
    'limiar_acerto_inimigo': 10,
    'turnos_imunidade': 2,
    'multiplicador_chance_combate': 2,
    'penalidade_golem': -2,
    'multiplicador_critico_inimigo': 200,
    'tempo_mensagem_critico': 6.0,
    'tempo_mensagem_padrao': 4.5,
    'tempo_mensagem_curto': 3.0,
}

COMBATE.update({
    'duracao_encerramento_vitoria': 3.0,
    'duracao_encerramento_fuga': 2.0,
})

INTERFACE_USUARIO = {
    'altura_painel_em_quadriculos': 2,
    'deslocamento_esquerda_painel': 180,
    'espacamento_elementos_painel': 10,
    'quantidade_espacos_painel': 8,
    'margem_direita_espaco_painel': 20,
    'margem_interna_esquerda_painel': 7,
    'margem_interna_direita_painel': 4,
    'espacamento_interno_painel': 0,
    
    'tamanho_fonte_padrao': 14,
    'tamanho_fonte_combate': 10,
    'duracao_msg_cabeca_padrao': 2.0,
    'duracao_msg_cabeca_erro': 3.0,
    'duracao_mensagem_feedback': 1.5,
    'deslocamento_y_reiniciar': 70,
    'atraso_clique_morte': 3,
    'imagens_preenchimento_barra': [
        "assets/barra cor 1.png",
        "assets/barra cor 2.png",
        "assets/barra cor 3.png",
        "assets/barra cor 4.png",
        "assets/barra cor 5.png",
        "assets/barra cor 6.png",
        "assets/barra cor 7.png",
        "assets/barra cor 8.png",
    ]
}

MENSAGENS = {
    'erro_pa_duplicada': "Só posso carregar uma pá...",
    'erro_faca_duplicada': "Só posso carregar uma faca...",
    'erro_escavacao_falha': "Não consegui...",
    'investigacao_nada': "Nada",
    'investigacao_template': "{posicao}: {item} {chance}%",
    'investigacao_direcoes': {
        (-1, -1): "Superior Esquerda",
        (0, -1): "Superior Centro",
        (1, -1): "Superior Direita",
        (-1, 0): "Meio Esquerda",
        (0, 0): "Centro",
        (1, 0): "Meio Direita",
        (-1, 1): "Inferior Esquerda",
        (0, 1): "Inferior Centro",
        (1, 1): "Inferior Direita",
    }
}

TIPO_TERRENO_RUNA = 5
TIPO_TERRENO_PAREDE = 3
TIPO_TERRENO_BURACO = 4
TIPO_TERRENO_INIMIGO = 6
