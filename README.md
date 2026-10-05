# Simulación numérica con agentes: saturación inicial de Volve en OPM Flow

Material de una clase de hasta cuatro horas para ingenieros de reservorios. Un agente de terminal
(Claude Code) maneja un simulador numérico abierto (OPM Flow) para reproducir la saturación de agua
de los perfiles de dos pozos del campo Volve, y compara distintas formas de hacerlo.

El ejercicio es el de un programa de saturación-altura: elegir curvas de presión capilar, tipos de
roca y contactos para que el modelo arranque con el agua donde la midieron los perfiles. La
diferencia es que el cálculo lo hace el equilibrio del propio simulador, así que lo que se ajusta
es lo que después inicializa el modelo de campo.

Las diapositivas y un resumen con las figuras están en
[mpodeley.github.io/clase-opm-agentes](https://mpodeley.github.io/clase-opm-agentes/).

## Qué se ve en la clase

| Bloque | Tiempo | Qué pasa |
| --- | --- | --- |
| El problema | 15 min | El perfil de 15/9-F-12, qué significa reproducirlo y con qué número se mide |
| Instalación | 25 min | OPM Flow en un contenedor, el entorno de Python y Claude Code, con un caso de prueba |
| El agente lee el deck | 35 min | El agente explica el modelo keyword por keyword, corre el caso base y lee el resultado |
| Pausa | 10 min | |
| Alternativas de ajuste | 45 min | Función J, tipos de roca, escalado de extremos y SWATINIT, comparados en una tabla |
| El contacto | 30 min | Contacto plano, dos sistemas o contacto inclinado, con el segundo pozo a la vista |
| Pausa | 10 min | El loop queda corriendo |
| Loop autónomo | 30 min | El agente prueba variantes solo, con reglas y un tope; se lee qué conservó y qué descartó |
| Controles y cierre | 20 min | Qué revisa y firma el ingeniero, y los límites del ejercicio |

Suma 3 h 40 min. El guion con el minuto a minuto está en `docente/guion.md` y las diapositivas en
`slides/clase.md`.

## Instalación

Hace falta Linux, macOS o Windows con WSL (Windows Subsystem for Linux), y cuatro programas:

| Programa | Para qué | Cómo se instala |
| --- | --- | --- |
| Podman o Docker | Correr OPM Flow sin compilarlo | `sudo apt install podman` en Ubuntu, `brew install podman` en macOS |
| uv | El entorno de Python | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| git | El historial de experimentos del loop | Viene con casi cualquier sistema |
| Claude Code | El agente | `curl -fsSL https://claude.ai/install.sh \| bash` |

En macOS, Podman necesita una máquina virtual: `podman machine init` y `podman machine start`,
una sola vez.

Con eso instalado:

```bash
git clone https://github.com/mpodeley/clase-opm-agentes.git
cd clase-opm-agentes
instalacion/instalar.sh     # baja la imagen de OPM Flow (1.2 GB), arma el entorno y baja los datos
instalacion/verificar.sh    # corre un caso de prueba y el caso base del ejercicio
```

`verificar.sh` termina con `todo en orden` si las tres piezas funcionan: Flow responde, corre SPE1
(el primer caso comparativo de la Society of Petroleum Engineers) y el caso base del ejercicio da
su puntaje.

Con Docker, anteponé `CONTENEDOR=docker` a los dos comandos. Si ya tenés OPM Flow instalado en el
sistema, exportá `FLOW=/ruta/a/flow` y el contenedor no se usa. En Ubuntu, OPM publica paquetes
propios: las instrucciones están en [opm-project.org](https://opm-project.org).

La imagen del simulador está fijada por su hash en `sw/correr.py`, y los archivos de Volve por el
suyo en `datos/preparar_datos.py`. Dos personas que instalan en días distintos corren lo mismo.

## Correr un caso

```bash
uv run evaluar.py
```

Tarda uno o dos segundos. Arma el deck, corre Flow, lee la saturación inicial y la compara con los
perfiles:

```
grafico: corridas/ultima/perfil.png
---
caso: A: curva única y un contacto
rmse_ajuste: 0.1772
rmse_ajuste_hugin: 0.1283
rmse_ajuste_bajo_hugin: 0.2041
sesgo_ajuste: 0.0566
error_hcpv_ajuste: -0.1374
rmse_validacion: 0.4906
...
n_parametros: 4
```

`rmse_ajuste` es la raíz del error cuadrático medio (RMSE, root mean square error) entre la
saturación simulada y la del perfil en el pozo 15/9-F-12, celda por celda. `rmse_validacion` es lo
mismo en 15/9-F-11 B, que el caso no ve. `error_hcpv` es el error relativo en el volumen poral de
hidrocarburo a lo largo del pozo.

El caso se define en `caso.py`, el único archivo que se edita. En `corridas/ultima/` quedan el
deck (`SW.DATA`), la salida de Flow, una tabla (`sw.csv`) y la figura.

## El modelo

Una fila de celdas, una por metro de pozo, desde el tope de la Formación Hugin hasta el final del
perfil. Cada celda lleva su profundidad, su porosidad, su permeabilidad y su volumen de arcilla,
promediados del perfil interpretado. Entre celdas no hay flujo: cada una se equilibra sola, con la
curva de presión capilar y el nivel de agua libre que le asigne el caso.

Así el mismo armado sirve para un pozo desviado y para uno horizontal, y el caso puede usar
cualquier keyword de inicialización de Flow: `SWOF`, `JFUNC`, `SATNUM`, `ENDSCALE` con `SWL`,
`SWATINIT`, `EQUIL` y `EQLNUM`.

| Pozo | Rol | Celdas | Perfilado |
| --- | --- | --- | --- |
| 15/9-F-12 | Ajuste | 379 | 2007, antes de que el campo produjera |
| 15/9-F-11 B | Validación | 1,277 | 2013, con cinco años de producción e inyección de agua |

## El ejercicio con el agente

```bash
ejercicio/preparar.sh ~/sw-volve
cd ~/sw-volve
claude
```

`preparar.sh` arma una carpeta de trabajo aparte, con su propio `CLAUDE.md`, los permisos del
agente y cuatro pedidos (`PEDIDO-1.md` a `PEDIDO-4.md`) que se le pasan de a uno. El agente puede
editar `caso.py` y correr `evaluar.py`; no puede tocar la métrica, los datos ni salir a internet.
Los casos de referencia de `docente/soluciones/` no se copian.

La primera vez, Claude Code pregunta si confiás en la carpeta. Hasta que aceptes, ignora los
permisos de `.claude/settings.json` y pide confirmación para cada comando.

El cuarto pedido lanza el loop de `program.md`, una adaptación de
[autoresearch](https://github.com/karpathy/autoresearch): el agente cambia el caso, corre, anota
el resultado en `results.tsv` y conserva o descarta el cambio con git, hasta 15 experimentos o
20 minutos.

## Resultados de referencia

Salen de `uv run docente/tabla.py`, con los casos de `docente/soluciones/` ajustados por un
optimizador clásico (Nelder-Mead, `docente/optimizar.py`).

| Caso | Ajustado con | RMSE en F-12 | RMSE en F-11 B | Parámetros |
| --- | --- | ---: | ---: | ---: |
| A: curva única y un contacto | F-12 | 0.163 | 0.497 | 4 |
| B: función J de Leverett | F-12 | 0.159 | 0.484 | 4 |
| C: tres tipos de roca | F-12 | 0.163 | 0.473 | 12 |
| D: agua connata por celda | F-12 | 0.158 | 0.490 | 5 |
| E: SWATINIT | F-12 | 0.000 | 0.486 | 383 |
| F0: un contacto plano | Los dos | 0.234 | 0.332 | 4 |
| F1: un contacto por sistema | Los dos | 0.220 | 0.230 | 5 |
| F2: contacto inclinado | Los dos | 0.261 | 0.232 | 5 |

Tres lecturas que la clase discute:

- De A a D el error en F-12 cambia en el tercer decimal. Con cuatro parámetros ya se llega al piso
  que deja la variabilidad del perfil metro a metro.
- SWATINIT lleva el error a cero en el pozo donde se impone y no mejora nada en el otro.
- Dos sistemas con contactos a 2,937 y 3,156 m y un contacto inclinado 105 m por kilómetro
  ajustan casi igual. Los perfiles no los separan.

## Qué no se puede afirmar con esto

- **Dónde está el contacto de Volve.** El conjunto no trae presiones de formación ni ensayos de
  laboratorio. Las densidades de los fluidos son un supuesto, y cualquier cambio en ellas se
  compensa con la presión de entrada de la curva.
- **Que F-11 B valide la saturación inicial.** Se perfiló en 2013, con cinco años de
  producción e inyección de agua detrás. Su saturación es igual o mayor que la original.
- **Que un contacto inclinado exista.** El ajuste lo admite tanto como admite dos compartimentos.
  Sostener 105 m por kilómetro pediría unos 3 bar por kilómetro de gradiente en el acuífero.
- **Que estos parámetros sirvan para un modelo de campo.** Son 2 de los 22 pozos de desarrollo del campo, sin variograma
  ni modelo de facies. El ejercicio muestra el método de trabajo con el agente.

## Datos

Los perfiles, las trayectorias, los topes y el mapa del tope de Hugin son parte del conjunto que
Equinor liberó en 2018, y se bajan de espejos públicos fijados por commit.

Datos de Equinor y los ex socios de la licencia Volve (ExxonMobil Exploration & Production Norway
AS, Bayerngas Norge AS), bajo la
[Equinor Open Data Licence](https://cdn.equinor.com/files/h61q9gi9/global/de6532f6134b9a953f6c41bac47a0c055a3712d3.pdf).
El deck SPE1 de `instalacion/` viene de [opm-data](https://github.com/OPM/opm-data), bajo la Open
Database License.

## Pruebas

```bash
uv run pytest
```

Las de `tests/test_flow.py` corren Flow y comparan su saturación inicial contra la fórmula cerrada
de saturación-altura, con curva única, con función J y con SWATINIT.
