---
marp: true
theme: podeley
paginate: true
header: 'Simulación numérica con agentes · **OPM Flow sobre Volve**'
footer: 'clase-opm-agentes'
---

<!-- _class: portada -->

# Un agente ajusta la función J

Clase de 3 h 45 min · ingeniería de reservorios · **OPM Flow · Claude Code · Volve**

<!--
0:00 · portada mientras entra la gente
Ventanas: A este deck; B terminal en el repo; C terminal en ~/sw-volve con
el agente SIN lanzar, letra grande y tema claro; D visor de imágenes sobre
~/sw-volve/corridas; E navegador con bitacora.html; F fuera de pantalla, el
guion y docente/plan-b/tabla.md.
El minuto a minuto completo está en docente/guion.md.
-->

---

<!-- _class: agenda -->

## Hoy

| Bloque | Tiempo | Qué hacemos |
| --- | --- | --- |
| El campo y el dataset | 25 min | Mapa, superficies, secciones, producción y qué pozos sirven para ajustar |
| Lectura rápida de perfiles | 20 min | Arenas, porosidad, agua como BVW, agua irreducible y agua móvil |
| PVT y presiones | 15 min | Densidades, gradientes y los tres contactos que circulan |
| Instalación | 20 min | OPM Flow en un contenedor, el entorno de Python y Claude Code |
| Pausa | 10 min | |
| Repaso de J y el deck | 25 min | Qué es la función J; el agente lee el deck y muestra dónde vive el ajuste |
| Ajuste de J | 40 min | Una J, el modelo del operador y su forma reajustada; el pozo de control |
| Pausa | 10 min | El loop queda corriendo |
| Loop con hipótesis a la vista | 30 min | El agente prueba variantes solo y escribe cada hipótesis antes de correr |
| El contacto de F-4 | 15 min | Contacto inclinado contra agua colgada en una cubeta de la base |
| Controles y cierre | 15 min | Qué revisa y firma el ingeniero, y los límites de lo que vimos |

<!--
2 min · acumulado 0:02
Todo corre en mi máquina. Ustedes se llevan el repo para repetirlo.
La clase sirve si al final pueden decir qué le pedirían a un agente y qué
le revisarían.
-->

---

<!-- _class: seccion -->

## El campo y el dataset

Bloque 1 de 9 · **25 min**

<!--
0 min · acumulado 0:02
Arranca 0:00, termina 0:25.
-->

---

## Volve, en un minuto

- Campo de petróleo del mar del Norte noruego, cinco kilómetros al norte de Sleipner Øst, con 80 m de agua
- Descubierto en 1993; produjo de 2008 a 2016 con **inyección de agua**
- Reservorio: arenisca del Jurásico Medio, **Formación Hugin**, entre 2,700 y 3,100 m
- 10.0 millones de Sm³ de petróleo producidos; el operador informó 54% de recuperación

<!--
2 min · acumulado 0:04
Sm³: metro cúbico en condiciones estándar. Los datos de campo son de la
ficha de la Norwegian Offshore Directorate (Sodir); el acumulado sale del
archivo de producción del operador. Equinor liberó el conjunto en 2018.
-->

---

<!-- _class: figura -->

## Dónde están los pozos

![Mapa del tope de la Formación Hugin con los seis pozos del ejercicio y la entrada de otros doce pozos al reservorio](img/mapa-hugin.png)

Cada pozo tiene un color y lo conserva en todas las figuras de la clase.

<!--
3 min · acumulado 0:07
Un alto de unos 1.5 por 2.5 km con el tope cerca de 2,800 m en la cresta.
En color, los seis pozos que usamos, con su tramo dentro del Hugin. Los
tres 19 son pozos de exploración de 1993 a 1998; los F salen de la
plataforma. Los puntos negros son los otros pozos con tope del Hugin.
-->

---

<!-- _class: figura -->

## Las superficies del conjunto

![Mapas de la discordancia de la base del Cretácico, el tope y la base de la Formación Hugin, y el espesor del Hugin](img/superficies.png)

Tres horizontes en la misma escala de profundidad, y el espesor del Hugin entre dos de ellos.

<!--
3 min · acumulado 0:10
BCU: base Cretaceous unconformity, la discordancia de la base del
Cretácico, el sello regional. En nuestros pozos el Hugin tiene de 18 m (19 SR) a 126 m (19 BT2) de
espesor vertical, y se adelgaza hacia el oeste.
No hay en público superficies de Sleipner ni de Skagerrak, ni polígonos
de falla: los topes de pozo son la única fuente para lo que está debajo.
-->

---

<!-- _class: figura -->

## Los seis pozos, en sección

![Sección a lo largo de cada pozo con la discordancia, el tope y la base del Hugin, y la trayectoria coloreada por saturación de agua](img/secciones.png)

Claro es petróleo, oscuro es agua. Solo el tramo dentro del Hugin entra al modelo.

<!--
4 min · acumulado 0:14
19 SR, F-12, F-4 y 19 A cruzan el Hugin con petróleo, cada uno a una
profundidad distinta: entre los cuatro cubren de 2,818 a 3,101 m. 19 BT2
lo cruza entero en agua, de 3,149 a 3,275 m. F-11 B corre cerca del tope
y entra y sale por fallas.
La línea de los horizontes sale del mapa, con su incertidumbre.
-->

---

<!-- _class: figura -->

## Qué pozos muestran el estado inicial

![Producción mensual de petróleo y agua e inyección de agua del campo, de 2008 a 2016](img/produccion.png)

