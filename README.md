# Sitio web de jplus2

Sitio promocional de jplus2, en inglés y español. Es un sitio estático: HTML, CSS y un script pequeño, sin base de
datos ni programas en el servidor, así que funciona en cualquier servidor web.

## Qué hay en esta carpeta

| Carpeta o archivo | Para qué sirve |
| --- | --- |
| `public/` | **El sitio listo para publicar.** Esto es lo que se sube al servidor. |
| `content/en.json`, `content/es.json` | Todos los textos del sitio, uno por idioma. |
| `site.json` | Datos generales: versión, enlace de descarga, correo de contacto, enlace de donación. |
| `assets/` | Estilo (`css/styles.css`), script (`js/main.js`), imágenes (`img/`) e instalador (`downloads/`). |
| `build.py` | Genera `public/` a partir de lo anterior. Solo necesita Python 3. |

`public/` se genera de nuevo cada vez, y lo que no venga de las otras carpetas se borra: no edites nada allí, edita `content/`, `site.json` o `assets/`.

## Ver el sitio en tu Mac

```bash
python3 build.py serve
```

Abre http://localhost:8080. Para detenerlo, pulsa Ctrl-C.

## Cambiar algo

1. Edita el texto en `content/es.json` y en `content/en.json` (las dos tienen la misma estructura).
2. Genera el sitio otra vez:

```bash
python3 build.py
```

3. Sube la carpeta `public/` al servidor.

Los textos pueden usar `{version}`, `{size}` y `{email}`, que se rellenan con los valores de `site.json`.

### Publicar una versión nueva de jplus2 Lite

El sitio ofrece **jplus2 Lite** (gratis); la versión completa solo se consigue en el Mac App Store, así que su instalador no debe estar en este sitio ni en el repositorio.

El instalador Lite **no está en el sitio**: se aloja como archivo de un Release de GitHub, y GitHub cuenta cada descarga.

1. Crea el Release con el instalador (desde `dmg/` del proyecto "J++ Lite"):

```bash
gh release create lite-1.0.1 "/ruta/J++-Lite-1.0.1.dmg" --repo jleiton22-CR/jpp --title "jplus2 Lite 1.0.1" --notes "jplus2 Lite 1.0.1" --latest=false
```

2. En `site.json` cambia `version`, `download_size`, `download_sha256` y `download_url` a la dirección del archivo
   del Release (`https://github.com/jleiton22-CR/jpp/releases/download/lite-1.0.1/J%2B%2B-Lite-1.0.1.dmg`; el `+` se
   escribe `%2B`). La huella sale de `shasum -a 256 archivo.dmg`, o de `gh api repos/jleiton22-CR/jpp/releases/tags/lite-1.0.1 --jq '.assets[0].digest'`.
3. Genera y publica.

Todos los botones de descarga llevan a `thanks.html` (página de gracias), que inicia la descarga una vez por sesión,
explica la instalación y muestra la huella SHA-256. Esa página no se indexa (`noindex` y `robots.txt`).

Mientras `download_url` esté vacío, los botones de descarga dicen "Próximamente".

### Contador de descargas

```bash
./contador.sh
```

Muestra cuántas veces se ha descargado cada instalador de cada Release y el total. Es el contador de GitHub: suma
cada descarga completa del archivo, así que una misma persona que descargue dos veces cuenta dos, y a veces puede
tardar unos minutos en actualizarse. El sitio no usa analíticas ni scripts de terceros.

### Contador de visitas (GoatCounter)

