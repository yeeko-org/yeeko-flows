Justificacion, se separo la logica de mensajeria interpretativa, la interpretacion de datos en formato diccionario a instancias de objetos BaseModel y de nuevo a formato diccionario, la implementacion de las especialidades complicaban la documentacion y mantenimieno del servicio, por lo que se decicio separarlo en una libreria con  las clases abstractas para request y responce, y los modelos de entrada y salidad de datos,  tambien la implementacion para la mensajeria de whatsapp



para la implementacion en Flow se realizaron algunas modificaciones la siguiente grafica representa como estan relacionadas las clases

Clases Abstractas y modelos base: Declaran los metodos, tipos de parametros y tipos de datos de salida esperados, asi como las funciones mas generales, tyambien los modelos representativos de los datos de entrada y salida genericos

Mensajegira Whatsapp: Esta libreria implementa todos los metodos abstractos para que se puedan interpretar datos dictos del webhook configurado en apps de meta y mandar mensajes a sus servicios.

Sobreescritura en flow: La libreria esta desacoplada del sistema principal, por lo que los metodos relacionados a los modelos deben reinplementarse para gestionar los datos de la infraestructura

este desacoplamiento mejora el mantenimiento


cambiar el enfoque por un interprete mas simple sin necesidad de sobreescribir clases para que pueda efectuarse mas facil el mantenimiento