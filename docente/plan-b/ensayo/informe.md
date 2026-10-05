# Ajuste de la función J del Hugin: corrida `ajuste/oct5`

Doce experimentos en OPM Flow, del caso base a una función J de un solo exponente. Inicio 20:41,
último experimento 20:48 del 5 de octubre de 2026. Quedaron 2 experimentos además de la base y se
descartaron 9.

## El caso final

Una función J de Leverett para todo el Hugin, sin meseta de agua irreducible, y un nivel de agua
libre (FWL):

```
Sw = J^-0.284            J = Pc · √(k/φ) / (σ·cosθ),  σ·cosθ = 2 mN/m
FWL = 3,150 m TVDSS
```

La curva llega a Sw = 1 en J = 1. Con 200 mD y 22% de porosidad eso es 0.6 m sobre el FWL, y con
10 mD son 2.8 m. A J = 100 da Sw = 0.27 y a J = 1,000 da 0.14.

En el deck son tres keywords. `SATNUM` y `EQLNUM` valen 1 en todas las celdas y no hay `SWL`.

```
JFUNC
 WATER 2 1* 0.5 0.5 XY /
SWOF                               -- 30 filas, J adimensional en la cuarta columna
 0.038019 0.000000 1.000000 100000
 ...
 1.000000 1.000000 0.000000 1 /
EQUIL
 3150.000 330 3150.000 0 1* 1* 1* 1* 0 /
```

Los parámetros contados son dos: el exponente (0.284) y el FWL (3,150 m). El coeficiente de la
curva quedó fijo en 1 y σ·cosθ es el del operador.

| Métrica | Base | Caso final |
| --- | ---: | ---: |
| `rmse_ajuste` | 0.1424 | 0.1121 |
| RMSE 19 SR | 0.0819 | 0.0493 |
| RMSE 19 A | 0.0934 | 0.0879 |
| RMSE 19 BT2 | 0.1096 | 0.1096 |
| RMSE F-12 | 0.1132 | 0.0915 |
| RMSE F-4 | 0.2012 | 0.1422 |
| `rmse_control` (F-11 B) | 0.2048 | 0.1207 |
| `sesgo_control` | −0.0379 | +0.0078 |
| Error en volumen poral de hidrocarburo, ajuste | +8.4% | −1.8% |
| Error en volumen poral de hidrocarburo, control | +4.9% | −1.4% |
| FWL (m TVDSS) | 3,120 | 3,150 |
| `n_parametros` | 4 | 2 |

## Los doce experimentos

| N.º | Hipótesis | `rmse_ajuste` | `rmse_control` | Parámetros | Estado |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | Base: Brooks-Corey con Swirr 0.10, FWL 3,120 m | 0.1424 | 0.2048 | 4 | base |
| 2 | Sin meseta: Sw = 0.68·J^-0.22, FWL 3,120 m | 0.1125 | 0.1761 | 3 | queda |
| 3 | FWL en 3,150 m con la curva del 2 reajustada | 0.1116 | 0.1201 | 3 | descartado |
| 4 | Swirr lineal en log k (forma del operador) | 0.1155 | 0.1821 | 5 | descartado |
| 5 | Sin coeficiente: Sw = J^-0.284, FWL 3,150 m | 0.1121 | 0.1207 | 2 | queda |
| 6 | Sw según la altura sola, sin `JFUNC` | 0.1238 | 0.1297 | 3 | descartado |
| 7 | Dos tipos de roca por permeabilidad (corte en 28 mD) | 0.1101 | 0.1184 | 4 | descartado |
| 8 | Swirr = 0.20·VSH, agua ligada a la arcilla | 0.1129 | 0.1280 | 3 | descartado |
| 9 | FWL del operador (3,120 m) con la curva del 5 | 0.1153 | 0.1771 | 2 | descartado |
| 10 | Exponente de k libre en `JFUNC` (0.41) | 0.1118 | 0.1178 | 3 | descartado |
| 11 | Arena limpia y arena arcillosa (corte en VSH 0.215) | 0.1102 | 0.1287 | 4 | descartado |
| 12 | Hipérbola de Thomeer con umbral de entrada | 0.1135 | 0.1254 | 3 | descartado |

