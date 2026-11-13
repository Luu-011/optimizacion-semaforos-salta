import unittest

from models.queue_model import (
    calcular_demora_webster,
    calcular_mmc,
    calcular_mu_efectiva,
    calcular_webster,
)


class TestQueueModel(unittest.TestCase):
    def test_mmc_con_un_servidor_coincide_con_mm1(self):
        resultado = calcular_mmc(lamda=4, mu=6, c=1)

        self.assertAlmostEqual(resultado["rho"], 2 / 3)
        self.assertAlmostEqual(resultado["P_espera"], 2 / 3)
        self.assertAlmostEqual(resultado["Lq"], 4 / 3)
        self.assertAlmostEqual(resultado["Wq"], 1 / 3)
        self.assertAlmostEqual(resultado["Ws"], 1 / 2)
        self.assertAlmostEqual(resultado["Ls"], 2)

    def test_ley_de_little_para_la_cola(self):
        lamda = 15
        resultado = calcular_mmc(lamda=lamda, mu=6, c=3)

        self.assertAlmostEqual(
            resultado["Lq"],
            lamda * resultado["Wq"],
        )

    def test_mmc_rechaza_un_sistema_inestable(self):
        with self.assertRaisesRegex(ValueError, "inestable"):
            calcular_mmc(lamda=12, mu=5.5, c=2)

    def test_mu_efectiva(self):
        # s=24 veh/min/carril y g/C=45/90=0,5; entonces μ=12.
        self.assertAlmostEqual(
            calcular_mu_efectiva(
                flujo_saturacion_veh_min_por_carril=24,
                verde_efectivo_s=45,
                ciclo_s=90,
            ),
            12,
        )

    def test_webster_reproduce_el_ejemplo_del_informe(self):
        resultado = calcular_webster(
            fases=[
                {
                    "nombre": "Av. Bicentenario",
                    "demanda_veh_h": 1424,
                    "carriles": 3,
                },
                {
                    "nombre": "Av. Entre Ríos",
                    "demanda_veh_h": 1187,
                    "carriles": 2,
                },
            ],
            flujo_saturacion_veh_h_por_carril=1440,
            tiempo_perdido_total_s=8,
        )

        self.assertAlmostEqual(resultado["ciclo_webster_s"], 65.835948, places=5)
        self.assertAlmostEqual(
            resultado["fases"][0]["verde_efectivo_s"],
            25.700855,
            places=5,
        )
        self.assertAlmostEqual(
            resultado["fases"][1]["verde_efectivo_s"],
            32.135093,
            places=5,
        )
        self.assertAlmostEqual(
            resultado["demora_media_ponderada_s"],
            22.940759,
            places=5,
        )

    def test_webster_rechaza_flujo_sobresaturado(self):
        with self.assertRaisesRegex(ValueError, "sobresaturada"):
            calcular_webster(
                fases=[
                    {"nombre": "Fase 1", "demanda_veh_h": 8000, "carriles": 1},
                    {"nombre": "Fase 2", "demanda_veh_h": 1000, "carriles": 1},
                ],
                flujo_saturacion_veh_h_por_carril=1440,
                tiempo_perdido_total_s=8,
            )

    def test_webster_rechaza_verde_igual_al_ciclo(self):
        with self.assertRaisesRegex(ValueError, "menor que"):
            calcular_demora_webster(
                demanda_veh_h=500,
                carriles=1,
                flujo_saturacion_veh_h_por_carril=1440,
                ciclo_s=90,
                verde_efectivo_s=90,
            )


if __name__ == "__main__":
    unittest.main()
