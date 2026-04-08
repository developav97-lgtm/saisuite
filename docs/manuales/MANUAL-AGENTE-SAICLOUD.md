---
title: Manual de Instalación del Agente Saicloud
module: general
category: manual
source: ValMen Tech — SaiCloud
---

# Manual de Instalacion del Agente Saicloud

> **Version:** 1.1.0
> **Ultima actualizacion:** Abril 2026
> **Audiencia:** Personal de TI del cliente o usuario final con permisos de administrador en Windows

---

## Contenido

1. [Que es el Agente Saicloud](#1-que-es-el-agente-saicloud)
2. [Requisitos previos](#2-requisitos-previos)
3. [Lo que recibe de ValMen Tech](#3-lo-que-recibe-de-valmen-tech)
4. [Instalacion paso a paso](#4-instalacion-paso-a-paso)
5. [Probar la conexion](#5-probar-la-conexion)
6. [Instalar como servicio de Windows](#6-instalar-como-servicio-de-windows)
7. [Verificar funcionamiento](#7-verificar-funcionamiento)
8. [Gestion del servicio](#8-gestion-del-servicio)
9. [Configuracion multi-empresa](#9-configuracion-multi-empresa)
10. [Solucion de problemas](#10-solucion-de-problemas)
11. [Soporte tecnico](#11-soporte-tecnico)
12. [Referencia rapida de comandos](#12-referencia-rapida-de-comandos)

---

## 1. Que es el Agente Saicloud

El **Agente Saicloud** es un programa que se instala en el computador donde funciona Saiopen (su sistema contable). Su funcion es enviar automaticamente los datos contables de Saiopen hacia la nube de Saicloud, para que usted pueda consultarlos desde cualquier lugar a traves de la plataforma web.

El agente sincroniza la siguiente informacion:

| Dato | Descripcion |
|------|-------------|
| **Movimientos contables (GL)** | Todos los asientos del libro diario |
| **Plan de cuentas** | La estructura de cuentas contables (PUC) |
| **Terceros** | Clientes, proveedores y demas terceros |
| **Departamentos y centros de costo** | Clasificaciones organizacionales |
| **Proyectos** | Proyectos contables registrados en Saiopen |
| **Actividades** | Actividades asociadas a los proyectos |

El agente funciona de forma silenciosa en segundo plano como servicio de Windows. Una vez instalado, se inicia automaticamente cada vez que el computador se enciende y no requiere intervencion manual.

---

## 2. Requisitos previos

### En el computador del cliente

- **Sistema operativo:** Windows 10 o superior, version de 64 bits
- **Saiopen instalado y funcionando** con base de datos Firebird 2.5
- **Servicio de Firebird activo** (se instala automaticamente junto con Saiopen)
- **Conexion a internet** estable
- **Permisos de administrador** en el computador

### Antes de iniciar

El equipo de ValMen Tech debe haber completado la creacion de su empresa en la plataforma Saicloud. Usted recibira un archivo `.zip` pre-configurado — eso es todo lo que necesita para instalar.

> **No necesita conocer ni escribir ninguna contrasena, token ni URL.** Todo viene dentro del archivo que le entrega ValMen Tech.

---

## 3. Lo que recibe de ValMen Tech

ValMen Tech le entregara (por correo o descarga) un archivo comprimido llamado:

```
saicloud-agent-v1.0.0-windows-x64.zip
```

Dentro de ese archivo vienen exactamente dos archivos:

| Archivo | Descripcion |
|---------|-------------|
| `agent.exe` | El programa del agente |
| `saicloud-agent.json` | El archivo de configuracion pre-listo con todos los datos de su empresa |

> **Importante:** El archivo `saicloud-agent.json` contiene informacion confidencial de su empresa y de la conexion. No lo comparta con terceros ni lo envie por canales no seguros.

---

## 4. Instalacion paso a paso

### Paso 1: Crear la carpeta del agente

Abra **CMD** o **PowerShell** como administrador y ejecute:

```
mkdir C:\SaicloudAgent\logs
```

O manualmente en el Explorador de archivos:
1. Abra el disco `C:\`
2. Cree la carpeta `SaicloudAgent`
3. Dentro de ella cree la carpeta `logs`

La estructura debe quedar asi:

```
C:\SaicloudAgent\
C:\SaicloudAgent\logs\
```

### Paso 2: Copiar los archivos

1. Descomprima el archivo `.zip` que le entrego ValMen Tech.
2. Copie **ambos archivos** dentro de `C:\SaicloudAgent\`:
   - `agent.exe`
   - `saicloud-agent.json`

Al terminar, la carpeta debe contener:

```
C:\SaicloudAgent\
    agent.exe
    saicloud-agent.json
    logs\
```

> **Importante:** No cambie el nombre de los archivos ni los mueva a otra ubicacion.

### Paso 3: Configurar la ruta de la base de datos (interfaz web)

El unico dato que debe ajustar es la **ruta del archivo .FDB** de Saiopen en su computador. Lo hace desde la interfaz web del agente — no necesita editar ningun archivo de texto.

1. Abra **CMD** como administrador y ejecute:

```
cd C:\SaicloudAgent
agent.exe config
```

2. El agente abrira automaticamente su navegador en `http://localhost:8765`.

3. Vera la pantalla del configurador con la conexion de su empresa ya precargada (nombre, credenciales y token vienen del archivo entregado por ValMen Tech).

4. Haga clic en el boton **Editar** de la conexion.

5. En el campo **Database Path (.fdb)**, escriba la ruta correcta del archivo de base de datos Firebird de Saiopen en su computador:

   > **Como encontrar la ruta:**
   > - Abra el Explorador de archivos y busque el archivo `.FDB` de Saiopen.
   > - Generalmente esta en `C:\SAIOPEN\DATOS\` o en la carpeta de instalacion de Saiopen.
   > - Use barras inclinadas hacia adelante `/` en lugar de `\`. Ejemplo: `C:/SAIOPEN/DATOS/MIEMPRESA.FDB`

6. Haga clic en **Guardar**.

7. Cierre el navegador y vuelva al CMD. Presione `Ctrl + C` para cerrar el configurador.

---

## 5. Probar la conexion

Antes de instalar el servicio, verifique que todo funciona correctamente.

### Abrir CMD como administrador

1. Presione la tecla **Windows**.
2. Escriba `cmd`.
3. Haga clic derecho sobre **Simbolo del sistema** y seleccione **Ejecutar como administrador**.
4. Navegue a la carpeta del agente:

```
cd C:\SaicloudAgent
```

### Ejecutar la prueba

```
agent.exe test --id conn_001
```

### Resultado exitoso

```
Testing connection: Mi Empresa S.A.S (conn_001)
--------------------------------------------------
  Testing Firebird connection... OK (GL records: 15432, max CONTEO: 15432)
  Testing Saicloud API connection... OK

  Summary:
    Total GL records: 15432
    Last synced CONTEO: 0
    Pending records: 15432

Connection test PASSED.
```

Esto confirma que:
- El agente se conecta correctamente a la base de datos Firebird local
- El agente se comunica con la nube de Saicloud

### Resultado fallido

Si ve un mensaje como:

```
Connection test FAILED: <descripcion del error>
```

Consulte la seccion [Solucion de problemas](#10-solucion-de-problemas).

---

## 6. Instalar como servicio de Windows

Un **servicio de Windows** es un programa que se ejecuta automaticamente en segundo plano, sin necesidad de abrirlo manualmente. Al instalarlo como servicio, el agente se iniciara automaticamente cada vez que encienda el computador.

En la ventana de **CMD** (ejecutada como administrador), ejecute:

```
cd C:\SaicloudAgent
agent.exe install
```

Resultado exitoso:

```
Saicloud Agent installed as Windows Service successfully.
```

> **Importante:** Este comando debe ejecutarse como administrador. Si ve un error de permisos, cierre la ventana y vuelvala a abrir haciendo clic derecho > **Ejecutar como administrador**.

El servicio queda activo automaticamente y se iniciara en cada arranque de Windows.

---

## 7. Verificar funcionamiento

### Desde la linea de comandos

```
cd C:\SaicloudAgent
agent.exe status
```

Vera una salida similar a:

```
Saicloud Agent v1.0.0
Log Level: info
Log File: C:/SaicloudAgent/logs/agent.log
Configurator Port: 8765

Connections (1):
--------------------------------------------------------------------------------
  [ENABLED] Mi Empresa S.A.S (conn_001)
    Firebird: localhost:3050 C:/SAIOPEN/DATOS/MIEMPRESA.FDB
    Saicloud: https://api.saicloud.co (company: ...)
    GL Interval: 15 min | Ref Interval: 24 hrs | Batch Size: 500
    Last CONTEO GL: 0
    Last Sync ACCT: never | CUST: never | LISTA: never
```

| Campo | Significado |
|-------|-------------|
| `[ENABLED]` | La conexion esta activa y sincronizando |
| `[DISABLED]` | La conexion esta desactivada |
| `GL Interval: 15 min` | Los movimientos contables se sincronizan cada 15 minutos |
| `Ref Interval: 24 hrs` | Las tablas de referencia se sincronizan cada 24 horas |
| `Last CONTEO GL: 0` | La primera sincronizacion aun no ha ocurrido (normal al inicio) |
| `Last Sync ACCT: never` | La primera sincronizacion de referencia aun no ha ocurrido |

> Despues de unos minutos, vuelva a ejecutar `agent.exe status`. Los valores de `Last CONTEO GL` y `Last Sync` cambiaran, indicando que la sincronizacion esta en progreso.

### Desde el panel de servicios de Windows

1. Presione **Windows + R**, escriba `services.msc` y presione **Enter**.
2. Busque **Saicloud Agent** en la lista.
3. Verifique que el **Estado** sea **En ejecucion**.
4. Verifique que el **Tipo de inicio** sea **Automatico**.

---

## 8. Gestion del servicio

### Iniciar, detener y reiniciar

Desde `services.msc`:
1. Presione **Windows + R**, escriba `services.msc`, presione **Enter**.
2. Busque **Saicloud Agent**.
3. Clic derecho para ver las opciones: **Iniciar**, **Detener**, **Reiniciar**.

> **Nota:** Si recibe un archivo de configuracion actualizado de ValMen Tech, copie el nuevo `saicloud-agent.json` en `C:\SaicloudAgent\` y reinicie el servicio.

### Desinstalar el servicio

Si necesita eliminar el agente (por ejemplo, al migrar a otro equipo):

```
cd C:\SaicloudAgent
agent.exe uninstall
```

Resultado:

```
Saicloud Agent Windows Service removed successfully.
```

Esto elimina el servicio de Windows pero no borra la carpeta. Para eliminar completamente el agente, borre la carpeta `C:\SaicloudAgent\` despues de desinstalar.

---

## 9. Configuracion multi-empresa

Si en el mismo computador tiene varias bases de datos de Saiopen (empresas hermanas o sucursales), ValMen Tech le entregara un `saicloud-agent.json` con multiples conexiones ya configuradas.

Cada conexion tiene su propio `"id"` (`conn_001`, `conn_002`, etc.) y sincroniza de forma independiente. Si una empresa tiene un error de conexion, las demas siguen funcionando normalmente.

Para verificar el estado de una conexion especifica:

```
agent.exe test --id conn_002
```

Despues de agregar nuevas conexiones al archivo de configuracion, reinicie el servicio desde `services.msc` para que tome los cambios.

---

## 10. Solucion de problemas

### Error: No se puede conectar a Firebird

**Mensaje:** `Connection test FAILED: cannot connect to Firebird`

| Causa | Solucion |
|-------|----------|
| Servicio de Firebird no activo | Abra `services.msc`, busque **Firebird Server** o **Firebird Guardian** e inicielo |
| Ruta de base de datos incorrecta | Verifique la ruta en `saicloud-agent.json` — recuerde usar barras `/` en lugar de `\` |
| Credenciales de Firebird incorrectas | Las predeterminadas son usuario `SYSDBA`, contrasena `masterkey`. Consulte a su proveedor si fueron cambiadas |
| Puerto 3050 bloqueado | Si Firebird esta en otro equipo de la red, verifique que el puerto 3050 este abierto en el firewall |

### Error: No se puede conectar a la nube

**Mensaje:** `Connection test FAILED: cannot reach Saicloud API`

| Causa | Solucion |
|-------|----------|
| Sin conexion a internet | Abra el navegador y verifique que puede acceder a paginas web |
| Firewall o antivirus bloquea | Agregue `agent.exe` como excepcion en el firewall y antivirus |
| Proxy requerido | Configure el proxy en las opciones de internet de Windows |

### Error: Credenciales invalidas (Error 401)

**Mensaje:** `Connection test FAILED: 401 Unauthorized`

El token de autenticacion expiro o es invalido. Contacte a soporte de ValMen Tech para recibir un archivo `saicloud-agent.json` actualizado.

### El servicio no inicia

| Causa | Solucion |
|-------|----------|
| Carpeta de logs no existe | Verifique que existe `C:\SaicloudAgent\logs\`. Si no, creela |
| Archivo de configuracion danado | Ejecute `agent.exe serve` en CMD para ver el error. Si el archivo esta danado, solicite uno nuevo a ValMen Tech |
| Permisos insuficientes | Verifique que el agente tiene permisos de escritura en `C:\SaicloudAgent\` |

### Revisar los registros del agente

1. Abra el Explorador de archivos.
2. Navegue a `C:\SaicloudAgent\logs\`.
3. Abra `agent.log` con el Bloc de notas.
4. Busque lineas con la palabra `ERROR` para identificar el problema.

> **Para soporte:** Envie el archivo `agent.log` al equipo de ValMen Tech junto con la descripcion del problema.

---

## 11. Soporte tecnico

| Canal | Contacto |
|-------|----------|
| **Correo electronico** | soporte@valmentech.com |
| **WhatsApp** | Numero proporcionado en su contrato de servicio |

### Informacion util al contactar soporte

1. **Version del agente:** `agent.exe version` (ej: `saicloud-agent v1.0.0`)
2. **Mensaje de error:** Copie el texto exacto que aparece
3. **Archivo de logs:** `C:\SaicloudAgent\logs\agent.log`
4. **Version de Windows:** Clic derecho en **Este equipo** > **Propiedades**

---

## 12. Referencia rapida de comandos

> Todos los comandos deben ejecutarse desde `C:\SaicloudAgent\` en CMD o PowerShell abierto **como administrador**.

| Comando | Descripcion |
|---------|-------------|
| `agent.exe test --id conn_001` | Prueba la conexion indicada |
| `agent.exe install` | Instala el agente como servicio de Windows |
| `agent.exe uninstall` | Desinstala el servicio de Windows |
| `agent.exe status` | Muestra el estado de todas las conexiones |
| `agent.exe serve` | Inicia la sincronizacion en modo manual (sin servicio, util para diagnostico) |
| `agent.exe version` | Muestra la version del agente |
| `agent.exe help` | Muestra todos los comandos disponibles |

---

## Guia para ValMen Tech — Preparacion del paquete de instalacion

> Esta seccion es interna. No se entrega al cliente.

### Como preparar el zip para un cliente nuevo

1. Copie `saicloud-agent.example.json` y renombrelo a `saicloud-agent.json`.
2. Obtenga el **Company ID** y el **Agent Token** del cliente desde Saicloud:
   - Ingrese a Saicloud con su cuenta de superadmin.
   - Vaya a **Administracion → Empresa → Integracion** (en la cuenta del cliente, o desde el panel de tenants).
   - Copie el **Company ID** y el **Token del Agente** que aparecen en esa pantalla.
   
   > El token se genera automaticamente al crear el tenant. Si el tenant ya existe y no tiene token, creelo desde el panel admin: **Administracion → Tenants → [seleccionar empresa] → Tokens del agente → Nuevo token**.

3. Complete los campos del cliente en `saicloud-agent.json`:
   - `connections[0].name` — nombre de la empresa
   - `connections[0].firebird.database` — ruta del .FDB (confirmar con el cliente)
   - `connections[0].saicloud.company_id` — **Company ID** copiado en el paso 2
   - `connections[0].saicloud.agent_token` — **Token del Agente** copiado en el paso 2
4. Complete las credenciales SQS (ya estan configuradas globalmente — no cambiar a menos que roten):
   - `sqs.secret_access_key` — el Secret Key del usuario `saicloud-agent` (guardado en la boveda)
5. Cree el zip con los dos archivos: `agent.exe` + `saicloud-agent.json`.
6. Entregue el zip al cliente por canal seguro.

### Datos SQS del agente (configuracion global — igual para todos los clientes)

| Campo | Valor |
|-------|-------|
| `transport` | `sqs` |
| `sqs.access_key_id` | `AKIAXBIY476C5BT4V2P4` |
| `sqs.region` | `us-east-1` |
| `sqs.queue_url` | `https://sqs.us-east-1.amazonaws.com/483772923781/saicloud-to-cloud-prod` |
| `sqs.secret_access_key` | En la boveda de contrasenas de ValMen Tech |

---

*ValMen Tech — Saicloud*
*Manual version 1.1.0 — Abril 2026*
