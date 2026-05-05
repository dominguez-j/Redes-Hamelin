# TP N° 1. File Transfer

Implementación de una aplicación de red de arquitectura cliente-servidor para carga y descarga de archivos binarios, con una implementación de un protocolo RDT sobre UDP

Grupo 6:
 - Daiana Aldrey - 110624
 - Dídimo Paez - 98910
 - Jonathan Dominguez - 110057
 - Mateo Godoy Serrano - 110912
 - Michelle Chen - 105506

# Ejecución

Primero hay que crear el entorno:

`python3 -m venv venv`

`source venv/bin/activate`

Dentro de la carpeta src:

## Server

#### Para ver los comandos:

`python3 -m start_server -h`

#### Uso:

`python3 -m start_server [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]`

#### Ej:

`python3 -m start_server -v -H 10.0.0.1 -p 9001 -s ../storage_server`

## Client

### Subida

#### Para ver los comandos:

`python3 -m upload -h`

#### Uso:

`python3 -m upload [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME] [-r protocol]`

#### Ej:

`python3 -m upload -v -H 10.0.0.1 -p 9001 -s ../examples -n prueba-a.txt -r sr`

### Descarga

#### Para ver los comandos:

`python3 -m download -h`

#### Uso:

`python3 -m download [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME] [-r protocol]`

#### Ej:

`python3 -m download -v -H 10.0.0.1 -p 9001 -d ../storage_client -n prueba-a.txt -r sr`

## Plugin de Wireshark

[Ir a la documentación del plugin de Wireshark](https://github.com/Mateo-Serrano-2004/TP-Redes-RDTP/blob/develop/wireshark/DOCS.md)

# Instalación mininet

Se instala con:

`sudo apt install mininet`

`sudo apt install -y xterm tcpdump iperf3 net-tools`

# Correr con mininet

`sudo mn --topo single,3 --mac --link tc,loss=10 --xterms`

Para habilitar el copy-paste en xterms hay que hacer:

1) En consola poner:  `nano ~/.Xresources`
2) Pegar esto en ese archivo:

    `XTermselectToClipboard: true
    XTermtranslations: #override \n\
    Ctrl Shift <Key> C: copy-selection(CLIPBOARD) \n\
    Ctrl Shift <Key> V: insert-selection(CLIPBOARD)`

3) Luego hacer: `Ctrl + O -> Enter -> Ctrl + X`
4) En consola poner: `xrdb -merge ~/.Xresources`