`rmse_control` está anotado en cada fila y ninguna decisión lo usó.

## Hipótesis que se cumplieron

**La nube de J contra Sw no tiene meseta (experimento 2).** Entre 20 y 330 m sobre el contacto la
Sw del perfil sigue bajando con J. Sacar el Swirr de 0.10 bajó `rmse_ajuste` de 0.1424 a 0.1125 con
un parámetro menos, y F-4 pasó de 0.201 a 0.145. Un piso de Sw agregado después a la ley de
potencias no cambia el ajuste en la cuenta previa (0.1121 con piso en 0.10).

**El escalado de Leverett hace falta (experimento 6).** Con una curva de Pc igual para toda la
roca el RMSE sube 0.012, y sube donde alternan capas de 50 y de 3,000 mD a la misma altura: F-4
pasa de 0.142 a 0.167 y F-12 de 0.092 a 0.100.

**El exponente 0.5 alcanza (experimento 10).** Liberar el exponente de la permeabilidad da 0.41 y
mejora 0.0003.

**El coeficiente de la curva y el FWL se compensan (experimentos 3, 5 y 9).** Con el coeficiente
libre, mover el FWL de 3,120 a 3,150 m cambia `rmse_ajuste` en 0.0009. Con el coeficiente fijo en
1, el contacto en 3,150 m da 0.1121 y en 3,120 m da 0.1153, casi todo en 19 A (0.088 contra
0.114). Los cinco pozos de ajuste solos no fijan el FWL dentro de ese rango de 30 m.

**No hay umbral de entrada visible (experimento 12).** La hipérbola de Thomeer con umbral en
J = 2.1 mejora 19 A (0.076) y empeora F-4 y F-12; el total queda en 0.1135.

## Hipótesis que no se cumplieron

**El agua irreducible según la roca, con la forma del operador (experimento 4).** Predije 0.1116
y salió 0.1155. 19 A mejoró de 0.082 a 0.056, y F-4 y 19 SR empeoraron. La función J ya lleva la
permeabilidad, y un `SWL` por celda encima le pide a los pozos cosas opuestas.

**El agua ligada a la arcilla (experimento 8).** Predije 0.1115 y salió 0.1129. La base de F-4 no
ganó el agua que le falta: F-4 pasó de 0.142 a 0.148.

En los dos casos falló también mi cuenta previa. La tabla de `SWOF` del caso arranca en Sw = 0.03
a 0.04 y Flow reescala desde ese valor hasta el `SWL` de la celda, así que el resultado sale 0.02
más seco que lo calculado. Los coeficientes de esos dos experimentos no son los óptimos de su
forma; la cuenta previa estima que el óptimo mejora menos de 0.001, y eso no está verificado en
Flow.

**Los dos tipos de roca (experimentos 7 y 11).** Las predicciones numéricas se cumplieron (0.110)
y la hipótesis física no: dos regiones `SATNUM` ganan 0.002 con dos parámetros más. El corte por
permeabilidad mejora 19 A y el corte por arcilla mejora F-4 (0.133) a costa de 19 A, 19 SR y F-12.

Los dos grupos dicen lo mismo sobre la roca. El Hugin neto de estos pozos se comporta como una sola
familia de gargantas una vez escalado por √(k/φ), y la arcilla y la permeabilidad no agregan
información a la saturación inicial. Es una hipótesis que sostienen cinco pozos y ningún dato de
laboratorio.

## Lo que sigue mal ajustado

F-4 concentra el 50% del error cuadrático y 19 BT2 el 23%. Sin 19 BT2 y sin la base de F-4, las
356 celdas restantes tienen un RMSE de 0.081.

| Tramo | Celdas | Sw del perfil | Sw simulada | RMSE |
| --- | ---: | ---: | ---: | ---: |
| F-4, 3,005 a 3,033 m | 46 | 0.447 | 0.243 | 0.247 |
| F-4, 2,931 a 3,005 m | 119 | 0.160 | 0.189 | 0.067 |
| 19 A, 3,060 a 3,101 m | 44 | 0.246 | 0.326 | 0.107 |
| 19 BT2, 3,150 a 3,274 m | 128 | 0.953 | 1.000 | 0.110 |