El primer petróleo fue el 12 de febrero de 2008. Lo perfilado después ya no es saturación inicial.

<!--
3 min · acumulado 0:17
La regla de la clase: se ajusta solo con pozos perfilados antes de
producir. Cuando se perfiló F-11 B el campo producía unas cinco veces más
agua que petróleo: su perfil sirve de control y no de dato de ajuste.
F-4 es el caso límite: sus perfiles de reservorio son del 7 y del 11 de
febrero de 2008, la semana anterior al primer petróleo.
-->

---

## Cinco pozos para ajustar, uno de control

| Pozo | Perfilado | Hugin (m TVDSS) | Arena neta | Rol |
| --- | --- | --- | ---: | --- |
| 15/9-19 SR | 1993 | 2,861 a 2,880 | 23 m | Ajuste |
| 15/9-19 A | 1997 | 3,013 a 3,101 | 88 m | Ajuste |
| 15/9-19 BT2 | 1998 | 3,149 a 3,275 | 128 m | Ajuste, todo en agua |
| 15/9-F-12 | 2007 | 2,818 a 2,910 | 126 m | Ajuste |
| 15/9-F-4 | 7 y 11 de febrero de 2008 | 2,931 a 3,033 | 165 m | Ajuste |
| 15/9-F-11 B | 2013 | 2,829 a 3,171 | 431 m | Control |

<!--
3 min · acumulado 0:20
TVDSS: true vertical depth subsea, metros verticales bajo el nivel del
mar. La arena neta está en metros de pozo, una celda por metro.
El control nunca se le muestra al caso. Como es posterior a cinco años de
inyección, su Sw es igual o mayor que la inicial: un buen modelo de
saturación inicial queda igual o por debajo de ese perfil.
-->

---

## Qué trae el conjunto y qué usamos

| El conjunto completo | Lo que usa la clase |
| --- | --- |
| Unos 40,000 archivos, cerca de 5 TB | 24 archivos, 52 MB |
| Sísmica 3D y 4D | |
| Modelos estático y dinámico | El deck de campo, solo para leerlo |
| Perfiles de pozo, crudos e interpretados | Interpretado de 6 pozos, crudos de 2 |
| Trayectorias, topes y superficies | 3 trayectorias, los topes, 3 horizontes |
| Producción, presiones e informes | La mensual, 1 ensayo de presión, 2 informes |

<!--
3 min · acumulado 0:23
Todo se baja de espejos públicos y queda fijado por su hash. Los dos
informes son el petrofísico del operador de 2006 y el PVT de laboratorio
del petróleo de F-4.
-->

---

<!-- _class: figura -->

## Lo que hay que reproducir

![Saturación de agua de la arena neta del Hugin contra profundidad en los cinco pozos de ajuste](img/sw-profundidad.png)

Cinco pozos en una sola escala de profundidad: 450 m entre el más alto y el más bajo.

<!--
2 min · acumulado 0:25
Preguntar a la sala: ¿dónde pondrían el contacto? Anotar dos o tres
respuestas, vuelven en el bloque 3.
Petróleo hasta 3,101 m en 19 A, agua desde 3,149 m en 19 BT2. Ningún pozo
vio el contacto.
Cierre del bloque 1.
-->

---

<!-- _class: seccion -->

## Lectura rápida de perfiles

Bloque 2 de 9 · **20 min**

<!--
0 min · acumulado 0:25
Arranca 0:25, termina 0:45.
-->

---

<!-- _class: figura -->

## F-12: la arena, la porosidad y el agua

![Lectura rápida de 15/9-F-12: rayos gamma con arena neta, resistividad, densidad y neutrón, porosidad, saturación de agua y volumen de fluidos](img/quicklook-f12.png)

De izquierda a derecha: dónde hay arena, qué dice la resistividad, cuánta porosidad y cuánta agua.

<!--
5 min · acumulado 0:30
No hay potencial espontáneo (SP): los pozos se perforaron con lodo base
aceite. La arena se marca con rayos gamma y volumen de arcilla.
Leer las pistas en orden. La última es la que importa para hoy: BVW (bulk
volume water) es porosidad por saturación, el agua por unidad de roca.
El celeste claro es agua que la roca retiene; el azul oscuro, agua que
puede moverse.
-->

---

<!-- _class: figura -->

## F-4: el agua móvil aparece en la base

![Lectura rápida de 15/9-F-4: la resistividad cae y el agua móvil crece hacia la base del Hugin](img/quicklook-f4.png)

La resistividad cae desde 3,005 m y por debajo de 3,015 m la Sw media es 0.51.

<!--
5 min · acumulado 0:35
En F-4 la zona de transición está dentro del pozo: debajo de 3,015 m hay
agua móvil. En 19 A, 70 m más abajo, casi no la hay. Esa diferencia es la
pregunta del bloque 8: ¿hay una cubeta en la base?
Dato de procedencia: la permeabilidad de F-12 en el archivo de 2007 es
unas 40 veces menor que la revisión de 2009 del operador. Usamos la
revisión. La función J depende de la raíz de k.
-->

---

<!-- _class: figura -->

## ¿Cuánta del agua es irreducible?

![Gráfico de Buckles de los cinco pozos de ajuste y saturación de agua contra permeabilidad con la línea de agua irreducible del operador](img/buckles.png)

Agua irreducible (Swirr): la que la roca retiene por capilaridad a cualquier altura. Lo que la supera es agua móvil.

