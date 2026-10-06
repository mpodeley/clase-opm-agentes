# Ajuste de la función J

Loop de experimentos para que el agente busque, solo, la función J que mejor inicializa la
saturación de agua del Hugin de Volve en OPM Flow. Es una adaptación de
[autoresearch](https://github.com/karpathy/autoresearch) a un problema de reservorios: en lugar
de entrenar una red, cada experimento cambia un caso de ajuste y corre una inicialización.

Lo que distingue a este loop es que **cada experimento es una hipótesis escrita antes de correr**.
Un número que baja sin una razón física detrás no sirve.

## Preparación

1. Proponé un nombre para la corrida con la fecha de hoy (por ejemplo `oct5`). La rama
   `ajuste/<nombre>` no tiene que existir.
2. Creá la rama: `git checkout -b ajuste/<nombre>`.
3. Leé `CLAUDE.md`, `caso.py`, `sw/modelo.py` y `sw/pozo.py`. Son cortos.
4. Creá `results.tsv` con la fila de encabezado y nada más.
5. Anotá la hora de inicio con `date +%H:%M`.

## Qué podés tocar

- **Sí:** `caso.py`. Es el único archivo que editás. Forma de la curva, exponentes de la función
  J, agua irreducible según la roca, regiones de saturación: todo lo que acepta `Case`.
- **No:** `evaluar.py`, `sw/`, `datos/`. La métrica es la de `sw/puntaje.py` y no se discute.
- **No:** más de un nivel de agua libre. El contacto de F-4 es otro ejercicio.
- **No:** instalar paquetes.

## Objetivo

Bajar `rmse_ajuste` con un caso que un ingeniero pueda defender:

- **Hasta 6 parámetros**, contados con honestidad: cada número que elegiste mirando el resultado
  es un parámetro. El arnés rechaza un caso que declare más.
- **Nivel de agua libre (FWL) entre 3,100 y 3,220 m TVDSS.** Es el rango que dejan los datos: el
  informe del operador da 3,120 ± 15 m, el modelo de campo usa 3,200 m, hay petróleo hasta
  3,101 m en 19 A y agua desde 3,148 m en 19 BT2.
- **Agua irreducible entre 0.02 y 0.60**, y decreciente con la calidad de roca si depende de ella.
- `rmse_control` se anota en cada experimento y **nunca** se usa para decidir. El pozo de control
  se perfiló con el campo en producción: su Sw es igual o mayor que la inicial, así que un buen
  caso queda igual o por debajo de ese perfil (`sesgo_control` cerca de cero o negativo).

**Criterio de simplicidad.** Una mejora de menos de 0.002 no se conserva. Una mejora que agrega
parámetros se conserva solo si baja `rmse_ajuste` al menos 0.004 por parámetro agregado. Sacar un
parámetro sin empeorar más de 0.002 se conserva siempre.

## El ciclo

La primera corrida es la base: `caso.py` tal como está, con el mensaje `base`.

1. **Hipótesis.** Antes de tocar nada, decidí qué vas a cambiar y por qué. Editá `caso.py` y
   hacé el commit con tres mensajes, en este orden:

   ```
   git commit -am "<la hipótesis en una oración: qué cambia en el modelo>" \
       -m "mecanismo: <por qué eso acerca el modelo a la roca; qué pozo o tramo debería mejorar>" \
       -m "prediccion: <el número que esperás: rmse_ajuste de X a Y, y qué pasa en qué pozo>"
   ```

2. **Corrida.** `uv run evaluar.py --experimento > run.log 2>&1`. No uses `tee` ni imprimas la
   salida completa. La corrida queda archivada en `corridas/exp-NN-<commit>/` con tu mensaje.
3. **Resultado.**
   `grep -E "^(rmse_ajuste|rmse_control|sesgo_control|error_hcpv_ajuste|n_parametros|rmse_[0-9F]|fwl):" run.log`
4. Si el `grep` sale vacío, la corrida falló: `tail -n 30 run.log`. Un error de tipeo se arregla
   y se vuelve a correr; una idea que no funciona se anota como `crash` y se sigue.
5. **Lectura.** Agregá una fila a `results.tsv` (separado por tabuladores, sin commitear):

   ```
   commit	rmse_ajuste	rmse_control	n_parametros	status	lectura
   ```

   `lectura` dice en una oración si la predicción se cumplió y qué aprendiste, aunque el
   experimento se descarte. `status` es `keep`, `discard` o `crash`.
6. Si cumple el objetivo y el criterio de simplicidad, queda (`keep`). Si no,
   `git reset --hard HEAD~1` (`discard`).
7. `uv run bitacora.py` actualiza `bitacora.html`, que es lo que mira la sala.

Cada tres experimentos mirá la figura del último (`corridas/exp-NN-<commit>/perfil.png`): el
número no dice dónde está el error. El panel de la derecha muestra la nube de J contra Sw de cada
pozo y la curva del caso.

Buscá hipótesis de **forma** antes que de **valor**. Mover un parámetro un 5% no es una hipótesis.

## Cuándo parar

A los **12 experimentos** o a los **20 minutos** de la hora de inicio, lo que pase primero. No
preguntes si seguís: hasta ese límite trabajás solo.

Al parar, corré `uv run bitacora.py --animacion`, que además arma `animacion.gif` con un cuadro por
experimento, y escribí `informe.md` con:

1. El caso final: su forma, sus parámetros, `rmse_ajuste` por pozo, `rmse_control`, el error en
   volumen poral de hidrocarburo y el FWL.
2. Las hipótesis que se cumplieron y las que no, y qué dice cada grupo sobre la roca.
3. Qué pozo o tramo sigue mal ajustado y por qué creés que pasa.
4. Qué tendría que revisar un ingeniero antes de usar este caso en un modelo de campo.
