"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia as mecânicas específicas do ambiente da Caverna, incluindo
    interações com runas, buracos e armadilhas.

RESPONSABILIDADE:
    1. Detecção de Queda: Verificar se o jogador está sobre um buraco e processar a queda.
    2. Ativação de Runas: Controlar a progressão de ativação de runas e suas consequências.
    3. Armadilhas: Revelar tiles de inimigo quando runas de combate são ativadas.
    4. Transições: Gerenciar a entrada/saída entre Deserto e Caverna através da passagem.

REGRAS DE USO:
    - Instanciar passando referências ao jogador, mapa e sistema de combate.
    - Chamar 'atualizar(tempo_decorrido)' a cada frame quando o jogador está na caverna.
    - Métodos retornam estados que devem ser processados pelo main (ex: morreu_por_queda).

NOTAS DE IMPLEMENTAÇÃO:
    - Centraliza toda lógica de gameplay específica da caverna que estava no jogador.py.
    - Utiliza cálculos de distância para verificar se o jogador está no centro de tiles especiais.
-------------------------------------------------------------------
"""
import config


class MecanicasCaverna:
    def __init__(self, jogador, mapa, sistema_combate):
        self.jogador = jogador
        self.mapa = mapa
        self.sistema_combate = sistema_combate
        
        self._esta_em_queda = False
        self._temporizador_queda = 0.0
        self._duracao_queda = config.JOGABILIDADE.get('duracao_queda_buraco', 0.5)
        self.morreu_por_queda = False
        
        self._esta_ativando_runa = False
        self._temporizador_ativacao = 0.0
        self._duracao_ativacao = config.JOGABILIDADE.get('duracao_ativacao_runa', 6.0)
        
        self._esta_entrando_na_passagem = False
        self._temporizador_entrada = 0.0
        self._duracao_entrada = config.JOGABILIDADE['duracao_entrada_passagem']
        self.solicitacao_transicao = False

        self._ja_printou_passagem = False
    
    def atualizar(self, tempo_decorrido, esta_movendo):
        largura_sprite = self.jogador.andar_direita_1.width
        altura_sprite = self.jogador.andar_direita_1.height
        
        posicao_base_sprite_x = self.jogador.posicao_pixel_x + largura_sprite / 2
        posicao_base_sprite_y = self.jogador.posicao_pixel_y + altura_sprite

        coluna_sprite = int(posicao_base_sprite_x / self.mapa.largura_quadriculo)
        linha_sprite = int(posicao_base_sprite_y / self.mapa.altura_quadriculo)
        quadriculo_sprite = self.mapa.obter_quadriculo_por_coordenada_grade(coluna_sprite, linha_sprite)

        self._atualizar_animacao_queda(tempo_decorrido, posicao_base_sprite_x, posicao_base_sprite_y, coluna_sprite, linha_sprite, esta_movendo)
        self._atualizar_ativacao_runa(tempo_decorrido, posicao_base_sprite_x, posicao_base_sprite_y, coluna_sprite, linha_sprite, esta_movendo)
        self._atualizar_entrada_passagem(tempo_decorrido, posicao_base_sprite_x, posicao_base_sprite_y, coluna_sprite, linha_sprite, quadriculo_sprite, esta_movendo)
    
    def _atualizar_animacao_queda(self, tempo_decorrido, posicao_base_sprite_x, posicao_base_sprite_y, coluna_sprite, linha_sprite, esta_movendo):
        eh_buraco = self.mapa.eh_buraco(coluna_sprite, linha_sprite)
        esta_no_centro_buraco = False
        
        if eh_buraco:
            centro_x = (coluna_sprite * self.mapa.largura_quadriculo) + (self.mapa.largura_quadriculo / 2)
            centro_y = (linha_sprite * self.mapa.altura_quadriculo) + (self.mapa.altura_quadriculo / 2)
            distancia = ((posicao_base_sprite_x - centro_x)**2 + (posicao_base_sprite_y - centro_y)**2)**0.5
            if distancia < config.JOGABILIDADE.get('limiar_distancia_centro_buraco', 10): 
                esta_no_centro_buraco = True
        
        if esta_no_centro_buraco:
            self._esta_em_queda = True
            self._temporizador_queda += tempo_decorrido
            if self._temporizador_queda >= self._duracao_queda:
                self.morreu_por_queda = True
                print(f"Caiu em um buraco!")
        else:
            self._esta_em_queda = False
            self._temporizador_queda = 0.0
    
    def _atualizar_ativacao_runa(self, tempo_decorrido, posicao_base_sprite_x, posicao_base_sprite_y, coluna_sprite, linha_sprite, esta_movendo):
        eh_runa = self.mapa.eh_runa(coluna_sprite, linha_sprite)
        esta_no_centro_runa = False
        
        if eh_runa:
            centro_x = (coluna_sprite * self.mapa.largura_quadriculo) + (self.mapa.largura_quadriculo / 2)
            centro_y = (linha_sprite * self.mapa.altura_quadriculo) + (self.mapa.altura_quadriculo / 2)
            distancia = ((posicao_base_sprite_x - centro_x)**2 + (posicao_base_sprite_y - centro_y)**2)**0.5
            if distancia < config.JOGABILIDADE.get('limiar_distancia_centro_runa', 15): 
                esta_no_centro_runa = True

        if esta_no_centro_runa and not esta_movendo:
            self._esta_ativando_runa = True
            self._temporizador_ativacao += tempo_decorrido
            
            if self._temporizador_ativacao >= self._duracao_ativacao:
                self._temporizador_ativacao = 0.0
                self._esta_ativando_runa = False
                
                posicao_atual = (coluna_sprite, linha_sprite)
                if posicao_atual != self.mapa.posicao_runa_final:
                    self.transformar_runa_em_inimigo(coluna_sprite, linha_sprite)
                    print(f"Ativou uma runa! Golem apareceu!")
                    
                    if self.sistema_combate:
                        self.sistema_combate.iniciar_combate(nome_inimigo='golem')
                else:
                    print(f"Ativou a runa final! Venceu!")
        else:
            if esta_movendo:
                self._esta_ativando_runa = False
                self._temporizador_ativacao = 0.0
    
    def _atualizar_entrada_passagem(self, tempo_decorrido, posicao_base_sprite_x, posicao_base_sprite_y, coluna_sprite, linha_sprite, quadriculo_sprite, esta_movendo):
        if esta_movendo:
            self._esta_entrando_na_passagem = False
            self._temporizador_entrada = 0.0
            self._ja_printou_passagem = False
            return
        
        eh_passagem = quadriculo_sprite and getattr(quadriculo_sprite, 'eh_passagem', False)
        tem_sobreposicao = quadriculo_sprite and quadriculo_sprite.tem_sobreposicao()
        esta_no_centro = False

        if eh_passagem and tem_sobreposicao:
            centro_x = (coluna_sprite * self.mapa.largura_quadriculo) + (self.mapa.largura_quadriculo / 2)
            centro_y = (linha_sprite * self.mapa.altura_quadriculo) + (self.mapa.altura_quadriculo / 2)
            distancia = ((posicao_base_sprite_x - centro_x)**2 + (posicao_base_sprite_y - centro_y)**2)**0.5
            if distancia < config.JOGABILIDADE.get('limiar_distancia_centro_runa', 15):
                esta_no_centro = True
                if not self._ja_printou_passagem:
                    print(f"Passagem encontrada! Pressione parado para entrar...")
                    self._ja_printou_passagem = True

        if esta_no_centro:
            self._esta_entrando_na_passagem = True
            self._temporizador_entrada += tempo_decorrido
            if self._temporizador_entrada >= self._duracao_entrada:
                self.solicitacao_transicao = True
                self._temporizador_entrada = 0.0
                self._esta_entrando_na_passagem = False
                self._ja_printou_passagem = False
        else:
            self._esta_entrando_na_passagem = False
            self._temporizador_entrada = 0.0
            self._ja_printou_passagem = False
    
    def transformar_runa_em_inimigo(self, coluna, linha):
        from PPlay.sprite import Sprite
        
        quadriculo = self.mapa.obter_quadriculo_por_coordenada_grade(coluna, linha)
        if not quadriculo:
            return

        caminho_base = config.RECURSOS.get('padrao_base_quadriculo_caverna')
        novo_caminho = caminho_base.replace('1.png', f'{config.TIPO_TERRENO_INIMIGO}.png')
        
        nova_imagem = Sprite(novo_caminho)
        nova_imagem.x = quadriculo.imagem_quadriculo.x
        nova_imagem.y = quadriculo.imagem_quadriculo.y
        
        quadriculo.imagem_quadriculo = nova_imagem
        quadriculo.indice_variacao_terreno = config.TIPO_TERRENO_INIMIGO
    
    def esta_caindo(self):
        return self._esta_em_queda
    
    def progresso_queda(self):
        if not self._esta_em_queda:
            return 0.0
        return min(1.0, self._temporizador_queda / max(1e-6, self._duracao_queda))
    
    def esta_ativando_runa(self):
        return self._esta_ativando_runa
    
    def progresso_ativacao(self):
        if not self._esta_ativando_runa:
            return 0.0
        return min(1.0, self._temporizador_ativacao / max(1e-6, self._duracao_ativacao))
    
    def esta_entrando_passagem(self):
        return self._esta_entrando_na_passagem
    
    def progresso_entrada(self):
        if not self._esta_entrando_na_passagem:
            return 0.0
        return min(1.0, self._temporizador_entrada / max(1e-6, self._duracao_entrada))
    
    def resetar_estado(self):
        self._esta_em_queda = False
        self._temporizador_queda = 0.0
        self.morreu_por_queda = False
        
        self._esta_ativando_runa = False
        self._temporizador_ativacao = 0.0
        
        self._esta_entrando_na_passagem = False
        self._temporizador_entrada = 0.0
        self.solicitacao_transicao = False
        self._ja_printou_passagem = False