<!--
6 min · acumulado 0:41
Izquierda, Buckles: los puntos sobre una línea de BVW constante tienen
solo agua irreducible. F-12, 19 SR y buena parte de 19 A y F-4 caen entre
0.02 y 0.04. 19 BT2 queda aparte: es agua.
Derecha: Sw contra permeabilidad con la línea de Swirr del operador. Con
esa línea, hay agua móvil en el 17% de la arena de 19 A, el 27% de F-12,
el 37% de F-4 y el 99% de 19 BT2.
Mucho punto queda por debajo de la línea: el Swirr del operador es alto
para estos pozos. Vuelve en el bloque 6.
-->

---

<!-- _class: cita -->

## La función J tiene que explicar **el agua móvil**; el resto lo fija la roca

<!--
4 min · acumulado 0:45
La idea que ordena el ajuste. El agua irreducible depende de la calidad
de roca y no de la altura. Lo que cambia con la altura sobre el contacto
es el agua móvil, y eso es lo que describe una función J.
Cierre del bloque 2.
-->

---

<!-- _class: seccion -->

## PVT y presiones

Bloque 3 de 9 · **15 min**

<!--
0 min · acumulado 0:45
Arranca 0:45, termina 1:00.
-->

---

## Lo que dicen los fluidos

| Dato | Valor | Fuente |
| --- | --- | --- |
| Densidad del petróleo en reservorio | 720 kg/m³ | Ensayo de 19 A (1997) y PVT de F-4 (2008) |
| Densidad del agua de formación | 1,065 kg/m³ | Informe petrofísico del operador (2006) |
| Presión de burbuja | 213 a 236 bar | PVT de F-4 y ensayo de 19 A |
| Presión inicial | 336.5 ± 0.5 bar | Ensayo de 19 A |
| Temperatura | 107 a 112 °C | Los dos |

La diferencia de densidades, 345 kg/m³, da **0.034 bar de presión capilar por metro** sobre el nivel de agua libre.

<!--
4 min · acumulado 0:49
PVT: presión, volumen y temperatura, el estudio de fluidos. El petróleo
está subsaturado: 100 bar por encima de la burbuja. No hay gas libre y el
modelo es de dos fases.
Estas dos densidades son las que usó el operador para su modelo de
saturación-altura y las que quedan fijas en nuestro deck.
-->

---

<!-- _class: figura -->

## Tres fuentes de presión, tres contactos

![Presión de formación contra profundidad: 16 puntos en agua de 19 BT2, el ensayo de 19 A y la muestra de F-4, con las líneas de agua y petróleo](img/presiones.png)

El cruce de las dos líneas da 3,196 ± 14 m. El informe del operador dice 3,120 ± 15 m; su modelo de campo usa 3,200 m.

<!--
6 min · acumulado 0:55
La línea de agua sale de 16 puntos del probador de formación de 19 BT2:
0.1053 bar por metro, 1,074 kg/m³. La de petróleo pasa por el ensayo de
19 A con 720 kg/m³.
Medio bar de error en el ensayo mueve el cruce 14 m. Y 19 BT2 puede estar
en otro bloque.
El punto de F-4 queda 6.7 bar por encima de la línea de petróleo: o la
presión de 19 A está referida a otra profundidad, o son bloques
distintos. No hay presiones en F-12.
-->

---

## Lo que se sabe del contacto

- **Perfiles**: petróleo hasta 3,101 m (19 A), agua desde 3,149 m (19 BT2). Nadie lo vio
- **Informe del operador, 2006**: nivel de agua libre (**FWL**, free water level) en 3,120 ± 15 m, por modelado con función J
- **Presiones**: 3,196 ± 14 m
- **Modelo de campo, 2016**: 12 regiones de equilibrio; la principal en 3,200 m, otras en 3,025 y 2,910 m

Nuestro ajuste deja el FWL libre entre **3,100 y 3,220 m**.

<!--
5 min · acumulado 1:00
Volver a las respuestas del bloque 1.
El rango de 120 m es lo que dejan los datos. Dentro de ese rango, el
contacto es un parámetro más del ajuste.
Cierre del bloque 3.
-->

---

<!-- _class: seccion -->

## Instalación

Bloque 4 de 9 · **20 min**

<!--
0 min · acumulado 1:00
Arranca 1:00, termina 1:20.
-->

---

## Cuatro piezas

- **Podman o Docker**: correr OPM Flow sin compilarlo
- **uv**: el entorno de Python, siempre igual
- **git**: el historial de experimentos
- **Claude Code**: el agente

OPM Flow es un simulador de petróleo negro de código abierto. Lee el mismo formato de deck que los comerciales.

<!--
4 min · acumulado 1:04
OPM: Open Porous Media. Para quien usa Eclipse: las keywords son las
mismas, con algunas sin soporte.
-->

---

<!-- _class: panel -->

## Dos comandos

`instalacion/instalar.sh`

`instalacion/verificar.sh`

La imagen del simulador y los datos quedan **fijados por su hash**.

<!--
9 min · acumulado 1:13
Ventana B. instalar.sh: leer las tres etapas en voz alta. La imagen ya
está bajada; decir que la primera vez pesa 1.2 GB.
verificar.sh: Flow responde, SPE1 corre en cerca de un segundo, el caso
base da su puntaje.
Después, uv run evaluar.py a mano: mostrar el bloque de números y abrir
la figura en la ventana D.
-->

---

## La carpeta del agente

