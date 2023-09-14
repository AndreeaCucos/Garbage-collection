from pathFinder import FloydWarshallInterface, EulerInterface
from graph import GraphInterface
from abc import ABC, abstractmethod


# Structura claselor șablonului Strategy au fost preluate de la adresa:
# https://refactoring.guru/design-patterns/strategy/python/example
class Context:
    def __init__(self, strategy):
        self.strategy = strategy

    def set_strategy(self, strategy):
        self.strategy = strategy

    def path(self, jti, id_cartier):
        return self.strategy.findPath(jti, id_cartier)


class Strategy(ABC):
    @abstractmethod
    def findPath(self, jti, id_cartier):
        pass


class ChinesePostmanStrategy(Strategy):
    def __init__(self, graph: GraphInterface, floyd: FloydWarshallInterface, euler: EulerInterface):
        self.graph = graph
        self.floyd = floyd
        self.euler = euler

    def findPath(self, jti, id_cartier):
        """
            Funcția findPath determină traseul optimizat prin
            rezolvarea problemei poștașului chinez.

            Parametrii:
                jti (str): identificatorul unic al jwt-ului utilizatorului
                id_cartier (int): identificatorul cartierului

            Returnează:
                (list): conține ordinea de parcurgere a nodurilor
                        sau None în cazul în care digraful nu este conex.
        """
        # Inițial verificăm dacă digraful este conex și dacă este rezolvabil.
        if self.graph.is_connected() and self.graph.check_if_solvable():
            # Determinăm matricea de adiacență.
            adjacency, nodes = self.graph.adjacency_matrix(jti, id_cartier)
            # Determinăm nodurile de grad impar.
            odds = self.graph.get_odd_vertices(adjacency)
            print(len(odds))
            if len(odds) >= 20:
                return None, None
            else:
                # Creăm digraful sub forma unui dicționar astfel:
                # {nod1: {nod2: i}}, unde i = 1 dacă există arc
                # de la nod1 la nod2, 0 în caz contrar.(valoarea
                # lui i indică numărul de parcurgeri al unui arc)
                graph_edges = self.graph.create_traverse_graph()
                # Dacă nu există noduri de grad impar în digraf se poate găsi imediat
                # un ciclu eulerian.
                if len(odds) == 0:
                    print('Nu exista noduri care au grad de intrare diferit de cel de iesire.')
                    # Creăm cele două liste în care salvăm gradele de intrare, respectiv
                    # de ieșire, pentru fiecare nod.
                    in_degrees, out_degrees = self.graph.get_in_out_degrees(graph_edges)

                    # Determinăm ciclul eulerian.
                    cycle = self.euler.euler_cycle_graph(graph_edges, adjacency,
                                                     in_degrees, out_degrees)
                    print(cycle)
                    # Extragem denumirile străzilor aferente ordinii de parcurgere
                    # ale arcelor.
                    street_names = []
                    streets = self.graph.get_streets()
                    i = 0
                    while i < len(cycle) - 1:
                        pair = [cycle[i], cycle[i + 1]]
                        for street in streets:
                            if street[0] == pair:
                                name = ' - '
                                if street[1] != '':
                                    name = street[1]
                                record = (i, f'Intersecția {pair[0]} spre '
                                         f'intersecția {pair[1]}', name)
                                if record not in street_names:
                                    street_names.append(record)
                        i += 1
                    return cycle, street_names
                else:
                    d_plus = []  # listă de noduri care necesită arce de intrare
                    d_minus = []  # listă de noduri care necesită arce de ieșire

                    # Formăm cele două liste care conțin nodurile cu deficit de intrare, respectiv de ieșire.
                    for node in odds:
                        if odds[node] > 0:
                            cnt = odds[node]
                            while cnt != 0:
                                d_plus.append(node)
                                cnt -= 1
                        else:
                            cnt = odds[node]
                            while cnt != 0:
                                d_minus.append(node)
                                cnt += 1
                    print(f"NUMAR NODURI GRAD IMPAR: {len(odds)}")
                    print(f'd_minus = {d_minus}')
                    print(f'd_plus = {d_plus}')
                    # Determinăm listele care conțin perechile de noduri
                    # formate din nodurile ale căror grad de intrare diferă de cel de ieșire.
                    pairs = self.graph.get_pairs(d_minus, d_plus)
                    # Apelăm metoda de calcul a algoritmului Floyd-Warshall.
                    self.floyd.floyd_warshall(adjacency)
                    # Parcurgem lista de liste de perechi. Pentru fiecare listă din aceasta,
                    # calculăm costul drumului pentru fiecare pereche și le adunăm.
                    # Lista de drumuri împreună cu costul ei total este salvată în
                    # dicționarul sums.
                    sums = {}
                    index = 0
                    for lista_mea in pairs:
                        sums[index] = 0
                        total_cost = 0
                        lista = []
                        for pair in lista_mea:
                            path = self.floyd.makePath(pair[0], pair[1])
                            cost = self.graph.get_cost_from_path(path)
                            total_cost += cost
                            lista.append(path)
                        sums[index] = [lista, total_cost]
                        index += 1
                    # Din dicționarul de drumuri determinat anterior alegem
                    # înregistrarea al cărui cost total este minim.
                    min_sum = float('inf')
                    # Lista paths_to_double va conține lista de drumuri care trebuie
                    # parcurse de mai multe ori.
                    paths_to_double = []
                    for path in sums:
                        if sums[path][1] < min_sum:
                            min_sum = sums[path][1]
                            paths_to_double = sums[path][0]

                    print(f'dublez {paths_to_double} cu costul {min_sum}')

                    # Adăugăm parcurgerea drumurilor determinate anterior în dicționarul
                    # de parcurgeri.
                    self.graph.double_paths_in_graph(graph_edges, paths_to_double)
                    # Determinăm pentru fiecare nod din digraf gradul de intrare și de ieșire.
                    in_degrees, out_degrees = self.graph.get_in_out_degrees(graph_edges)
                    # Calculăm pentru fiecare nod diferența dintre gradul de intrare și cel de
                    # ieșire.
                    diff = list(map(lambda x, y: x - y, in_degrees, out_degrees))
                    # Dacă diferența aceasta este 0 pentru toate nodurile înseamnă că în digraf
                    # nu mai există noduri de grad impar și poate fi determinat un ciclu eulerian.
                    if all(x == 0 for x in diff):
                        print('Se poate gasi un ciclu eulerian')
                        in_degrees, out_degrees = self.graph.get_in_out_degrees(graph_edges)
                        cycle = self.euler.euler_cycle_graph(graph_edges, adjacency, in_degrees, out_degrees)
                        print(cycle)
                        # Extragem denumirile străzilor.
                        street_names = []
                        streets = self.graph.get_streets()
                        i = 0
                        while i < len(cycle) - 1:
                            for street in streets:
                                pair = [cycle[i], cycle[i + 1]]
                                if street[0] == pair:
                                    name = ' - '
                                    if street[1] != '':
                                        name = street[1]
                                    record = (i, f'Intersecția {pair[0]} spre intersecția {pair[1]}', name)
                                    if record not in street_names:
                                        street_names.append(record)
                            i += 1
                        return cycle, street_names
                    else:
                        # În caz contrar, când încă există noduri de grad impar, problema nu poate
                        # fi rezolvată.
                        return None, None
        else:
            # Digraful nu este conex.
            print(f'Digraful nu e conex.')
            return None, None
