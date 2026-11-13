import unittest

from models.simulation import ejecutar_simulacion


class TestSimulation(unittest.TestCase):
    def test_mantiene_compatibilidad_con_llamada_anterior(self):
        resultado = ejecutar_simulacion(
            lamda=15,
            mu=6,
            c=3,
            num_vehiculos=500,
        )

        self.assertIn("Wq_simulado", resultado)
        self.assertEqual(resultado["total_vehiculos_simulados"], 500)
        self.assertEqual(resultado["replicas"], 1)
        self.assertIsNone(resultado["IC95_Wq_min"]["inferior"])

    def test_aplica_calentamiento_replicas_y_intervalo(self):
        resultado = ejecutar_simulacion(
            lamda=15,
            mu=6,
            c=3,
            num_vehiculos=1200,
            warmup=200,
            replicas=3,
            seed_base=42,
        )

        self.assertEqual(resultado["total_vehiculos_simulados"], 3600)
        self.assertEqual(resultado["total_vehiculos_medidos"], 3000)
        self.assertEqual(resultado["num_vehiculos_por_replica"], 1200)
        self.assertEqual(resultado["vehiculos_descartados_por_replica"], 200)
        self.assertEqual(resultado["vehiculos_medidos_por_replica"], 1000)
        self.assertEqual(len(resultado["resultados_replicas"]), 3)
        self.assertLessEqual(
            resultado["IC95_Wq_min"]["inferior"],
            resultado["media_Wq_min"],
        )
        self.assertGreaterEqual(
            resultado["IC95_Wq_min"]["superior"],
            resultado["media_Wq_min"],
        )

    def test_misma_semilla_reproduce_los_mismos_resultados(self):
        argumentos = {
            "lamda": 15,
            "mu": 6,
            "c": 3,
            "num_vehiculos": 1000,
            "warmup": 100,
            "replicas": 3,
            "seed_base": 42,
        }

        primero = ejecutar_simulacion(**argumentos)
        segundo = ejecutar_simulacion(**argumentos)

        self.assertEqual(
            primero["resultados_replicas"],
            segundo["resultados_replicas"],
        )
        self.assertEqual(primero["media_Wq_min"], segundo["media_Wq_min"])

    def test_rechaza_sistema_inestable(self):
        with self.assertRaisesRegex(ValueError, "inestable"):
            ejecutar_simulacion(
                lamda=12,
                mu=5.5,
                c=2,
                num_vehiculos=1000,
            )

    def test_rechaza_calentamiento_mayor_o_igual_al_total(self):
        with self.assertRaisesRegex(ValueError, "warmup"):
            ejecutar_simulacion(
                lamda=15,
                mu=6,
                c=3,
                num_vehiculos=100,
                warmup=100,
            )


if __name__ == "__main__":
    unittest.main()
