---
marp: true
theme: podeley
paginate: true
header: 'Simulación numérica con agentes · **OPM Flow sobre Volve**'
footer: 'clase-opm-agentes'
---

<!-- _class: portada -->

# Un agente maneja el simulador

Clase de 3 h 45 min · ingeniería de reservorios · **OPM Flow · Claude Code · Volve**

<!--
0:00 · portada mientras entra la gente
Ventanas: A este deck; B terminal en el repo; C terminal en ~/sw-volve con
el agente SIN lanzar, letra grande y tema claro; D visor de imágenes sobre
~/sw-volve/corridas; E editor para SW.DATA; F fuera de pantalla, el guion y
docente/plan-b/tabla.md.
El minuto a minuto completo está en docente/guion.md.
-->

---

<!-- _class: agenda -->

## Hoy

| Bloque | Tiempo | Qué hacemos |
| --- | --- | --- |
| El campo y el problema | 20 min | Volve en mapa y sección, qué datos hay, y con qué número se mide el ajuste |
| Instalación | 25 min | OPM Flow en un contenedor, el entorno de Python y Claude Code |
| El agente lee el deck | 35 min | Explica el modelo keyword por keyword, corre el caso base y lee el resultado |
| Pausa | 10 min | |
| Alternativas de ajuste | 45 min | Función J, tipos de roca, escalado de extremos y SWATINIT, en una tabla |
| El contacto | 30 min | Plano, dos sistemas o inclinado, con el segundo pozo a la vista |
| Pausa | 10 min | El loop queda corriendo |
| Loop autónomo | 30 min | El agente prueba variantes solo; leemos qué conservó y qué descartó |
| Controles y cierre | 20 min | Qué revisa y firma el ingeniero, y los límites de lo que vimos |

<!--
2 min · acumulado 0:02
Todo corre en mi máquina. Ustedes se llevan el repo para repetirlo.
La clase sirve si al final pueden decir qué le pedirían a un agente y qué
le revisarían.
-->

---

<!-- _class: seccion -->

## El campo y el problema

Bloque 1 de 7 · **20 min**

<!--
0 min · acumulado 0:02
Arranca 0:00, termina 0:20.
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
archivo de producción del operador.
Equinor liberó el conjunto en 2018.
-->

---

<!-- _class: figura -->

## Dónde están los pozos

![Mapa del tope de la Formación Hugin con la entrada de 18 pozos al reservorio y las trayectorias de F-12 y F-11 B](img/mapa-hugin.png)

En naranja, los dos pozos del ejercicio y su trayectoria dentro del intervalo perfilado.

<!--
3 min · acumulado 0:07
Un alto estructural de unos 1.5 por 2.5 km, con el tope cerca de 2,800 m en la
cresta. F-12 entra cerca de la cresta y se desplaza 300 m hacia el este. F-11 B
entra 500 m al nordeste y recorre 1,200 m hacia el flanco este.
Los puntos negros son las entradas al Hugin de los otros 16 pozos con tope.
-->

---

<!-- _class: figura -->

## Los dos pozos, en sección

![Sección a lo largo de F-12 y F-11 B: trayectoria coloreada por saturación de agua, con el tope del Hugin del mapa](img/secciones.png)

Claro es petróleo, oscuro es agua. F-11 B tiene un tramo horizontal y vuelve a entrar al Hugin a través de fallas.

<!--
3 min · acumulado 0:10
F-12 atraviesa el Hugin en 90 m verticales y sigue en Sleipner y Skagerrak.
F-11 B corre pegado al tope: baja de 2,829 a 3,182 m en 1,200 m de
desplazamiento. Mirar los colores: hay tramos claros por debajo de 3,100 m.
La línea punteada es el tope según el mapa, con su incertidumbre.
-->

---

<!-- _class: figura -->

## Cuándo se perfiló cada pozo

![Producción mensual de petróleo y agua e inyección de agua del campo, de 2008 a 2016](img/produccion.png)

F-12 se perfiló en 2007, antes del primer petróleo. Cuando se perfiló F-11 B el campo ya producía más agua que petróleo.

