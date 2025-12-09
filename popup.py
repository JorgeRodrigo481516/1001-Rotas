"""
-------------------------------------------------------------------
DESCRIÇÃO:
        Módulo responsável por implementar popups (telas modais) do jogo "1001 Rotas".

RESPONSABILIDADE:
        1. Centralizar a implementação das telas modais (ex.: tela de morte, tela de combate).
        2. Fornecer uma API consistente para mostrar/ocultar, atualizar, desenhar e processar
             eventos de popups.
        3. Isolar detalhes de renderização e posicionamento de recursos gráficos usados pela
             interface modal.
        4. Manter compatibilidade com a API anterior de fim de jogo para facilitar a migração.

REGRAS DE USO:
        - Instanciar os popups passando a `janela` (`PPlay.Window`).
        - Chamar `atualizar(dt)` e `desenhar()` a partir do loop principal quando apropriado.
        - Usar `mostrar()` / `ocultar()` (ou métodos específicos como `aguardar_clique_apos_morte()`)
            para controlar a visibilidade dos popups.
        - A lógica de domínio (detecção de morte, resolução de combate) é responsabilidade de
            outros módulos; este módulo apenas exibe a UI correspondente.

NOTAS DE IMPLEMENTAÇÃO:
        - Depende de `PPlay` para imagens e entrada (mouse/teclado) e de chaves em `config`
            para localizar recursos e parâmetros de interface.
        - `TelaMorte` preserva a API usada previamente (`aguardar_clique_apos_morte`,
            `verificar_clique_reiniciar`, atributo `esta_visivel`) para compatibilidade com
            chamadas existentes em `main.py` e outros módulos.
        - `TelaCombate` é um esqueleto que deve ser estendido para integrar o
            `SistemaCombate` (barras, botões de ação, callbacks de resultado).
        - Não implementa regras de jogo (por exemplo, decidir se o jogador morreu); quem
            detectar essas condições deve chamar os métodos deste módulo para exibir os popups.
-------------------------------------------------------------------
"""
from PPlay.window import Window
from PPlay.gameimage import GameImage
import config


class Popup:
    def __init__(self, janela: Window):
        self.janela = janela
        self.esta_visivel = False
        self.tempo = 0.0

    def mostrar(self):
        self.esta_visivel = True
        self.tempo = 0.0

    def ocultar(self):
        self.esta_visivel = False

    def atualizar(self, dt: float):
        self.tempo += dt

    def desenhar(self):
        raise NotImplementedError

    def processar_evento(self, mouse, teclado):
        pass


class TelaMorte(Popup):
    def __init__(self, janela: Window):
        super().__init__(janela)
        self.fundo_morte = GameImage(config.RECURSOS['fundo_morte'])
        self.fundo_morte.x = (janela.width - self.fundo_morte.width) / 2
        self.fundo_morte.y = (janela.height - self.fundo_morte.height) / 2

        self.botao_reiniciar = GameImage(config.RECURSOS['botao_reiniciar'])
        self.botao_reiniciar.x = (janela.width - self.botao_reiniciar.width) / 2
        self.botao_reiniciar.y = self.fundo_morte.y + self.fundo_morte.height - config.INTERFACE_USUARIO['deslocamento_y_reiniciar']

        self.tempo = 0.0
        self.atraso_clique = config.INTERFACE_USUARIO.get('atraso_clique_morte', 0.6)

    def aguardar_clique_apos_morte(self):
        self.esta_visivel = True
        self.tempo = 0.0

    def ocultar(self):
        self.esta_visivel = False

    def atualizar(self, tempo_decorrido):
        self.tempo += tempo_decorrido

    def verificar_clique_reiniciar(self, mouse):
        return (self.tempo >= self.atraso_clique and
                mouse.is_button_pressed(1) and
                mouse.is_over_object(self.botao_reiniciar))

    def desenhar(self):
        if self.esta_visivel:
            self.fundo_morte.draw()
            self.botao_reiniciar.draw()


