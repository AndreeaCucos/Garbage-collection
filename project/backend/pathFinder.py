import random
from abc import ABC, abstractmethod


class FloydWarshallInterface(ABC):
    @abstractmethod
    def floyd_warshall(self, adjacency_matrix):
        pass

    @abstractmethod
    def get_matrix_and_neighbours(self):
        pass

    @abstractmethod
    def makePath(self, node1, node2):
        pass


class FloydWarshall(FloydWarshallInterface):
    """
        Constructorul clasei FloydWarshall, instanțiază matricea
        de distanțe și cea de drumuri cu None.
    """
    def __init__(self):
        self.distances = None
        self.neighbours = None

    def floyd_warshall(self, adj_matrix):
        """
            Funcția floyd_warshall implementează algoritmul Floyd-Warshall
            de determinare a distanțelor cele mai mici între toate perechile
            de noduri din digraf și a vecinilor corespunzători.

            Pramaterii:
                adj_matrix (list(list)): matricea de adiacență a digrafului.
        """
        n = len(adj_matrix)

        #  Inițializare matrice de distanțe și cea de drumuri.
        self.distances = [[float('inf') for _ in range(n)] for _ in range(n)]
        self.neighbours = [[-1] * n for _ in range(n)]
        for i in range(n):
            self.distances[i][i] = 0
            for j in range(n):
                if adj_matrix[i][j] != 0:
                    self.distances[i][j] = adj_matrix[i][j]
                    self.neighbours[i][j] = j

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if self.distances[i][j] > self.distances[i][k] + self.distances[k][j]:
                        self.distances[i][j] = self.distances[i][k] + self.distances[k][j]
                        self.neighbours[i][j] = self.neighbours[i][k]

    def get_matrix_and_neighbours(self):
        """
            Funcția get_matrix_and_neighbours returnează matricea de
            distanțe și cea de drumuri.

            Returnează:
                self.distances (list(list)): matricea de distanțe;
                self.neighbours (list(list)): matricea cu drumuri.
        """
        return self.distances, self.neighbours

    def makePath(self, src, dest):
        """
            Funcția makePath returnează un drum între 2 noduri.

            Parametrii:
                src (int): nodul inițial;
                dest (int): nodul final.
            Returnează:
                path (list): conține drumul de la nodul inițial la cel de final
                    sau None în cazul în care nu există o cale directă între ele.
                    (distanța e infinită, nedeterminată)
        """
        if self.neighbours[src][dest] == -1:
            return None
        path = [src]
        while src != dest:
            src = self.neighbours[src][dest]
            path.append(src)
        return path


class EulerInterface(ABC):
    @abstractmethod
    def check_euler_path(self, size, in_degrees, out_degrees):
        pass

    @abstractmethod
    def euler_cycle_graph(self, graph, matrix, in_degrees, out_degrees):
        pass


class Euler(EulerInterface):
    """
        Constructorul clasei Euler, inițializează ciclul cu o listă goală.
    """
    def __init__(self):
        self.path = []

    def check_euler_path(self, size, in_degrees, out_degrees):
        """
        Funcția check_euler_path verifică dacă există noduri de grad impar
        în digraf după execuția etapelor anterioare.

        Parametrii:
            size (int): nodul inițial;
            in_degrees (list): conține gradele de intrare ale nodurilor;
            out_degrees (list): conține gradele de ieșire ale nodurilor.

        Returnează:
            (list): conține nodul inițial și final sau valori None în cazul
                    în care mai există noduri de grad impar.
        """
        start, end = None, None
        count_odds = 0
        for i in range(size - 1):
            if in_degrees[i] != out_degrees[i]:
                count_odds += 1
                if count_odds >= 1:
                    return None, None
                # if in_degrees[i] < out_degrees[i]:
                #     start = i
                # else:
                #     end = i
        if count_odds == 0:
            start = end = random.randint(0, size - 1)
        return start, end

    def euler_cycle_graph(self, graph, matrix, in_degrees, out_degrees):
        """
        Funcția euler_cycle_graph determină ciclul eulerian.

        Parametrii:
            graph (Dictionary): digraful cu parcurgerile arcelor;
            matrix (list(list)): matricea de adiacență.
            in_degrees (list): listă care conține gradele de intrare ale nodurilor;
            out_degrees (list): listă care conține gradele de ieșire ale nodurilor.

        Returnează:
            (list): listă care conține ciclul eulerian căutat
                sau None în cazul în care în digraf există noduri
                de grad impar.
        """
        size = len(matrix)
        start, end = self.check_euler_path(size, in_degrees, out_degrees)
        if start is None and end is None:
            return None
        else:
            stack = [start]
            self.path = []
            while stack:
                current = stack[-1]
                if out_degrees[current] == 0:
                    self.path.append(stack.pop())
                else:
                    for i in range(size):
                        if matrix[current][i] != 0:
                            if graph[current][i] != 1:
                                graph[current][i] -= 1
                            else:
                                matrix[current][i] = 0
                            out_degrees[current] -= 1
                            in_degrees[i] -= 1
                            stack.append(i)
                            break
            return list(reversed(self.path))
