Última pregunta: ¿por qué hay agua en la base de F-4?

En F-4 el perfil muestra agua móvil desde unos 3,015 m, con Sw 0.34 en roca de 3,000 mD. En 19 A hay petróleo sin agua móvil hasta 3,101 m. Están a 960 m uno del otro. Evaluá dos hipótesis, cada una con un parámetro más sobre el mejor caso de un solo contacto:

1. Contacto inclinado: un nivel de agua libre que sube de 19 A hacia F-4, como escalones de regiones de equilibrio (EQLNUM). Guardalo en casos/t.py y probá cinco inclinaciones entre −120 y +60 metros por kilómetro, reajustando el nivel en 19 A en cada una.
2. Agua colgada: todo es una misma estructura, pero un bajo de la base del Hugin retuvo agua bajo F-4. En el deck es una segunda región de equilibrio solo para las celdas de F-4, con su propio nivel. Guardalo en casos/p.py y probá seis niveles locales entre 3,000 y 3,100 m.

Para cada hipótesis armá la tabla de rmse_ajuste, RMSE de F-4, RMSE de 19 A, rmse_control y sesgo_control. Para la mejor inclinación, calculá el gradiente de presión en el acuífero que haría falta para sostenerla, con las densidades de sw/modelo.py.

Cerrá en media página: cuál de las dos sostienen los datos, qué le pide cada una a la geología, y qué dato del campo distinguiría una cubeta de un bloque separado con su propio contacto.
