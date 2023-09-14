import itertools

import osmnx as ox
import networkx as nx
import time
from abc import ABC, abstractmethod
import graph_database


class GraphInterface(ABC):
    @abstractmethod
    def is_connected(self):
        pass

    @abstractmethod
    def check_if_solvable(self):
        pass

    @abstractmethod
    def adjacency_matrix(self, jti, location):
        pass

    @abstractmethod
    def get_coordinates(self, jti, id_cartier):
        pass

    @abstractmethod
    def get_odd_vertices(self, adjacency_matrix):
        pass

    @abstractmethod
    def get_cost_from_path(self, path):
        pass

    @abstractmethod
    def create_traverse_graph(self):
        pass

    @abstractmethod
    def double_paths_in_graph(self, graph_edges, paths_to_double):
        pass

    @abstractmethod
    def get_in_out_degrees(self, graph_edges):
        pass

    @abstractmethod
    def get_streets(self):
        pass

    @abstractmethod
    def get_pairs(self, d_minus, d_plus):
        pass


class Graph(GraphInterface):
    __graph = None

    def __init__(self, location, size, jti, id_cartier):
        # Încercăm să extragem digraful pe baza informațiilor
        # transmise de utilizator.
        # În cazul unor erori la creare, toate informațiile legate
        # de digraf vor fi None.
        try:
            l = [float(location[0]), float(location[1])]
            # Extragem digraful pe baza informațiilor primite.
            start_time = time.time()

            G = ox.graph_from_point(l, dist=size, simplify=True,
                                    network_type='drive', truncate_by_edge=True)

            # Extragem componentele conexe din digraful creat anterior.
            strongly_connected_components = nx.strongly_connected_components(G)

            # Determinăm cea mai mare componentă conexă și o folosim mai departe în calcule.
            largest_strongly_connected_component = max(strongly_connected_components, key=len)
            self.__graph = G.subgraph(largest_strongly_connected_component)
            end_time = time.time()

            elapsed_time = end_time - start_time
            print("CREARE DIGRAF: {:.2f} seconds".format(elapsed_time))

            # Dacă există deja un digraf salvat în baza de date Neo4j aferent utilizatorului
            # curent îl ștergem. (înseamnă că a introdus altă valoare pentru rază)
            if graph_database.check_graph_exists(jti, id_cartier):
                start_time = time.time()
                graph_database.delete_nodes(jti, id_cartier)
                end_time = time.time()
                elapsed_time = end_time - start_time
                print("STERGERE DIGRAF: {:.2f} seconds".format(elapsed_time))
            graph_database.save_graph_to_neo4j(self.__graph, jti, id_cartier)

            self.nodes_to_number = {}
            self.streets = []
            self.adj_matrix = [[0 for i in range(len(self.__graph.nodes))]
                               for j in range(len(self.__graph.nodes))]

        except Exception as exp:
            self.__graph = None
            self.adj_matrix = self.nodes_to_number = self.streets = None
            self.coords = None

    def adjacency_matrix(self, jti, id_cartier):
        """
            Funcția adjacency_matrix întoarce matricea de adiacență
            a digrafului și dicționarul cu indecșii nodurilor.

            Parametrii:
                jti (str): identificatorul unic al jwt-ului utilizatorului
                id_cartier (int): identificatorul cartierului

            Returnează:
                adjacency (list(list)): matricea de adiacență
                nodes (Dictionary): dicționar de forma {nod: i}, i={0..N},
                    N = numărul de noduri din digraf
                    sau None și None în cazul în care există erori la
                    crearea digrafului.
        """
        if self.__graph is None:
            return None, None
        else:
            self.adj_matrix, self.nodes_to_number, self.streets = \
                graph_database.retrieve_adj_nodes(jti, id_cartier)
            return self.adj_matrix, self.nodes_to_number

    def get_coordinates(self, jti, id_cartier):
        """
            Funcția get_coordinates returnează coordonatele
            nodurilor digrafului.

            Parametrii:
                jti (str): identificatorul unic al jwt-ului utilizatorului;
                id_cartier (int): identificatorul cartierului.

            Returnează:
                (None): dacă există erori la crearea digrafului;
                (Dictionary): dicționar care are drept cheie numarul
                              nodului, iar valoarea este o listă care
                              conține coordonatele punctului.
        """
        if self.__graph is None:
            return None
        else:
            self.coords = graph_database.retrieve_coord(jti, id_cartier)
            return self.coords

    def get_streets(self):
        """
            Funcția get_streets returnează denumirile străzilor.

            Returnează:
                (None): dacă există erori la crearea digrafului;
                (list): listă care conține perechi de forma: lista cu cele
                    două noduri care delimitează strada și denumirea străzii.
        """
        if self.__graph is None:
            return None
        else:
            return self.streets

    def is_connected(self):
        """
            Funcția is_connected verifică dacă digraful este conex
            utilizând algoritmul de căutare în adâncime.

            Returnează:
                (list): listă ce conține nodurile vizitate.
        """
        adj = nx.adjacency_matrix(self.__graph).todense()
        visited = [False] * len(adj)
        stack = [0]
        visited[0] = True
        while stack:
            vertex = stack.pop()
            for i in range(len(adj)):
                if adj[vertex][i] and not visited[i]:
                    visited[i] = True
                    stack.append(i)
        return all(visited)

    def check_if_solvable(self):
        """
            Funcția check_if_solvable verifică dacă problema poștașului
            chinez poate fi rezolvată pe digraful curent.
            Mai exact, verifică dacă numărul de arce de intrare care
            trebuie să fie adăugate digrafului este egal cu numărul
            de arce de ieșire.

            Returnează:
                (boolean): True dacă este posibil, False în caz contrar.
        """
        adj = nx.adjacency_matrix(self.__graph).todense()
        odd_nodes = self.get_odd_vertices(adj)

        # Pentru ca problema să poată fi rezolvată este nevoie ca toate
        # nodurile care au nevoie de un arc de intrare să aibă
        # corespondent un alt nod care are nevoie de un arc de ieșire
        suma_plus = 0
        suma_minus = 0
        for node in odd_nodes:
            if odd_nodes[node] > 0:
                suma_plus += odd_nodes[node]
            else:
                suma_minus += odd_nodes[node]
        if suma_plus == (-1) * suma_minus:
            return True
        return False

    def get_odd_vertices(self, matrix):
        """
            Funcția get_odd_vertices returnează nodurile de grad impar.

            Parametrii:
                matrix (list(list)): matricea de adiacență a digrafului.

            Returnează:
                (list): listă formată din nodurile de grad impar
                        (noduri a căror diferență dintre gradul de ieșire
                         și gradul de intrare este diferită de 0).
        """
        odds = {}
        size = len(matrix)
        for i in range(size):
            in_degree = 0
            out_degree = 0
            for j in range(size):
                if matrix[i][j] != 0:
                    out_degree += 1
                if matrix[j][i] != 0:
                    in_degree += 1
            total = out_degree - in_degree
            if total != 0:
                odds[i] = total
        return odds

    def get_cost_from_path(self, path):
        """
            Funcția get_cost_from_path returnează costul unui traseu.

            Parametrii:
                path (list): conține nodurile care formează traseul.

            Returnează:
                (float): costul traseului.
        """
        # Parcurgem matricea de adiacență și adunăm costul
        # arcelor din traseu.
        sum = 0
        for i in range(len(path) - 1):
            sum += self.adj_matrix[path[i]][path[i + 1]]
        return sum

    def get_in_out_degrees(self, graph):
        """
            Funcția get_in_out_degrees calculează numărul de arce
            de intrare și numărul
            de arce de ieșire ale nodurilor din digraf.

            Parametrii:
                graph (list): digraful.

            Returnează:
                (list(list)): conține 2 liste: prima formată din
                                numărul de arce de intrare,
                                respectiv a doua, formată din numărul de
                                arce de ieșire pentru fiecare nod din digraf.
        """
        size = len(self.adj_matrix)
        in_degrees = [0] * size
        out_degrees = [0] * size

        for i in range(size):
            for j in range(size):
                if self.adj_matrix[i][j] != 0:
                    out_degrees[i] += graph[i][j]
                    in_degrees[j] += graph[i][j]
        return in_degrees, out_degrees

    def create_traverse_graph(self):
        """
            Funcția create_traverse_graph crează digraful sub forma
            unui dicționar astfel: {nod1: {nod2: i}},
            unde i = 1 dacă există arc de la nod1 la nod2 și 0 în
            caz contrar. Această valoare reprezintă numărul posibil
            inițial de parcurgeri ale arcelor.

            Returnează:
                (Dictionary): dicționarul în care este înregistrat
                            numărul de parcurgeri ale muchiilor.
        """
        graph = {}
        size = len(self.adj_matrix)
        for i in range(size):
            edges = {}
            for j in range(size):
                if self.adj_matrix[i][j] != 0:
                    edges[j] = 1
            graph[i] = edges
        return graph

    def double_paths_in_graph(self, graph, paths):
        """
            Funcția double_paths_in_graph incrementează numărul de parcurgeri
            ale unei muchii în digraf. Primește ca parametru o listă care
            reprezintă drumul care trebuie dublat în digraf și
            prin parcurgerea acestei liste este incrementată valoarea aferentă nodului.

            Parametrii:
                graph (Dictionary): dicționarul creat de funcția create_traverse_graph();
                paths (list): conține calea care trebuie dublată în digraf.
        """
        for path in paths:
            index = 0
            while index < len(path) - 1:
                i = path[index]
                j = path[index + 1]
                graph[i][j] += 1
                index += 1

    def get_pairs(self, d_minus, d_plus):
        """
            Funcția get_pairs crează toate combinațiile posibile de
            perechi de noduri de forma (u, v), unde u este un element din d_minus,
            iar v este un element din d_plus.

            Parametrii:
                d_minus (list): listă care conține nodurile ale căror grad de ieșire este
                                mai mic decât cel de intrare;
                d_plus (list): listă care conține nodurile ale căror grad de intrare este
                                mai mic decât cel de ieșire.
            Returnează: (list): listă care conține toate combinațiile de perechi.
        """
        # Listă în care salvăm toate perechile.
        all_pairs = []

        # Generăm toate permutările posibile ale listei d_minus.
        permutari = itertools.permutations(d_minus, len(d_plus))

        # Pentru fiecare permutare creată anterior, combinăm fiecare permutare cu lista d_plus.
        for p in permutari:
            combination = zip(p, d_plus)
            all_pairs.append(list(combination))

        # Din lista generată anterior extragem doar combinațiile de perechi unice prin
        # eliminarea duplicatelor.
        # Mai întâi sortăm perechile crescător după primul element.
        # Apoi, transformăm fiecare sub-listă de perechi în tuple pentru a putea aplica set.
        # În urma aplicării funcției set sunt eliminate duplicatele.
        lista_unica = list(set(map(tuple, [sorted(sublista) for sublista in all_pairs])))

        rezultat_final = [list(sublista) for sublista in lista_unica]

        return rezultat_final

    # def choose_pair(self, pairList, pairs, lst):
    #     """
    #         Funcția choose_pair determină dacă este corect să adăugăm o pereche în listă.
    #
    #         Parametrii: pairList - lista care conține toate perechile găsite până în momentul
    #                                 curent;
    #                     pairs - perechea pe care o testez
    #
    #         Returnează: list - perechea în cazul în care poate fi adăugată, None în caz contrar
    #     """
    #     flat_list = [item for sublist in pairs for item in sublist]
    #     for pair2 in pairList:
    #
    #         # Dacă un nod are modulul diferenței dintre gradul de ieșire și gradul de intrare
    #         # mai mare decât 1, atunci acesta va apărea în lista lst de mai multe ori.
    #         # Când creăm perechile, verificăm dacă acest nod a apărut de atâtea ori de
    #         # câte arce de intrare, respectiv ieșire, are nevoie.
    #         count1 = lst.count(pair2[0])
    #         count2 = lst.count(pair2[1])
    #         check1 = False
    #         check2 = False
    #         if count1 > 1:
    #             if pair2[0] in flat_list:
    #                 if flat_list.count(pair2[0]) < count1:
    #                     check1 = True
    #
    #         if count2 > 1:
    #             if pair2[1] in flat_list:
    #                 if flat_list.count(pair2[1]) < count2:
    #                     check2 = True
    #
    #         if check1 == True and check2 == False:
    #             return pair2
    #
    #         if check1 == False and check2 == True:
    #             return pair2
    #
    #         # Dacă nodurile din pereche nu se află în nicio pereche din
    #         # lista de liste, o putem adăuga.
    #         if (pair2[0] not in flat_list) and (pair2[1] not in flat_list):
    #             return pair2
    #
    # def check_if_pair_contains_all_nodes(self, pairs, lst):
    #     """
    #         Funcția check_if_pair_contains_all_nodes verifică dacă
    #         listele de perechi determinate conțin toate nodurile
    #         ale căror grade de intrare diferă de cele de ieșire.
    #
    #         Parametrii: pairs - listele de liste de perechi;
    #                     lst - lista care conține toate nodurile ale căror
    #                      grad de ieșire diferă de cel de intrare.
    #
    #         Returnează: lista de perechi care îndeplinește conditiția.
    #     """
    #     lst.sort()
    #     final_pairs = []
    #     for i in range(len(pairs)):
    #         temp = pairs[i][0]
    #         for j in range(1, len(pairs[i])):
    #             temp = temp + pairs[i][j]
    #         temp.sort()
    #         if temp == lst:
    #             final_pairs.append(pairs[i])
    #     return final_pairs
    #
    # def get_pairs(self, lst, d_plus, d_minus):
    #     """
    #         Funcția get_pairs se ocupă cu determinarea tuturor perechilor posibile
    #         de noduri ale căror grad de intrare diferă de gradul de ieșire.
    #         Parametrii: lst - listă în care se află toate nodurile ale căror grad de
    #                             intrare diferă de gradul de ieșire;
    #                     d_plus - listă care conține nodurile ale căror grad de intrare
    #                                 este mai mic decât cel de ieșire;
    #                     d_minus - listă care conține nodurile ale căror grad de ieșire
    #                                 este mai mic decât cel de intrare.
    #         Returnează: listă de liste care conține perechile.
    #     """
    #     # Formăm un dicționar în care cheia este un nod din lista d_minus
    #     # și valoarea este o listă de perechi posibile cu elementele din lista d_plus
    #     d = {}
    #     for i in d_minus:
    #         for j in d_plus:
    #             pair = [i, j]
    #             key = i
    #             if key not in d:
    #                 d[key] = []
    #             d[key].append(pair)
    #     # Parcurgem aceste perechi și formăm o listă în care salvăm mai multe liste
    #     # care vor conține perechile posibile cu nodurile acestea.
    #     pairs = []
    #     for key in d:
    #         stack = d[key]
    #         while len(stack) != 0:
    #             pair = [stack[0]]
    #             for key2 in d:
    #                 if key != key2:
    #                     result = self.choose_pair(d[key2], pair, lst)
    #                     if result is not None:
    #                         pair.append(result)
    #             stack.pop(0)
    #             if len(pair) >= 1:
    #                 pairs.append(pair)
    #     return self.check_if_pair_contains_all_nodes(pairs, lst)