- **`CLAUDE.md`**: qué es el proyecto, las reglas y las trampas conocidas
- **`caso.py`**: el único archivo que puede editar
- **`evaluar.py`** y **`sw/`**: el arnés y la métrica, de solo lectura
- **`.claude/settings.json`**: puede correr `evaluar.py` y usar git local; no puede salir a internet, borrar ni tocar los datos

<!--
7 min · acumulado 1:20
Ventana B: ejercicio/preparar.sh, y después abrir settings.json. Leer la
lista de permisos y la de prohibiciones.
Lo que el agente no debe hacer se escribe como permiso, y lo que debe
saber se escribe en CLAUDE.md.
Cierre del bloque 4. Pausa de 10 minutos.
-->

---

<!-- _class: seccion -->

## Repaso de J y el deck

Bloque 5 de 9 · **25 min**

<!--
0 min · acumulado 1:30
Arranca 1:30, termina 1:55.
-->

---

## La función J, en tres líneas

- En equilibrio, la presión capilar crece con la altura **H** sobre el nivel de agua libre: Pc = Δρ · g · H
- Leverett la normaliza por la calidad de roca: **J = Pc · √(k/φ) / (σ · cosθ)**
- Si la roca es de una misma familia, J contra Sw es **una sola curva**

El operador usó una potencia: Swn = a · J^−b, con Sw = Swn · (1 − Swirr) + Swirr.

<!--
4 min · acumulado 1:34
Swn: saturación normalizada entre el agua irreducible y uno.
Lo que supone: una sola familia de roca, mojabilidad uniforme, drenaje
primario, y que k y φ del perfil representan la garganta poral. Cuando
alguno falla, la nube de puntos se abre.
σ·cosθ en reservorio no se mide: es un parámetro de escala. Lo dejamos
fijo en el valor del operador, 2 mN/m, para comparar con su informe.
-->

---

<!-- _class: figura -->

## Qué compra la función J

![Tres perfiles de saturación contra altura para rocas de 10, 100 y 1,000 mD, y las mismas tres rocas colapsadas en una sola curva de J](img/repaso-j.png)

Tres rocas dan tres perfiles de saturación y una sola curva de J: se ajusta una curva en lugar de una por roca.

<!--
4 min · acumulado 1:38
Izquierda: a igual altura, la roca de 10 mD tiene mucha más agua que la
de 1,000 mD. Derecha: las tres caen sobre la misma J.
El ajuste de hoy son los parámetros de esa curva, más el contacto.
-->

---

## El modelo y el deck de campo

- **Nuestro modelo**: una celda por metro de pozo, con su profundidad y su roca; `MULTX` en cero, cada celda se equilibra sola
- **El deck de campo de Equinor**: 12 regiones de `EQUIL` y **presión capilar cero**. El agua inicial es un arreglo `SWL` por celda
- Sin presión capilar no hay zona de transición: el agua es la irreducible hasta el contacto

Con una función J, la saturación sale de la roca y la altura, y predice donde no hay pozo.

<!--
4 min · acumulado 1:42
Lo verifiqué en el deck público: la columna de presión capilar de sus
tablas de saturación es cero y no usa JFUNC ni SWATINIT.
Las dos formas son legítimas. La de campo honra el volumen del
geomodelo; la de J explica por qué el agua está donde está.
-->

---

<!-- _class: panel -->

## Primer pedido

`claude`, y adentro el texto de `PEDIDO-1.md`

Correr el caso base, **explicar el deck**, leer la figura y listar los supuestos. Sin cambiar nada.

<!--
6 min · acumulado 1:48
Ventana C. Aceptar el diálogo de confianza leyéndolo en voz alta.
Narrar qué herramienta llama: lee archivos, corre evaluar.py con
--fragmento, abre SW.DATA, mira perfil.png.
El caso base da rmse_ajuste 0.142 y control 0.205.
-->

---

<style scoped>pre { font-size: 15.5px; line-height: 1.32; } h2 { margin-bottom: 10px; }</style>

## Dónde vive el ajuste en el deck

```
-- ===== AJUSTE_GRID.INC
JFUNC
 WATER 2 1* 0.5 0.5 XY /          -- tensión, exponentes de φ y de k
-- ===== AJUSTE_PROPS.INC
SWOF
--   Sw        krw      kro      J
 0.064510 0.000000 1.000000 100000
   ...  (27 filas más)
 0.900894 0.714661 0.011223 0.462126
 1.000000 1.000000 0.000000 0.298 /
-- ===== AJUSTE_SWL.INC
-- Sin escalado de extremos: el agua irreducible es la de la tabla.
-- ===== AJUSTE_SOLUTION.INC
EQUIL
 3150.000 330 3150.000 0 1* 1* 1* 1* 0 /      -- nivel de agua libre
```

<!--
5 min · acumulado 1:53
Es la salida de evaluar.py --fragmento para el caso J1, sin los
comentarios. El deck está
partido: SW.DATA es el esqueleto, MODELO_*.INC la grilla y los fluidos,
que no cambian, y estos archivos lo que decide un caso.
Con JFUNC, la cuarta columna de SWOF deja de ser presión capilar en bar y
pasa a ser J.
Cuatro parámetros a la vista: la J de entrada (0.298), la forma de la
tabla (dos números) y el contacto.
-->

---

<!-- _class: cita -->

## Un caso nuevo es un **diff de tres archivos chicos**

<!--
2 min · acumulado 1:55
Lo que hace revisable el trabajo del agente: cada cambio de caso toca
solo AJUSTE_*.INC. Lo vamos a ver en el bloque que sigue.
Cierre del bloque 5.
-->

---

<!-- _class: seccion -->

