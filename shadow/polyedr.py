from math import pi, sqrt, acos
from functools import reduce
from operator import add
from common.r3 import R3


class Segment:
    """ Одномерный отрезок """

    # Параметры конструктора: начало и конец отрезка (числа)

    def __init__(self, beg, fin):
        self.beg, self.fin = beg, fin

    # Отрезок вырожден?
    def is_degenerate(self):
        return self.beg >= self.fin

    # Пересечение с отрезком
    def intersect(self, other):
        if other.beg > self.beg:
            self.beg = other.beg
        if other.fin < self.fin:
            self.fin = other.fin
        return self

    # Разность отрезков
    # Разность двух отрезков всегда является списком из двух отрезков!
    def subtraction(self, other):
        return [Segment(
            self.beg, self.fin if self.fin < other.beg else other.beg),
            Segment(self.beg if self.beg > other.fin else other.fin, self.fin)]


class Edge:
    """ Ребро полиэдра """
    # Начало и конец стандартного одномерного отрезка
    SBEG, SFIN = 0.0, 1.0

    # Параметры конструктора: начало и конец ребра (точки в R3)
    def __init__(self, beg, fin):
        self.beg, self.fin = beg, fin
        # Список «просветов»
        self.gaps = [Segment(Edge.SBEG, Edge.SFIN)]

    # Учёт тени от одной грани
    def shadow(self, facet):
        # «Вертикальная» грань не затеняет ничего
        if facet.is_vertical():
            return
        # Нахождение одномерной тени на ребре
        shade = Segment(Edge.SBEG, Edge.SFIN)
        for u, v in zip(facet.vertexes, facet.v_normals()):
            shade.intersect(self.intersect_edge_with_normal(u, v))
            if shade.is_degenerate():
                return

        shade.intersect(
            self.intersect_edge_with_normal(
                facet.vertexes[0], facet.h_normal()))
        if shade.is_degenerate():
            return
        # Преобразование списка «просветов», если тень невырождена
        gaps = [s.subtraction(shade) for s in self.gaps]
        self.gaps = [
            s for s in reduce(add, gaps, []) if not s.is_degenerate()]

    # Преобразование одномерных координат в трёхмерные
    def r3(self, t):
        return self.beg * (Edge.SFIN - t) + self.fin * t

    # Пересечение ребра с полупространством, задаваемым точкой (a)
    # на плоскости и вектором внешней нормали (n) к ней
    def intersect_edge_with_normal(self, a, n):
        f0, f1 = n.dot(self.beg - a), n.dot(self.fin - a)
        if f0 >= 0.0 and f1 >= 0.0:
            return Segment(Edge.SFIN, Edge.SBEG)
        if f0 < 0.0 and f1 < 0.0:
            return Segment(Edge.SBEG, Edge.SFIN)
        x = - f0 / (f1 - f0)
        return Segment(Edge.SBEG, x) if f0 < 0.0 else Segment(x, Edge.SFIN)


class Facet:
    """ Грань полиэдра """

    # Параметры конструктора: список вершин

    def __init__(self, vertexes):
        self.vertexes = vertexes
        self.edges = []

    # «Вертикальна» ли грань?
    def is_vertical(self):
        return self.h_normal().dot(Polyedr.V) == 0.0

    # Нормаль к «горизонтальному» полупространству
    def h_normal(self):
        n = (
                self.vertexes[1] - self.vertexes[0]).cross(
            self.vertexes[2] - self.vertexes[0])
        return n * (-1.0) if n.dot(Polyedr.V) < 0.0 else n

    # Нормали к «вертикальным» полупространствам, причём k-я из них
    # является нормалью к грани, которая содержит ребро, соединяющее
    # вершины с индексами k-1 и k
    def v_normals(self):
        return [self._vert(x) for x in range(len(self.vertexes))]

    # Вспомогательный метод
    def _vert(self, k):
        n = (self.vertexes[k] - self.vertexes[k - 1]).cross(Polyedr.V)
        return (
            n * (-1.0)
            if n.dot(self.vertexes[k - 1] - self.center()) < 0.0
            else n
        )

    # Центр грани
    def center(self):
        return sum(self.vertexes, R3(0.0, 0.0, 0.0)) * \
            (1.0 / len(self.vertexes))


