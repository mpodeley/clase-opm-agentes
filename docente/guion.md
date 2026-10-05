# Guion del docente

Clase de 3 h 45 min en formato demostración: todo corre en tu máquina y se proyecta. La sala son
ingenieros de reservorios. Conocen presión capilar, función J y contactos; lo nuevo para ellos es
OPM Flow y el trabajo con un agente.

El hilo de la clase: mirar bien los datos, ajustar con pocos parámetros solo los pozos que
muestran el estado inicial, y dejar un pozo afuera para controlar.

## El día anterior

1. `instalacion/verificar.sh` termina con `todo en orden`.
2. `uv run docente/tabla.py` regenera `docente/plan-b/`: los casos de referencia con su deck, su
   fragmento, su figura y `tabla.md`. Es el plan B de los bloques 5, 6 y 8.
3. Ensayo cronometrado de los cuatro pedidos en una carpeta de prueba:
   `ejercicio/preparar.sh ~/sw-volve-ensayo`, y adentro `claude` con cada `PEDIDO-N.md`.
4. `ejercicio/preparar.sh ~/sw-volve` deja lista la carpeta de la clase, con el agente sin lanzar.
   Entrar una vez con `claude` y aceptar el diálogo de confianza: sin eso ignora los permisos.
5. `slides/build.sh` regenera las figuras y el deck.
6. Para mostrar la instalación sin esperar la descarga, la imagen queda bajada.

## Ventanas

| Ventana | Qué tiene |
| --- | --- |
| A | Las diapositivas (`slides/clase.html`) |
| B | Terminal en el repo, para la instalación y `verificar.sh` |
| C | Terminal en `~/sw-volve`, letra grande, tema claro: acá vive el agente |
| D | Visor de imágenes sobre `~/sw-volve/corridas/`, para las figuras |
| E | Navegador con `~/sw-volve/bitacora.html`, para el loop |
| F | Fuera de pantalla: `docente/plan-b/tabla.md` y este guion |

## Minuto a minuto

### Bloque 1 · El campo y el dataset (0:00 a 0:25)

- 0:00. Qué van a ver: un agente que maneja un simulador, sobre un problema que ellos conocen.
- 0:02. Volve en un minuto: mar del Norte, 80 m de agua, Formación Hugin entre 2,700 y 3,100 m,
  producido de 2008 a 2016 con inyección de agua, datos liberados en 2018.
- 0:04. El mapa: un alto de 1.5 por 2.5 km. Seis pozos en color, y cada color sigue al pozo en
  toda la clase.
- 0:07. Las superficies: discordancia de la base del Cretácico, tope y base del Hugin, y el
  espesor. No hay superficies públicas de lo que está debajo.
- 0:10. Las secciones: cuatro pozos con petróleo entre 2,818 y 3,101 m, 19 BT2 entero en agua
  desde 3,149 m, F-11 B entrando y saliendo por fallas.
- 0:14. La producción y la regla: solo se ajusta con pozos perfilados antes del 12 de febrero de
  2008. F-4 es el caso límite (7 y 11 de febrero). F-11 B, de 2013, es el control.
- 0:17. La tabla de los seis pozos.
- 0:20. Qué trae el conjunto completo y qué usamos: 24 archivos, 52 MB.
- 0:23. Lo que hay que reproducir: Sw contra profundidad, los cinco pozos. Preguntar dónde
  pondrían el contacto y anotar dos o tres respuestas.

### Bloque 2 · Lectura rápida de perfiles (0:25 a 0:45)

- 0:25. F-12, pista por pista. No hay SP: lodo base aceite. BVW separa agua irreducible de móvil.
- 0:30. F-4: la resistividad cae desde 3,005 m; debajo de 3,015 m la Sw media es 0.51. Contar acá
  lo de la permeabilidad de F-12: el archivo de 2007 da 40 veces menos que la revisión de 2009.
- 0:35. Buckles y Sw contra permeabilidad. Agua móvil en el 17% de la arena de 19 A, 27% de F-12,
  37% de F-4 y 99% de 19 BT2, con el Swirr del operador.
- 0:41. La idea que ordena el ajuste: la función J explica el agua móvil; la irreducible la fija
  la roca.

### Bloque 3 · PVT y presiones (0:45 a 1:00)

- 0:45. La tabla de fluidos: 720 y 1,065 kg/m³, burbuja entre 213 y 236 bar, presión inicial
  336.5 bar. Petróleo subsaturado, modelo de dos fases. 0.034 bar de presión capilar por metro.