<!--
2 min · acumulado 0:12
En total: 10.0 millones de Sm³ de petróleo, 15.3 de agua producida y 30.3
de agua inyectada. Esto vuelve en el bloque 5: el perfil de F-11 B no es un
estado inicial.
-->

---

## Qué trae el conjunto y qué usamos

| El conjunto completo | Lo que usa la clase |
| --- | --- |
| Unos 40,000 archivos, cerca de 5 TB | 7 archivos, 13 MB |
| Sísmica 3D y 4D | |
| Modelos estático y dinámico | |
| Perfiles de pozo, crudos e interpretados | Perfil interpretado de 2 pozos |
| Trayectorias, topes y mapas | 2 trayectorias, los topes, el tope del Hugin |
| Producción diaria y mensual | La mensual, para el contexto |
| Perforación en tiempo real, informes | |

<!--
2 min · acumulado 0:14
El conjunto oficial trae el modelo de simulación de Equinor. No lo usamos:
armamos uno propio desde los perfiles, que corre en un segundo y deja
ajustar en vivo.
-->

---

<!-- _class: figura -->

## ¿Dónde pondrías el contacto?

![Perfil interpretado de 15/9-F-12: saturación de agua, porosidad y permeabilidad contra profundidad](img/perfil-f12.png)

Profundidad en metros verticales bajo el nivel del mar (TVDSS, true vertical depth subsea).

<!--
3 min · acumulado 0:17
Preguntar a la sala y anotar dos o tres respuestas: vuelven en el bloque 5.
Lo que se ve: Sw baja en el Hugin, con picos en las capas de mala calidad;
Sw alta desde la base del Hugin, cerca de 2,910 m, en Sleipner y Skagerrak.
-->

---

## Qué significa reproducirlo

- El simulador arranca en equilibrio: **`EQUIL`** más una curva de presión capilar dan la Sw de cada celda
- Comparamos esa Sw con la del perfil, celda por celda
- El número es la raíz del error cuadrático medio (**RMSE**, root mean square error)

Es el trabajo de un programa de saturación-altura, hecho con el equilibrio del propio simulador.

<!--
2 min · acumulado 0:19
La ventaja de hacerlo en el simulador: lo que se ajusta acá es exactamente
lo que después inicializa el modelo de campo. No hay traducción entre dos
programas.
-->

---

<!-- _class: cita -->

## Lo que este conjunto **no nos da** para el ajuste: presiones y laboratorio

<!--
1 min · acumulado 0:20
En los archivos que usamos no hay presiones de formación, presión capilar
de laboratorio ni informe de fluidos (PVT: presión, volumen y temperatura).
Todo lo de hoy se ajusta contra perfiles y nada más.
Cierre del bloque 1.
-->

---

<!-- _class: seccion -->

## Instalación

Bloque 2 de 7 · **25 min**

<!--
0 min · acumulado 0:20
Arranca 0:20, termina 0:45.
-->

---

## Cuatro piezas

- **Podman o Docker**: correr OPM Flow sin compilarlo
- **uv**: el entorno de Python, siempre igual
- **git**: el historial de experimentos
- **Claude Code**: el agente

OPM Flow es un simulador de petróleo negro de código abierto. Lee el mismo formato de deck que los comerciales.

<!--
5 min · acumulado 0:25
OPM: Open Porous Media. Lo mantienen Equinor, SINTEF y NORCE entre otros.
Para quien usa Eclipse: las keywords son las mismas, con algunas sin soporte.
-->

---

<!-- _class: panel -->

## Dos comandos

`instalacion/instalar.sh`

`instalacion/verificar.sh`

La imagen del simulador y los datos quedan **fijados por su hash**.

<!--
12 min · acumulado 0:37
Ventana B. instalar.sh: leer las tres etapas en voz alta. La imagen ya está
bajada; decir que la primera vez pesa 1.2 GB.
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
8 min · acumulado 0:45
Ventana B: ejercicio/preparar.sh, y después abrir settings.json. Leer la
lista de permisos y la de prohibiciones.
La idea para llevarse: lo que el agente no debe hacer se escribe como
permiso, y lo que debe saber se escribe en CLAUDE.md.
Cierre del bloque 2.
-->

---

<!-- _class: seccion -->

## El agente lee el deck

Bloque 3 de 7 · **35 min**