class Polyedr:
    """ Полиэдр """
    # вектор проектирования
    V = R3(0.0, 0.0, 1.0)

    # Параметры конструктора: файл, задающий полиэдр
    def __init__(self, file):

        # списки вершин, рёбер и граней полиэдра
        self.vertexes, self.edges, self.facets = [], [], []

        # список строк файла
        with open(file) as f:
            for i, line in enumerate(f):
                if i == 0:
                    # обрабатываем первую строку;
                    # buf - вспомогательный массив
                    buf = line.split()
                    # коэффициент гомотетии
                    self.c = float(buf.pop(0))
                    # углы Эйлера, определяющие вращение
                    alpha, beta, gamma = (float(x) * pi / 180.0 for x in buf)
                elif i == 1:
                    # во второй строке число вершин, граней и рёбер полиэдра
                    nv, nf, ne = (int(x) for x in line.split())
                elif i < nv + 2:
                    # задание всех вершин полиэдра
                    x, y, z = (float(x) for x in line.split())
                    self.vertexes.append(R3(x, y, z).rz(
                        alpha).ry(beta).rz(gamma))
                else:
                    # вспомогательный массив
                    buf = line.split()
                    # количество вершин очередной грани
                    size = int(buf.pop(0))
                    # массив вершин этой грани
                    vertexes = list(self.vertexes[int(n) - 1] for n in buf)
                    # задание рёбер грани
                    facet_edges = []
                    for n in range(size):
                        edge = Edge(vertexes[n - 1], vertexes[n])
                        self.edges.append(edge)
                        facet_edges.append(edge)

                    facet = Facet(vertexes)
                    facet.edges = facet_edges  # связь грани и ее ребер
                    self.facets.append(facet)

            self.perimetr = self.calculate()

    # Метод изображения полиэдра
    def draw(self, tk):  # pragma: no cover
        tk.clean()
        for e in self.edges:
            for f in self.facets:
                e.shadow(f)
            for s in e.gaps:
                p1 = e.r3(s.beg) * self.c
                p2 = e.r3(s.fin) * self.c
                tk.draw_line(p1, p2)

    def calculate(self):
        for e in self.edges:
            e.gaps = [Segment(Edge.SBEG, Edge.SFIN)]

        # 1. Сначала рассчитываем тени для всех ребер от всех граней
        for e in self.edges:
            for f in self.facets:
                if e in f.edges:
                    continue
                e.shadow(f)

        total_perimeter = 0.0

        for facet in self.facets:
            # Все ребра грани в тени
            all_edges_shadowed = all(len(e.gaps) == 0 for e in facet.edges)
            if not all_edges_shadowed:
                continue

            # Расстояние от центра до плоскости x = 2 строго меньше 1
            center = facet.center()
            dist_to_plane = abs(center.x - 2.0)
            if not (dist_to_plane < 1.0):
                continue

            # Угол между нормалью грани и вертикальной осью <= 10 градусов
            n = facet.h_normal()
            n_len = sqrt(n.dot(n))

            if n_len == 0:
                continue

            cos_alpha = abs(n.dot(Polyedr.V)) / n_len
            cos_alpha = max(0.0, min(1.0, cos_alpha))
            angle_normal_axis = acos(cos_alpha)

            if not (angle_normal_axis <= 10.0 * pi / 180.0):
                continue

            # грань хорошая - считаем периметр ее проекции (на XY)
            facet_proj_perimeter = 0.0
            for e in facet.edges:
                dx = e.beg.x - e.fin.x
                dy = e.beg.y - e.fin.y
                facet_proj_perimeter += sqrt(dx * dx + dy * dy)

            total_perimeter += facet_proj_perimeter

        return total_perimeter