- 0:49. Las presiones: 16 puntos en agua de 19 BT2 (0.1053 bar/m), el ensayo de 19 A y la
  muestra de F-4. El cruce da 3,196 ± 14 m. El punto de F-4 queda 6.7 bar sobre la línea.
- 0:55. Los contactos que circulan: perfiles (3,101 a 3,149 m), informe (3,120 ± 15 m),
  presiones (3,196 m), modelo de campo (3,200 m y otros). Volver a las respuestas del bloque 1.
  El ajuste deja el contacto libre entre 3,100 y 3,220 m.

### Bloque 4 · Instalación (1:00 a 1:20)

- 1:00. Las cuatro piezas: contenedor, `uv`, git, Claude Code.
- 1:04. Ventana B: `instalacion/instalar.sh` y `verificar.sh`. Señalar los hashes. Después,
  `uv run evaluar.py` a mano.
- 1:13. `ejercicio/preparar.sh` y qué hay en la carpeta: `CLAUDE.md`, los pedidos y
  `.claude/settings.json`. Leer permisos y prohibiciones.

### Pausa (1:20 a 1:30)

### Bloque 5 · Repaso de J y el deck (1:30 a 1:55)

- 1:30. La función J en tres líneas y lo que supone. σ·cosθ fijo en 2 mN/m, el valor del operador.
- 1:34. La figura: tres rocas, tres perfiles, una curva.
- 1:38. Nuestro modelo (una fila de celdas) y el deck de campo de Equinor: 12 regiones de
  equilibrio, presión capilar cero, agua connata por celda.
- 1:42. Ventana C: `claude`, y pegar `PEDIDO-1.md`. Narrar qué herramienta llama. El caso base da
  `rmse_ajuste` 0.142 y `rmse_control` 0.205.
- 1:48. El fragmento del deck en pantalla: `JFUNC`, `SWOF`, `EQUIL`. Cuatro parámetros a la vista.
- 1:53. Un caso nuevo es un diff de tres archivos chicos.

Plan B: `docente/plan-b/base/` y `docente/plan-b/j1/fragmento.txt`.

### Bloque 6 · Ajuste de J (1:55 a 2:35)

- 1:55. Pegar `PEDIDO-2.md`: J1, el modelo del operador sin tocar, y J2. Unos 12 minutos.
- 1:57. Mientras corre, la diapositiva de los tres casos. Apuesta: ¿el modelo de 2006 sin tocar
  ajusta mejor o peor que una J nueva?
- 2:07. La figura del operador: 0.122 sin ajustar nada, y sesgo de +0.066 en el control.
- 2:13. La figura de J1: 0.112, contacto en 3,150 m, y la transición de F-11 B predicha.
- 2:19. La tabla. Compararla con `comparacion.md`:

  | Caso | Ajuste | F-4 | Control | Sesgo del control | FWL | Parámetros |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: |
  | Base | 0.142 | 0.201 | 0.205 | −0.038 | 3,120 m | 4 |
  | J1 | 0.112 | 0.147 | 0.122 | −0.003 | 3,150 m | 4 |
  | OP | 0.122 | 0.151 | 0.197 | +0.066 | 3,120 m | 0 |
  | J2 | 0.114 | 0.149 | 0.142 | +0.003 | 3,151 m | 5 |

- 2:25. El diff del deck entre J1 y el operador.
- 2:30. Cierre: con cuatro parámetros alcanza y el control lo confirma. Qué eligió el agente.
- 2:33. Pegar `PEDIDO-3.md` y dejar el loop corriendo durante la pausa.

Si el informe se contradice: es verdad. La tabla 11 da `Swirr = 0.45 − 0.105·log k` para Volve
y la figura 20.b rotula `0.412 − 0.088·log k`. El caso de referencia sigue la tabla.

### Pausa (2:35 a 2:45)

### Bloque 7 · Loop con hipótesis a la vista (2:45 a 3:15)

- 2:45. El diagrama del flujo: qué escribe la persona, qué edita el agente, qué queda fijo.
- 2:49. Qué le cambiamos a autoresearch. Abrir `program.md` y leer el formato del commit.
- 2:52. Ventana E: `bitacora.html` en vivo. El reproductor, la curva de error y cada experimento.
- 2:57. La animación del ensayo, cuadro a cuadro.
- 3:00. Las hipótesis del ensayo, en tres diapositivas. Preguntar antes de mostrar cada veredicto.
- 3:06. Cómo leerlas: forma o valor, predicción cumplida o no, ajuste contra control.
- 3:11. El agente y el optimizador clásico.

