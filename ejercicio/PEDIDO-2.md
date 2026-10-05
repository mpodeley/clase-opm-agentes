Ahora ajustá la función J, con pocas formas y pocos parámetros. Tres casos, cada uno guardado en casos/ y corrido con su etiqueta:

- J1: una sola función J de Leverett y un contacto (la forma del caso base). Ajustá sus cuatro parámetros en ocho corridas como máximo.
- OP: el modelo del operador tal como está en la tabla 11 de su informe (datos/volve/referencia/statoil_3781-06_petrofisica_2006.pdf, páginas 49 a 52) y el FWL de su tabla 10, sin ajustar nada. Si el informe se contradice en algún número, decímelo y decí cuál usaste.
- J2: la misma forma del operador, con sus constantes ajustadas a estos pozos, en ocho corridas como máximo.

Para cada paso de J1 a J2 mostrame el diff de los archivos AJUSTE_*.INC contra el caso anterior. Al terminar escribí comparacion.md con una tabla de los tres casos (rmse_ajuste, el RMSE de cada pozo, rmse_control, sesgo_control, error en volumen poral de hidrocarburo, FWL, n_parametros) y, para cada uno, una oración sobre qué gana y qué cuesta. Decime cuál llevarías a un modelo de campo y qué pozo queda peor ajustado.
