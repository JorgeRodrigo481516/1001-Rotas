"""
-------------------------------------------------------------------
DESCRIÇÃO:
    Gerencia o HUD (Heads-Up Display) e centraliza as regras de 
    sobrevivência (Sede, Sol) e gestão de inventário.

RESPONSABILIDADE:
    1. Visualização: Renderizar barras de status, slots de inventário e mensagens de feedback.
    2. Simulação: Controlar a evolução temporal dos status (taxas de sede/sol por segundo).
    3. Regras de Negócio: Aplicar custos de ações (investigar) e benefícios de itens (beber).
    4. Inventário: Gerenciar adição, remoção e uso de itens nos slots.
    5. Interface de Combate: Fornecer métodos para o sistema de combate aplicar dano/cura e verificar condições.

REGRAS DE USO:
    - 'atualizar(delta_tempo)' deve ser chamado a cada frame para processar a simulação.
    - Métodos como 'consumir_bebida', 'aplicar_custo_investigacao' e 'aplicar_dano_combate' encapsulam a lógica de jogo.
    - 'verificar_estado_derrota()' centraliza a checagem de Game Over.

NOTAS DE IMPLEMENTAÇÃO:
    - Centraliza a lógica matemática de sobrevivência para retirar essa carga do 'main.py', 'jogador.py' e 'sistema_combate.py'.
    - Barras de status usam sprites de preenchimento repetidos para visualização dinâmica.
-------------------------------------------------------------------
"""
from PPlay.sprite import Sprite
import config


