# Guion del docente

Clase de 3 h 45 min en formato demostración: todo corre en tu máquina y se proyecta. La sala son
ingenieros de reservorios. Conocen presión capilar, función J y contactos; lo nuevo para ellos es
OPM Flow y el trabajo con un agente.

## El día anterior

1. `instalacion/verificar.sh` termina con `todo en orden`.
2. `uv run docente/tabla.py` regenera `docente/plan-b/`: los ocho casos de referencia con su deck,
   su figura y `tabla.md`. Es el plan B de los bloques 3 a 5.
3. Ensayo cronometrado de los cuatro pedidos en una carpeta de prueba:
   `ejercicio/preparar.sh ~/sw-volve-ensayo`, y adentro `claude` con cada `PEDIDO-N.md`. Guardá
   `comparacion.md`, `results.tsv` e `informe.md` del ensayo en `docente/plan-b/ensayo/`. Es el
   plan B de los bloques 4 a 6.
4. `ejercicio/preparar.sh ~/sw-volve` deja lista la carpeta de la clase, con el agente sin lanzar.
5. Para mostrar la instalación en limpio en el bloque 2 sin esperar la descarga, la imagen queda
   bajada y se muestra el comando con su salida ya en caché.

## Ventanas

| Ventana | Qué tiene |
| --- | --- |
| A | Las diapositivas (`slides/clase.html`) |
| B | Terminal en el repo, para la instalación y `verificar.sh` |
| C | Terminal en `~/sw-volve`, letra grande, tema claro: acá vive el agente |
| D | Visor de imágenes sobre `~/sw-volve/corridas/`, para las figuras |
| E | Editor con `corridas/ultima/SW.DATA` |
| F | Fuera de pantalla: `docente/plan-b/tabla.md` y este guion |

## Minuto a minuto

### Bloque 1 · El campo y el problema (0:00 a 0:20)

- 0:00. Qué van a ver: un agente que maneja un simulador, sobre un problema que ellos conocen.
  La clase sirve si al final pueden decir qué le pedirían y qué le revisarían.
- 0:02. Volve en un minuto: mar del Norte, 80 m de agua, Formación Hugin entre 2,700 y 3,100 m,
  producido de 2008 a 2016 con inyección de agua, datos liberados en 2018.
- 0:04. El mapa del tope del Hugin: un alto de unos 1.5 por 2.5 km con 18 pozos. F-12 entra cerca de
  la cresta; F-11 B entra 500 m al nordeste y recorre 1,200 m hacia el flanco este.
- 0:07. La sección: las dos trayectorias coloreadas por Sw. F-11 B tiene un tramo horizontal y
  tramos claros (petróleo) por debajo de 3,100 m.
- 0:10. La producción: F-12 se perfiló en 2007, antes del primer petróleo; F-11 B en 2013, con
  el campo produciendo más agua que petróleo.
- 0:12. Qué trae el conjunto completo (unos 40,000 archivos, cerca de 5 TB, con sísmica y el
  modelo de simulación de Equinor) y qué usamos (7 archivos).
- 0:14. La figura del perfil de F-12 sin simulación. Preguntar a la sala: ¿dónde pondrían el
  contacto? Anotar dos o tres respuestas para el bloque 5.
- 0:17. Qué significa reproducirlo: el simulador inicializa con `EQUIL` y una curva de presión
  capilar; se compara celda por celda con el perfil. El número es `rmse_ajuste`.
- 0:19. Lo que no hay en lo que usamos: presiones y laboratorio. Queda dicho desde el principio.

### Bloque 2 · Instalación (0:20 a 0:45)

- 0:20. Las cuatro piezas: contenedor, `uv`, git, Claude Code. Mostrar la tabla del README.
- 0:25. Ventana B: `instalacion/instalar.sh`. Leer en voz alta las tres etapas. Señalar el hash
  de la imagen: la versión del simulador queda fijada.
- 0:32. `instalacion/verificar.sh`. SPE1 corre en cerca de un segundo. Para quien usa un
  simulador comercial: es el mismo formato de deck.
