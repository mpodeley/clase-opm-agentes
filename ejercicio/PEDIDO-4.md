Última pregunta: ¿vale la pena la hipótesis de un contacto inclinado?

En F-4 el perfil muestra agua móvil desde unos 3,020 m, y en 19 A hay petróleo sin agua móvil hasta 3,101 m. Están a 960 m uno del otro.

1. Tomá el mejor caso con un solo contacto y agregale un nivel de agua libre inclinado en la dirección de 19 A hacia F-4, como escalones de regiones de equilibrio (EQLNUM). Guardalo en casos/t.py. Es un parámetro más.
2. Probá cinco inclinaciones entre −80 y +80 metros por kilómetro, reajustando solo el nivel de agua libre en cada una, y armá la tabla de rmse_ajuste, RMSE de F-4, RMSE de 19 A y rmse_control contra inclinación.
3. Para la mejor inclinación, calculá el gradiente de presión en el acuífero que haría falta para sostenerla, con las densidades de sw/modelo.py.
4. Decime si la mejora justifica el parámetro, qué otra explicación tienen los datos (bloques separados por fallas, con un contacto cada uno) y qué dato del campo lo decidiría.

Respondé en media página, con los números.
