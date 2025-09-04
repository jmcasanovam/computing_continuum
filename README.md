# Infraestructura de Microservicios para el desarrollo de Sistemas Inteligentes Autoadaptativos bajo el paradigma Computing Continuum

Este trabajo presenta el diseño e implementación de una infraestructura de microservicios bajo el paradigma de la Continuidad Computacional (Computing Continuum), orientada a la creación de sistemas inteligentes autoadaptativos. En este trabajo, se integran dispositivos IoT, nodos en el borde, niebla y nube para distribuir dinámicamente las cargas de procesamiento, optimizando así la eficiencia energética, la latencia y la escalabilidad del sistema.

El sistema que se desarrolla permite a los usuarios enviar datos fisiológicos desde dispositivos inteligentes, como pulseras o relojes, que son procesados
para predecir su estado o actividad (por ejemplo, “durmiendo”, “sedentario” o “activo”). El sistema se apoya en algoritmos de aprendizaje automático para realizar inferencias personalizadas para cada usuario en los nodos de borde, mientras que los modelos globales se entrenan y actualizan en la nube con datos procedentes de todos los usuarios.

La infraestructura se gestiona de forma autoadaptativa mediante el ciclo MAPE-K, aplicado sobre los recursos del sistema. Cada nodo exporta métricas de su estado (carga, disponibilidad, rendimiento). Posteriormente, a partir de los datos de todos los nodos, un microservicio analiza posibles desviaciones, planifica ajustes y los ejecuta en tiempo real, permitiendo una orquestación dinámica y eficiente de los microservicios desplegados.

Este trabajo intenta contribuir al avance en la gestión inteligente de sistemas distribuidos, y pretende explorar las bases para futuras aplicaciones en ámbitos como la salud conectada.


---

## Memoria del Proyecto

Para una visión completa sobre los fundamentos teóricos, la arquitectura, la implementación y el análisis de resultados, consulta el documento principal del proyecto:

**[TFG - Jose Manuel Casanova Martinez](./TFG-Jose-Manuel-Casanova-Martinez.pdf)**

---
