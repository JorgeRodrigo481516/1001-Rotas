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
    """
    DESCRIÇÃO:
        Encapsula comportamentos específicos do ambiente de caverna (quedas, runas, passagens).

    RESPONSABILIDADE:
        - Detectar e processar quedas em buracos, ativação de runas e transições por passagens.
        - Comunicar resultados (ex.: `morreu_por_queda`, `pedido_transicao_ambiente`) ao loop principal.

    REGRAS DE USO:
        - Instanciar com referências `jogador`, `mapa` e `sistema_combate`.
        - Chamar `atualizar(tempo_decorrido, esta_movendo)` a cada frame quando o jogador estiver na caverna.

    NOTAS DE IMPLEMENTAÇÃO:
        - Usa cálculos de distância para determinar se o jogador está centrado em tiles especiais.
    """
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
        self.pedido_transicao_ambiente = False

        self._aviso_passagem_mostrado = False
    
    def atualizar(self, tempo_decorrido, esta_movendo):
        """
        DESCRIÇÃO:
            Atualiza o estado das mecânicas da caverna (queda, ativação de runas, entrada em passagens).

        RESPONSABILIDADE:
            - Calcular posição do jogador em termos de quadriculo e delegar atualizações específicas.

        REGRAS DE USO:
            - Deve ser invocado a cada frame pelo `Jogador` ou loop principal.

        NOTAS DE IMPLEMENTAÇÃO:
            - Não retorna valores; altera flags internas e atributos observáveis pelo código externo.
        """
        largura_sprite = self.jogador.sprite_andar_direita_1.width
        altura_sprite = self.jogador.sprite_andar_direita_1.height
        
        posicao_base_sprite_x = self.jogador.posicao_pixel_x + largura_sprite / 2
        posicao_base_sprite_y = self.jogador.posicao_pixel_y + altura_sprite

        coluna_sprite = int(posicao_base_sprite_x / self.mapa.largura_quadriculo)
        linha_sprite = int(posicao_base_sprite_y / self.mapa.altura_quadriculo)
        quadriculo_sprite = self.mapa.obter_quadriculo_por_coordenada(coluna_sprite, linha_sprite)

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
                interface_usuario = getattr(self.jogador, 'interface_usuario', None)
                (interface_usuario.exibir_mensagem('sede','Caiu em um buraco!') if interface_usuario else print('Caiu em um buraco!'))
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
                interface_usuario = getattr(self.jogador, 'interface_usuario', None)
                if interface_usuario and getattr(interface_usuario, 'lendo_pergaminho', False):
                    return
                self._esta_ativando_runa = True
                self._temporizador_ativacao += tempo_decorrido

                if self._temporizador_ativacao >= self._duracao_ativacao:
                    self._temporizador_ativacao = 0.0
                    self._esta_ativando_runa = False

                    posicao_atual = (coluna_sprite, linha_sprite)
                    if posicao_atual != self.mapa.posicao_runa_final:
                        self.transformar_runa_em_inimigo(coluna_sprite, linha_sprite)
                        interface_usuario = getattr(self.jogador, 'interface_usuario', None)
                        (interface_usuario.exibir_mensagem('sede', 'Ativou uma runa! Golem apareceu!') if interface_usuario else print('Ativou uma runa! Golem apareceu!'))
                        if self.sistema_combate:
                            self.sistema_combate.iniciar_combate(nome_inimigo='golem')
                    else:
                        interface_usuario = getattr(self.jogador, 'interface_usuario', None)
                        (interface_usuario.exibir_mensagem('sede', 'Ativou a runa final! Venceu!') if interface_usuario else print('Ativou a runa final! Venceu!'))
                        try:
                            if interface_usuario:
                                lista = getattr(interface_usuario, 'pergaminhos_coletados', [])
                                indice_inicial = lista[0] if lista else 0
                                interface_usuario.abrir_leitura(indice_inicial, referencia=True)
                        except Exception:
                            pass
        else:
            if esta_movendo:
                self._esta_ativando_runa = False
                self._temporizador_ativacao = 0.0
    
    def _atualizar_entrada_passagem(self, tempo_decorrido, posicao_base_sprite_x, posicao_base_sprite_y, coluna_sprite, linha_sprite, quadriculo_sprite, esta_movendo):
        if esta_movendo:
            self._esta_entrando_na_passagem = False
            self._temporizador_entrada = 0.0
            self._aviso_passagem_mostrado = False
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
                if not self._aviso_passagem_mostrado:
                    interface_usuario = getattr(self.jogador, 'interface_usuario', None)
                    (interface_usuario.exibir_mensagem('sede','Passagem encontrada! Pressione parado para entrar...') if interface_usuario else print('Passagem encontrada! Pressione parado para entrar...'))
                    self._aviso_passagem_mostrado = True

        if esta_no_centro:
            self._esta_entrando_na_passagem = True
            self._temporizador_entrada += tempo_decorrido
            if self._temporizador_entrada >= self._duracao_entrada:
                self.pedido_transicao_ambiente = True
                self._temporizador_entrada = 0.0
                self._esta_entrando_na_passagem = False
                self._aviso_passagem_mostrado = False
        else:
            self._esta_entrando_na_passagem = False
            self._temporizador_entrada = 0.0
            self._aviso_passagem_mostrado = False
    
    def transformar_runa_em_inimigo(self, coluna, linha):
        """
        DESCRIÇÃO:
            Transforma a runa na posição indicada em um tile de inimigo (atualiza a imagem do quadriculo).

        RESPONSABILIDADE:
            - Delegar a transformação para o `Mapa` via `transformar_quadriculo_em_inimigo`.

        REGRAS DE USO:
            - Recebe coordenadas (coluna, linha) válidas dentro do mapa.

        NOTAS DE IMPLEMENTAÇÃO:
            - Não faz checagens extensas; assume que a posição contém uma runa válida quando chamada.
        """
        self.mapa.transformar_quadriculo_em_inimigo(coluna, linha)
    
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
        self.pedido_transicao_ambiente = False
        self._aviso_passagem_mostrado = False
