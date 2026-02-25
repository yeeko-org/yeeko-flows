# Arquitectura de Capas

La organización del sistema está basada en una arquitectura de capas, con una variante donde los modelos de Django realizan la función de modelos de dominio. Esto tiene como objetivo simplificar la arquitectura, aunque separa el código en capas especializadas.

- **Presentación:** Webhooks, APIs y Django-admin.
- **Interfaz:** Implementación de servicios para comportamientos específicos de cada plataforma de mensajería.
- **Servicios:** Clases y lógicas del sistema como FlowManager, procesadores y servicios, incluyendo notificaciones.
- **Infraestructura:** Modelos de datos basados en Django, que cumplen la función de persistencia en la base de datos.

Siguiendo esta arquitectura de capas, las importaciones solo se permiten hacia el interior de las capas, nunca en sentido contrario, y las operaciones deben cumplir con el propósito de la capa.

## Infraestructura

En esta capa se declaran únicamente clases del tipo `models.Model` clásicos de Django, y pueden incluir operadores siempre que solo involucren procesamiento y cálculos de datos.

## Servicios

En esta sección se declaran e implementan la mayoría de las funciones generales, dejando secciones con declaraciones abstractas para su implementación particular en las diferentes plataformas.

### FlowManager

Esta clase es responsable de manejar el flujo completo de trabajo, comenzando con la entrada de datos y culminando con el envío de mensajes. Maneja tres secciones principales:

- Request
- Process
- Response

### Request

La clase **Request** se encarga de homologar los diccionarios particulares de cada plataforma en una estructura uniforme, comprobar y obtener las instancias y, para los nuevos miembros, crear todos los registros necesarios. En la capa de servicios, el ordenamiento de datos se declara de forma abstracta para su futura implementación. Su función principal culmina con la lista de instancias **InputAccount**.

    InputAccount:
        account: Account
        members: List[InputSender]
            member: MemberAccount
            messages: List[
                TextMessage |
                InteractiveMessage |
                EventMessage |
                MediaMessage
            ]
        statuses: List[EventMessage]
        raw_data: dict
        api_record: ApiRecord

### Process

Cada **InputAccount** se considera una aplicación diferente, y de estas, cada miembro de su lista de miembros se procesa individualmente sin afectar a los demás.

Los mensajes de cada **InputSender** también se procesan individualmente, pero es necesario discernir acciones más precisas para los casos donde lleguen múltiples mensajes, ya que lo habitual es una sola interacción del usuario a la vez.

La lista de mensajes está compuesta por varias instancias homologadas que, independientemente de su origen, siempre tendrán la misma estructura de clase, denominadas `request.message_model`. Todos tienen como base común la clase `MessageBase`.

Consulta los detalles de cada tipo de mensaje:

    MessageBase:
        message_id: str
        timestamp: int
        context_id: str

Además, los mensajes como **TextMessage**, **InteractiveMessage** y **MediaMessage** heredan las operaciones de interacción para obtener la referencia de origen y la interacción detonante.

    InteractionMessage(MessageBase):
        interaction: Optional[Interaction]

Junto con el mensaje se envía una nueva instancia de **Response**. El **FlowManager** tiene una referencia a esta instancia en una lista, con un **Response** por cada mensaje.

Al procesarse, los mensajes se distinguen por su tipo de clase y se envían al procesador correspondiente:

- **TextMessage** → TextMessageProcessor
- **InteractiveMessage** → InteractiveProcessor
- **EventMessage** → StateProcessor
- **MediaMessage** → MediaProcessor

_Consulta los detalles del modelo Message para más información._

Dentro de cada procesador, se enviará a otros procesadores dependiendo del contenido del mensaje y el flujo. Ejemplo:

    InteractiveMessage -> InteractiveProcessor -> BehaviorProcessor -> PieceProcessor -> FragmentProcessor

_Consulta la sección de procesadores para más información._

### Response

De manera simplificada, **Response** se encarga de enviar mensajes finales a las plataformas y, en segundo plano, registrar las interacciones y seguimientos.

La instancia de **Response** que se envía a los procesadores para cada mensaje de entrada tiene la función de almacenar los mensajes generados por los procesadores, realizar el seguimiento de errores y el envío final de mensajes.

Similar a los modelos **MessageBase** de **Request**, **Response** maneja una serie de estructuras estandarizadas que, con cada implementación, se adaptan a la estructura JSON de cada plataforma.

    Message:
        body: str
        header: Optional[str | Header] = None
        footer: Optional[str] = None
        fragment_id: Optional[int] = None

Para una mejor administración de los mensajes, en lugar de enviarlos uno por uno al instante, se acumulan en una lista que es enviada en su totalidad en un único paso, una vez que todos los mensajes de entrada han sido procesados.

    Response.message_list = [] --> Processor --> Add message --> End Processor --> Response.message_list = [Message, Message]

## Interfaz

En esta capa se implementan las funciones y formatos específicos de cada plataforma. Dado que la plataforma utiliza modelos estándar, se requiere que la información de entrada se transforme al formato estándar y que los mensajes también se transformen a la estructura JSON esperada por cada plataforma.

No todos los servicios requieren estas particularidades, solo aquellos que manipulan datos específicos de cada plataforma.

## Presentación

Esta capa es el contacto directo con el usuario, donde se implementan los webhooks, el administrador y las APIs.