El sitio puede contar visitas con [GoatCounter](https://www.goatcounter.com): gratis, sin cookies, y guarda solo totales
(páginas visitadas, de qué sitio vienen, tipo de navegador), no la IP. Está **apagado** hasta que se escriba el nombre de la cuenta.

1. Crea la cuenta gratis en https://www.goatcounter.com/signup y elige un nombre (por ejemplo `jplus2`).
2. En `site.json` escribe ese nombre en `goatcounter_code` (solo minúsculas, números y guiones).
3. Genera y publica. El script se añade solo a las páginas, y la política de privacidad cambia sola de "sin analíticas" a la
   frase que explica el conteo, en inglés y en español.
4. Las visitas se ven en `https://NOMBRE.goatcounter.com` (inicias sesión con tu cuenta).

No cuenta a quien envía "No rastrear", ni cuando abres el sitio en tu Mac con `python3 build.py serve`.
Para apagarlo, deja `goatcounter_code` vacío y publica de nuevo. Las descargas se siguen contando con `./contador.sh`.

### Cuando jplus2 esté en el Mac App Store

Pon la dirección de la app en `app_store_url` de `site.json`. Mientras esté vacía, la sección "Lite y Completa"
y el final de la página muestran "Mac App Store · enlace próximamente"; con la dirección puesta, esos botones
pasan a ser enlaces al Mac App Store. Las páginas `privacy.html` y `support.html` sirven como "Privacy Policy URL" y
"Support URL" en App Store Connect.

### Idiomas

La primera vez que alguien entra, el sitio se abre en el idioma de su sistema: español si el sistema está en
español, inglés en cualquier otro caso. El interruptor **EN | ES** de la barra cambia de idioma, y el navegador
del visitante recuerda esa elección para las siguientes visitas.

### Cambiar las capturas de pantalla

Las capturas están en `assets/img/`, cada una en dos versiones: `nombre-light.jpg` y `nombre-dark.jpg`. El sitio
muestra la clara o la oscura según el sistema del visitante. Reemplaza los archivos con el mismo nombre, o cambia
el campo `image` de la función en `content/*.json`.

### Cambiar colores

Los colores están al principio de `assets/css/styles.css`, una vez para el modo claro y otra para el oscuro.

## Publicar (GitHub Pages)

El sitio está en https://jplus2.com y se publica desde el repositorio `jleiton22-CR/jpp` con GitHub Pages.
El dominio `jplus2.com` está registrado en Squarespace; sus registros DNS (cuatro A y un CNAME para `www`) apuntan a
GitHub, y el archivo `assets/CNAME` le dice a GitHub qué dominio usar.
Después de cualquier cambio:

```bash
./publish.sh "qué cambió"
```

Genera el sitio, guarda el proyecto en la rama `main` y sube `public/` a la rama `gh-pages`, que es la que
GitHub muestra. El cambio se ve en uno o dos minutos.

## Publicar en otro servidor web

Sube **el contenido** de `public/` a la carpeta pública del servidor (suele llamarse `public_html`, `www` o `htdocs`).
Los enlaces son relativos, así que el sitio funciona tanto en la raíz del dominio como en una subcarpeta.

- **Hosting con panel o FTP:** arrastra el contenido de `public/` con el administrador de archivos o con un cliente FTP.
- **Servidor propio con SSH:**

```bash
rsync -av --delete public/ usuario@servidor:/var/www/jpp/
```

- **GitHub Pages, Netlify o Cloudflare Pages:** publica la carpeta `public/`; no necesitan ningún paso de compilación.

Cuando tengas el dominio, escribe su dirección en `base_url` de `site.json` (por ejemplo `https://www.ejemplo.com`)
y genera de nuevo. Con eso el sitio añade la imagen para compartir en redes (el icono de jplus2), las etiquetas de
idioma para los buscadores, `sitemap.xml` y `robots.txt`.

## Marca (jplus2)

El producto se llama **jplus2** (en minúsculas, igual que la app de macOS) y su icono es la J con "+" sobre un "2". El nombre sale
de `app_name` en `site.json` y de los textos de `content/*.json`. Los iconos del sitio (`assets/img/icon-*.png`, `favicon.png`,
`apple-touch-icon.png`, `og.png` y `favicon.ico`) se generan de `appstore/icon/icon-light-1024.png` e `icon-dark-1024.png` del proyecto de la app.

**Pendiente cuando se reconstruya Lite con la marca nueva:** hoy el instalador Lite todavía se llama "J++ Lite" por dentro (archivo
`J++-Lite-1.0.0.dmg`, app "J++ Lite" y su icono viejo), así que los pasos de instalación de `thanks.html` y `support.html`
citan esos nombres reales. Al publicar el nuevo instalador, cambia en `content/*.json` las frases que dicen "J++ Lite" y
"J++-Lite" (están en `thanks.steps`, `thanks`, `support_page` y en `build.py`, en el comando `shasum`).

## Notas

- **El sitio ofrece solo jplus2 Lite** (Release `lite-1.0.0` de GitHub, enlazado desde `site.json`). La sección "Lite y Completa" compara las
  dos versiones; si cambian las funciones de Lite, edita `editions` en `content/*.json`.
- **La sección del iPad** (`ipad` en `content/*.json`) anuncia una versión para el próximo lanzamiento, marcada como
  "planeada, los detalles pueden cambiar". Su captura (`ipad-light.jpg`, `ipad-dark.jpg`) viene del autotest del proyecto "J++ Ipad".
- El instalador que genera el proyecto J++ está firmado de forma local (ad hoc), así que en otros Mac macOS muestra
  el aviso de "desarrollador no identificado". La página de soporte explica cómo abrirlo. Para evitar el aviso,
  firma el instalador con un Developer ID de Apple (ver `scripts/make-installer.sh` en el proyecto J++).
- El sitio no usa cookies, analíticas ni scripts de terceros, y así lo dice la política de privacidad. Si añades
  alguno, actualiza `privacy_page` en los dos archivos de `content/`.
- Las capturas vienen de `help/images/` del proyecto jplus2. A las que traían marcadores numerados de la guía se les
  quitaron los marcadores.
