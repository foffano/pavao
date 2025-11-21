# Monitoramento Another Place 🛍️

Este projeto é uma ferramenta de monitoramento de preços e estoque para produtos da loja Another Place. Ele consiste em um coletor de dados (scraper) e um dashboard interativo para visualização.

## Estrutura do Projeto

- `app.py`: Script principal de coleta de dados. Varre o sitemap da loja, verifica preços e disponibilidade (via JSON e HTML) e salva no banco de dados.
- `dashboard.py`: Dashboard interativo feito em Streamlit para visualizar os dados coletados.
- `monitoramento_anotherplace.db`: Banco de dados SQLite onde o histórico é armazenado.

## Instalação

1. **Pré-requisitos**: Python 3.8 ou superior.
2. **Instalar dependências**:
   Abra o terminal na pasta do projeto e execute:
   ```bash
   pip install requests beautifulsoup4 tqdm streamlit pandas plotly
   ```

## Como Usar

### 1. Coletar Dados
Para atualizar o banco de dados com as informações mais recentes dos produtos, execute:

```bash
python app.py
```
Isso irá:
- Ler o sitemap da loja.
- Verificar cada produto.
- Salvar o histórico no arquivo `.db`.

### 2. Visualizar Dashboard
Para abrir o painel de controle e ver os gráficos e tabelas:

```bash
python -m streamlit run dashboard.py
```
*Nota: Se o comando `streamlit` direto não funcionar, use o `python -m streamlit` conforme acima.*

## Funcionalidades do Dashboard

- **KPIs**: Total de produtos, preço médio, itens em promoção.
- **Filtros**: Por categoria, disponibilidade e status de promoção.
- **Gráficos**:
  - Histograma de preços.
  - Gráfico de pizza de disponibilidade.
  - Evolução de preços (para os top produtos).
- **Tabela**: Visualização detalhada de todos os registros.

## Banco de Dados

O arquivo `monitoramento_anotherplace.db` contém a tabela `historico_precos` com as seguintes colunas principais:
- `data_coleta`: Data e hora da verificação.
- `produto_nome`: Nome do produto.
- `sku`: Código do produto.
- `preco_atual` & `preco_original`: Valores monetários.
- `disponivel`: Status de estoque (1 = Sim, 0 = Não).
- `metodo_verificacao`: Se foi via JSON ou checagem extra no HTML.