Referencia del ensayo del 5 de octubre de 2026 (`docente/plan-b/ensayo/`): 12 experimentos en 9
minutos, 3 conservados y 9 descartados. Solo cambió `caso.py`. El caso final tiene 2 parámetros,
`Sw = J^−0.284` con el contacto en 3,150 m: `rmse_ajuste` 0.112 y `rmse_control` 0.121, lo mismo
que el J1 de cuatro parámetros ajustado con optimizador. Lo que sirve para la discusión:

- La primera hipótesis fue de forma y dio casi toda la mejora: sacar la meseta de agua
  irreducible (de 0.142 a 0.113, con un parámetro menos).
- Probó sin escalado de Leverett y el error subió a 0.124: el escalado vale 0.011.
- Swirr por permeabilidad, Swirr por arcilla, dos tipos de roca, exponente de k libre y curva de
  Thomeer no llegaron al umbral de 0.004 por parámetro.
- Con el contacto del operador (3,120 m) el ajuste empeora 0.003 y el control pasa de 0.121 a
  0.177.
- Su informe dice que la base de F-4 concentra la mitad del error y propone contactos distintos
  para F-4 y 19 A. Es el puente al bloque 8.
- Avisó que eligió los valores con una cuenta propia fuera de Flow, y que esa cuenta falló en los
  dos experimentos con `SWL`.

Si el loop no terminó: Esc y pedirle el informe con lo que tenga.

### Bloque 8 · ¿Contacto inclinado? (3:15 a 3:30)

- 3:15. Pegar `PEDIDO-4.md`. Mientras corre: F-4 con agua móvil desde 3,015 m, 19 A con petróleo
  hasta 3,101 m, a 960 m uno del otro.
- 3:18. La figura del barrido (`docente/plan-b/barrido_inclinacion.tsv`):

  | Inclinación (m por km) | Ajuste | F-4 | 19 A | Control |
  | ---: | ---: | ---: | ---: | ---: |
  | 0 | 0.114 | 0.149 | 0.058 | 0.142 |
  | −45 | 0.107 | 0.136 | 0.073 | 0.209 |
  | −90 | 0.097 | 0.108 | 0.061 | 0.193 |
  | −120 | 0.099 | 0.114 | 0.055 | 0.143 |

- 3:23. ¿Vale la pena? A favor: 0.017 por un parámetro. En contra: el control no mejora, y 90 m
  por kilómetro piden unos 3 bar por kilómetro en el acuífero. La otra explicación son bloques
  con contactos distintos: el modelo de campo tiene una región en 3,025 m, y el punto de presión
  de F-4 está 6.7 bar sobre la línea de 19 A.
- 3:28. Qué dato lo decide: presiones de formación en F-4 y en 19 A, del mismo momento.

El control no es monótono con la inclinación (con −120 vuelve a 0.143). Si alguien lo pregunta:
depende de dónde cae el contacto a lo largo de F-11 B, que cruza varias regiones. Por eso la
conclusión se apoya en el gradiente y en las presiones, y el control solo dice que no mejora.

### Bloque 9 · Controles y cierre (3:30 a 3:45)

- 3:30. Qué revisa el ingeniero antes de firmar un caso armado por un agente:
  1. El caso vive en su propia carpeta, con el caso base al lado.
  2. Un diff contra el caso base, leído.
  3. La lista de supuestos y de valores por defecto del simulador.
  4. La versión del simulador y los datos, fijados.
  5. Un pozo de control que el caso nunca vio.
  6. Un ingeniero firma.
- 3:36. Los límites: la sección "Qué no se puede afirmar con esto" del README.
- 3:40. Para llevarse, y preguntas.

## Si algo falla

| Qué | Qué hacer |
| --- | --- |
| El contenedor no arranca | `FLOW=/ruta/a/flow` si hay un Flow nativo; si no, seguir con `docente/plan-b/` |
| El agente edita algo que no debe | Lo frena el permiso. Mostrarlo: es parte de la clase |
| Flow rechaza un deck | El agente lee el final de `flow.log`. Dejar que lo resuelva una vez; a la segunda, plan B |
| El loop no termina a tiempo | Interrumpirlo con Esc y pedirle el informe con lo que tenga |
| Sin red | Solo la necesita el agente. Los bloques 5 a 8 se dan desde el plan B |
