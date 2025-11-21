import cloudscraper
import sqlite3
import time
import random
from datetime import datetime
from tqdm import tqdm
from bs4 import BeautifulSoup

# --- CONFIGURAÇÕES ---
MAIN_SITEMAP_URL = "https://anotherplace.com.br/sitemap.xml"
DB_NAME = "monitoramento_anotherplace.db"

# Inicializa o scraper
scraper = cloudscraper.create_scraper()

# --- 1. BANCO DE DADOS ---
def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_coleta DATETIME,
            produto_nome TEXT,
            sku TEXT,
            categoria TEXT,
            url TEXT,
            imagem_url TEXT,
            tags TEXT,
            preco_original REAL,
            preco_atual REAL,
            em_promocao BOOLEAN,
            disponivel BOOLEAN,
            variante_id TEXT,
            metodo_verificacao TEXT
        )
    ''')
    conn.commit()
    return conn

# --- 2. CHECAGEM DE ESTOQUE EXTRA (VIA HTML) ---
def check_html_availability(url):
    """
    Se o JSON falhar, baixamos o HTML e procuramos a tag que o Google lê.
    """
    try:
        r = scraper.get(url, timeout=10)
        html = r.text
        
        # Pista 1: Schema.org (Padrão Ouro)
        if '"availability": "http://schema.org/InStock"' in html or '"availability":"http://schema.org/InStock"' in html:
            return True
        if '"availability": "http://schema.org/OutOfStock"' in html:
            return False
            
        # Pista 2: Botão de Comprar
        # Se encontrar texto "Esgotado" visível em botões chave
        soup = BeautifulSoup(html, 'html.parser')
        buttons = soup.find_all('button', type='submit')
        for btn in buttons:
            if 'esgotado' in btn.text.lower() or 'sold out' in btn.text.lower():
                return False
                
        # Se não achou "Esgotado" explícito, assume que tem (para evitar falsos negativos)
        return True 
    except:
        return False # Na dúvida, se der erro de conexão, marca falso

# --- 3. SITEMAPS E URLS (Padrão) ---
def get_product_sitemaps(main_url):
    try:
        print(f"Buscando sitemap principal: {main_url}", flush=True)
        response = scraper.get(main_url, timeout=10)
        print(f"Status sitemap principal: {response.status_code}", flush=True)
        
        soup = BeautifulSoup(response.content, 'xml')
        sitemaps = []
        for loc in soup.find_all('loc'):
            url = loc.text.strip()
            # Filtro mais abrangente para garantir que pega o sitemap de produtos
            if 'products' in url:
                sitemaps.append(url)
        print(f"Sitemaps encontrados: {sitemaps}", flush=True)
        return sitemaps
    except Exception as e:
        print(f"Erro ao buscar sitemap principal: {e}", flush=True)
        return []

def get_product_urls(sitemap_url):
    try:
        print(f"Buscando URLs em: {sitemap_url}", flush=True)
        response = scraper.get(sitemap_url, timeout=10)
        soup = BeautifulSoup(response.content, 'xml')
        urls = []
        for loc in soup.find_all('loc'):
            url = loc.text.strip()
            if '/products/' in url:
                urls.append(url)
        print(f"URLs encontradas: {len(urls)}", flush=True)
        return urls
    except Exception as e:
        print(f"Erro ao buscar URLs do sitemap {sitemap_url}: {e}", flush=True)
        return []

# --- 4. EXTRAÇÃO DE DADOS INTELIGENTE ---
def get_product_data(product_url):
    json_url = f"{product_url}.json"
    
    try:
        response = scraper.get(json_url, timeout=15)
        if response.status_code != 200: return {"error": f"Status {response.status_code}"}
            
        data = response.json().get('product')
        if not data or not data.get('variants'): return {"error": "Dados inválidos"}
            
        variant = data['variants'][0]
        
        # Dados básicos
        title = data.get('title', 'Sem Título')
        product_type = data.get('product_type', 'Outros')
        tags = data.get('tags', '')
        if isinstance(tags, list): tags = ", ".join(tags)
        
        image_url = ""
        if data.get('images') and len(data['images']) > 0:
            image_url = data['images'][0].get('src', '')
            
        sku = variant.get('sku', '')

        # Preços
        try: price = float(variant.get('price', 0))
        except: price = 0.0
        
        original_price = variant.get('compare_at_price')
        if original_price:
            try:
                original_price = float(original_price)
                is_promo = True
            except:
                original_price = price
                is_promo = False
        else:
            original_price = price
            is_promo = False
            
        # --- LÓGICA DE DISPONIBILIDADE (CORREÇÃO) ---
        # 1. Tenta pegar do JSON
        available = variant.get('available')
        method = "JSON"
        
        # 2. Se for None (JSON escondeu a info), vai pro HTML
        if available is None:
            available = check_html_availability(product_url)
            method = "HTML_CHECK"
            
        return {
            "title": title,
            "sku": sku,
            "categoria": product_type,
            "url": product_url,
            "imagem_url": image_url,
            "tags": tags,
            "original": original_price,
            "current": price,
            "is_promo": is_promo,
            "available": available,
            "id": variant.get('id'),
            "method": method
        }
        
    except Exception as e:
        return {"error": str(e)}

# --- 5. LOOP PRINCIPAL ---
def main():
    conn = setup_database()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("--- FASE 1: Mapeando produtos ---")
    sitemaps = get_product_sitemaps(MAIN_SITEMAP_URL)
    todos_links = []
    for sm in sitemaps:
        print(f"Lendo sitemap: {sm}")
        urls = get_product_urls(sm)
        print(f"  > Encontrados {len(urls)} produtos.")
        todos_links.extend(urls)
    
    total = len(todos_links)
    print(f"\n📋 Coletando {total} produtos (Modo Sequencial Seguro)...")
    
    salvos = 0
    
    with tqdm(total=total, unit="prod") as pbar:
        for url in todos_links:
            result = get_product_data(url)
            
            if result and "error" not in result:
                cursor.execute('''
                    INSERT INTO historico_precos 
                    (data_coleta, produto_nome, sku, categoria, url, imagem_url, tags, preco_original, preco_atual, em_promocao, disponivel, variante_id, metodo_verificacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, 
                    result['title'], 
                    result['sku'], 
                    result['categoria'], 
                    result['url'], 
                    result['imagem_url'],
                    result['tags'],
                    result['original'], 
                    result['current'], 
                    result['is_promo'], 
                    result['available'], 
                    result['id'],
                    result['method']
                ))
                salvos += 1
                if salvos % 10 == 0: conn.commit()
            else:
                # Opcional: Logar erro
                # tqdm.write(f"Erro em {url}: {result.get('error')}")
                pass
            
            pbar.update(1)
            # Delay para evitar bloqueio
            time.sleep(random.uniform(0.5, 1.0))

    conn.commit()
    conn.close()
    print(f"\n🏁 Sucesso! {salvos} produtos verificados.")

if __name__ == "__main__":
    main()