- 0:37. `uv run evaluar.py` a mano, sin agente. Mostrar el bloque de números y abrir la figura.
- 0:41. `ejercicio/preparar.sh` y qué hay en la carpeta: `CLAUDE.md`, los pedidos y
  `.claude/settings.json`. Leer la lista de permisos y la de prohibiciones.

### Bloque 3 · El agente lee el deck (0:45 a 1:20)

- 0:45. Ventana C: `claude`, y pegar `PEDIDO-1.md`. Aceptar el diálogo de confianza leyéndolo.
- 0:47. Mientras trabaja, narrar qué herramienta llama: lee archivos, corre `evaluar.py`, abre el
  deck, mira la figura.
- 0:55. La explicación del deck. Conviene que aparezcan: `DIMENS` con una sola fila de celdas,
  `TOPS` por celda, `MULTX` en cero, `SWOF`, `EQUIL`. Si no nombra alguna, preguntársela.
- 1:05. La lectura de la figura. Valores de referencia del caso base: `rmse_ajuste` 0.177, 0.128
  dentro del Hugin y 0.204 debajo. El nivel de agua libre está en 2,920 m.
- 1:13. Los supuestos. Tienen que salir las densidades de los fluidos y el contacto. Pregunta
  para la sala: ¿qué otro supuesto ven ustedes?
- 1:17. Cierre: el agente todavía no cambió nada. Leyó, corrió y explicó.

Plan B: `docente/plan-b/a/` tiene el deck y la figura.

### Pausa (1:20 a 1:30)

### Bloque 4 · Alternativas de ajuste (1:30 a 2:15)

- 1:30. Pegar `PEDIDO-2.md`. Son cuatro alternativas y hasta seis corridas cada una: entre 10 y
  15 minutos de trabajo del agente.
- 1:32. Mientras corre, una diapositiva por alternativa, con la keyword que usa. Pedir a la sala
  que apueste cuál va a ajustar mejor.
- 1:50. `comparacion.md`. Compararla con `docente/plan-b/tabla.md`:

  | Caso | RMSE en F-12 | En el Hugin | RMSE en F-11 B | Parámetros |
  | --- | ---: | ---: | ---: | ---: |
  | A: curva única | 0.163 | 0.124 | 0.497 | 4 |
  | B: función J | 0.159 | 0.110 | 0.484 | 4 |
  | C: tres tipos de roca | 0.163 | 0.130 | 0.473 | 12 |
  | D: agua connata por celda | 0.158 | 0.106 | 0.490 | 5 |
  | E: SWATINIT | 0.000 | 0.000 | 0.486 | 383 |

- 1:57. Tres puntos para discutir, con la figura de cada caso en la ventana D:
  - De A a D la diferencia está en el tercer decimal. La función J gana dentro del Hugin (de 0.124
    a 0.110) porque sigue las capas de mala calidad; debajo del Hugin nadie mejora.
  - Tres tipos de roca con 12 parámetros no superan a la función J con 4.
  - SWATINIT da cero en F-12 y 0.486 en F-11 B: no predice fuera del pozo. Además Flow lo ignora
    debajo del nivel de agua libre, y por eso el caso de referencia baja el contacto a 3,200 m.
- 2:10. Qué eligió el agente para un modelo de campo y si la sala está de acuerdo.

Si el agente se demora, cortarlo en la alternativa que esté y mostrar el resto desde el plan B.

### Bloque 5 · El contacto (2:15 a 2:45)

- 2:15. Volver a las respuestas del bloque 1 sobre el contacto. Pegar `PEDIDO-3.md`.
- 2:17. Mientras corre: la trayectoria de F-11 B. Entra al Hugin a 2,829 m y sigue hasta 3,182 m,
  con petróleo por debajo de 3,100 m. En F-12 hay agua desde 2,910 m.
- 2:27. Los tres casos de referencia:

  | Caso | RMSE en F-12 | RMSE en F-11 B | Contactos |
  | --- | ---: | ---: | --- |
  | F0: un contacto plano | 0.234 | 0.332 | 2,986 m |
  | F1: un contacto por sistema | 0.220 | 0.230 | Hugin 3,156 m; debajo 2,937 m |
  | F2: contacto inclinado | 0.261 | 0.232 | 2,994 m en F-12, 105 m por kilómetro |