class TelaCombate(Popup):
    def __init__(self, janela: Window):
        super().__init__(janela)
        self.fundo_combate = GameImage(config.RECURSOS['fundo_combate'])
        self.protagonista = GameImage(config.RECURSOS['protagonista_combate'])

        self.botao_atacar = GameImage(config.RECURSOS['botao_atacar'])
        self.botao_defender = GameImage(config.RECURSOS['botao_defender'])
        self.botao_item = GameImage(config.RECURSOS['botao_item'])
        self.botao_fugir = GameImage(config.RECURSOS['botao_fugir'])

        self.imagem_tempestade = GameImage(config.RECURSOS['inimigo_tempestade'])
        self.imagem_serpente = GameImage(config.RECURSOS['inimigo_serpente'])
        self.imagem_golem = GameImage(config.RECURSOS['inimigo_golem'])

        self.inimigo = None
        self.jogador = None
        self.acao_selecionada = None
        self._posicionar_elementos()

    def _posicionar_elementos(self):
        self.fundo_combate.x = (self.janela.width - self.fundo_combate.width) / 2
        self.fundo_combate.y = (self.janela.height - self.fundo_combate.height) / 2 + 20

        centro_x = self.fundo_combate.x + self.fundo_combate.width / 2
        centro_y = self.fundo_combate.y + self.fundo_combate.height / 2

        self.protagonista.x = centro_x - self.protagonista.width - 50
        self.protagonista.y = centro_y - self.protagonista.height / 2 - 30

        self.imagem_tempestade.x = centro_x + 50
        self.imagem_tempestade.y = centro_y - self.imagem_tempestade.height / 2 - 30

        self.imagem_serpente.x = centro_x + 50
        self.imagem_serpente.y = centro_y - self.imagem_serpente.height / 2 - 30

        self.imagem_golem.x = centro_x + 50
        self.imagem_golem.y = centro_y - self.imagem_golem.height / 2 - 30

        espacamento = 20
        largura_total_botoes = (self.botao_atacar.width + self.botao_defender.width + 
                               self.botao_item.width + self.botao_fugir.width + espacamento * 3)

        inicio_x = self.fundo_combate.x + (self.fundo_combate.width - largura_total_botoes) / 2
        y_botoes = self.fundo_combate.y + self.fundo_combate.height - self.botao_atacar.height - 30 - 15

        self.botao_atacar.x = inicio_x
        self.botao_atacar.y = y_botoes

        self.botao_defender.x = self.botao_atacar.x + self.botao_atacar.width + espacamento
        self.botao_defender.y = y_botoes

        self.botao_item.x = self.botao_defender.x + self.botao_defender.width + espacamento
        self.botao_item.y = y_botoes

        self.botao_fugir.x = self.botao_item.x + self.botao_item.width + espacamento
        self.botao_fugir.y = y_botoes

    def atualizar_posicoes(self):
        self._posicionar_elementos()

    def iniciar_combate(self, inimigo, jogador, callback_resultado=None):
        self.inimigo = inimigo
        self.jogador = jogador
        self.callback_resultado = callback_resultado
        self.mostrar()

    def escolher_acao(self, indice_acao: int):
        self.acao_selecionada = indice_acao

    def atualizar(self, dt: float):
        super().atualizar(dt)

    def desenhar(self, inimigo_atual=None, mensagens=None):
        if not self.esta_visivel:
            return
        self.fundo_combate.draw()
        self.protagonista.draw()
        if inimigo_atual is not None:
            inimigo_atual['imagem'].draw()

        self.botao_atacar.draw()
        self.botao_defender.draw()
        self.botao_item.draw()
        self.botao_fugir.draw()

        if mensagens:
            x_atual = self.fundo_combate.x + 40 + 10
            y_texto = self.fundo_combate.y + 40
            for texto, cor in mensagens:
                self.janela.draw_text(
                    texto,
                    x_atual,
                    y_texto,
                    size=config.INTERFACE_USUARIO['tamanho_fonte_combate'],
                    color=cor,
                    font_name="Arial",
                    bold=True
                )
                largura_estimada = len(texto) * 6
                x_atual += largura_estimada


