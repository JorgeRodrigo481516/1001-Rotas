# 🏜️ 1001 Rotas

Jogo 2D de sobrevivência e exploração em Python com PPlay.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-orange)
![Licenca](https://img.shields.io/badge/licenca-a%20definir-lightgrey)

## Sobre o jogo

**1001 Rotas** é um jogo em que você explora o **Deserto** e a **Caverna** tentando sobreviver à sede e ao sol, escavar recursos, investigar o terreno e enfrentar inimigos. O progresso inclui ativação de runas na caverna e transição entre ambientes conectados por passagens.

- Resolução da janela: **800 x 728**

## Funcionalidades principais

- **Mapa procedural**: geração de grid com 6 variações de tiles no Deserto e na Caverna, incluindo paredes, buracos, runas e inimigos.
- **Mecânicas de sobrevivência**: barras de Sede e Sol evoluem com o tempo e podem causar game over.
- **Escavação**: ação com duração e teste de d20, com bônus ao usar Pá.
- **Investigação**: leitura probabilística dos 9 tiles ao redor, com chance de informação imprecisa.
- **Inventário**: 8 slots para itens (água, pá, faca), com regras de duplicata e usos limitados.
- **Combate por turnos**: inimigos Tempestade, Serpente e Golem; ações de atacar, defender, item e fugir.
- **Mecânicas da caverna**: quedas em buracos, ativação de runas, armadilhas e transição Deserto↔Caverna.
- **Telas especiais**: tela de morte, tela de combate e leitura de pergaminhos.
- **Áudio**: trilha sonora e efeitos de ações (beber, escavar e investigar).

## Estrutura do projeto

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Ponto de entrada, orquestrador e game loop |
| `config.py` | Constantes globais: dimensões, cores, balanceamento, caminhos de assets |
| `mapa.py` | Construção e renderização do grid, escavação, investigação e passagens |
| `jogador.py` | Movimentação, animação, ações e integração com sistemas do jogo |
| `interface_usuario.py` | HUD (status, inventário, mensagens), áudio e lógica de sobrevivência |
| `sistema_combate.py` | Combate por turnos, lógica de inimigos e integração com HUD |
| `mecanicas_caverna.py` | Quedas, runas, armadilhas e transições de ambiente |
| `popup.py` | Telas modais (morte, combate e leitura) |
| `assets/` | Sprites (PNG), tiles, ícones e áudios (OGG) |

## Pré-requisitos

- Python 3.x
- Biblioteca **PPlay** (`PPlay.window`, `PPlay.sprite`, `PPlay.sound`, `PPlay.gameimage`)

Instalação:

```bash
pip install pplay
```

## Como executar

Na raiz do repositório:

```bash
python main.py
```

## Controles

### Exploração

- **Setas direcionais**: movimentação (`RIGHT`, `LEFT`, `UP`, `DOWN`)
- **SPACE**: iniciar escavação
- **X**: iniciar investigação (fora da caverna)
- **F**: ativar/desativar sistema de foco
- **I**: abrir inventário padrão
- **P**: abrir inventário de pergaminhos
- **1 a 8**: usar/acionar item do slot correspondente (quando aplicável)

> Observação: nesta versão, os controles de movimento implementados no código usam setas direcionais.

### Combate

- **Mouse (clique esquerdo)** nos botões: **Atacar**, **Defender**, **Item** e **Fugir**

### Telas e interface

- **Mouse (clique esquerdo)**: navegação na leitura de pergaminhos e ações de interface
- **Mouse (clique esquerdo)** no botão **Reiniciar** na tela de morte

## Balanceamento e configuração

Os parâmetros de gameplay estão centralizados em `config.py`, incluindo:

- `velocidade_jogador`
- `max_sede` / `max_sol`
- `dificuldade_escavacao`
- dano base e limiares do combate

Para ajustar dificuldade e ritmo de jogo, edite os valores de `JOGABILIDADE`, `COMBATE` e `INTERFACE_USUARIO` nesse arquivo.

## Créditos / Autores

- Jorge Rodrigo (repositório original)
- Contribuidores do projeto

> Se este projeto for parte de disciplina/curso, inclua aqui instituição, turma e período.

## Licença

Licença **a definir**.