<!--
0 min · acumulado 0:45
Arranca 0:45, termina 1:20.
-->

---

<!-- _class: panel -->

## Primer pedido

`claude`, y adentro el texto de `PEDIDO-1.md`

Correr el caso base, **explicar el deck**, leer la figura y listar los supuestos. Sin cambiar nada.

<!--
10 min · acumulado 0:55
Ventana C. Aceptar el diálogo de confianza leyéndolo en voz alta.
Narrar qué herramienta llama en cada vuelta: lee archivos, corre
evaluar.py, abre SW.DATA, mira perfil.png.
-->

---

## El modelo: una fila de celdas

- Una celda por metro de pozo, cada una con **su profundidad y su roca**
- `DIMENS` con una sola fila; `TOPS` distinto en cada celda
- `MULTX` en cero: no hay flujo, cada celda se equilibra sola
- `SWOF` da la curva; `EQUIL` da el nivel de agua libre (**FWL**, free water level)

El mismo armado sirve para el pozo desviado y para el horizontal.

<!--
10 min · acumulado 1:05
Ventana E con SW.DATA al lado de la explicación del agente. Si no nombró
alguna de estas keywords, preguntársela en vivo.
Aclarar que es el cálculo de inicialización de un modelo, aislado: acá
nada fluye.
-->

---

<!-- _class: figura -->

## Caso base: una curva y un contacto

![Caso A: saturación del perfil y simulada en F-12 y en F-11 B](img/caso-a.png)

Curva única ajustada: RMSE 0.163 en F-12, y 0.497 en el pozo que el caso no vio.

<!--
8 min · acumulado 1:13
La figura es la del caso A ya ajustado; el caso base sin ajustar da 0.177.
Dentro del Hugin 0.124, debajo 0.185. Una sola curva no puede seguir los
picos de Sw de las capas de mala calidad.
En F-11 B el modelo pone agua donde el perfil muestra petróleo: vuelve en
el bloque 5.
-->

---

<!-- _class: cita -->

## El agente todavía **no cambió nada**: leyó, corrió y explicó

<!--
7 min · acumulado 1:20
Antes de la frase, los supuestos que listó el agente. Tienen que salir las
densidades de los fluidos y el contacto. Pregunta a la sala: ¿qué otro
supuesto ven ustedes?
Cierre del bloque 3. Pausa de 10 minutos.
-->

---

<!-- _class: seccion -->

## Alternativas de ajuste

Bloque 4 de 7 · **45 min**

<!--
0 min · acumulado 1:30
Arranca 1:30, termina 2:15. Pegar PEDIDO-2.md apenas vuelven: el agente
necesita entre 10 y 15 minutos.
-->

---

<!-- _class: acentos -->

## Cuatro formas de decir dónde está el agua

- **Función J de Leverett** (`JFUNC`): una curva adimensional, escalada en cada celda por √(k/φ)
- **Tipos de roca** (`SATNUM`): tres clases de calidad, una curva para cada una
- **Escalado de extremos** (`ENDSCALE`, `SWL`): una forma de curva, agua connata por celda
- **`SWATINIT`**: el perfil impuesto celda a celda; el simulador reescala la presión capilar

<!--
18 min · acumulado 1:48
Mientras el agente trabaja. Una vuelta por cada alternativa con la keyword
que usa. Pedir a la sala que apueste cuál va a ajustar mejor y cuál
llevarían a un modelo de campo.
-->

---

## Lo que dio

| Caso | RMSE en F-12 | En el Hugin | RMSE en F-11 B | Parámetros |
| --- | ---: | ---: | ---: | ---: |
| A: curva única | 0.163 | 0.124 | 0.497 | 4 |
| B: función J | 0.159 | 0.110 | 0.484 | 4 |
| C: tres tipos de roca | 0.163 | 0.130 | 0.473 | 12 |
| D: agua connata por celda | 0.158 | 0.106 | 0.490 | 5 |
| E: SWATINIT | 0.000 | 0.000 | 0.486 | 383 |

<!--
7 min · acumulado 1:55
Esta es la tabla de referencia, ajustada con un optimizador clásico.
Compararla con comparacion.md, la que acaba de escribir el agente: los
números van a diferir en el tercer decimal.
-->

---

