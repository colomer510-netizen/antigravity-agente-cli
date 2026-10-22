"""Pruebas unitarias para chat_ollama: seguridad, extractor y optimizaciones low-resource."""

import unittest

from chat_ollama import (
    MAX_OUTPUT_LINES,
    MAX_TURNS_HISTORY,
    OPTIMAL_THREADS,
    compactar_salida_comando,
    es_comando_peligroso,
    es_comando_seguro,
    extraer_comando_y_contexto,
    obtener_nombre_usuario,
    podar_historial,
)


class TestAgenteSeguridad(unittest.TestCase):
    def test_comandos_seguros_lectura(self):
        """Verifica que los comandos de solo lectura se clasifiquen como seguros."""
        comandos_seguros = [
            "uname -r",
            "free -h",
            "df -h /",
            "uptime",
            "uptime -p",
            "sensors",
            "ip -br addr",
            "ls -la",
            "cat /etc/os-release",
            "compgen -c | grep disk",
            "apropos compression",
            "whatis tar",
            "whereis python3",
            "help cd",
            "lsblk -e7 -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINTS",
            "uname -r && free -h",
        ]
        for cmd in comandos_seguros:
            self.assertTrue(es_comando_seguro(cmd), f"Fallo: {cmd} debería ser seguro")

    def test_comandos_peligrosos_bloqueo(self):
        """Verifica que comandos potencialmente destructivos NO se auto-ejecuten."""
        comandos_peligrosos = [
            "rm -rf /",
            "rm -r carpeta/",
            "mkfs.ext4 /dev/sdb",
            "dd if=/dev/zero of=/dev/sda",
            "chmod -R 777 /",
            "shutdown now",
            "reboot",
            "poweroff",
            "systemctl poweroff",
            "ls && rm -rf /",
            "free -h ; reboot",
        ]
        for cmd in comandos_peligrosos:
            self.assertFalse(
                es_comando_seguro(cmd), f"Fallo: {cmd} NO debería ser seguro"
            )
            self.assertTrue(
                es_comando_peligroso(cmd), f"Fallo: {cmd} debería ser peligroso"
            )

    def test_comandos_desconocidos_no_seguros(self):
        """Comandos desconocidos o alucinaciones no deben auto-ejecutarse."""
        comandos_raros = [
            "4.4.0-36-generic",
            "mi_script_inventado",
            "touch archivo.txt",
        ]
        for cmd in comandos_raros:
            self.assertFalse(es_comando_seguro(cmd))


class TestAgenteExtractor(unittest.TestCase):
    def test_extractor_comandos_cmd(self):
        """Verifica la extracción limpia del comando CMD: y el contexto previo."""
        texto = "Consultando memoria RAM...\nCMD: free -h"
        cmd, ctx = extraer_comando_y_contexto(texto)
        self.assertEqual(cmd, "free -h")
        self.assertEqual(ctx, "Consultando memoria RAM...")

    def test_extractor_ignora_bloques_en_explicaciones(self):
        """Verifica que bloques ```bash dentro de respuestas conversacionales no se ejecuten."""
        texto_explicativo = (
            "Para consultar más detalles puedes usar los siguientes comandos:\n"
            "1. Memoria:\n```bash\nfree -h\n```\nFin de la explicación."
        )
        cmd, _ = extraer_comando_y_contexto(texto_explicativo)
        self.assertIsNone(cmd, "No debe extraer comandos de textos explicativos")


class TestAgenteLowResource(unittest.TestCase):
    def test_parametros_low_resource(self):
        """Verifica que los parámetros de bajo consumo estén configurados correctamente."""
        self.assertGreaterEqual(OPTIMAL_THREADS, 1)
        self.assertLessEqual(OPTIMAL_THREADS, 4)
        self.assertEqual(MAX_OUTPUT_LINES, 16)
        self.assertEqual(MAX_TURNS_HISTORY, 4)

    def test_compactar_salida_larga(self):
        """Verifica el truncamiento de salidas extensas para no sobrecargar CPU."""
        lineas_largas = "\n".join([f"linea_{i}" for i in range(50)])
        salida = compactar_salida_comando(lineas_largas, max_lineas=16)
        lineas_resultado = salida.splitlines()
        self.assertLessEqual(len(lineas_resultado), 18)
        self.assertIn("Se omitieron 34 líneas", salida)

    def test_podar_historial(self):
        """Verifica que el historial no crezca indefinidamente y conserve el SYSTEM_PROMPT."""
        history = [{"role": "system", "content": "prompt"}]
        for i in range(30):
            history.append({"role": "user", "content": f"msg {i}"})
        podado = podar_historial(history)
        self.assertEqual(podado[0]["role"], "system")
        self.assertLessEqual(len(podado), MAX_TURNS_HISTORY * 3 + 1)


class TestAgenteUsuario(unittest.TestCase):
    def test_obtener_nombre_usuario_dinamico(self):
        """Verifica que el nombre de usuario se detecte dinámicamente."""
        nombre = obtener_nombre_usuario()
        self.assertIsInstance(nombre, str)
        self.assertTrue(len(nombre) > 0)


if __name__ == "__main__":
    unittest.main()
