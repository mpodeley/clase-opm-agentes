# Ajuste de saturación inicial

Loop de experimentos para que el agente busque, solo, la mejor forma de inicializar la saturación
de agua del pozo 15/9-F-12 de Volve en OPM Flow. Es una adaptación de
[autoresearch](https://github.com/karpathy/autoresearch) a un problema de reservorios: en lugar de
entrenar una red, cada experimento cambia un caso de ajuste y corre una inicialización.

## Preparación

1. Proponé un nombre para la corrida con la fecha de hoy (por ejemplo `oct5`). La rama
   `ajuste/<nombre>` no tiene que existir.
2. Creá la rama: `git checkout -b ajuste/<nombre>`.
3. Leé `CLAUDE.md`, `caso.py`, `sw/modelo.py` y `sw/pozo.py`. Son cortos.
4. Creá `results.tsv` con la fila de encabezado y nada más.
5. Anotá la hora de inicio con `date +%H:%M`.

## Qué podés tocar

- **Sí:** `caso.py`. Es el único archivo que editás. Curvas, función J, tipos de roca, escalado
  de extremos, regiones de equilibrio y contactos: todo lo que acepta `Case`.
- **No:** `evaluar.py`, `sw/`, `datos/`. La métrica es la de `sw/puntaje.py` y no se discute.
- **No:** `swatinit`. Imponer el perfil celda a celda no es un ajuste: no predice nada fuera del pozo.
- **No:** `--ver-validacion`. El pozo F-11 B queda oculto durante todo el loop.
- **No:** instalar paquetes.

## Objetivo

Bajar `rmse_ajuste` con un caso que un ingeniero pueda defender:

- `n_parametros` de 8 como máximo, contado con honestidad: cada número que elegiste mirando el
  resultado es un parámetro, incluidos los límites entre tipos de roca.
- Valores físicos: saturación irreducible entre 0.02 y 0.45, nivel de agua libre (FWL) entre
  2,850 y 3,300 m TVDSS, índice `lam` entre 0.2 y 5.
- `rmse_validacion` se anota en cada experimento y **nunca** se usa para decidir.

**Criterio de simplicidad.** Una mejora de menos de 0.003 no se conserva. Una mejora que agrega
parámetros se conserva solo si baja `rmse_ajuste` al menos 0.005 por parámetro agregado. Sacar un
parámetro sin empeorar más de 0.003 se conserva siempre.

## El ciclo

La primera corrida es la base: `caso.py` tal como está.

1. Escribí en una línea la hipótesis del experimento: qué cambiás y qué esperás ver.
2. Editá `caso.py` y hacé `git commit -am "<hipótesis>"`.
3. Corré `uv run evaluar.py > run.log 2>&1`. No uses `tee` ni imprimas la salida completa.
4. Leé el resultado:
   `grep -E "^(rmse_ajuste|rmse_ajuste_hugin|rmse_validacion|error_hcpv_ajuste|n_parametros):" run.log`
5. Si el `grep` sale vacío, la corrida falló: `tail -n 30 run.log`. Un error de tipeo se arregla
   y se vuelve a correr; una idea que no funciona se anota como `crash` y se sigue.
6. Agregá una fila a `results.tsv` (separado por tabuladores, sin commitear):

   ```
   commit	rmse_ajuste	rmse_validacion	n_parametros	status	descripcion
   a1b2c3d	0.1772	0.4906	4	keep	base: curva única y un contacto
   b2c3d4e	0.1510	0.4712	4	keep	función J en lugar de curva única
   c3d4e5f	0.1498	0.4650	7	discard	tres tipos de roca: mejora menor a 0.005 por parámetro
   ```

7. Si cumple el objetivo y el criterio de simplicidad, queda (`keep`). Si no,
   `git reset --hard HEAD~1` (`discard`).

Cada tres experimentos mirá `corridas/ultima/perfil.png`: el número no dice dónde está el error.

## Cuándo parar

A los **15 experimentos** o a los **20 minutos** de la hora de inicio, lo que pase primero. No
preguntes si seguís: hasta ese límite trabajás solo.

Al parar, escribí `informe.md` con:

1. La tabla de `results.tsv` completa.
2. El caso final: parámetros, `rmse_ajuste`, `rmse_validacion`, error en volumen poral de hidrocarburo.
3. Qué intervalos de F-12 siguen mal ajustados y por qué creés que pasa.
4. Qué tendría que revisar un ingeniero antes de usar este caso en un modelo de campo.
