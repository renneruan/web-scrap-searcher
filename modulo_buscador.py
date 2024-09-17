from collections import defaultdict

WITHOUT_DATA = -1


def score_by_frequence(linhas):
    contagem = dict([(linha[0], 0) for linha in linhas])
    for linha in linhas:
        # print(linha)
        contagem[linha[0]] += 1
    return contagem


def score_by_distance(linhas):
    if len(linhas) == 0 or len(linhas[0]) <= 2:
        # Se tiver menos que 2 palavras, distância será 1
        return dict([(linha[0], 1.0) for linha in linhas])

    # Inicializa scores de distância com valor máximo
    distancias = dict([(linha[0], 1000000) for linha in linhas])
    for linha in linhas:
        # Calcula o módulo da distância entre as palavras
        dist = sum([abs(linha[i] - linha[i - 1]) for i in range(2, len(linha))])
        # Se distância menor que a registrada substitui pelo novo valor
        if dist < distancias[linha[0]]:
            distancias[linha[0]] = dist
    return distancias


def score_by_location(linhas):
    # Inicializa scores de localização com valor máximo
    localizacoes = dict([linha[0], 1000000] for linha in linhas)
    for linha in linhas:
        soma = sum(linha[1:])  # Soma localização das palavras

        # Se valor menor que o já registrado substitui pelo novo
        if soma < localizacoes[linha[0]]:
            localizacoes[linha[0]] = soma
    return localizacoes


def retrieve_word_id(word, connection):
    retorno = WITHOUT_DATA  # não existe a palavra no índice
    with connection.cursor() as cursor:
        cursor.execute("select idpalavra from palavras where palavra = %s", word)
        if cursor.rowcount > 0:
            retorno = cursor.fetchone()[0]
    return retorno


def search_words(words, connection):
    fields_names = "p1.idurl"
    tables_names = ""
    clauses = ""
    words_ids = []

    words_to_search = words.split(" ")
    table_number = 1
    for count, palavra in enumerate(words_to_search):
        word_id = retrieve_word_id(palavra, connection)

        if word_id > 0:
            words_ids.append(word_id)
            if table_number > 1:
                tables_names += ", "
                clauses += " and "
                clauses += "p%d.idurl = p%d.idurl and " % (
                    table_number - 1,
                    table_number,
                )
            fields_names += ", p%d.localizacao" % table_number
            tables_names += " palavra_localizacao p%d" % table_number
            clauses += "p%d.idpalavra = %d" % (table_number, word_id)
            table_number += 1
        else:
            print(f"Palavra {count} não encontrada.")

    query = "SELECT %s FROM %s WHERE %s" % (
        fields_names,
        tables_names,
        clauses,
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = [row for row in cursor]

        # linha apresenta [(idurl, idp1, idp2)...]
        return rows


def get_url_name_by_id(idurl, connection):
    retorno = ""

    with connection.cursor() as cursor:
        cursor.execute("select url from urls where idurl = %s", idurl)
        if cursor.rowcount > 0:
            retorno = cursor.fetchone()[0]
    return retorno


def get_best_by_score_type(type, rows):
    reverse = 0
    if type == "frequence":
        reverse = 1
        scores = score_by_frequence(rows)
    elif type == "distance":
        scores = score_by_distance(rows)
    elif type == "location":
        scores = score_by_location(rows)
    else:
        scores = dict([row[0], 0] for row in rows)

    scoresordenado = sorted(
        [(score, url) for (url, score) in scores.items()], reverse=reverse
    )
    return scoresordenado


def get_score_by_weight(s1, s2, s3):
    novos_scores = defaultdict(list)

    # Juntamos as listas de scores e invertemos para uma lista de objetos
    # Em que o ID dos objetos é o id da url
    for lista in [s1, s2, s3]:
        for score, id_ in lista:
            novos_scores[id_].append(score)
    lista_por_id = [{id_: valores} for id_, valores in novos_scores.items()]

    pesos_finais = {}
    for scores_url in lista_por_id:
        for url, values in scores_url.items():
            # Frequência
            peso1 = values[0] * 0.01
            # Distância
            peso2 = (100 - values[1]) / 30
            # Localização
            peso3 = (1000 - values[2]) / 200

            pesos_finais[url] = peso1 + peso2 + peso3

    # Função lambda para fazer a ordenação pelo valor do score e não pelo ID
    return sorted(pesos_finais.items(), key=lambda item: item[1], reverse=1)


def pesquisa(consulta, connection):
    rows = search_words(consulta, connection)

    sorted_scores_1 = get_best_by_score_type("frequence", rows)
    sorted_scores_2 = get_best_by_score_type("distance", rows)
    sorted_scores_3 = get_best_by_score_type("location", rows)

    print("\nResultados para score por frequência")
    for score, idurl in sorted_scores_1[0:3]:
        print("%.2f\t%s" % (score, get_url_name_by_id(idurl, connection)))

    print("\nResultados para score por distância")
    for score, idurl in sorted_scores_2[0:3]:
        print("%.2f\t%s" % (score, get_url_name_by_id(idurl, connection)))

    print("\nResultados para score por localização")
    for score, idurl in sorted_scores_3[0:3]:
        print("%.2f\t%s" % (score, get_url_name_by_id(idurl, connection)))

    scores_peso = get_score_by_weight(sorted_scores_1, sorted_scores_2, sorted_scores_3)
    print("\nResultados com utilização de pesos para scores")
    for idurl, score in scores_peso[0:3]:
        print("%.2f\t%s" % (score, get_url_name_by_id(idurl, connection)))