**La base de F-4.** El perfil tiene el doble de agua que el modelo a 115 a 145 m sobre el FWL, en
roca de 149 mD de media geométrica. 19 A, 70 m más abajo y con roca de 53 mD, tiene Sw de 0.25.
Ninguna de las cinco formas de roca probadas le da agua a la base de F-4 sin quitarle petróleo a
19 A. Hipótesis: los dos pozos tienen contactos distintos, por un nivel de agua libre inclinado o
por bloques separados por fallas. El programa excluye más de un FWL, así que no se probó.

**19 BT2.** El pozo está entero bajo el FWL y el modelo le pone Sw = 1. El perfil promedia 0.953 y
12 de las 128 celdas netas bajan de 0.90. Un equilibrio de drenaje no puede reproducir eso con
ningún contacto del rango permitido. Hipótesis: petróleo residual bajo el contacto o ruido de la
interpretación en zona de agua. Ese 0.110 es un piso para cualquier caso de este ejercicio.

**19 A entre 3,060 y 3,101 m.** El modelo pone 0.08 más de agua que el perfil. Es el costo de
tener una sola curva: las formas que lo corrigen (experimentos 4, 7 y 12) empeoran F-4.

## Qué revisar antes de llevarlo a un modelo de campo

1. **El FWL.** 3,150 m es el tope del agua de 19 BT2 y queda 15 m por debajo del rango del
   operador (3,120 ± 15 m). Con esta curva los pozos de ajuste lo prefieren por 0.003 de RMSE,
   casi todo en 19 A. El pozo de control cambia mucho más entre los dos contactos:
   `sesgo_control` es +0.055 con 3,120 m y +0.008 con 3,150 m. Ese dato no decidió nada acá y
   pide una revisión con presiones de formación, que este ajuste no usó.
2. **La cola de la curva.** Sin meseta, Sw sigue bajando con la altura. La tabla termina en
   Sw = 0.038 a J = 100,000 y las celdas del ajuste llegan a J cercanos a 3,000 (Sw = 0.10). Un
   modelo de campo con más columna o más permeabilidad que estos pozos va a extrapolar por debajo
   de lo que muestran los perfiles.
3. **La permeabilidad.** J va con √k. El KLOGH de F-12, F-4 y 19 BT2 es la revisión de 2009; el
   modelo de campo tiene que usar una permeabilidad coherente con esa, o el exponente cambia.
4. **Las curvas de laboratorio.** El ajuste salió de perfiles. Falta comparar Sw = J^-0.284 con
   las presiones capilares de corona del informe del operador (sección 6 y tabla 11), que no leí
   en esta corrida.
5. **El contacto de F-4.** Un solo FWL deja 46 celdas con la mitad del agua del perfil. En un
   modelo con regiones de equilibrio (`EQLNUM`), como el de Equinor, ese bloque necesita su propia
   decisión.
6. **El control.** F-11 B se perfiló con cinco años de inyección. Un `sesgo_control` de +0.008
   está dentro de lo que el control permite afirmar: el caso no pone más agua inicial que la que
   tenía el pozo en 2013. No permite afirmar que la saturación inicial de F-11 B esté bien.

## Cómo se eligieron los números

Cada experimento se escribió como hipótesis en el commit antes de correr. Para dar un número a la
predicción usé una cuenta propia del equilibrio fuera del repo (Sw a partir de J, celda por celda,
solo con los cinco pozos de ajuste), que reproduce a Flow en el caso base: 0.1425 contra 0.1424.
Los coeficientes de cada forma salieron de ese ajuste por mínimos cuadrados y cada uno está contado
como parámetro. La consecuencia es que las predicciones acertaron más de lo que acertaría una
hipótesis sin cuenta previa, salvo en los dos experimentos con `SWL`.

El punto de partida fue el caso base: en este repo no había otros casos en `casos/` aparte de
`base.py`.
