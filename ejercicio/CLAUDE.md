# Saturación inicial de Volve en OPM Flow

Este proyecto ajusta la forma de inicializar la saturación de agua (Sw) de un modelo de simulación
para que reproduzca los perfiles interpretados de dos pozos del campo Volve (mar del Norte, Equinor,
datos públicos). Es lo que hace un programa de saturación-altura, pero usando el equilibrio del
propio simulador: lo que se ajusta acá es exactamente lo que OPM Flow va a inicializar.

Quienes miran son ingenieros de reservorios. Conocen presión capilar, función J y contactos; no
conocen este repo ni OPM. Explicá en esos términos y mostrá las keywords del deck cuando ayude.

## Cómo funciona

- `caso.py`: el caso de ajuste. Su función `build(cells)` devuelve un `Case`.
- `evaluar.py`: arnés fijo. Arma el deck, corre Flow en un contenedor, lee la saturación inicial,
  la compara con el perfil e imprime un bloque `clave: valor`. Tarda uno o dos segundos.
- `sw/pozo.py`: lee los perfiles y arma las celdas. `sw/modelo.py`: escribe el deck.
  `sw/puntaje.py`: la métrica. `sw/correr.py`: el contenedor. `sw/graficar.py`: la figura.
- `corridas/ultima/`: el deck `SW.DATA`, la salida de Flow, `sw.csv` y `perfil.png` de la última corrida.

Corré siempre con `uv run evaluar.py`. Para guardar una corrida aparte: `--caso casos/b.py --salida corridas/b`.

## El modelo

Una fila de celdas, una por metro de pozo, desde el tope de la Formación Hugin hasta el fin del
perfil. Cada celda tiene su profundidad, su porosidad (PHIF), su permeabilidad (KLOGH) y su
volumen de arcilla (VSH), promediados del perfil. No hay flujo entre celdas (`MULTX` en cero):
cada una se equilibra sola, con la curva de presión capilar y el nivel de agua libre que le toquen.

| Pozo | Rol | Celdas | Perfilado | Geometría |
| --- | --- | --- | --- | --- |
| 15/9-F-12 | ajuste | 379 | 2007, antes de producir | desviado, 2,819 a 3,044 m TVDSS |
| 15/9-F-11 B | validación | 1,277 | 2013, tras cinco años de producción e inyección de agua | casi horizontal, 2,829 a 3,182 m TVDSS |

Profundidades en metros bajo el nivel del mar (TVDSS), positivas hacia abajo. Presiones en bar.

Los fluidos están fijos en `sw/modelo.py`: petróleo de 750 kg/m³ y agua de 1,040 kg/m³ en
condiciones de reservorio, que dan 0.0284 bar de presión capilar por metro sobre el nivel de agua
libre. No hay informe PVT en los datos: es un supuesto.

## Reglas

1. Solo editás `caso.py`, y copias de casos en `casos/`. No tocás `evaluar.py`, `sw/` ni `datos/`.
2. `cells.sw` trae el perfil de F-12 y `NaN` en F-11 B. La validación es ciega salvo que el
   pedido diga `--ver-validacion`.
3. `n_parameters` se cuenta con honestidad: cada número elegido mirando el resultado suma uno.
4. Un resultado se informa con su número: `rmse_ajuste`, `rmse_validacion`, `n_parametros` y el
   error en volumen poral de hidrocarburo. Sin adjetivos.
5. Lo que no sale de los datos se escribe como hipótesis. No hay presiones de formación, ensayos
   de laboratorio ni PVT en este conjunto.
6. No hay internet y no hace falta. No instalás paquetes.
7. Antes de dar por bueno un caso, mirá `corridas/ultima/perfil.png`.

## Trampas conocidas

- La métrica cubre toda la columna de F-12, no solo el Hugin: debajo están Sleipner y Skagerrak,
  con roca pobre y Sw alta.
- `JFUNC` exige `ENDSCALE` en el deck; el arnés lo agrega solo.
- Con `swatinit`, Flow ignora el valor impuesto en las celdas que quedan debajo del nivel de agua
  libre: ahí pone Sw = 1.
- F-11 B se perfiló con el campo en producción. Su Sw es igual o mayor que la inicial, nunca menor.
- Un `rmse_ajuste` bajo con muchos parámetros no es un buen ajuste. Mirá `rmse_validacion`.
