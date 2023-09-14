import osmnx as ox
from graph import Graph
from pathFinder import FloydWarshall, Euler
import strategy

graph_class = None
floyd = FloydWarshall()
euler = Euler()
ch = None
context = None


def coords(location, size, jti, id_cartier):
    """
        Funcția coords instanțiază obiectul de tip Graph și returnează
        coordonatele nodurilor digrafului.

        Parametrii:
            location (list): conține coordonatele centrului zonei alese
            size (int): valoarea razei cercului creat având drept centru
                        punctul cu coordonatele din parametrul location
            jti (str): identificatorul unic al jwt-ului utilizatorului
            id_cartier (int): identificatorul cartierului
        Returnează:
            (None): dacă există erori la crearea digrafului
            (Dictionary): dicționar care are drept cheie numărul nodului,
                          iar valoarea este o listă care conține coordonatele
                          punctului
    """
    global graph_class
    graph_class = Graph(location, int(size), jti, id_cartier)
    return graph_class.get_coordinates(jti, id_cartier)


def get_adj_matrix(jti, id_cartier):
    """
        Funcția get_adj_matrix întoarce matricea de adiacență a
        digrafului și dicționarul cu indecșii nodurilor.

        Parametrii:
            jti (str): identificatorul unic al jwt-ului utilizatorului
            id_cartier (int): identificatorul cartierului

        Returnează:
            adjacency (list(list)): matricea de adiacență
            nodes (Dictionary): dicționar de forma {nod: i}, i={0..N},
                N = numărul de noduri din digraf sau None și None în
                cazul în care există erori la crearea digrafului.
    """
    adjacency, nodes = graph_class.adjacency_matrix(jti, id_cartier)
    return adjacency, nodes


def get_context():
    """
        Funcția get_context instanțiază contextul.

        Returnează:
            context (ChinesePostmanSolver): contextul de rezolvare a problemei poștașului chinez.
    """
    context = strategy.Context(strategy.ChinesePostmanStrategy(graph_class, floyd, euler))
    return context


def get_path(jti, id_cartier):
    """
        Funcția get_path returnează traseul optimizat pe care trebuie
        să îl parcurgă utilizatorul.

        Parametrii:
            jti (str): identificatorul unic al jwt-ului utilizatorului
            id_cartier (int): identificatorul cartierului

        Returnează:
            (None): în cazul în care digraful nu este conectat.
            (list): listă care conține ordinea de parcurgere a nodurilor.
    """
    global context
    return get_context().path(jti, id_cartier)

# următoarele două funcții sunt preluate de la adresa:
# https://github.com/gboeing/osmnx-examples/blob/main/notebooks/03-graph-place-queries.ipynb


def check_address(cartier, oras):
    """
        Funcția check_address verifică dacă adresa introdusă există sau nu.

        Parametrii:
            cartier (str): denumirea cartierului căutat.
            oras (str): denumirea orașului căutat.

        Returnează:
            (boolean): True dacă aceasta există, False în caz contrar.
    """
    try:
        results = ox.geocode(f'{cartier}, {oras}')
        if results:
            return True
        else:
            return False
    except Exception as e:
        return False


def check_city(oras):
    """
        Funcția check_city verifică dacă orașul introdus există sau nu.

        Parametrii:
            oras (str): denumirea orașului căutat.

        Returnează:
            (boolean): True dacă acesta există, False în caz contrar.
    """
    try:
        check = ox.geocode_to_gdf(oras)
        if check.empty:
            return False
        else:
            return True
    except Exception as e:
        return False