<!-- _class: figura -->

## La función J sigue las capas

![Caso B: función J de Leverett, saturación del perfil y simulada](img/caso-b.png)

Con los mismos cuatro parámetros, el error dentro del Hugin baja de 0.124 a 0.110.

<!--
6 min · acumulado 2:01
Comparar con la figura del caso A: ahora el simulado tiene los picos.
De A a D la diferencia total está en el tercer decimal: debajo del Hugin
nadie mejora.
Tres tipos de roca con 12 parámetros no superan a la función J con 4.
-->

---

<!-- _class: figura -->

## SWATINIT: cero en el pozo, nada fuera de él

![Caso E: SWATINIT con el perfil celda a celda](img/caso-e.png)

383 parámetros. En F-11 B, donde no hay perfil que imponer, el error es 0.486.

<!--
6 min · acumulado 2:07
Dos cosas. Una: no predice. Dos: Flow ignora SWATINIT debajo del nivel de
agua libre y pone Sw = 1, así que para honrar el perfil hubo que bajar el
contacto a 3,200 m. El contacto dejó de ser un dato del modelo.
-->

---

<!-- _class: cita -->

## Con cuatro parámetros ya se llega **al piso del perfil**

<!--
8 min · acumulado 2:15
Qué eligió el agente para un modelo de campo, y si la sala está de acuerdo.
El piso: la variabilidad metro a metro del perfil que ninguna función de
la calidad de roca explica.
Cierre del bloque 4.
-->

---

<!-- _class: seccion -->

## El contacto

Bloque 5 de 7 · **30 min**

<!--
0 min · acumulado 2:15
Arranca 2:15, termina 2:45. Pegar PEDIDO-3.md al empezar.
-->

---

## Dos pozos que no cuentan lo mismo

- En **F-12** hay agua desde la base del Hugin, cerca de 2,910 m
- En **F-11 B** hay petróleo por debajo de 3,100 m

Tres explicaciones, cada una un caso ajustado con los dos pozos a la vista:

1. F0: un contacto plano
2. F1: dos sistemas, el Hugin por un lado y Sleipner con Skagerrak debajo (`EQLNUM`)
3. F2: un contacto inclinado, en escalones de regiones de equilibrio

<!--
12 min · acumulado 2:27
Volver a las respuestas del bloque 1 sobre el contacto.
Mientras el agente corre: la trayectoria de F-11 B entra al Hugin a 2,829 m
y sigue hasta 3,182 m.
-->

---

<!-- _class: figura -->

## Dos sistemas

![Caso F1: un contacto para el Hugin y otro para Sleipner y Skagerrak](img/caso-f1.png)

Contactos en 3,156 m para el Hugin y 2,937 m para lo que está debajo. RMSE 0.220 y 0.230.

<!--
3 min · acumulado 2:30
Mirar F-12: con una sola función J para los dos pozos, el Hugin de F-12
empeora respecto del caso B. La curva no se traslada de un pozo al otro.
-->

---

<!-- _class: figura -->

## Un contacto inclinado

![Caso F2: contacto inclinado desde F-12 hacia F-11 B](img/caso-f2.png)

105 m por kilómetro. RMSE 0.261 y 0.232: en F-11 B, casi lo mismo que dos sistemas.

<!--
3 min · acumulado 2:33
El contacto plano único (F0) da 0.234 y 0.332.
Los perfiles no separan F1 de F2.
-->

---

## Lo que los perfiles no deciden

- **105 m por kilómetro** pide unos 3 bar por kilómetro de gradiente en el acuífero
- F-11 B se perfiló en 2013: parte de su agua puede ser de barrido
- Una sola función J no ajusta bien los dos pozos a la vez

El dato que lo decide son las **presiones de formación** en los dos pozos, y no están.

<!--
10 min · acumulado 2:43
Preguntar si alguien vio una inclinación así en un campo de este tamaño.
La cuenta: la inclinación por la diferencia de densidades sobre la densidad
del agua da el gradiente de carga hidráulica; 0.105 por 290 sobre 1,040 es
0.029, unos 3 bar por kilómetro.
El agente ajusta las tres hipótesis igual de bien. Elegir entre ellas es
trabajo de ingeniería.
-->

---

