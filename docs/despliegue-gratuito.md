# Despliegue gratuito para pruebas y sustentación

El proyecto está preparado para Flask en Render Free, PostgreSQL en Neon Free y generación docente con Groq. No requiere Ollama ni GPU local. La publicación y la validación contra la base remota todavía requieren las cuentas del propietario y sus variables de entorno.

## Configuración necesaria

Crear un proyecto PostgreSQL gratuito y guardar su conexión como `DATABASE_URL` en el servidor. Usar una URL con TLS, por ejemplo la conexión pooled que ofrece Neon con `sslmode=require`. No subir esta conexión ni las claves al repositorio.

Crear un servicio mediante el archivo `render.yaml` del repositorio. El archivo fija el plan gratuito y deja el despliegue automático desactivado. Se necesitan estas variables:

| Variable | Valor |
| --- | --- |
| `DATABASE_URL` | Conexión PostgreSQL remota, configurada como secreto |
| `GROQ_API_KEY` | Clave de Groq configurada como secreto |
| `AI_PROVIDER` | `groq` |
| `GROQ_MODEL` | `openai/gpt-oss-20b`, sujeto a disponibilidad en la cuenta |
| `SECRET_KEY` | Generada por el hosting; conservarla estable entre reinicios |
| `USE_MOCK_DATA` | `false` |
| `APP_ENV` | `production` |
| `COOKIE_SECURE` | `true` para HTTPS |

El comando de arranque aplica esquema y migraciones antes de iniciar Gunicorn. No importa el padrón real automáticamente ni borra datos. Usa un proceso y seis hilos; las conexiones se reutilizan con un pool de hasta seis conexiones. `/live` comprueba que Flask está vivo; `/health` comprueba también la conexión PostgreSQL. El estado de IA informa configuración, no certifica la validez de la clave ni la disponibilidad del modelo.

Antes de la prueba final puede verificarse la persistencia transaccional con `tests/test_postgres_release_integration.py`, configurando `TEST_DATABASE_URL` en el entorno de ejecución. Esa prueba crea un esquema temporal propio y elimina solamente ese esquema al terminar. Sin esa variable se omite explícitamente: las pruebas con datos simulados no sustituyen la verificación de PostgreSQL real.

La primera publicación requiere que el propietario conecte GitHub al hosting. No aceptar un cambio a un plan de pago si el objetivo sigue siendo S/0. Los servicios pueden cambiar sus requisitos de verificación de cuenta: que un plan sea gratuito no garantiza que nunca se solicite verificación adicional.

## Cuentas de demostración

Para crear usuarios ficticios, configurar temporalmente `DEMO_PASSWORD` con una contraseña propia de al menos doce caracteres y ejecutar:

```powershell
.\.venv\Scripts\python.exe scripts\setup_db.py
.\.venv\Scripts\python.exe scripts\seed_demo.py
```

Las cuentas nuevas son `docente_demo`, `alumno_demo_4`, `alumno_demo_5` y `alumno_demo_6`. Las cuentas preexistentes no cambian. La contraseña no se imprime. El docente prepara los temas, materiales y exámenes para cada grado. El padrón real, las entregas y las presentaciones subidas se conservan localmente y se excluyen del repositorio público. Para importar explícitamente el padrón existente, usar `setup_db.py --seed` desde la copia local que conserva ese archivo, sobre la base elegida y revisando previamente su contenido.

## Archivos en hosting gratuito

El disco de Render Free es efímero. Por eso los archivos nuevos pequeños se conservan también en PostgreSQL cuando está configurada `DATABASE_URL`. El límite por archivo es de 20 MB. Esta elección reduce la cantidad de servicios para una demostración pequeña; no es una arquitectura de almacenamiento para un colegio con años de videos.

Las presentaciones se recuperan desde PostgreSQL si desaparece su copia de disco. Los trabajos se descargan mediante una comprobación de sesión y pertenencia. Para persistir archivos históricos cuyo registro ya está en la base remota, ejecutar desde la computadora que conserva esos archivos:

```powershell
.\.venv\Scripts\python.exe scripts\persist_existing_files.py
```

Ese script copia archivos, no migra el padrón ni las notas. Un respaldo de PostgreSQL debe conservarse antes de cualquier traslado de datos. Para esta demostración es preferible empezar con cuentas ficticias y cargar los materiales seleccionados desde el portal docente.

## Funcionamiento de IA y calificación

La clave nunca se envía al navegador. Groq es el proveedor inicial. Para probar NVIDIA, configurar `AI_PROVIDER=nvidia`, `NVIDIA_API_KEY` y un `NVIDIA_MODEL` disponible en la cuenta. El cambio es explícito: no se encadenan dos proveedores automáticamente. El acceso gratuito de prueba de NVIDIA está limitado por sus términos y no debe asumirse como un servicio permanente de producción.

Cada llamada tiene un tiempo de espera configurado de 25 segundos y la generación de juegos no repite automáticamente una respuesta inválida. Si falla la API, se identifica el contenido de respaldo como `fallback`; los juegos siguen pendientes de revisión docente antes de publicarse. Esta espera configurada no equivale a una latencia real medida ni a una garantía de disponibilidad.

El docente dispone del botón «Preparar práctica» en sus materiales. Las preguntas se guardan y comparten por material y grado. Los materiales publicados antiguos sin práctica preparada reciben preguntas deterministas de respaldo; el estudiante no invoca un modelo externo. Puede repetir las prácticas. Cada intento conserva sus preguntas y el servidor califica esa misma versión, sin regenerarla.

Al pulsar Comenzar se inicia el intento del examen y su plazo de treinta minutos. La vista previa no inicia el reloj. Recargar no reinicia el plazo ni cambia las preguntas. Después de enviar, se requiere autorización del profesor para otro intento. El docente accede a `/teacher/settings` para definir pesos y a `/teacher/exam-reopening` para autorizar reaperturas. El último intento de cada actividad identificada cuenta en el promedio; el historial permanece guardado. Los registros heredados sin identidad de actividad mantienen su tratamiento anterior, por lo que se recomienda validar o limpiar los datos de demostración antes de presentarlos como libreta definitiva.

Los juegos guardan historial de entrenamiento y puntos separados; no escriben notas. Los juegos históricos también se excluyen de los promedios revisados. Mientras no se configuren pesos, se muestra un promedio provisional. Con pesos definidos, los exámenes deben pesar más que las prácticas; si falta una categoría, la nota ponderada queda pendiente. Las entregas nuevas se califican de 0 a 20 y su porcentaje se deriva multiplicando por cinco.

## Preparación del día de la sustentación

1. Abrir la URL con anticipación para permitir el arranque del servicio gratuito y comprobar `/health`.
2. Confirmar el inicio de sesión docente y alumno desde las dos laptops.
3. Preparar y revisar las actividades antes del ingreso de los alumnos. Hacer una generación en vivo separada si se necesita demostrar la API.
4. Revisar que los porcentajes de prácticas y exámenes correspondan al acuerdo con el docente.
5. Completar práctica, examen y reapertura; comprobar que jugar repetidamente no cambia el promedio.
6. Reiniciar el servicio y comprobar que notas y archivos siguen disponibles.
7. Grabar el piloto con la aplicación desplegada. Conservar el video para demostrar el recorrido si falla la conectividad del local.

Render Free puede suspenderse tras quince minutos de inactividad y documenta aproximadamente un minuto de arranque. Neon también puede suspender cómputo inactivo. S/0 implica aceptar estos arranques; abrir antes es parte de la preparación. No se usan peticiones artificiales permanentes para eludir los límites del plan.

Fuentes consultadas: [Render Free](https://render.com/docs/free), [Neon Free](https://neon.com/pricing), [Groq API](https://console.groq.com/docs/openai), [modelos de Groq](https://console.groq.com/docs/models), [términos de prueba de NVIDIA](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf).
