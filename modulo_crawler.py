from bs4 import BeautifulSoup
import urllib3
from urllib.parse import urljoin
import re
import nltk

# !pip install lxml
# !pip install nltk
# !pip install beautifulsoup4


http = urllib3.PoolManager()  # Variável para realizar conexões

WITHOUT_DATA = -1
PAGE_WITH_WORDS = -2


def get_clean_text(sopa):
    """
    Realiza a limpeza do HTML da URL, retirando tags de script, style
      e espaços em branco
    """
    for tags in sopa(["script", "style"]):
        tags.decompose()
    return " ".join(sopa.stripped_strings)


def get_processed_text(text):
    """
    Processa o texto HTML para remover stop words, resgata o radical das
      palavras e realiza a transformação para minúsculo
    """

    stop_words = nltk.corpus.stopwords.words("portuguese")
    stemmer = nltk.stem.RSLPStemmer()
    splitter = re.compile("\\W+")

    # Resgata apenas conjunto de letras consideradas palavras
    splitted_text = [p for p in splitter.split(text) if p != ""]

    processed_words = []
    for word in splitted_text:
        # Retorna radical de palavras com minúsculo
        stemmed_word = stemmer.stem(word.lower())

        # Insere nas palavras retornadas todas que não estão nas stop words
        # ou que possuem tamanho maior que 1
        if (stemmed_word not in stop_words) and len(word) > 1:
            processed_words.append(stemmed_word)

    return processed_words


def retrieve_page(url, connection):
    """
    Resgata página no banco de dados a partir da URL fornecida
    Retorna se a página é existente e se tem palavras já inseridas
    """

    return_value = WITHOUT_DATA
    with connection.cursor() as cursor_url:
        # Query para resgatar url no banco
        cursor_url.execute("SELECT idurl FROM urls WHERE url = %s", url)

        if cursor_url.rowcount > 0:
            idurl = cursor_url.fetchone()[0]

            # Caso url no banco, verifica existência de palavras a associadas
            with connection.cursor() as cursor_word:
                cursor_word.execute(
                    "SELECT idurl FROM palavra_localizacao WHERE idurl = %s", idurl
                )

                if cursor_word.rowcount > 0:
                    return_value = PAGE_WITH_WORDS
                else:
                    # Caso página exista sem palavras, retorna id para inserção
                    return_value = idurl

    return return_value


def insert_page(url, connection):
    """
    Insere página a partir de uma URL fornecida
    """
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO urls (url) VALUES (%s)", url)
        # Após a inserção o cursor armazena o ID do elemento inserido
        new_page_id = cursor.lastrowid
        return new_page_id


def retrieve_word(word, connection):
    """
    Resgata palavra salva e indexada em banco de dados
    """
    retorno = WITHOUT_DATA
    with connection.cursor() as cursor:
        cursor.execute("select idpalavra from palavras where palavra = %s", word)
        if cursor.rowcount > 0:
            # print(f"Palavra '{word}' existente")
            retorno = cursor.fetchone()[0]
        # else:
        # print(f"Palavra '{word}' não cadastrada")

    return retorno


def insert_word(word, connection):
    """
    Inserção de nova palavra em banco de dados
    """
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO palavras (palavra) VALUES (%s)", word)
        new_word_id = cursor.lastrowid
        return new_word_id


def insert_word_location(page_id, word_id, location, connection):
    """
    Armazena localização da palavra na URL em que esta foi resgatada
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO palavra_localizacao (idurl, idpalavra, localizacao) VALUES (%s, %s, %s)",
            (page_id, word_id, location),
        )
        word_location_id = cursor.lastrowid
        return word_location_id


def indexer(url, sopa, connection):
    """
    Função para indexar o texto da url desejada, verificado a existência
    de registros
    """
    page_status = retrieve_page(url, connection)

    """
    Verifica status da página, caso cadastrada e com palavras retorna
    Caso não foi possível encontrar a página, registra a url
    Caso registrada mas sem palavras, utiliza o ID para armazenar palavras
    """
    if page_status == PAGE_WITH_WORDS:
        print("URL já indexada e com palavras: " + url)
        return
    elif page_status == WITHOUT_DATA:
        print("URL não encontrada, necessário inserção: " + url)
        page_id = insert_page(url, connection)
    elif page_status > 0:
        print("URL existente porém sem palavras: " + url)
        page_id = page_status

    # Processamento de texto para indexação de palavras
    cleaned_text = get_clean_text(sopa)
    words = get_processed_text(cleaned_text)
    for count, word in enumerate(words):

        word_id = retrieve_word(word, connection)
        if word_id == WITHOUT_DATA:
            word_id = insert_word(word, connection)

        insert_word_location(page_id, word_id, count, connection)


def crawler(paginas, profundidade, connection):
    """
    Função de Crawler
    Realiza a indexação em profundidade de textos HTML acessados a partir de uma url raiz
    Navega-se para os links filhos, de acordo com o parâmetro profundidade
    """

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for i in range(profundidade):
        novas_paginas = set()  # Conjunto

        print(f"Analisando profundidade {i+1}")
        for count, pagina in enumerate(paginas):
            print(f"Página {count+1}/{len(paginas)}")
            print(f"Recuperando dados para a página {pagina}")

            try:
                dados_pagina = http.request("GET", pagina)
            except:
                print("Erro ao abrir a pagina " + pagina)
                continue

            sopa = BeautifulSoup(dados_pagina.data, "lxml")
            indexer(pagina, sopa, connection)

            links = sopa.find_all("a")

            for link in links:
                if "href" in link.attrs:
                    url = urljoin(pagina, str(link.get("href")))
                    if url.find("'") != -1:
                        continue
                    url = url.split("#")[0]  # pego tudo antes do #
                    if url[0:4] == "http":  # se comeca com http
                        novas_paginas.add(url)

        paginas = novas_paginas
        print("Total de paginas presentes nesta URL: ", len(paginas))
