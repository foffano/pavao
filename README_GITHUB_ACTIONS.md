# 🤖 Automação com GitHub Actions - Scraper Pavão

Este projeto usa **GitHub Actions** para executar automaticamente o script de scraping 4 vezes por dia e manter o banco de dados atualizado.

## 📋 Configuração Inicial

### 1. Criar Repositório no GitHub

1. Acesse [github.com](https://github.com) e faça login
2. Clique em **"New repository"** (botão verde)
3. Configure:
   - **Nome**: `pavao-scraper` (ou o nome que preferir)
   - **Visibilidade**: Pode ser **Private** (recomendado) ou Public
   - **NÃO** marque "Initialize with README" (já temos arquivos locais)
4. Clique em **"Create repository"**

### 2. Fazer Push do Código Local

Abra o terminal/PowerShell na pasta do projeto e execute:

```bash
# Inicializar repositório Git (se ainda não foi feito)
git init

# Adicionar todos os arquivos
git add .

# Fazer o primeiro commit
git commit -m "🚀 Configuração inicial do scraper com GitHub Actions"

# Conectar ao repositório remoto (substitua SEU_USUARIO e NOME_REPO)
git remote add origin https://github.com/SEU_USUARIO/NOME_REPO.git

# Enviar para o GitHub
git branch -M main
git push -u origin main
```

### 3. Verificar Configuração

1. Acesse seu repositório no GitHub
2. Vá em **Actions** (aba no topo)
3. Você verá o workflow **"Scraper Pavão"**
4. Clique em **"Run workflow"** → **"Run workflow"** para testar manualmente

## ⏰ Horários de Execução

O script roda automaticamente nos seguintes horários (Brasília/BRT):

- **06:00** - Primeira coleta do dia
- **12:00** - Coleta do meio-dia
- **18:00** - Coleta da tarde
- **00:00** - Coleta da meia-noite

> **Nota**: Os horários são configurados em UTC no arquivo `.github/workflows/scraper.yml`. Se precisar ajustar, lembre-se que BRT = UTC-3.

## 📊 Monitorar Execuções

### Ver Logs em Tempo Real

1. Acesse **Actions** no seu repositório
2. Clique na execução mais recente
3. Clique em **"scrape"** para ver os logs detalhados
4. Você verá a saída do script, incluindo:
   - Número de produtos encontrados
   - Progresso da coleta
   - Mensagem de sucesso

### Verificar Histórico

- Todas as execuções ficam registradas em **Actions**
- Você pode ver execuções bem-sucedidas ✅ e falhas ❌
- Cada execução mostra data, hora e duração

## 💾 Acessar o Banco de Dados

### Opção 1: Baixar do GitHub

1. No repositório, clique no arquivo `monitoramento_pavao.db`
2. Clique em **"Download"** (botão no canto superior direito)
3. Abra com [DB Browser for SQLite](https://sqlitebrowser.org/)

### Opção 2: Clonar/Pull do Repositório

```bash
# Se já tem o repositório clonado
git pull origin main

# O arquivo monitoramento_pavao.db será atualizado automaticamente
```

### Opção 3: Usar GitHub API (Avançado)

Você pode criar um script Python para baixar automaticamente:

```python
import requests

url = "https://raw.githubusercontent.com/SEU_USUARIO/NOME_REPO/main/monitoramento_pavao.db"
response = requests.get(url)

with open("monitoramento_pavao.db", "wb") as f:
    f.write(response.content)
```

## 🔧 Configurações Avançadas

### Alterar Frequência de Execução

Edite `.github/workflows/scraper.yml` e modifique as linhas `cron`:

```yaml
schedule:
  # Exemplo: executar a cada 6 horas
  - cron: '0 */6 * * *'
  
  # Exemplo: executar apenas às 12:00 UTC (09:00 BRT)
  - cron: '0 12 * * *'
```

**Sintaxe do Cron:**
```
┌───────────── minuto (0 - 59)
│ ┌───────────── hora (0 - 23)
│ │ ┌───────────── dia do mês (1 - 31)
│ │ │ ┌───────────── mês (1 - 12)
│ │ │ │ ┌───────────── dia da semana (0 - 6) (Domingo = 0)
│ │ │ │ │
* * * * *
```

### Executar Manualmente

1. Vá em **Actions** → **Scraper Pavão**
2. Clique em **"Run workflow"**
3. Selecione a branch `main`
4. Clique em **"Run workflow"** novamente

## 🐛 Troubleshooting

### O workflow não está executando

- **Verifique**: Repositórios privados têm limite de 2.000 minutos/mês grátis
- **Solução**: Veja o uso em **Settings** → **Billing**

### Erro de permissão ao fazer commit

- **Causa**: O `GITHUB_TOKEN` não tem permissão de escrita
- **Solução**: Vá em **Settings** → **Actions** → **General** → **Workflow permissions** → Marque **"Read and write permissions"**

### O banco de dados não está sendo atualizado

1. Verifique os logs da execução em **Actions**
2. Procure por erros na etapa **"Commit and push database"**
3. Certifique-se de que o script `app.py` está criando o arquivo `monitoramento_pavao.db`

### Erro "Resource not accessible by integration"

- **Solução**: Vá em **Settings** → **Actions** → **General**
- Em **Workflow permissions**, selecione **"Read and write permissions"**
- Marque **"Allow GitHub Actions to create and approve pull requests"**

## 📈 Limites do Plano Gratuito

- ✅ **2.000 minutos/mês** para repositórios privados
- ✅ **Ilimitado** para repositórios públicos
- ✅ Cada execução do script leva ~2-5 minutos
- ✅ 4 execuções/dia × 30 dias = 120 execuções/mês
- ✅ 120 × 5 min = **600 minutos/mês** (bem dentro do limite!)

## 🎯 Próximos Passos

1. ✅ Configurar repositório no GitHub
2. ✅ Fazer push do código
3. ✅ Testar execução manual
4. ✅ Aguardar primeira execução automática
5. ✅ Verificar que o banco está sendo atualizado
6. 🔄 Monitorar regularmente em **Actions**

## 📞 Suporte

Se tiver problemas:
1. Verifique os logs em **Actions**
2. Consulte a [documentação do GitHub Actions](https://docs.github.com/en/actions)
3. Verifique se todas as permissões estão corretas

---

**Criado com ❤️ usando GitHub Actions**
