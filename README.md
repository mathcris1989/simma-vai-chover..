# Vai chover? — SIMMA | versão 2

Protótipo Streamlit com identidade visual institucional, previsão horária, indicadores experimentais de atenção meteorológica, mapas municipais com setas de direção estimada do vento, visualizador de satélite CPTEC/INPE com botão alternativo e exportação CSV.

## Estrutura

- `app.py` — aplicação Streamlit.
- `requirements.txt` — dependências Python.
- `assets/logo_simma.png` — logo oficial da SIMMA já incluída.

## Como instalar e executar no Windows

1. Extraia a pasta do ZIP para um local de sua preferência.
2. Abra a pasta `vai_chover_v3` no Explorador de Arquivos.
3. Clique na barra de endereço, digite `cmd` e pressione Enter.
4. Instale as dependências:

```bat
py -m pip install -r requirements.txt
```

5. Inicie o painel:

```bat
py -m streamlit run app.py
```

Para encerrar, volte ao terminal e pressione `Ctrl+C`.

## Como acrescentar a logo SIMMA

A logo oficial já está incluída em `assets/logo_simma.png` e será exibida automaticamente no cabeçalho.

## Recursos desta versão

- Previsão de 3 dias com gráficos para as próximas 24, 48 ou 72 horas.
- Temperatura, sensação térmica, umidade, precipitação, nebulosidade, pressão, vento e rajadas.
- Indicadores experimentais de atenção para chuva, rajadas e sensação térmica.
- Abas de mapas para Canarana, Água Boa, Querência, Nova Xavantina, Gaúcha do Norte e Ribeirão Cascalheira.
- Seta de vento que aponta para onde o vento sopra; o ângulo é calculado a partir da direção de origem fornecida pelo modelo.
- Visualizador CPTEC/INPE em quadro incorporado quando permitido, com botão para abrir a fonte oficial.
- Tabela horária e exportação CSV.

## Limitações e uso responsável

- As coordenadas são aproximadas e os valores representam a previsão de modelo para essas coordenadas, não uma observação de estação local.
- A direção do vento é uma estimativa do modelo Open-Meteo, não uma medição local em tempo real.
- Os critérios de atenção são demonstrativos e não constituem alertas oficiais. Não substituem INMET, Defesa Civil ou autoridades locais.
- A incorporação do visualizador de satélite pode ser bloqueada pelo site de origem. O botão alternativo continuará disponível.
- Respeite os termos de uso, atribuição e reprodução da Open-Meteo e do CPTEC/INPE antes de publicar ou utilizar comercialmente.
- Esta versão é uma evolução paralela; mantenha a pasta/ZIP da versão anterior como cópia de segurança.


## Integração com satélite

A aba **Satélite** tenta incorporar o visualizador oficial do CPTEC/INPE DSAT por meio de um quadro integrado e mantém um botão para abrir o visualizador diretamente. O provedor pode impedir a incorporação em sites externos; nesse caso, use o botão alternativo. O protótipo não baixa nem redistribui imagens do provedor.