## Ajuste de J

Bloque 6 de 9 · **40 min**

<!--
0 min · acumulado 1:55
Arranca 1:55, termina 2:35. Pegar PEDIDO-2.md al empezar: el agente
necesita unos 12 minutos.
-->

---

<!-- _class: acentos -->

## Tres casos y nada más

- **J1**: una función J de Leverett y un contacto. Cuatro parámetros
- **OP**: el modelo del operador tal como está en su informe de 2006, **sin ajustar**
- **J2**: la forma del operador, con Swirr según permeabilidad, reajustada a estos pozos. Cinco parámetros

El agente lee el informe, arma los tres y muestra el diff entre uno y otro.

<!--
12 min · acumulado 2:07
Mientras el agente trabaja. Pedir a la sala que apueste: ¿el modelo de
2006 sin tocar ajusta mejor o peor que una J nueva de cuatro parámetros?
Si el agente encuentra que la tabla 11 y las figuras del informe no
coinciden, mostrarlo: es verdad. La tabla da Swirr = 0.45 − 0.105 log k
para Volve; la figura 20.b rotula 0.412 − 0.088 log k.
-->

---

<!-- _class: figura -->

## El modelo del operador, sin tocar

![Caso OP: perfil y simulado en los seis pozos y nube de J contra Sw normalizada](img/caso-op.png)

RMSE de ajuste 0.122 sin ajustar un solo número. En el control pone más agua que la que hay: sesgo +0.066.

<!--
6 min · acumulado 2:13
Leer la figura: seis pozos en una escala de profundidad, el FWL como
línea de trazos, y a la derecha la nube de J de cada pozo con la curva.
Un modelo de 2006, hecho con pozos de Sleipner Øst y dos de Volve,
reproduce pozos que no existían cuando se escribió.
Su debilidad está en el control: da más agua inicial que la que F-11 B
tiene después de cinco años de inyección. El Swirr es alto.
-->

---

<!-- _class: figura -->

## Una sola J, cuatro parámetros

![Caso J1: perfil y simulado en los seis pozos y nube de J contra Sw](img/caso-j1.png)

RMSE de ajuste 0.112 y control 0.122, con el contacto en 3,150 m y sin sesgo en el control.

<!--
6 min · acumulado 2:19
El contacto queda en 3,150 m: entre el petróleo de 19 A y el agua de
19 BT2, que es donde los datos lo acotan.
Mirar F-11 B: la transición que el modelo predice entre 3,100 y 3,170 m
está en el perfil de 2013. El caso nunca vio ese pozo.
El peor pozo es F-4: 0.147. El modelo no pone agua en su base.
-->

---

## Lo que dio

| Caso | Ajuste | F-4 | Control | Sesgo del control | FWL | Parámetros |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base, sin ajustar | 0.142 | 0.201 | 0.205 | −0.038 | 3,120 m | 4 |
| J1: una función J | 0.112 | 0.147 | 0.122 | −0.003 | 3,150 m | 4 |
| OP: operador, 2006 | 0.122 | 0.151 | 0.197 | +0.066 | 3,120 m | 0 |
| J2: forma del operador | 0.114 | 0.149 | 0.142 | +0.003 | 3,151 m | 5 |

Error en volumen poral de hidrocarburo: de −1.0% a −2.2% en los tres casos ajustados o publicados.

<!--
6 min · acumulado 2:25
Tabla de referencia, ajustada con un optimizador clásico. Compararla con
comparacion.md, la que acaba de escribir el agente.
Tres lecturas. Una: el quinto parámetro de J2 no compra nada; J2 puede
colapsar en J1 y da 0.112. Dos: los dos ajustes llevan el contacto a
3,150 m sin que nadie se lo pida. Tres: F-4 queda mal en todos.
-->

---

<style scoped>pre { font-size: 15.5px; line-height: 1.32; } h2 { margin-bottom: 10px; }</style>

## De J1 al operador, en el deck

```diff
 SWOF
- 0.064510 0.000000 1.000000 100000
- 0.900894 0.714661 0.011223 0.462126
- 1.000000 1.000000 0.000000 0.298 /
+ 0.001000 0.000000 1.000000 1028.89
+ 0.788046 0.488995 0.045014 2.54222
+ 1.000000 1.000000 0.000000 2.05164 /
--- AJUSTE_SWL.INC
- -- Sin escalado de extremos: el agua irreducible es la de la tabla.
+ SWL   -- 1173 valores, de 0.020 a 0.765
--- AJUSTE_SOLUTION.INC
- 3150.000 330 3150.000 0 1* 1* 1* 1* 0 /
+ 3120.000 330 3120.000 0 1* 1* 1* 1* 0 /
```

<!--
5 min · acumulado 2:30
Es diff corridas/j1/fragmento.txt corridas/op/fragmento.txt, recortado.
Tres cambios y se leen: la tabla pasa a ir de 0 a 1 porque el agua
irreducible sale de SWL celda por celda; la J de entrada sube de 0.3 a 2;
el contacto sube 30 m.
Esto es lo que un ingeniero revisa antes de aceptar un caso.
-->

---

<!-- _class: cita -->

## Con **cuatro parámetros** alcanza, y el control lo confirma

<!--
5 min · acumulado 2:35
Qué eligió el agente para un modelo de campo y si la sala está de acuerdo.
J1 es el caso parsimonioso: menos parámetros, mejor control. Su punto
débil es que casi no tiene agua irreducible (0.02): toda el agua la
explica la altura. Un petrofísico puede preferir J2 por eso.
Antes de la pausa: pegar PEDIDO-3.md y dejar el loop corriendo.
Cierre del bloque 6. Pausa de 10 minutos.
-->