class TelaLeitura(Popup):
    def __init__(self, janela: Window):
        super().__init__(janela)
        caminho_pergaminho = config.RECURSOS.get('pergaminho')
        caminho_fundo = config.RECURSOS.get('fundo_leitura')
        caminho_back = config.RECURSOS.get('botao_back')
        caminho_next = config.RECURSOS.get('botao_next')

        self.imagem_pergaminho = GameImage(caminho_pergaminho) if caminho_pergaminho else None
        self.fundo_leitura = GameImage(caminho_fundo) if caminho_fundo else None
        if self.fundo_leitura is not None:
            self.fundo_leitura.x = (self.janela.width - self.fundo_leitura.width) / 2
            self.fundo_leitura.y = (self.janela.height - self.fundo_leitura.height) / 2

        self.botao_back = GameImage(caminho_back) if caminho_back else None
        self.botao_next = GameImage(caminho_next) if caminho_next else None

        self._clique_processado = False

    def desenhar(self, pergaminhos_coletados, indice_leitura_atual, lendo_pergaminho):
        if not lendo_pergaminho:
            return
        if self.fundo_leitura is not None:
            self.fundo_leitura.draw()

        if indice_leitura_atual is not None:
            texto = f"Fragmento de Historia #{indice_leitura_atual + 1}"
            largura_texto = len(texto) * 10
            x_texto = self.fundo_leitura.x + (self.fundo_leitura.width - largura_texto) / 2
            self.janela.draw_text(texto, x_texto, self.fundo_leitura.y + 50, size=20, color=config.CORES['branco'], bold=True)

            instrucao = "Pressione 'I' para fechar"
            largura_instrucao = len(instrucao) * 5
            x_instrucao = self.fundo_leitura.x + (self.fundo_leitura.width - largura_instrucao) / 2
            y_instrucao = self.fundo_leitura.y + self.fundo_leitura.height - 150
            self.janela.draw_text(instrucao, x_instrucao, y_instrucao, size=14, color=config.CORES['branco'])

        espacamento = 50
        botoes = []
        if self.botao_back is not None:
            botoes.append(self.botao_back)
        if self.botao_next is not None:
            botoes.append(self.botao_next)

        if botoes and self.fundo_leitura is not None:
            largura_total_botoes = sum(b.width for b in botoes) + espacamento * (len(botoes) - 1)
            inicio_x = self.fundo_leitura.x + (self.fundo_leitura.width - largura_total_botoes) / 2
            y_botoes = self.fundo_leitura.y + self.fundo_leitura.height - (botoes[0].height if botoes else 0) - 30 - 15

            lista_pergs = sorted(pergaminhos_coletados) if pergaminhos_coletados else []
            has_prev = False
            has_next = False
            if indice_leitura_atual is not None and lista_pergs:
                try:
                    pos = lista_pergs.index(indice_leitura_atual)
                except ValueError:
                    pos = 0
                has_prev = pos > 0
                has_next = pos < (len(lista_pergs) - 1)

            x_atual = inicio_x
            if self.botao_back is not None:
                self.botao_back.x = x_atual
                self.botao_back.y = y_botoes
                if has_prev:
                    self.botao_back.draw()
                x_atual += self.botao_back.width + espacamento

            if self.botao_next is not None:
                self.botao_next.x = x_atual
                self.botao_next.y = y_botoes
                if has_next:
                    self.botao_next.draw()

    def processar_evento(self, dispositivo_mouse, pergaminhos_coletados, indice_leitura_atual):
        if not (self.botao_back or self.botao_next):
            return None

        if dispositivo_mouse.is_button_pressed(1):
            if not self._clique_processado:
                self._clique_processado = True

                lista_pergs = sorted(pergaminhos_coletados) if pergaminhos_coletados else []
                if not lista_pergs:
                    return None

                if indice_leitura_atual not in lista_pergs:
                    indice_leitura_atual = lista_pergs[0]

                try:
                    pos = lista_pergs.index(indice_leitura_atual)
                except ValueError:
                    pos = 0

                if self.botao_back is not None and dispositivo_mouse.is_over_object(self.botao_back):
                    if pos > 0:
                        return lista_pergs[pos - 1]
                    return None

                if self.botao_next is not None and dispositivo_mouse.is_over_object(self.botao_next):
                    if pos < len(lista_pergs) - 1:
                        return lista_pergs[pos + 1]
                    return None
        else:
            self._clique_processado = False
        return None

