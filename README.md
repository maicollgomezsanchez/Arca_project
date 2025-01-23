# Control Interface Project

Este proyecto está diseñado con Kivy, una librería Python para desarrollar aplicaciones con interfaces gráficas. Se centra en un sistema de control con múltiples modos (Manual, Semi, Auto) y una serie de botones para manejar el tiempo de viaje, el tiempo de espera y activar funciones especiales como un "buzzer" y "comer fichas". 

## Descripción del Proyecto

Este sistema permite gestionar diferentes modos de operación (manual, semi, automático) mediante un conjunto de botones. Además, proporciona control sobre el tiempo de viaje y el tiempo de espera, y permite activar una serie de botones especiales como el buzzer. La interfaz gráfica está construida en Kivy utilizando el lenguaje de diseño KV para definir el layout.

### Funcionalidades:
1. **Modos de Operación**:
   - **Manual**: Operación controlada manualmente por el usuario.
   - **Semi**: Semi-automatizado con intervención del usuario.
   - **Auto**: Completamente automatizado.

2. **Control de Tiempos**:
   - Incremento y decremento del tiempo de viaje y el tiempo de espera mediante los botones "+" y "-".

3. **Botones Especiales**:
   - Activar "Descarga" con el botón "ACTIVAR DESCARGA".
   - "Comer Fichas" y activar el buzzer.

4. **Estado del Sistema**:
   - Los botones de "START", "PAUSE" y "STOP" permiten controlar el estado del sistema.

### Estructura de Archivos:
1. **main.py**: Contiene el código Python que maneja la lógica de la aplicación.
2. **interface.kv**: Define el diseño y la apariencia de la interfaz de usuario utilizando el lenguaje KV de Kivy.

---

## Requisitos

Para ejecutar este proyecto, necesitas tener instaladas las siguientes dependencias:

- **Python** 3.x
- **Kivy** 2.x

Puedes instalar Kivy usando pip:

```bash
pip install kivy