- 2:33. La discusión que importa:
  - F1 y F2 ajustan casi igual. Los perfiles no separan las dos explicaciones.
  - 105 m por kilómetro pide unos 3 bar por kilómetro de gradiente en el acuífero. Preguntar si
    alguien vio algo así en un campo de este tamaño.
  - F-11 B es de 2013. Parte de su agua puede ser de barrido. Un ajuste de saturación inicial
    contra ese perfil mezcla dos cosas.
  - Al ajustar los dos pozos con una sola función J, F-12 empeora (de 0.159 a 0.220). La curva no
    se traslada de un pozo al otro.
- 2:41. Qué dato lo decidiría: presiones de formación en los dos pozos.
- 2:43. Pegar `PEDIDO-4.md` y dejar el loop corriendo durante la pausa.

### Pausa (2:45 a 2:55)

### Bloque 6 · Loop autónomo (2:55 a 3:25)

- 2:55. Qué está haciendo: mostrar `program.md`. Tres piezas: un archivo fijo con la métrica, un
  archivo que el agente edita, y las reglas que escribió una persona.
- 3:00. `results.tsv` en vivo y `git log --oneline`. Cada fila es un commit; lo descartado no
  queda en la rama.
- 3:05. El loop llega a su tope. Leer `informe.md` completo.
- 3:13. Comparar con el optimizador clásico: `docente/optimizar.py` usa unas 250 corridas y cerca
  de cuatro minutos para ajustar cuatro parámetros de una forma fija. El agente usa 15 corridas y
  cambia la forma del modelo. Son herramientas para preguntas distintas.
- 3:19. Lo que el loop no ve: `rmse_validacion` se anota y no decide. Mirar si el caso final
  mejoró o empeoró en F-11 B.

Referencia del ensayo del 5 de octubre de 2026 (`docente/plan-b/ensayo/`): 15 experimentos en 17
minutos, 7 conservados y 8 descartados. `rmse_ajuste` bajó de 0.177 a 0.109 con 4 parámetros, y
`rmse_validacion` de 0.491 a 0.327. Solo cambió `caso.py`. Tres cosas de ese informe sirven para
la discusión:

- El salto grande (de 0.159 a 0.117) vino de separar el Hugin de lo que está debajo y bajar el
  contacto, un cambio de forma que el optimizador clásico no puede hacer.
- El caso final dejó de usar la permeabilidad y puso el contacto en 3,192 m, 148 m debajo de la
  última muestra de F-12. El agente lo declara como hipótesis de ajuste.
- El agente avisó que la figura muestra el panel de F-11 B, así que la validación no fue ciega a
  la vista aunque el número no decidió nada.

Plan B: `docente/plan-b/ensayo/`.

### Bloque 7 · Controles y cierre (3:25 a 3:45)

- 3:25. Qué revisa el ingeniero antes de firmar un caso armado por un agente:
  1. El caso vive en su propia carpeta, con el caso base al lado.
  2. Un diff contra el caso base, leído.
  3. La lista de supuestos y de valores por defecto del simulador.
  4. La versión del simulador fijada.
  5. La misma descripción, armada dos veces, da el mismo resultado.
  6. Un ingeniero firma.
- 3:33. Los límites de lo que se vio: la sección "Qué no se puede afirmar con esto" del README.
- 3:38. Cómo repetirlo: el repo, los dos scripts de instalación y `preparar.sh`.
- 3:41. Preguntas.

## Si algo falla

| Qué | Qué hacer |
| --- | --- |
| El contenedor no arranca | `FLOW=/ruta/a/flow` si hay un Flow nativo; si no, seguir con las figuras de `docente/plan-b/` |
| El agente edita algo que no debe | Lo frena el permiso. Mostrarlo: es parte de la clase |
| Flow rechaza un deck | El agente lee el final de `flow.log`. Dejar que lo resuelva una vez; a la segunda, plan B |
| El loop no termina a tiempo | Interrumpirlo con Esc y pedirle el informe con lo que tenga |
| Sin red | Solo la necesita el agente. Los bloques 3 a 6 se dan desde el plan B |