<!-- _class: panel -->

## Antes de la pausa

El texto de `PEDIDO-4.md`

El agente sigue **solo**: 15 experimentos o 20 minutos.

<!--
2 min · acumulado 2:45
Ventana C. Pegar el pedido y dejarlo corriendo. Pausa de 10 minutos.
Cierre del bloque 5.
-->

---

<!-- _class: seccion -->

## Loop autónomo

Bloque 6 de 7 · **30 min**

<!--
0 min · acumulado 2:55
Arranca 2:55, termina 3:25.
-->

---

## Tres piezas

- **Un archivo fijo**: `evaluar.py` y la métrica. El agente no los toca
- **Un archivo editable**: `caso.py`
- **Las reglas, escritas por una persona**: `program.md`

Cada experimento es un commit. Si mejora, queda; si no, se deshace. Todo se anota en `results.tsv`.

<!--
5 min · acumulado 3:00
Es una adaptación de autoresearch, de Andrej Karpathy, pensado para
entrenar redes. Lo que cambia acá: un tope de experimentos, un máximo de
8 parámetros, SWATINIT prohibido y el pozo de validación oculto.
Abrir program.md y leer el criterio de simplicidad.
-->

---

<!-- _class: panel -->

## Qué hizo mientras no mirábamos

`results.tsv` · `git log --oneline` · `informe.md`

Buscá una idea que **descartó** y por qué.

<!--
13 min · acumulado 3:13
Ventana C. results.tsv fila por fila; git log muestra solo lo conservado.
Leer informe.md completo: caso final, intervalos mal ajustados, qué
revisaría un ingeniero.
Si no terminó: Esc y pedirle el informe con lo que tenga. Plan B en
docente/plan-b/ensayo/.
-->

---

## El agente y el optimizador

| | Optimizador clásico | Agente en loop |
| --- | --- | --- |
| Corridas | Unas 250 | 15 |
| Qué cambia | Cuatro números de una forma fija | La forma del modelo |
| Qué deja | Un mínimo | Un historial con hipótesis |

Son herramientas para preguntas distintas, y se combinan.

<!--
12 min · acumulado 3:25
docente/optimizar.py: Nelder-Mead, cerca de cuatro minutos por caso.
Lo que el loop no ve: rmse_validacion se anota y no decide. Mirar si el
caso final mejoró o empeoró en F-11 B.
Cierre del bloque 6.
-->

---

<!-- _class: seccion -->

## Controles y cierre

Bloque 7 de 7 · **20 min**

<!--
0 min · acumulado 3:25
Arranca 3:25, termina 3:45.
-->

---

## Antes de firmar un caso armado por un agente

1. El caso vive en su carpeta, con el caso base al lado
2. Un **diff** contra el caso base, leído
3. La lista de supuestos y de valores por defecto del simulador
4. La versión del simulador, fijada
5. La misma descripción, armada dos veces, da el mismo resultado
6. Un ingeniero **firma**

<!--
8 min · acumulado 3:33
Cada control tuvo su ejemplo hoy: la carpeta de trabajo, git, la lista de
supuestos del primer pedido, el hash de la imagen, la tabla del agente
contra la de referencia.
-->

---

## Qué no se puede afirmar con esto

- Dónde está el contacto de Volve: no hay presiones, y las densidades son un supuesto
- Que F-11 B valide la saturación inicial: es un perfil de 2013
- Que el contacto esté inclinado: dos compartimentos ajustan igual
- Que estos parámetros sirvan para un modelo de campo: son 2 pozos de 22

<!--
5 min · acumulado 3:38
El ejercicio muestra el método de trabajo con el agente. El resultado de
reservorios queda abierto, y está bien decirlo así.
-->

---

<!-- _class: acentos -->

## Para llevarse

- Lo que el agente debe saber va en **`CLAUDE.md`**; lo que no debe hacer, en los permisos
- Una **métrica fija** y un solo archivo editable hacen comparable todo lo que pruebe
- El agente ajusta varias hipótesis igual de bien: **elegir entre ellas** sigue siendo tu trabajo

<!--
7 min · acumulado 3:45
Cómo repetirlo: el repo, instalar.sh, verificar.sh y preparar.sh.
Preguntas.
-->