---

<!-- _class: seccion -->

## Loop con hipótesis a la vista

Bloque 7 de 9 · **30 min**

<!--
0 min · acumulado 2:45
Arranca 2:45, termina 3:15.
-->

---

<!-- _class: figura -->

## El flujo de autoresearch

![Diagrama del ciclo: una persona escribe program.md; el agente escribe una hipótesis, edita caso.py y hace commit; evaluar.py corre Flow y la métrica; el agente lee el resultado, decide si queda o se descarta, y todo se ve en bitacora.html](img/flujo-loop.svg)

Una persona escribe las reglas; el agente solo edita un archivo; la métrica y los datos no se tocan.

<!--
4 min · acumulado 2:49
Es una adaptación de autoresearch, de Andrej Karpathy, pensado para
entrenar redes: un archivo fijo con la métrica, un archivo que el agente
edita y un texto con las reglas.
Cada experimento es un commit. Si mejora y es simple, queda; si no, git
reset. Nada se pierde: la bitácora guarda también lo descartado.
-->

---

## Qué le cambiamos al original

| En autoresearch | Acá |
| --- | --- |
| Corre sin fin | 12 experimentos o 20 minutos |
| Cualquier cambio vale | Hasta 6 parámetros y FWL entre 3,100 y 3,220 m |
| Se anota qué se probó | La hipótesis y la predicción van **en el commit, antes de correr** |
| Una métrica | La de ajuste decide; la de control se anota y no decide |
| Un registro en texto | `bitacora.html`: cada experimento con su diff y su figura |

<!--
3 min · acumulado 2:52
Abrir program.md y leer el formato del commit: hipótesis, mecanismo y
predicción. Como el commit es anterior a la corrida, nadie puede escribir
la hipótesis mirando el resultado.
El criterio de simplicidad: una mejora que agrega parámetros se conserva
solo si baja el error 0.004 por parámetro.
-->

---

<!-- _class: panel -->

## Qué hizo mientras no mirábamos

`bitacora.html` · `results.tsv` · `informe.md`

Buscá una hipótesis que **no se cumplió** y qué aprendió de eso.

<!--
5 min · acumulado 2:57
Ventana E, bitacora.html. Arriba, el reproductor y la curva del error de
ajuste y la del control por experimento: marca llena, conservado; hueca,
descartado. Abajo, cada experimento con su hipótesis, el mecanismo, la
predicción, el resultado, la lectura, el diff del deck y la figura.
Si no terminó: Esc y pedirle el informe con lo que tenga. Plan B en
docente/plan-b/ensayo/.
-->

---

<!-- _class: figura -->

## El loop, cuadro a cuadro

![Animación del loop: en cada cuadro, la hipótesis del experimento, los perfiles de los seis pozos, la nube de J con la curva del caso y el error de ajuste y de control](img/loop.gif)

Un cuadro por experimento: la hipótesis arriba, los perfiles y la función J abajo, el error a la derecha.

<!--
3 min · acumulado 3:00
Es el ensayo del 5 de octubre de 2026: 12 experimentos en 9 minutos, 3
conservados. El GIF avanza solo cada 4 segundos; en bitacora.html está el
mismo reproductor con pausa y flechas.
Mirar tres cosas mientras corre: cómo se mueve la curva negra sobre la
nube de J, qué pozo cambia de un cuadro al otro, y que el error de
ajuste casi no baja después del segundo experimento.
-->

---

<!-- HIPOTESIS:INICIO -->

<style scoped>table { font-size: 19px; line-height: 1.3; width: 100%; } td { padding: 8px 14px 8px 0; } td:nth-child(2) { font-family: inherit; font-size: 19px; color: inherit; white-space: normal; } h2 { margin-bottom: 8px; max-width: none; }</style>

## Las hipótesis que surgieron (1 de 3)

| N.º | Hipótesis | Ajuste | Control | Parámetros | Veredicto |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | base | 0.142 | 0.205 | 4 | Queda |
| 2 | La curva J no tiene meseta de agua irreducible: Sw = a·J^-b (a = 0.68, b = 0.22), con el FWL del operador en 3,120 m | 0.112 | 0.176 | 3 | Queda |
| 3 | El nivel de agua libre está en 3,150 m, donde empieza el agua de 19 BT2, y no en los 3,120 m del operador (a = 0.83, b = 0.25) | 0.112 | 0.120 | 3 | Se descarta |
| 4 | El agua irreducible depende de la roca, como en el modelo del operador: Swirr = 0.156 − 0.038·log10(k), y sobre ella Swn = 0.48·J^-0.215 | 0.116 | 0.182 | 5 | Se descarta |

<!--
2 min · acumulado 3:02
Tabla del ensayo, tal como la escribió el agente: cada hipótesis es la
primera línea de un commit anterior a la corrida.
Leer dos o tres en voz alta: una que quedó, una que se descartó por
el criterio de simplicidad y una que empeoró.
-->

---

<style scoped>table { font-size: 19px; line-height: 1.3; width: 100%; } td { padding: 8px 14px 8px 0; } td:nth-child(2) { font-family: inherit; font-size: 19px; color: inherit; white-space: normal; } h2 { margin-bottom: 8px; max-width: none; }</style>

## Las hipótesis que surgieron (2 de 3)

