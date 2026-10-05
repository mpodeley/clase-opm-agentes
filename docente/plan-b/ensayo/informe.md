# Saturación inicial de F-12: informe del loop del 5 de octubre de 2026

Quince experimentos sobre `caso.py`, corridos en OPM Flow entre las 16:28 y las 16:43, rama
`ajuste/oct5`. El caso que queda inicializa la saturación de agua (Sw) de F-12 con `rmse_ajuste`
0.1089 y 4 parámetros. La base tenía 0.1772 con 4.

## Tabla de experimentos

La primera fila es la base. `rmse_validacion` se anotó en cada corrida y no intervino en ninguna
decisión.

| commit | rmse_ajuste | rmse_validacion | n_parametros | status | descripción |
| --- | --- | --- | --- | --- | --- |
| 38ff766 | 0.1772 | 0.4906 | 4 | keep | base: curva única (swirr 0.10, pe 0.10 bar, lam 1.0) y un contacto en 2,920 m |
| dc08dce | 0.1634 | 0.4977 | 4 | keep | curva única reajustada: swirr 0.15, pe 0.26 bar, lam 2.6, FWL 2,920 |
| b38ef1b | 0.1587 | 0.4837 | 4 | keep | función J única (swirr 0.09, J de entrada 0.0077, lam 0.61), FWL 2,917.5 |
| f5d6c35 | 0.1169 | 0.4163 | 7 | keep | dos funciones J por formación (Hugin / bajo Hugin), FWL 3,213: 0.0139 por parámetro agregado |
| 731f35c | 0.1189 | 0.4191 | 6 | keep | lam compartido entre las dos funciones J (0.20), FWL 3,300: un parámetro menos, empeora 0.0020 |
| 5756fd3 | 0.1165 | 0.4345 | 4 | keep | funciones J lineales en ln(J): Sw = a - 0.052 ln J, a = 0.285 (Hugin) y 0.897 (bajo Hugin), FWL 3,300: dos parámetros menos y mejora 0.0024 |
| 06f3529 | 0.1138 | 0.4875 | 5 | discard | FWL propio del Hugin en 2,909.2 más FWL 3,300 abajo: mejora 0.0027 por un parámetro, menos de 0.005 |
| 455e092 | 0.1078 | 0.3930 | 5 | keep | exponente de porosidad de JFUNC ajustado (alpha -5.64): a = -0.0876 / 0.4292, b 0.0335, FWL 3,049.4: mejora 0.0087 por un parámetro |
| efd981b | 0.1069 | 0.4423 | 6 | discard | FWL propio del Hugin (2,907.9) más FWL 3,047.9, alpha -7.02: mejora 0.0009 por un parámetro; el cálculo previo fuera de Flow prometía 0.102 y no se cumplió |
| 52d2227 | 0.1037 | 0.4348 | 6 | discard | FWL propio del Hugin en 2,909.2 más FWL 3,048.7, alpha -6.20, reajustado: mejora 0.0041 por un parámetro, menos de 0.005 |
| fec6540 | 0.1514 | 0.4349 | 4 | discard | una sola función para toda la columna (a -0.5698, b 0.0565, alpha -8.0), FWL 2,918.0: un parámetro menos pero empeora 0.0436 |
| ae7fd27 | 0.1116 | 0.3913 | 4 | discard | exponente de porosidad fijo en -1 (a 0.1407 / 0.7072, b 0.0475, FWL 3,105.4): un parámetro menos pero empeora 0.0038, más de 0.003 |
| 4a27c08 | 0.1428 | 0.4336 | 6 | discard | pendiente propia bajo el Hugin (b 0.0415 / 0.0209, alpha -7.77, FWL 3,048.7): empeora 0.0350; el cálculo previo fuera de Flow daba 0.104 |
| 1bd8e0e | 0.1059 | 0.3100 | 6 | discard | exponente de permeabilidad también libre (alpha -0.964, beta 0.0425, b 0.2706, FWL 3,184.7): mejora 0.0019 por un parámetro |
| e2bdc37 | 0.1089 | 0.3265 | 4 | keep | Sw = a - 0.3744 ln(J), J proporcional a Pc × porosidad (alpha -1, beta 0, sin KLOGH), a = -0.3854 / -0.0334, FWL 3,191.6: un parámetro menos, empeora 0.0011 |
| 80e97ab | 0.1085 | 0.3789 | 5 | discard | FWL propio del Hugin (3,082.7) más FWL 3,200.3 sobre la forma vigente: mejora 0.0004 por un parámetro |

## El caso final

Commit `e2bdc37`. Sw depende de la altura sobre el nivel de agua libre (FWL) multiplicada por la
porosidad, con una recta por formación y la misma pendiente en las dos:

```
Sw = a - b · ln(J)        J = Pc · PHIF / 9.549        Pc = 0.0284 bar/m · (FWL - TVDSS)
```

