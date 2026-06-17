import unittest
from shadow.polyedr import Polyedr
import os
import tempfile
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Test(unittest.TestCase):

    # центр грани далеко
    def test1(self):
        assert Polyedr("data/test1.geom").perimetr == 0

    # больше 10 градусов
    def test2(self):
        assert Polyedr("data/test2.geom").perimetr == 0

    # нет неосвещенной грани
    def test3(self):
        assert Polyedr("data/test3.geom").perimetr == 0

    # грань с углом между нормалью и вертикалью >10:
    def test4(self):
        assert Polyedr("data/test5.geom").perimetr == 0

    # грань с центром на расстоянии >= 1 от плоскости x=2
    def test5(self):
        assert Polyedr("data/test6.geom").perimetr == 0

    # грань с нулевой длиной нормали (вырожденная)
    def test6(self):
        assert Polyedr("data/test7.geom").perimetr == 0

    def test7(self):
        assert Polyedr("data/test8.geom").perimetr == 0

    def test8(self):
        assert Polyedr("data/test9.geom").perimetr == 0

    # тест на проверку угла
    def test_angle_continue(self):
        content = """1.0 0.0 0.0 0.0
8 2 8
1.0 -1.0 1.0
3.0 -1.0 1.0
3.0  1.0 1.0
1.0  1.0 1.0
1.5 -0.5 0.0
2.5 -0.5 0.2
2.5  0.5 0.2
1.5  0.5 0.0
4 1 2 3 4
4 5 6 7 8
"""
        test_file = "data/temp_angle.geom"
        with open(test_file, "w") as f:
            f.write(content)
        try:
            p = Polyedr(test_file)
            assert p.perimetr == 0
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_natural_nonzero(self):
        """две горизонтальные грани:
        верхняя полностью закрывает нижнюю"""
        geom_content = """1.0 0.0 0.0 0.0
8 2 8
1.0 -1.0 1.0
3.0 -1.0 1.0
3.0  1.0 1.0
1.0  1.0 1.0
1.5 -0.5 0.0
2.5 -0.5 0.0
2.5  0.5 0.0
1.5  0.5 0.0
4 1 2 3 4
4 5 6 7 8
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.geom',
                                         delete=False, dir='data') as tmp:
            tmp.write(geom_content)
            tmp_path = tmp.name

        try:
            p = Polyedr(tmp_path)
            result = p.perimetr
            print(f"DEBUG: result = {result}")
            for i, f in enumerate(p.facets):
                for j, e in enumerate(f.edges):
                    print(f"  Грань {i}, Ребро {j}: "
                          f"gaps = {[(s.beg, s.fin) for s in e.gaps]}")
            self.assertGreater(result, 0.0, f"Ожидался периметр > 0,"
                                            f"получили {result}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
