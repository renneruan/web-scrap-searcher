import modulo_crawler
import modulo_buscador
import pymysql

#!pip install pymysql

if __name__ == "__main__":
    # url = "https://brasilescola.uol.com.br/animais/tigre.htm"
    url = input("Informe a URL: ")

    profundidade = int(input("Informe a profundidade (recomendada: 2): "))
    # profundidade = 2
    print("Profundidade escolhida:", profundidade)

    try:
        # Necessário alterar para as crendenciais do seu banco de dados
        connection = pymysql.connect(
            host="localhost",
            user="root",
            passwd="1234",
            db="indice",
            use_unicode=True,
            charset="utf8mb4",
            autocommit=True,
        )
        print("Conexão com o BD bem sucedida!")

        modulo_crawler.crawler([url], profundidade, connection)

        palavras = input(
            "Digite as duas palavras desejadas (preferência para radical, ex: felin tigr): "
        )

        # palavras = "felin tigr"
        modulo_buscador.pesquisa(palavras, connection)
    except pymysql.MySQLError as e:
        # Captura todas as exceções MySQLError
        print(f"Erro ao conectar ao banco de dados: {e}")

    finally:
        # Verifica se a variável connection foi declarada para fechá-la
        if "connection" in locals() and connection.open:
            connection.close()
