# Sitio web de J++

Sitio promocional de J++, en inglés y español. Es un sitio estático: HTML, CSS y un script pequeño, sin base de
datos ni programas en el servidor, así que funciona en cualquier servidor web.

## Qué hay en esta carpeta

| Carpeta o archivo | Para qué sirve |
| --- | --- |
| `public/` | **El sitio listo para publicar.** Esto es lo que se sube al servidor. |
| `content/en.json`, `content/es.json` | Todos los textos del sitio, uno por idioma. |
| `site.json` | Datos generales: versión, enlace de descarga, correo de contacto, enlace de donación. |
| `assets/` | Estilo (`css/styles.css`), script (`js/main.js`), imágenes (`img/`) e instalador (`downloads/`). |
| `build.py` | Genera `public/` a partir de lo anterior. Solo necesita Python 3. |

`public/` se borra y se vuelve a crear en cada generación: no edites nada allí, edita `content/`, `site.json` o `assets/`.

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

### Publicar una versión nueva de J++

1. Copia el instalador a `assets/downloads/` (por ejemplo `J++-1.0.0.dmg`) y borra el anterior si lo hay.
2. En `site.json` cambia `version`, `download_url` (por ejemplo `downloads/J++-1.0.0.dmg`) y `download_size`.
3. Genera y publica.

Mientras `download_url` esté vacío, los botones de descarga dicen "Próximamente".

### Cuando J++ esté en el Mac App Store

Pon la dirección de la app en `app_store_url` de `site.json`. El segundo botón de la portada pasa a ser
"Consíguelo en el Mac App Store". Las páginas `privacy.html` y `support.html` sirven como "Privacy Policy URL" y
"Support URL" en App Store Connect.

### Cambiar las capturas de pantalla

Las capturas están en `assets/img/`, cada una en dos versiones: `nombre-light.jpg` y `nombre-dark.jpg`. El sitio
muestra la clara o la oscura según el sistema del visitante. Reemplaza los archivos con el mismo nombre, o cambia
el campo `image` de la función en `content/*.json`.

### Cambiar colores

Los colores están al principio de `assets/css/styles.css`, una vez para el modo claro y otra para el oscuro.

## Publicar (GitHub Pages)

El sitio está en https://jleiton22-cr.github.io/jpp/ y se publica desde el repositorio `jleiton22-CR/jpp`.
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
y genera de nuevo. Con eso el sitio añade la imagen para compartir en redes (el icono de J++), las etiquetas de
idioma para los buscadores, `sitemap.xml` y `robots.txt`.

## Notas

- **Por ahora el sitio no ofrece la descarga**: `download_url` está vacío en `site.json`, los botones dicen
  "Próximamente" y el instalador no está en el sitio. Para abrir la descarga, sigue "Publicar una versión nueva de J++".
- El instalador que genera el proyecto J++ está firmado de forma local (ad hoc), así que en otros Mac macOS muestra
  el aviso de "desarrollador no identificado". La página de soporte explica cómo abrirlo. Para evitar el aviso,
  firma el instalador con un Developer ID de Apple (ver `scripts/make-installer.sh` en el proyecto J++).
- El sitio no usa cookies, analíticas ni scripts de terceros, y así lo dice la política de privacidad. Si añades
  alguno, actualiza `privacy_page` en los dos archivos de `content/`.
- Las capturas vienen de `help/images/` del proyecto J++. A las que traían marcadores numerados de la guía se les
  quitaron los marcadores.