| Parámetro | Valor |
| --- | --- |
| `a`, Hugin | -0.3854 |
| `a`, Sleipner y Skagerrak | -0.0334 |
| `b`, pendiente compartida | 0.3744 |
| FWL | 3,191.6 m TVDSS |

Escrito en altura `h` en metros sobre el FWL, queda Sw = 1.792 - 0.3744 ln(h · PHIF) en el Hugin
y Sw = 2.144 - 0.3744 ln(h · PHIF) debajo, recortado a 1.

En el deck son dos tablas `SWOF` con J en la columna de presión capilar, `SATNUM` 1 en el Hugin
y 2 debajo (el límite es el tope del Sleipner del archivo de picks), una región de equilibrio y:

```
JFUNC
 WATER 30 1* -1 0 XY /
EQUIL
 3191.600 330 3191.600 0 /
```

| Métrica | Valor |
| --- | --- |
| `rmse_ajuste` | 0.1089 |
| `rmse_ajuste_hugin` | 0.1042 |
| `rmse_ajuste_bajo_hugin` | 0.1120 |
| `rmse_validacion` | 0.3265 |
| `n_parametros` | 4 |
| Error en volumen poral de hidrocarburo, F-12 | -0.30% |
| Error en volumen poral de hidrocarburo, F-11 B | -38.3% |
| Sesgo de Sw, F-12 | +0.0034 |
| Sesgo de Sw, F-11 B | +0.2385 |

### Cómo se contaron los parámetros

Cuatro números salieron del ajuste: las dos ordenadas, la pendiente y el FWL. Tres elecciones
quedaron fuera de la cuenta:

- Los exponentes de `JFUNC`, -1 para porosidad y 0 para permeabilidad. Se fijaron en esos valores
  después de que el ajuste libre del experimento `1bd8e0e` diera -0.964 y 0.0425. Quien los
  cuente como ajustados llega a 6 parámetros. Con esa cuenta el caso vigente sería `455e092`:
  `rmse_ajuste` 0.1078, `rmse_validacion` 0.3930, 5 parámetros, error en volumen poral de
  hidrocarburo de -0.22%.
- El piso de las tablas, Sw = 0.02, que es el mínimo de saturación irreducible que admite el
  pedido. Ninguna celda lo alcanza: el Sw simulado mínimo en F-12 es 0.058.
- El límite entre tipos de roca, que es un pick de formación.

Los valores de cada experimento se eligieron con un cálculo fuera de Flow que reproduce el
equilibrio sobre las celdas de F-12 (misma tabla, Sw promediado en el alto de celda). Coincidió
con Flow a 0.0006 o menos en todos los casos salvo dos: `4a27c08`, y `efd981b`, donde la versión
inicial del cálculo evaluaba solo el centro de celda y erró por 0.0045.

`perfil.png` trae el panel de F-11 B. Se miró tres veces durante el loop para revisar F-12, así
que la validación no fue ciega a la vista, aunque ninguna decisión de conservar o descartar usó
ese panel ni `rmse_validacion`.

## Intervalos de F-12 que siguen mal ajustados

El 42% del error cuadrático está en 14 de las 379 celdas. Por intervalo de 10 m:

| Intervalo (m TVDSS) | Sw perfil | Sw simulado | RMSE | Qué pasa |
| --- | --- | --- | --- | --- |
| 2,825–2,835, Hugin | 0.31 | 0.22 | 0.16 | Capa arcillosa en 2,830.5–2,832.2 m (VSH 0.59 a 0.82, PHIF 0.08 a 0.15) con Sw de 0.54 a 1.00; el caso da 0.29 a 0.53 |
| 2,855–2,865, Hugin | 0.05 | 0.15 | 0.11 | La mejor arena del pozo (media geométrica de KLOGH de 416 mD); el caso no baja de 0.12 en el intervalo |
| 2,895–2,910, base del Hugin | 0.33 a 0.72 | 0.26 a 0.64 | 0.10 a 0.16 | El perfil sube de 0.17 a más de 0.6 en 15 m; en 2,907.9–2,909.1 m marca 0.49 a 0.63 con PHIF 0.20 a 0.24 y el caso da 0.21 a 0.29 |
| 2,935–2,945, Sleipner | 0.83 | 0.89 | 0.17 | Tres celdas en 2,937.7–2,938.9 m con Sw 0.37 a 0.63; el caso da 0.73 a 0.93 |
| 2,965–2,975, Skagerrak | 0.84 | 0.88 | 0.17 | Dos celdas en 2,970 m con Sw 0.28 y 0.50, KLOGH menor a 0.1 mD y VSH 0.58 a 0.71; el caso da 0.83 y 0.85 |
| 3,025–3,035, Skagerrak | 0.71 | 0.83 | 0.18 | Tres celdas en 3,032–3,033 m con Sw 0.42 a 0.58; el caso da 0.78 a 0.86 |

