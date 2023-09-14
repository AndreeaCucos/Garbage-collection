import networkx as nx
from neo4j import GraphDatabase
import config2

driver = GraphDatabase.driver(config2.uri, auth=(config2.username, config2.password))


def save_graph_to_neo4j(graph, jti, id_cartier):
    """
        Funcția save_graph_to_neo4j() se ocupă cu salvarea nodurilor
        și a conexiunilor dintre acestea
        în baza de date Neo4j folosind drept identificator unic al
        înregistrării câmpul jti din
        cadrul token-ului utilizatorului și identificatorul cartierului.

        Parametrii:
            graph (networkx.classes.multidigraph.MultiDiGraph): digraful generat de OSMnx
            jti (str): identificatorul unic al jwt-ului utilizatorului
            id_cartier (int): identificatorul cartierului
    """
    with driver.session() as session:
        # Creăm un nou nod cu proprietățile jti și location.
        # Dacă acesta există deja în baza de date nu are loc
        # nicio acțiune.
        query = """
                MERGE (g:Graph {jti: $jti, location: $location})
                """
        session.run(query, jti=jti, location=str(id_cartier))

        for node, data in graph.nodes(data=True):
            # Creăm relațiile dintre nodul identificator al digrafului
            # și restul nodurilor aferente digrafului corespunzător
            # zonei selectate de utilizator.
            # Relația este creată prin ultima linie a codului,
            # MERGE (g)-[:CONTAINS]->(n)
            query = """
                        MERGE (n:Node {id: $id, lat: $lat, lon: $lon})
                        MERGE (g:Graph {jti: $jti, location: $location})
                        MERGE (g)-[:CONTAINS]->(n)
                    """
            session.run(query, id=node, lat=data["y"], lon=data["x"],
                        jti=jti, location=str(id_cartier))

        # Extragem denumirile străzilor(arcelor) digrafului.
        streets = {}
        for u, v, data in graph.edges(data=True):
            key = f"{u}, {v}"
            if 'name' in data:
                streets[key] = data['name']
            else:
                streets[key] = ''
        lengths = nx.get_edge_attributes(graph, 'length')
        # Creăm relațiile dintre nodurile digrafului.
        for key in lengths:
            u = key[0]
            v = key[1]
            length = lengths[key]
            street = streets[f"{u}, {v}"]
            # Creăm relația dintre nodurile u și v.
            # Relația conține la rândul ei o serie de proprietăți:
            # lungimea și denumirea străzii delimitată de cele două noduri.
            query = """
                        MATCH (u:Node {id: $u})
                        MATCH (v:Node {id: $v})
                        MERGE (u)-[:CONNECTED_TO {length: $length, 
                        street: $street}]->(v)
                     """
            session.run(query, u=u, v=v, length=length, street=street)


def retrieve_graph_from_neo4j(jti, id_cartier):
    """
        Funcția retrieve_graph_from_neo4j se ocupă cu extragerea
        informațiilor aferente digrafului curent afișat
        pe interfață din baza de date utilizând câmpul jti
        din cadrul jwt-ului utilizatorului și id-ul cartierului.

        Parametrii:
            jti (str): identificatorul unic al jwt-ului utilizatorului
            id_cartier (int): identificatorul cartierului

        Returnează:
            nodes (list) - conține nodurile și coordonatele aferente
            edges (list) - conține legăturile dintre noduri împreună
                            cu distanța dintre acestea
    """
    with driver.session() as session:
        # Extragem toate nodurile care sunt legate de nodul Graph cu proprietățile
        # primite de funcție ca parametrii.
        query = """
            MATCH (g:Graph {jti: $jti, location: $location})-[:CONTAINS]->(n:Node)
            RETURN n.id AS node_id, n.lat AS lat, n.lon AS lon
        """
        result = session.run(query, jti=jti, location=str(id_cartier))

        nodes = [(record["node_id"], {"y": record["lat"], "x": record["lon"]})
                 for record in result]

        # Extragem informațiile despre relațiile dintre nodurile digrafului
        # salvat în baza de date.
        query = """
            MATCH (u:Node)-[r:CONNECTED_TO]->(v:Node)
            RETURN u.id AS node1_id, v.id AS node2_id, r.length AS length, 
            r.street AS street
        """
        result = session.run(query)
        edges = [(record["node1_id"], record["node2_id"], record["length"],
                  record["street"]) for record in result]
    return nodes, edges