| N.º | Hipótesis | Ajuste | Control | Parámetros | Veredicto |
| ---: | --- | ---: | ---: | ---: | --- |
| 5 | La curva no necesita coeficiente: Sw = J^-b con b = 0.284, que llega a Sw = 1 en J = 1, y el FWL en 3,150 m, el tope del agua de 19 BT2 | 0.112 | 0.121 | 2 | Queda |
| 6 | La saturación depende solo de la altura sobre el contacto: una curva de Pc en bar igual para toda la roca, sin JFUNC (Sw = (Pc/0.09)^-0.38) | 0.124 | 0.130 | 3 | Se descarta |
| 7 | Hay dos tipos de roca con curva J distinta: por debajo de 28 mD el exponente es 0.339 y por encima 0.275 (dos regiones SATNUM) | 0.110 | 0.118 | 4 | Se descarta |
| 8 | El agua irreducible es agua ligada a la arcilla: Swirr = 0.20·VSH por celda (SWL), y sobre ella Swn = J^-0.316 | 0.113 | 0.128 | 3 | Se descarta |

<!--
2 min · acumulado 3:04
Preguntar antes de mostrar el veredicto: ¿esta la conservarían?
-->

---

<style scoped>table { font-size: 19px; line-height: 1.3; width: 100%; } td { padding: 8px 14px 8px 0; } td:nth-child(2) { font-family: inherit; font-size: 19px; color: inherit; white-space: normal; } h2 { margin-bottom: 8px; max-width: none; }</style>

## Las hipótesis que surgieron (3 de 3)

| N.º | Hipótesis | Ajuste | Control | Parámetros | Veredicto |
| ---: | --- | ---: | ---: | ---: | --- |
| 9 | El nivel de agua libre es el del informe del operador, 3,120 m, con la misma curva Sw = J^-b (b = 0.30) | 0.115 | 0.177 | 2 | Se descarta |
| 10 | La permeabilidad pesa menos que en Leverett: Pc = J·σ·φ^0.5/k^0.41 en JFUNC, con Sw = J^-0.309 | 0.112 | 0.118 | 3 | Se descarta |
| 11 | La arena arcillosa (VSH mayor que 0.215) tiene su propia curva, con exponente 0.259 contra 0.303 de la arena limpia (dos regiones SATNUM) | 0.110 | 0.129 | 4 | Se descarta |
| 12 | La curva tiene un umbral de entrada real y forma de hipérbola de Thomeer: Sw = 1 hasta J = 2.1 y después 1 − exp(−0.48/log10(J/2.1)) | 0.113 | 0.125 | 3 | Se descarta |

<!--
2 min · acumulado 3:06
Preguntar antes de mostrar el veredicto: ¿esta la conservarían?
-->

<!-- HIPOTESIS:FIN -->

---

## Cómo leer esas hipótesis

- **De forma o de valor**: cambiar cómo depende Sw de la roca es una hipótesis; mover un número 5% es un barrido
- **Predicción cumplida o fallida**: una que falla enseña más que una que acierta por poco
- **Ajuste contra control**: si el ajuste baja y el control sube, el modelo está aprendiendo los pozos y no la roca
- **Defendible o indefendible**: un caso que baja el error con un contacto fuera del rango físico se descarta aunque gane

<!--
5 min · acumulado 3:11
Recorrer la tabla anterior con estas cuatro preguntas.
En la primera versión de esta clase, sin rango para el contacto, el loop
terminó con el contacto 148 m debajo del pozo y una J sin permeabilidad.
Bajaba el error y nadie la habría firmado. Las reglas de program.md
salen de ese ensayo.
-->

---

## El agente y el optimizador

| | Optimizador clásico | Agente en loop |
| --- | --- | --- |
| Corridas | 250 a 400 por caso | 12 |
| Qué cambia | Los números de una forma fija | La forma del modelo |
| Qué deja | Un mínimo | Hipótesis, predicciones y lecturas |
| Qué no hace | Proponer otra forma | Garantizar el mínimo de cada forma |

Se combinan: el agente propone la forma y un optimizador le ajusta los números.

<!--
4 min · acumulado 3:15
docente/optimizar.py: Nelder-Mead, cuatro a seis minutos por caso.
Cierre del bloque 7.
-->

---

<!-- _class: seccion -->

## El contacto de F-4

Bloque 8 de 9 · **15 min**

<!--
0 min · acumulado 3:15
Arranca 3:15, termina 3:30. Pegar PEDIDO-4.md al empezar.
-->

---

## Dos pozos que no cuentan lo mismo

- En **F-4** hay agua móvil desde unos 3,015 m: Sw 0.34 a 3,020 m en roca de 3,000 mD
- En **19 A**, a 960 m, hay petróleo con Sw 0.26 hasta 3,101 m
- Con un solo contacto, F-4 es el pozo peor ajustado en todos los casos: 0.147 a 0.151

Dos hipótesis, un parámetro más cada una: un **contacto inclinado**, o **agua colgada** en una cubeta de la base del Hugin.

<!--
2 min · acumulado 3:17
Mientras el agente corre el pedido 4.
Sw 0.34 en roca de tres darcys no se explica por calidad de roca: a esa
altura sobre el contacto regional debería estar en agua irreducible.
Agua colgada (perched water): agua que quedó atrapada en un bajo de la
base y el petróleo no pudo desplazar. Todo es una misma estructura, con
un contacto local por encima del regional.
-->

---

<!-- _class: figura -->

## Hipótesis 1: un contacto inclinado

