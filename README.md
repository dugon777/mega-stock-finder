# Mega Stock Finder — versión gratis, automática y hospedable

Proyecto de investigación personal. **No es un sistema CAN SLIM completo ni genera órdenes de compra.**

## Tecnología sin facturación obligatoria

- GitHub Actions: actualiza el dataset de lunes a viernes a las 23:30 UTC (~17:30 Mérida, tras el cierre de NY incluso en verano). Las ejecuciones programadas pueden retrasarse o omitirse.
- GitHub Pages (repositorio público con cuenta GitHub Free): sirve `docs/index.html` sin servidor.
- Biblioteca Python `yfinance`: obtiene precios diarios de Yahoo Finance sin API key. **No es API oficial ni garantiza disponibilidad, exactitud o derecho de redistribución**. Úsalo para investigación personal y revisa los términos de los datos antes de publicar resultados derivados. Si cambian las políticas, sustituye el proveedor.
- Fuente opcional para fundamentales de EE. UU.: SEC `companyfacts` gratis, requiere User-Agent identificable. **Aún no conectado a este MVP**.
- Sin OpenAI API, por lo tanto cero consumo de tokens facturados. ChatGPT no necesita ejecutar un navegador todos los días para esta tarea.

## Publicarlo paso a paso (GitHub Pages con Actions)

1. Crea una cuenta en https://github.com/signup.
2. Crea un repositorio público llamado `mega-stock-finder`, con README desactivado. En un repositorio público el código y los datos publicados son visibles para todos.
3. Descomprime el ZIP, abre `mega_stock_gratis` y sube **el contenido de esa carpeta**, no la carpeta envolvente, a la raíz del repositorio. Incluye `.github/workflows/scan.yml` (en Windows quizá debas habilitar los archivos ocultos). Puedes arrastrar carpetas desde el explorador a **Add file → Upload files**. Después pulsa **Commit changes**. Comprueba que en la raíz aparezcan `docs/`, `scanner/`, `.github/`, `requirements.txt` y `universe.txt`.
4. En **Settings → Actions → General → Workflow permissions** selecciona **Read and write permissions** y guarda, si esa opción está disponible.
5. En **Settings → Secrets and variables → Actions → New repository secret** crea `SEC_USER_AGENT` con un identificador real y un email de contacto tuyo, por ejemplo `MegaStockFinder contacto@ejemplo.com` (reemplaza ese correo por uno propio válido). Nunca pongas contraseña ni token en ese campo.
6. En **Settings → Pages → Build and deployment → Source** elige **GitHub Actions** (NO "Deploy from a branch": este ZIP usa `actions/deploy-pages` para que también se actualice cuando el workflow haga un commit). Guarda.
7. Ve a **Actions → Daily stock scan → Run workflow → Run workflow** para la primera prueba. Revisa que los pasos de escaneo y **Publish dashboard** se pongan verdes. Puede requerirse permitir explícitamente los workflows desde la pestaña Actions.
8. En **Settings → Pages** verás la URL, normalmente `https://TU_USUARIO.github.io/mega-stock-finder/`. Comprueba que la web no muestre datos vacíos y que el último escaneo tenga fecha.
9. En días hábiles el workflow intenta ejecutarse a las 23:30 UTC (~17:30 Mérida). GitHub puede retrasar u omitir ejecuciones; datos de terceros pueden bloquear peticiones.

**Si ves un error:** busca el paso rojo dentro de Actions y comparte su texto. Si el primer escaneo falla por rate limits, configura temporalmente `SCAN_BATCH_SIZE: 30` en `.github/workflows/scan.yml` para la prueba. No confundas un universo SEC de miles de símbolos con miles de cotizaciones analizadas ese día.

## Ejecución local opcional

```
python -m pip install -r requirements.txt
python -m scanner.run
python -m http.server 8000 --directory docs
```

Navega a http://localhost:8000 para ver la web.

## Qué calcula hoy

SMA20/50/200, retornos a 20/63 sesiones, RS de 20 días contra SPY, volumen vs 50 días, máximo de las 40 sesiones anteriores, extensión, SMT de mínimos por bloques de 20 sesiones y un score técnico original no oficial.

### Advertencias imprescindibles

- El máximo de 40 días NO es un pivote confirmado de O'Neil ni clasifica bases cup-with-handle o flat base.
- La SMT usa SPY como aproximación a un índice. No contrasta los tres índices cash en swings equivalentes; puede producir falsos positivos.
- No analiza EPS, ventas, sectores, grupos industriales ni ratings IBD; el score no puede denominarse CAN SLIM compuesto.
- No permite cotizaciones en tiempo real, compra de acciones, acceso privado real o backtesting libre de sesgo. Los símbolos son una lista inicial, no todas las acciones americanas.
- Acciones con menos de 210 sesiones válidas reciben 'DATOS INSUFICIENTES'.
- Los datos de terceros pueden tener condiciones de licenciamiento incompatibles con publicación de precios. Una alternativa privada es usar Actions solo para generar artefactos descargables y no habilitar Pages.
- Las ejecuciones programadas pueden requerir reactivación si un repositorio público queda inactivo por tiempo prolongado. El sitio seguirá mostrando su fecha de última actualización.

## Próxima evolución (no incluida)

Agregar fundamentales punto-en-tiempo SEC, comparación por industrias con listas históricas, detección de swings/SMT multíndice, validación de bases, logging y backtesting fuera de muestra. Cualquier automatización más completa necesita probar fiabilidad y licencias de datos.

## Versión ampliada — descubrimiento automático (actualización)

**Ya no se limita a 63 acciones.** `scanner/universe.py` descubre los tickers registrados ante la SEC en Nasdaq/NYSE/NYSE American/Cboe y actualiza un caché. La SEC no promete que todos los símbolos sean acciones ordinarias; se filtrarán posteriormente fondos, ADR, instrumentos especiales y sociedades inactivas mediante metadatos adicionales.

* **Watchlist fija:** `universe.txt` (incluye PAY, GLBE, MGNI, VMD y CLFD) se ejecuta en cada análisis.
* **Universo amplio:** la SEC facilita miles de tickers; el escáner analiza **250 símbolos adicionales por ejecución** (configurable mediante `SCAN_BATCH_SIZE`), rotando de forma determinista.
* **Persistencia:** conserva los últimos resultados de los símbolos analizados y marca fechas. **No afirmar cobertura diaria completa**: analizar 6,000 acciones a 250/día implica varias semanas laborables por pasada. Si falla Yahoo, los registros previos se mantienen y se señala el intento fallido.
* **Preparación imprescindible:** En GitHub, `Settings → Secrets and variables → Actions`, crear un secreto `SEC_USER_AGENT` con un User-Agent descriptivo y un correo de contacto válido, por ejemplo `MegaStockFinder research contacto@dominio.com`. La SEC requiere un identificador adecuado. Sin él, el sistema usará el caché SEC (si existe) o únicamente `universe.txt`.
* **Restricciones:** yfinance es no oficial y puede bloquear solicitudes; incluso 250/día podría no funcionar bien. GitHub Actions puede retrasar ejecuciones. El código conserva controles para no publicar una actualización vacía.
* La interfaz muestra tanto universo descubierto como total de registros acumulados; no los confunda. Cada fila conserva su fecha original de cotización.