Hipótesis sobre las causas, ninguna verificable con este conjunto de datos:

- **Base del Hugin.** El perfil tiene la forma de una zona de transición sobre un contacto cerca
  de 2,909 m. El caso final usa un solo FWL en 3,191.6 m y no la reproduce. Con un FWL propio del
  Hugin en 2,909.2 m (`52d2227`), `rmse_ajuste_hugin` baja de 0.0989 (en `455e092`) a 0.0872, pero la mejora
  total fue de 0.0041 y el criterio pedía 0.005. Sobre la forma final el mismo cambio rindió
  0.0004 y el ajuste llevó ese contacto a 3,082.7 m.
- **Capas finas.** Las celdas arcillosas de 2,831 m y las de alta Sw aisladas miden un metro de
  pozo. Una función de altura y porosidad no las separa de la arena vecina; ni VSH ni KLOGH
  bajaron el error en los ensayos fuera de Flow (menos de 0.002).
- **Sw menor a 0.6 debajo del Hugin.** En once celdas de Sleipner y Skagerrak el perfil da
  entre 0.28 y 0.60, en roca con propiedades iguales a las de celdas vecinas con Sw de 0.9. Puede ser
  hidrocarburo residual o un efecto de la interpretación petrofísica en roca arcillosa.
- **Dependencia con la porosidad.** En el Hugin el Sw del perfil baja al subir PHIF, y por eso
  el escalado de Leverett (`alpha` 0.5) empeora el ajuste frente a `alpha` negativo. Si el Sw
  interpretado se calculó con Archie, esa dependencia viene en parte de la ecuación de
  interpretación y el caso la estaría copiando.

## Qué revisar antes de llevarlo a un modelo de campo

1. El FWL de 3,191.6 m. Queda 148 m debajo de la última muestra de F-12 (3,044 m) y 283 m
   debajo de la base del Hugin. Su función en el ajuste es dar Sw de 0.8 a 0.9 en Sleipner y
   Skagerrak, donde el equilibrio capilar con un contacto en la base del Hugin pondría Sw = 1.
   Es una hipótesis de ajuste. No hay presiones de formación en los datos para ubicar un
   contacto, y el caso con una sola función y FWL en 2,918 m (`fec6540`) dio 0.1514.
2. El hidrocarburo debajo del Hugin. El perfil de F-12 tiene ahí el 14% del volumen poral de
   hidrocarburo del pozo (4.85 de 33.60 m de porosidad por hidrocarburo). El caso lo reproduce
   (4.87) y en un modelo de campo lo extendería a toda la columna hasta 3,191.6 m. Conviene
   decidir si ese volumen existe y es móvil antes de aceptarlo en el volumen in situ.
3. El contacto del Hugin. La transición de 2,895–2,910 m sugiere un contacto cerca de
   2,909 m que el caso final no tiene. En los flancos, por debajo de esa profundidad, el caso
   pone petróleo en el Hugin con Sw de 0.2 a 0.3.
4. La forma de la función. `JFUNC` con exponentes -1 y 0 deja de ser un escalado de
   Leverett: la permeabilidad no interviene. Hay que confirmar que el simulador de destino
   acepta esos exponentes y que la porosidad del modelo de campo, a escala de celda, tiene la
   misma distribución que PHIF a un metro. Con `alpha` -1, una celda de porosidad 0.10 recibe
   0.26 más de Sw que una de 0.20 a igual altura.
5. La extrapolación en altura. F-12 cubre de 148 a 373 m sobre el FWL del caso. La recta en
   ln(h · PHIF) no tiene saturación irreducible y sigue bajando arriba del tope perfilado; el
   piso de la tabla es 0.02.
6. Los fluidos. El gradiente de 0.0284 bar/m sale de densidades supuestas (750 y
   1,040 kg/m³), sin informe PVT. Otro contraste de densidad cambia el FWL ajustado y las
   ordenadas, y deja el Sw de F-12 igual.
7. La validación. `rmse_validacion` es 0.3265 y el caso da 38.3% menos volumen poral de
   hidrocarburo que el perfil de F-11 B, con sesgo de Sw de +0.2385. F-11 B se perfiló en 2013
   con el campo en producción, y su Sw solo puede ser igual o mayor que la inicial; el caso da
   más agua que ese perfil, que es el sentido contrario al que explicaría el barrido. Con un pozo
   de ajuste y uno de validación no se puede afirmar que el caso prediga la Sw inicial fuera de
   F-12.
8. La pendiente propia bajo el Hugin. En `4a27c08` Flow dejó Sw = 1 en 131 celdas donde el
   cálculo previo daba cerca de 0.78, con una tabla de J que cubría de 4e-11 a 1e10. La causa no
   se investigó. Las tablas del caso final cubren J de 0.025 a 0.87 y Flow coincide con el
   cálculo previo.
