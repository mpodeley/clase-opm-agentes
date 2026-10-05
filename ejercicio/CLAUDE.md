# Saturación inicial de Volve en OPM Flow

Este proyecto ajusta la función J con que un modelo de simulación inicializa la saturación de agua
(Sw) de la Formación Hugin, para que reproduzca los perfiles interpretados de los pozos del campo
Volve (mar del Norte, Equinor, datos públicos). Es lo que hace un programa de saturación-altura,
pero usando el equilibrio del propio simulador: lo que se ajusta acá es lo que OPM Flow inicializa.

Quienes miran son ingenieros de reservorios. Conocen presión capilar, función J y contactos; no
conocen este repo ni OPM. Explicá en esos términos y mostrá las keywords del deck cuando ayude.

## Cómo funciona

- `caso.py`: el caso de ajuste. Su función `build(cells)` devuelve un `Case`.
- `evaluar.py`: arnés fijo. Arma el deck, corre Flow en un contenedor, lee la saturación inicial,
  la compara con los perfiles e imprime un bloque `clave: valor`. Tarda uno o dos segundos.
  - `--fragmento` imprime la parte del deck que decide el caso.
  - `--caso casos/j2.py --etiqueta j2` guarda otra corrida en `corridas/j2/`.
- `sw/pozo.py`: lee los perfiles y arma las celdas. `sw/modelo.py`: escribe el deck.
  `sw/puntaje.py`: la métrica. `sw/correr.py`: el contenedor. `sw/graficar.py`: la figura.
- `bitacora.py`: arma `bitacora.html` con los experimentos del loop.
- `corridas/<etiqueta>/`: el deck, la salida de Flow, `sw.csv`, `fragmento.txt` y `perfil.png`.

## El deck

Está partido para que el ajuste se vea. `SW.DATA` es el esqueleto. `MODELO_GRID.INC` y
`MODELO_PROPS.INC` tienen la grilla, la roca y los fluidos, y no cambian nunca. Lo que decide un
caso está en cinco archivos:

| Archivo | Keyword | Qué decide |
| --- | --- | --- |
| `AJUSTE_GRID.INC` | `JFUNC` | El escalado de Leverett y sus exponentes |
| `AJUSTE_PROPS.INC` | `SWOF` | La tabla de J contra Sw de cada región de saturación |
| `AJUSTE_SWL.INC` | `SWL` | El agua irreducible por celda, si el caso la escala |
| `AJUSTE_REGIONES.INC` | `SATNUM`, `EQLNUM` | Qué tabla y qué contacto le toca a cada celda |
| `AJUSTE_SOLUTION.INC` | `EQUIL` | El nivel de agua libre (FWL) de cada región |

## El modelo

Una fila de celdas, una por metro de pozo, solo dentro del Hugin. Cada celda tiene su profundidad,
su porosidad (PHIF), su permeabilidad (KLOGH) y una marca de arena neta. No hay flujo entre celdas
(`MULTX` en cero): cada una se equilibra sola.

| Pozo | Rol | Perfilado | Hugin (m TVDSS) | Celdas netas |
| --- | --- | --- | --- | ---: |
| 15/9-19 SR | ajuste | 1993 | 2,861 a 2,880 | 23 |
| 15/9-19 A | ajuste | 1997 | 3,013 a 3,101 | 88 |
| 15/9-19 BT2 | ajuste | 1998 | 3,149 a 3,275 | 128 |
| 15/9-F-12 | ajuste | 2007 | 2,818 a 2,910 | 126 |
| 15/9-F-4 | ajuste | febrero de 2008 | 2,931 a 3,033 | 165 |
| 15/9-F-11 B | control | 2013 | 2,829 a 3,171 | 431 |

El campo empezó a producir el 12 de febrero de 2008. Los cinco pozos de ajuste se perfilaron antes
y muestran el reservorio en estado inicial. F-11 B se perfiló con cinco años de producción e
inyección de agua: el caso nunca ve su perfil, y sirve de control.

Profundidades en metros bajo el nivel del mar (TVDSS), positivas hacia abajo.

Fluidos, fijos en `sw/modelo.py`: petróleo de 720 kg/m³ y agua de 1,065 kg/m³ en reservorio, los
que usó el operador. La función J usa σ·cosθ = 2 mN/m, también del operador, para que los valores
de J sean comparables con los de su informe.

## Lo que se sabe del campo

- Informe petrofísico del operador (Statoil, 2006), en `datos/volve/referencia/`. La sección 6
  (página 49 en adelante) describe su modelo: `Sw = Swn·(1 − Swirr) + Swirr`, con `Swn = a·J^−b`
  y `Swirr` lineal en el logaritmo de la permeabilidad. La tabla 11 da las constantes.
- El mismo informe dice que ningún pozo vio el contacto en perfiles: hay petróleo hasta 3,101 m
  en 19 A y agua desde 3,148 m en 19 BT2.
- El modelo de campo de Equinor (`datos/volve/referencia/VOLVE_2016.DATA`) no usa presión capilar:
  inicializa con `SWL` por celda y varias regiones de equilibrio.

## Reglas

1. Solo editás `caso.py`, y copias de casos en `casos/`. No tocás `evaluar.py`, `sw/` ni `datos/`.
2. `cells.sw` trae el perfil de los cinco pozos de ajuste y `NaN` en F-11 B.
3. `n_parameters` se cuenta con honestidad: cada número elegido mirando el resultado suma uno.
   El arnés rechaza más de 6.
4. Un resultado se informa con su número: `rmse_ajuste`, el RMSE por pozo, `rmse_control`,
   `n_parametros` y el error en volumen poral de hidrocarburo. Sin adjetivos.
5. Lo que no sale de los datos se escribe como hipótesis.
6. No hay internet y no hace falta. No instalás paquetes.
7. Antes de dar por bueno un caso, mirá su `perfil.png`.

## Trampas conocidas

- La métrica cuenta solo arena neta del Hugin. Las celdas no netas aparecen con fondo gris.
- `JFUNC` exige `ENDSCALE` en el deck; el arnés lo agrega solo.
- Con `swl`, la tabla de `SWOF` va de 0 a 1 y Flow la reescala entre el `SWL` de la celda y 1.
- La permeabilidad de F-12, F-4 y 19 BT2 es la revisión de 2009 del operador. La del archivo
  original de F-12 es unas 40 veces menor.
- 19 BT2 está entero en agua. Si un caso le pone petróleo, el contacto está demasiado abajo.
- Un `rmse_ajuste` bajo con un `sesgo_control` positivo es mala señal: el modelo pone más agua
  inicial que la que tiene el pozo de control después de cinco años de inyección.