![RMSE de ajuste, de F-4, de 19 A y del control contra la inclinación del nivel de agua libre](img/inclinacion.png)

Con 90 m por kilómetro el ajuste baja de 0.114 a 0.097. El control pasa de 0.142 a 0.193.

<!--
3 min · acumulado 3:20
Cada punto es un ajuste completo con esa inclinación fija.
La mejora está toda en F-4. El control no acompaña: el modelo pone agua
donde F-11 B, después de cinco años de inyección, todavía tiene petróleo.
Y sostener 90 m por kilómetro pide unos 3 bar por kilómetro de gradiente
en el acuífero: 0.090 por 345 sobre 1,065.
-->

---

<!-- _class: figura -->

## Hipótesis 2: agua colgada en una cubeta

![Mapa de la base del Hugin alrededor de F-4 con la cubeta contra la falla, y sección de oeste a este con el nivel de derrame, el nivel del modelo de campo y el del ajuste](img/cubeta.png)

La base del Hugin inclina hacia una falla justo donde la cruza F-4. Si la falla sella, queda una cubeta.

<!--
4 min · acumulado 3:24
La cuenta: se llena la base mapeada como un terreno y se ve hasta qué
nivel se sostiene el agua antes de derramar. Los escalones de más de 39
grados se toman como falla sellante.
Da una cubeta de 0.07 km² bajo F-4, con derrame en 3,016 m. Con 45 grados,
3,024 m. Con 56 grados no cierra. En los otros cuatro pozos no hay cubeta
con ninguno de los tres.
El modelo de campo de Equinor tiene una región de equilibrio propia,
rotulada "purged water", con contacto en 3,025 m.
-->

---

<!-- _class: figura -->

## El perfil pide el nivel local en 3,033 m

![RMSE de ajuste, de F-4 y del control contra el nivel de agua libre local bajo F-4](img/agua-colgada.png)

Con un nivel local en F-4 el ajuste baja de 0.112 a 0.090 y F-4 de 0.147 a 0.090. El control queda en 0.131.

<!--
3 min · acumulado 3:27
Caso P: la misma función J, el contacto regional en 3,146 m y una segunda
región de equilibrio para F-4. Un parámetro más.
El mínimo es agudo y cae en la base del Hugin de F-4. Queda 9 a 17 m por
debajo del derrame de la cubeta y 8 m por debajo del modelo de campo:
tres estimaciones independientes dentro de 17 m.
El control no se rompe: el nivel local no toca a F-11 B.
-->

---

## ¿Vale la pena?

| Hipótesis | Ajuste | F-4 | Control | Qué pide |
| --- | ---: | ---: | ---: | --- |
| Un contacto | 0.112 | 0.147 | 0.122 | Nada |
| Contacto inclinado | 0.097 | 0.108 | 0.193 | 3 bar por kilómetro en el acuífero |
| Agua colgada en F-4 | 0.090 | 0.090 | 0.131 | Una falla que selle y una base que no drene |

El agua colgada mejora más, no rompe el control y coincide con la estructura y con el modelo de campo.

<!--
3 min · acumulado 3:30
Lo que queda abierto. Un solo pozo no distingue una cubeta dentro de la
misma estructura de un bloque separado con su propio contacto: en los dos
casos F-4 tiene un nivel local. Lo decide la presión del petróleo: en una
cubeta es la misma que en el resto del campo; en otro bloque, no. El
punto de F-4 del bloque 3, 6.7 bar sobre la línea de 19 A, apunta a otro
bloque, pero las dos presiones son de fechas y referencias distintas.
Y la cubeta depende de qué pendiente se toma como falla sellante.
Cierre del bloque 8.
-->

---

<!-- _class: seccion -->

## Controles y cierre

Bloque 9 de 9 · **15 min**

<!--
0 min · acumulado 3:30
Arranca 3:30, termina 3:45.
-->

---

## Antes de firmar un caso armado por un agente

1. El caso vive en su carpeta, con el caso base al lado
2. Un **diff** contra el caso base, leído
3. La lista de supuestos y de valores por defecto del simulador
4. La versión del simulador y los datos, fijados
5. Un pozo de control que el caso **nunca vio**
6. Un ingeniero firma

<!--
6 min · acumulado 3:36
Cada control tuvo su ejemplo hoy: la carpeta de trabajo, el diff de los
AJUSTE_*.INC, la lista de supuestos del primer pedido, los hashes, F-11 B.
-->

---

## Qué no se puede afirmar con esto

- Dónde está el contacto: los datos lo dejan entre 3,100 y 3,220 m, y el ajuste lo pone en 3,150 m
- Que el agua de F-4 sea una cubeta y no otro bloque: un solo pozo no los distingue, y faltan presiones
- Que el control valide la saturación inicial: solo dice que el modelo no pone más agua que la de 2013
- Que estos parámetros sirvan para un modelo de campo: son 5 pozos, sin facies ni geomodelo

<!--
4 min · acumulado 3:40
El ejercicio muestra el método de trabajo con el agente. El resultado de
reservorios queda abierto, y está bien decirlo así.
-->

---

<!-- _class: acentos -->

## Para llevarse

- **Mirar los datos antes de ajustar**: qué pozo es de cuándo cambió todo el planteo
- **Pocas formas, pocos parámetros** y un pozo que el ajuste no ve
- **Una hipótesis escrita antes de correr** vuelve revisable lo que prueba un agente

<!--
5 min · acumulado 3:45
Cómo repetirlo: el repo, instalar.sh, verificar.sh y preparar.sh.
Preguntas.
-->
