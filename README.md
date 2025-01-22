
# Yeeko chat Flow

Yeeko Chat Flow es un sistema para enviar mensajes a través de plataformas de mensajería instantánea como WhatsApp, Messenger o Telegram, altamente flexible para adaptarse a múltiples necesidades mientras se mantiene una misma estructura para los flujos conversacionales. Con una estructura basada en una [arquitectura de capas](https://github.com/yeeko-org/yeeko-flows/wiki/Arquitectura-de-Capas) y altamente tipada.

Una de las claves principales del sistema son sus **modelos genericos** de mensajes de entrada y salida, lo que permite centrarse en el flujo y procesamiento conversacional, mientas los interpretes especializados en cada plataforma los transforman

    json -> request_model_class
    response_model_class -> json

## Flow

El flujo general se puede dividir en 4 etapas:

**ManagerFlow:** No es una etapa en sí, sino el orquestador donde se gestionan y almacenan los datos.

1. **Webhook:** Punto mas externo, el acceso público donde llegarán los mensajes que serán enviados al manejador de flujos.

2. **Request:** Se encarga de reorganizar los diccionarios en clases instanciadas, con la intención de tener una estructura homologada, donde, sin importar el origen de los datos, siempre se mantenga la misma estructura solicitante. También se encarga de verificar la existencia de usuarios o la creación de nuevos usuarios, y realiza el registro histórico de entrada.

3. **Process:** Esta etapa se encarga de procesar los mensajes entrantes en procesadores especializados para cada situación, desde los más simples, como los procesadores de texto, hasta los más complejos, como los botones que refieren a destinos con reglas de visualización.

4. **Response:** Se encarga de recibir los mensajes resultantes de los procesadores en forma de modelos generales y convertirlos en diccionarios especializados para las distintas plataformas. La estructura está pensada para calcular primero todos los mensajes y, en la etapa final del flujo, enviar todos los diccionarios a las plataformas. En esta última etapa se registra también la interacción de salida y sus disparadores.

![main flow](https://github.com/user-attachments/assets/18861e7d-699f-4930-9e19-ed4ec86b73c1)