def retrieve_adj_nodes(jti, id_cartier):
    """
        Funcția retrieve_adj_nodes determină matricea de adiacență a
        digrafului, un dicționar care conține
        valoarea fiecărui nod, în ordine crescătoare, având asignat
        un index pornind de la 0 și denumirile străzilor. Matricea de
        adiacență are în locurile în care nodurile sunt conectate
        valoarea distanței dintre acestea.

        Parametrii:
            jti (str): identificatorul unic al jwt-ului utilizatorului
            id_cartier (int): identificatorul cartierului

        Returnează:
            adj_matrix (list(list)): matricea de adiacență
            nodes_to_number (Dictionary): dicționar de forma {nod: i},
                                i={0..N}, N = numărul de noduri din digraf
            streets (list): listă în care sunt salvate denumirile străzilor
                            împreună cu cele două noduri care le
                            delimitează.
    """
    nodes, edges = retrieve_graph_from_neo4j(jti, id_cartier)
    nodes_to_number = {}
    index = 0
    for i in sorted(nodes):
        nodes_to_number[i[0]] = index
        index += 1
    streets = []
    adj_matrix = [[0 for _ in range(len(nodes))] for _ in range(len(nodes))]
    for key in nodes_to_number:
        for second_key in edges:
            if key in second_key:
                i = nodes_to_number[key]
                if key == second_key[0]:
                    j = nodes_to_number[second_key[1]]
                    adj_matrix[i][j] = second_key[2]
                    streets.append(([i, j], second_key[3]))
                else:
                    j = nodes_to_number[second_key[0]]
                    adj_matrix[j][i] = second_key[2]
                    streets.append(([i, j], second_key[3]))
    return adj_matrix, nodes_to_number, streets


def retrieve_coord(jti, id_cartier):
    """
        Funcția retrieve_coord crează un dicționar care are
        drept cheie valoarea nodului și valoarea este o listă
        care conține coordonata pe y și cea pe x a nodului. Aceasta
        ajută la afișarea nodurilor pe hartă în partea de frontend.

        Parametrii:
            jti (str): identificatorul unic al jwt-ului utilizatorului
            id_cartier (int): identificatorul cartierului

        Returnează:
            coords (Dictionary): conține coordonatele nodurilor
                                din digraf

    """
    nodes, edges = retrieve_graph_from_neo4j(jti, id_cartier)
    coords = {}
    for node in nodes:
        coords[node[0]] = [node[1]['y'], node[1]['x']]

    return coords


def delete_nodes(jti, id_cartier):
    """
        Funcția delete_nodes șterge din baza de date digraful
        aferent utilizatorului și a zonei pe care a parcurs-o.

        Parametrii:
            jti (str): identificatorul unic al jwt-ului utilizatorului
            id_cartier (int): identificatorul cartierului
    """
    # Căutăm toate nodurile care sunt conectate de nodul în care sunt salvate
    # informațiile utilizatorului și le ștergem, împreună cu relațiile dintre acestea.
    # Este șters inclusiv nodul identificator.
    query = (
        f"MATCH (nodeToDelete)-[r]-(connectedNode) "
        f"WHERE nodeToDelete.jti = '{jti}' and nodeToDelete.location='{id_cartier}' "
        "DETACH DELETE nodeToDelete, r, connectedNode"
    )
    with driver.session() as session:
        session.run(query, jti=jti, location=id_cartier)
    driver.close()


def delete_by_jti(jti):
    """
        Funcția delete_by_jti șterge din baza de date digraful
        aferent utilizatorului în momentul în care a expirat token-ul jwt.

        Parametrii:
            jti (str): identificatorul unic al jwt-ului utilizatorului
    """
    query = (
        f"MATCH (nodeToDelete)-[r]-(connectedNode) "
        f"WHERE nodeToDelete.jti = '{jti}'"
        "DETACH DELETE nodeToDelete, r, connectedNode"
    )
    with driver.session() as session:
        session.run(query, jti=jti)
    driver.close()


def check_graph_exists(jti, id_cartier):
    """
        Funcția check_graph_exists verifică dacă în baza de date
        există o înregistrare asociată utilizatorului curent.

        Parametrii:
            jti (str): identificatorul unic al jwt-ului utilizatorului
            id_cartier (int): identificatorul cartierului
    """
    # Căutăm un nod după valorile jti și location primite drept parametrii.
    query = f"MATCH (n) WHERE n.jti ='{jti}' and n.location='{id_cartier}' RETURN n"
    check = False  # Presupunem că nu există.
    with driver.session() as session:
        res = session.run(query, jti=jti, location=id_cartier)

        if res.single() is None:
            check = False
        else:
            check = True
    driver.close()
    print(check)
    return check