class InterfaceUsuario:
    def __init__(self, janela):
        self.janela = janela

        self.icone_sol = Sprite(config.RECURSOS['hud_sol'])
        self.barra_sol = Sprite(config.RECURSOS['hud_barra'])
        self.icone_sede = Sprite(config.RECURSOS['hud_sede'])
        self.barra_sede = Sprite(config.RECURSOS['hud_barra'])

        self.sede = config.GAMEPLAY['sede_inicial']
        self.sol = config.GAMEPLAY['sol_inicial']
        self._tempo_acumulado = 0.0

        self.espacos = []
        self.calcular_disposicao()

        if not hasattr(config, 'PREENCHIMENTOS_BARRA_HUD'):
            raise RuntimeError('config.PREENCHIMENTOS_BARRA_HUD must be defined (list of image paths)')

        self.sprites_preenchimento = []
        for caminho in config.PREENCHIMENTOS_BARRA_HUD:
            try:
                sprite = Sprite(caminho) if caminho is not None else None
            except Exception:
                sprite = None
            self.sprites_preenchimento.append(sprite)

        self._mensagem_sede = ""
        self._temporizador_mensagem_sede = 0.0
        self._mensagem_sol = ""
        self._temporizador_mensagem_sol = 0.0

    def calcular_disposicao(self):
        altura_tile = getattr(config, 'ALTURA_TILE', None)
        tiles_hud = getattr(config, 'ALTURA_HUD_EM_TILES', None)
        altura_hud = (altura_tile * tiles_hud) if (altura_tile and tiles_hud) else (self.icone_sol.height * 2)

        y = (altura_hud - self.icone_sol.height) / 2

        espaco_entre = getattr(config, 'ESPACAMENTO_ELEMENTOS_HUD', 6)
        deslocamento_esquerda = getattr(config, 'DESLOCAMENTO_ESQUERDA_HUD', 0)

        largura_total = (self.icone_sol.width + self.barra_sol.width + self.icone_sede.width + self.barra_sede.width) + espaco_entre * 3
        pos_x = ((self.janela.width - largura_total) / 2) - deslocamento_esquerda

        for sprite in (self.icone_sol, self.barra_sol, self.icone_sede, self.barra_sede):
            sprite.x = pos_x
            sprite.y = y
            pos_x += sprite.width + espaco_entre

        sprite_temporario = Sprite(config.RECURSOS['slot'])
        largura_espaco, altura_espaco = sprite_temporario.width, sprite_temporario.height
        del sprite_temporario

        contagem_espacos = getattr(config, 'QUANTIDADE_SLOTS_HUD', 8)
        margem_direita_espaco = getattr(config, 'MARGEM_DIREITA_SLOT_HUD', 10)
        x_espacos = self.janela.width - (contagem_espacos * largura_espaco) - margem_direita_espaco
        y_espacos = (altura_hud - altura_espaco) / 2

        self.espacos = [Sprite(config.RECURSOS['slot']) for _ in range(contagem_espacos)]
        for i, s in enumerate(self.espacos):
            s.x = x_espacos + i * largura_espaco
            s.y = y_espacos
        self.sobreposicoes_espacos = [None for _ in range(contagem_espacos)]
        self.nomes_itens = [None for _ in range(contagem_espacos)]

    def definir_valores(self, sede=None, sol=None):
        if sede is not None:
            self.sede = max(0, min(config.GAMEPLAY['max_sede'], int(sede)))
        if sol is not None:
            self.sol = max(0, min(config.GAMEPLAY['max_sol'], int(sol)))

    def atualizar(self, delta_tempo):
        self._tempo_acumulado += delta_tempo
        segundos_completos = int(self._tempo_acumulado)
        
        if segundos_completos >= 1:
            nova_sede = self.sede + (config.GAMEPLAY['taxa_sede_segundo'] * segundos_completos)
            novo_sol = self.sol + (config.GAMEPLAY['taxa_sol_segundo'] * segundos_completos)
            self.definir_valores(sede=nova_sede, sol=novo_sol)
            self._tempo_acumulado -= segundos_completos

        if self._temporizador_mensagem_sede > 0:
            self._temporizador_mensagem_sede -= delta_tempo
            if self._temporizador_mensagem_sede <= 0:
                self._mensagem_sede = ""
                self._temporizador_mensagem_sede = 0.0

        if self._temporizador_mensagem_sol > 0:
            self._temporizador_mensagem_sol -= delta_tempo
            if self._temporizador_mensagem_sol <= 0:
                self._mensagem_sol = ""
                self._temporizador_mensagem_sol = 0.0

    def desenhar(self):
        self.icone_sol.draw()
        self.barra_sol.draw()

        self.icone_sede.draw()
        self.barra_sede.draw()

        self._desenhar_barra_status(self.barra_sol, self.sol)
        self._desenhar_barra_status(self.barra_sede, self.sede)

        if self._mensagem_sol:
            texto_x = int(self.barra_sol.x + (self.barra_sol.width / 2) - (len(self._mensagem_sol) * 3))
            texto_y = int(self.barra_sol.y + self.barra_sol.height + 4)
            self.janela.draw_text(self._mensagem_sol, texto_x, texto_y, size=config.UI['tamanho_fonte_padrao'], color=config.CORES['preto'])

        if self._mensagem_sede:
            texto_x = int(self.barra_sede.x + (self.barra_sede.width / 2) - (len(self._mensagem_sede) * 3))
            texto_y = int(self.barra_sede.y + self.barra_sede.height + 4)
            self.janela.draw_text(self._mensagem_sede, texto_x, texto_y, size=config.UI['tamanho_fonte_padrao'], color=config.CORES['preto'])

        for s in self.espacos:
            s.draw()
        for overlay in getattr(self, 'sobreposicoes_espacos', []):
            if overlay is not None:
                overlay.draw()

    def _desenhar_barra_status(self, sprite_barra, valor):
        if valor <= 0:
            return

        exemplo_preenchimento = next((p for p in self.sprites_preenchimento if p is not None), None)
        if exemplo_preenchimento is None:
            return

        largura_bloco = int(exemplo_preenchimento.width)
        altura_bloco = int(exemplo_preenchimento.height)

        padding_esq = int(getattr(config, 'PREENCHIMENTO_HUD_PADDING_ESQUERDA', 0))
        padding_dir = int(getattr(config, 'PREENCHIMENTO_HUD_PADDING_DIREITA', 0))
        espaco_entre_blocos = int(getattr(config, 'ESPACAMENTO_PREENCHIMENTO_HUD', 0))

        largura_barra = int(sprite_barra.width)
        largura_util = max(0, largura_barra - padding_esq - padding_dir)

        passo_por_bloco = largura_bloco + espaco_entre_blocos
        if passo_por_bloco <= 0:
            return

        num_blocos = max(1, largura_util // passo_por_bloco)

        blocos_preenchidos = int((valor / float(config.GAMEPLAY['max_sede'])) * num_blocos)
        blocos_preenchidos = max(0, min(blocos_preenchidos, num_blocos))

        segmentos = max(1, len(self.sprites_preenchimento))
        blocos_por_segmento = max(1, num_blocos // segmentos)

        x_inicio = sprite_barra.x + padding_esq
        y_inicio = sprite_barra.y + (sprite_barra.height - altura_bloco) / 2

        for indice in range(blocos_preenchidos):
            indice_segmento = min(segmentos - 1, indice // blocos_por_segmento)
            sprite_para_desenhar = self.sprites_preenchimento[indice_segmento]
            if sprite_para_desenhar is None:
                continue

            pos_x = x_inicio + indice * passo_por_bloco
            sprite_para_desenhar.x = pos_x
            sprite_para_desenhar.y = y_inicio
            sprite_para_desenhar.draw()

    def processar_item_encontrado(self, nome_item):
        """Adiciona um item ao inventário baseado no nome, buscando o asset correto."""
        if not nome_item:
            return False
            
        caminho_imagem = config.RECURSOS.get(nome_item)
        if caminho_imagem:
            return self.adicionar_item(caminho_imagem, nome_item)
        return False

    def adicionar_item(self, caminho_imagem, nome_item=None):
        for i, ov in enumerate(self.sobreposicoes_espacos):
            if ov is None:
                sprite = Sprite(caminho_imagem)
                espaco = self.espacos[i]
                sprite.x = espaco.x + (espaco.width - sprite.width) / 2
                sprite.y = espaco.y + (espaco.height - sprite.height) / 2
                self.sobreposicoes_espacos[i] = sprite
                self.nomes_itens[i] = nome_item
                return True
        return False

    def usar_item(self, index):
        if index < 0 or index >= len(self.sobreposicoes_espacos):
            return False
        if self.sobreposicoes_espacos[index] is None:
            return False
        self.sobreposicoes_espacos[index] = None
        self.nomes_itens[index] = None
        return True

    def tem_item(self, nome_item):
        return nome_item in self.nomes_itens

    def remover_item(self, nome_item):
        try:
            index = self.nomes_itens.index(nome_item)
            self.sobreposicoes_espacos[index] = None
            self.nomes_itens[index] = None
            return True
        except ValueError:
            return False

    def recuperar_sede_escavacao(self):
        recuperacao = config.GAMEPLAY['recuperacao_sede_item']
        self.definir_valores(sede=self.sede + recuperacao)
        self.exibir_mensagem('sede', f'+{recuperacao}', duration=1.5)

    def consumir_bebida(self, indice_espaco):
        if self.usar_item(indice_espaco):
            recuperacao = config.GAMEPLAY['recuperacao_sede_beber']
            self.definir_valores(sede=self.sede - recuperacao)
            self.exibir_mensagem('sede', f"-{recuperacao}", duration=1.5)
            return True
        return False

    def aplicar_custo_investigacao(self):
        custo_sede = config.CUSTO_INVESTIGACAO_SEDE
        custo_sol = config.CUSTO_INVESTIGACAO_SOL
        
        self.definir_valores(sede=self.sede + custo_sede, sol=self.sol + custo_sol)
        self.exibir_mensagem('sede', f'+{custo_sede}', duration=1.5)
        self.exibir_mensagem('sol', f'+{custo_sol}', duration=1.5)

    def verificar_estado_derrota(self):
        return self.sede >= config.GAMEPLAY['max_sede'] or self.sol >= config.GAMEPLAY['max_sol']

    def aplicar_dano_combate(self, valor):
        self.definir_valores(sede=self.sede + valor)

    def aplicar_cura_combate(self, valor):
        self.definir_valores(sede=self.sede - valor)

    def possui_condicao_para_combate(self):
        vida_restante = config.GAMEPLAY['max_sede'] - self.sede
        return vida_restante >= config.GAMEPLAY['limiar_sede_combate']

    def exibir_mensagem(self, tipo, texto, duration=1.5):
        if tipo == 'sede':
            self._mensagem_sede = str(texto)
            self._temporizador_mensagem_sede = float(duration)
        elif tipo == 'sol':
            self._mensagem_sol = str(texto)
            self._temporizador_mensagem_sol = float(duration)
        else:
            return
