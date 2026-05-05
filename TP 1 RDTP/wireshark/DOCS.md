# Plugin de Wireshark

Para este trabajo, se implementó un script en Lua para agregar como plugin de Wireshark,
que permite interpretar el protocolo desarrollado, y un archivo de colores para una vista
más amigable.

Para *instalarlos*, manualmente, se debe seguir los siguientes pasos:

### Paso 1. Abrir Wireshark y tocar el botón de `Ayuda` o `Help`

![img1](img-1-ws.png)

### Paso 2. Abrir la sección `Acerca de Wireshark` o `About Wireshark`

![img2](img-2-ws.png)

### Paso 3. Abrir la sección `Carpetas` o `Folders`

![img3](img-3-ws.png)

## Instalación del plugin

### Paso 4.1. Abrir la carpeta `Plugins/Extensiones personales` o `Personal plugins`

![img4](img-4-ws.png)

### Paso 5.1. Pegar el [`plugin`](plugin.lua), de esta misma carpeta, en la carpeta que se abre

![img5](img-5-ws.png)

## Instalación de los colores

### Paso 4.2. Abrir la carpeta `Configuración personal` o `Personal config`

![img4](img-8-ws.png)

### Paso 5.2. Pegar el [`colorfilters`](colorfilters.lua), de esta misma carpeta, en la carpeta que se abre

> [!IMPORTANT]
> El archivo debe llamarse exactamente `colorfilters`

![img5](img-9-ws.png)

### Paso 6. Refrescar los plugins de Wireshark con `Ctrl` + `Shift` + `L`, o tocando la
### opción `Analizar` o `Analyze`

![img6](img-6-ws.png)

### Y seleccionar la opción `Recargar plugins/extensiones de Lua` o `Reload Lua Plugins`

![img7](img-7-ws.png)

## Verificar el ejemplo

En esta misma carpeta se encuentra un archivo `test.py` que genera un archivo `test_rfto.pcap`
en el root del proyecto, que sirve para simular paquetes y visualizarlos en Wireshark.

Puede modificarse el archivo si se conoce en profundidad el protocolo, y correrlo para
generar un nuevo ejemplo, o puede simplemente utilizarse el ejemplo proporcionado abriéndolo
con Wireshark.
