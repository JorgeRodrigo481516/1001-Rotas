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
import random


PERGAMINHOS = [
    {
        'a': "Ó Deus, tu és o meu Deus forte; eu te busco ansiosamente; a minha alma tem sede de ti; o meu corpo te almeja, numa terra árida, exausta, sem água.",
        'a_ref': "Salmos 63:1",
        'b': "Aquele, porém, que beber da água que eu lhe der nunca mais terá sede; pelo contrário, a água que eu lhe der será nele uma fonte a jorrar para a vida eterna.",
        'b_ref': "João 4:14"
    },
    {
        'a': "Se buscares a sabedoria como a prata e como a tesouros escondidos a procurares, então, entenderás o temor do SENHOR e acharás o conhecimento de Deus.",
        'a_ref': "Provérbios 2:4-5",
        'b': "O reino dos céus é semelhante a um tesouro oculto no campo, o qual certo homem, tendo-o achado, escondeu. E, transbordante de alegria, vai, vende tudo o que tem e compra aquele campo.",
        'b_ref': "Mateus 13:44"
    },
    {
        'a': "Vaidade de vaidades, diz o Pregador; vaidade de vaidades, tudo é vaidade.",
        'a_ref': "Eclesiastes 1:2",
        'b': "O espírito é o que vivifica; a carne para nada aproveita; as palavras que eu vos tenho dito são espírito e são vida.",
        'b_ref': "João 6:63"
    },
    {
        'a': "O coração do homem traça o seu caminho, mas o SENHOR lhe dirige os passos.",
        'a_ref': "Provérbios 16:9",
        'b': "Respondeu-lhe Jesus: Eu sou o caminho, e a verdade, e a vida; ninguém vem ao Pai senão por mim.",
        'b_ref': "João 14:6"
    },
    {
        'a': "Não to mandei eu? Sê forte e corajoso; não temas, nem te espantes, porque o SENHOR, teu Deus, é contigo por onde quer que andares.",
        'a_ref': "Josué 1:9",
        'b': "Estas coisas vos tenho dito para que tenhais paz em mim. No mundo, passais por aflições; mas tende bom ânimo; eu venci o mundo.",
        'b_ref': "João 16:33"
    },
    {
        'a': "Se eu digo: as trevas, com efeito, me encobrirão, e a luz ao redor de mim se fará noite, até as próprias trevas não te serão escuras: as trevas e a luz são a mesma coisa.",
        'a_ref': "Salmos 139:11-12",
        'b': "De novo, lhes falava Jesus, dizendo: Eu sou a luz do mundo; quem me segue não andará nas trevas; pelo contrário, terá a luz da vida.",
        'b_ref': "João 8:12"
    },
    {
        'a': "Faz forte ao cansado e multiplica as forças ao que não tem nenhum vigor.",
        'a_ref': "Isaías 40:29",
        'b': "Vinde a mim, todos os que estais cansados e sobrecarregados, e eu vos aliviarei.",
        'b_ref': "Mateus 11:28"
    },
    {
        'a': "Tudo fez Deus formoso no seu devido tempo; também pôs a eternidade no coração do homem, sem que este possa descobrir as obras que Deus fez desde o princípio até ao fim.",
        'a_ref': "Eclesiastes 3:11",
        'b': "Disse-me ainda: Tudo está feito. Eu sou o Alfa e o Ômega, o Princípio e o Fim. Eu, a quem tem sede, darei de graça da fonte da água da vida.",
        'b_ref': "Apocalipse 21:6"
    }
]

PERGAMINHOS_ATIVOS = None

def embaralhar_pergaminhos(seed=None):
    global PERGAMINHOS_ATIVOS
    rng = random.Random(seed)
    ordem = list(range(len(PERGAMINHOS)))
    rng.shuffle(ordem)
    PERGAMINHOS_ATIVOS = [PERGAMINHOS[i] for i in ordem]

def obter_pergaminhos():
    return PERGAMINHOS_ATIVOS if PERGAMINHOS_ATIVOS is not None else PERGAMINHOS


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
        self.botao_reiniciar.y = self.fundo_morte.y + self.fundo_morte.height - config.INTERFACE_USUARIO['deslocamento_y_reiniciar'] + 15

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
        caminho_reiniciar = config.RECURSOS.get('botao_reiniciar')
        self.botao_reiniciar = GameImage(caminho_reiniciar) if caminho_reiniciar else None

        self._clique_processado = False

    def desenhar(self, pergaminhos_coletados, indice_leitura_atual, lendo_pergaminho, referencia=False):
        if not lendo_pergaminho:
            return
        if self.fundo_leitura is not None:
            self.fundo_leitura.draw()

        if indice_leitura_atual is not None:
            texto = f"Fragmento de Historia #{indice_leitura_atual + 1}"
            largura_texto = len(texto) * 10
            x_texto = self.fundo_leitura.x + (self.fundo_leitura.width - largura_texto) / 2
            title_y = self.fundo_leitura.y + 50
            title_height = 20
            self.janela.draw_text(texto, x_texto, title_y, size=20, color=config.CORES['branco'], bold=True)

            instrucao = "Pressione 'I' para fechar"
            largura_instrucao = len(instrucao) * 5
            x_instrucao = self.fundo_leitura.x + (self.fundo_leitura.width - largura_instrucao) / 2
            y_instrucao = self.fundo_leitura.y + self.fundo_leitura.height - 150
            self.janela.draw_text(instrucao, x_instrucao, y_instrucao, size=14, color=config.CORES['branco'])

            base_apos_titulo = title_y + title_height + 10

            try:
                conteudo = None
                referencia_texto = None
                pergaminhos_ativos = obter_pergaminhos()
                if 0 <= indice_leitura_atual < len(pergaminhos_ativos):
                    chave = 'b' if referencia else 'a'
                    conteudo = pergaminhos_ativos[indice_leitura_atual].get(chave)
                    referencia_texto = pergaminhos_ativos[indice_leitura_atual].get(f"{chave}_ref")

                if referencia:
                    a_text = pergaminhos_ativos[indice_leitura_atual].get('a') if 0 <= indice_leitura_atual < len(pergaminhos_ativos) else None
                    a_ref = pergaminhos_ativos[indice_leitura_atual].get('a_ref') if 0 <= indice_leitura_atual < len(pergaminhos_ativos) else None
                    b_text = pergaminhos_ativos[indice_leitura_atual].get('b') if 0 <= indice_leitura_atual < len(pergaminhos_ativos) else None
                    b_ref = pergaminhos_ativos[indice_leitura_atual].get('b_ref') if 0 <= indice_leitura_atual < len(pergaminhos_ativos) else None

                    y_line = base_apos_titulo
                    if a_ref:
                        largura_ref = len(a_ref) * 8
                        x_ref = self.fundo_leitura.x + (self.fundo_leitura.width - largura_ref) / 2
                        self.janela.draw_text(a_ref, x_ref, y_line, size=16, color=config.CORES['branco'], bold=True)
                        y_line += 26

                    if a_text:
                        max_chars = 76
                        linhas_a = []
                        palavras = a_text.split(' ')
                        linha_atual = ''
                        for p in palavras:
                            if len(linha_atual) + 1 + len(p) <= max_chars:
                                linha_atual = (linha_atual + ' ' + p).strip()
                            else:
                                linhas_a.append(linha_atual)
                                linha_atual = p
                        if linha_atual:
                            linhas_a.append(linha_atual)

                        x_texto_base = self.fundo_leitura.x + 50
                        for l in linhas_a:
                            self.janela.draw_text(l, x_texto_base, y_line, size=16, color=config.CORES['branco'])
                            y_line += 26

                    y_line += 8

                    if b_ref:
                        largura_ref = len(b_ref) * 8
                        x_ref = self.fundo_leitura.x + (self.fundo_leitura.width - largura_ref) / 2
                        self.janela.draw_text(b_ref, x_ref, y_line, size=16, color=config.CORES['branco'], bold=True)
                        y_line += 26

                    if b_text:
                        max_chars = 76
                        linhas_b = []
                        palavras = b_text.split(' ')
                        linha_atual = ''
                        for p in palavras:
                            if len(linha_atual) + 1 + len(p) <= max_chars:
                                linha_atual = (linha_atual + ' ' + p).strip()
                            else:
                                linhas_b.append(linha_atual)
                                linha_atual = p
                        if linha_atual:
                            linhas_b.append(linha_atual)

                        x_texto_base = self.fundo_leitura.x + 50
                        for l in linhas_b:
                            self.janela.draw_text(l, x_texto_base, y_line, size=16, color=config.CORES['branco'])
                            y_line += 26
                else:
                    if referencia_texto:
                        largura_ref = len(referencia_texto) * 8
                        x_ref = self.fundo_leitura.x + (self.fundo_leitura.width - largura_ref) / 2
                        y_ref = base_apos_titulo
                        self.janela.draw_text(referencia_texto, x_ref, y_ref, size=16, color=config.CORES['branco'], bold=True)

                    if conteudo:
                        max_chars = 76
                        linhas = []
                        palavras = conteudo.split(' ')
                        linha_atual = ''
                        for p in palavras:
                            if len(linha_atual) + 1 + len(p) <= max_chars:
                                linha_atual = (linha_atual + ' ' + p).strip()
                            else:
                                linhas.append(linha_atual)
                                linha_atual = p
                        if linha_atual:
                            linhas.append(linha_atual)

                        if referencia_texto:
                            y_texto = base_apos_titulo + 26
                        else:
                            y_texto = base_apos_titulo
                        x_texto_base = self.fundo_leitura.x + 50
                        for l in linhas:
                            self.janela.draw_text(l, x_texto_base, y_texto, size=16, color=config.CORES['branco'])
                            y_texto += 26
            except Exception:
                pass
            except Exception:
                pass

        espacamento = 20
        botoes = []
        if self.botao_back is not None:
            botoes.append(self.botao_back)
        if referencia and self.botao_reiniciar is not None:
            botoes.append(self.botao_reiniciar)
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

            if referencia and self.botao_reiniciar is not None:
                self.botao_reiniciar.x = x_atual
                self.botao_reiniciar.y = y_botoes
                self.botao_reiniciar.draw()
                x_atual += self.botao_reiniciar.width + espacamento

            if self.botao_next is not None:
                self.botao_next.x = x_atual
                self.botao_next.y = y_botoes
                if has_next:
                    self.botao_next.draw()

    def processar_evento(self, dispositivo_mouse, pergaminhos_coletados, indice_leitura_atual, referencia=False):
        if not (self.botao_back or self.botao_next or (referencia and self.botao_reiniciar)):
            return None

        if dispositivo_mouse.is_button_pressed(1):
            if not self._clique_processado:
                self._clique_processado = True

                lista_pergs = sorted(pergaminhos_coletados) if pergaminhos_coletados else []
                if not lista_pergs:
                    if referencia and self.botao_reiniciar is not None and dispositivo_mouse.is_over_object(self.botao_reiniciar):
                        return 'RESTART'
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

                if referencia and self.botao_reiniciar is not None and dispositivo_mouse.is_over_object(self.botao_reiniciar):
                    return 'RESTART'

                if self.botao_next is not None and dispositivo_mouse.is_over_object(self.botao_next):
                    if pos < len(lista_pergs) - 1:
                        return lista_pergs[pos + 1]
                    return None
        else:
            self._clique_processado = False
        return None

