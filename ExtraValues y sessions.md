# Extras y  sesiones

Los Extras son los registros de valores agregados a un usuario, para el registro y control de datos, metadata, información de formularios y encuestas, o variables de flujos.

## Session

Las sesiones son una versión de las variables por usuario, un controlador global para todos los valores bajo el control de sesión del mismo usuario, y solo se puede indicar activa una a la vez.

    Session:
        member
        number(index)
        active

El comportamiento esperado es acceder a la información por la sesión activa y no por el índice.

## Extra

Es la declaración de la variable y su comportamiento esperado, ligados a un space.

    Extra:
        name
        description
        deleted

        classify
        space
        flow

        format

        has_session
        controller

- classify: es el clasificador para organizar, estilizar  o limitar la vista
- space: La pertenencia a un Space, permite manejar el mismo nombre entre distintos espacios.
- flow: el agrupador para indicar que es parte de un conjunto de mensajes.

### Format

Format declara el tipo de valor esperado y su comportamiento, por defecto str

- int: valores de tipo numérico que pueden usar operadores como contadores, adiciones y sustracciones.
- json: diccionarios complejos
- cv: pendiente de detalles

### Controladores y sesiones

Para ciertos casos, se requiere repetibilidad de los extras con distintos valores por usuario, por ejemplo, cuando se rellena el mismo formulario, pero para distintos propósitos, conservando las respuestas para cada momento y una forma de situarnos en ese momento

Se diseño 2 niveles de profundidad para este propósito, bajo el control de

- has_session: indica si esta bajo el control se Session, un controlador global por usuario, donde existe almenos una y solo se permite una activa al mismo tiempo. El registro de valores bajo este control se registran con el activo al momento.

- controler: Control numérico para permitir la repetibilidad por Extra, similar a una lista y este valor indica el índice.

#### Niveles de valor

- Nivel 0 (Extra, valor): Registro clásico de un valor por extra.
- Nivel 1 (ControlerValue, Extra, Value): Valor variable con acceso por el índice del controlador.
- Nivel 1 (Session, Extra, Value): Valor variable por la relacion con la sesión, su acceso esta restringido a la sesión activa.
- Nivel 2 (Session, ControlerValue, Extra, Value): La combinación de los 2 controles de nivel

# ExtraValue

El valor registrado a un usuario por medio de Member

    ExtraValue
        member
        extra
        value

        session
        controller_value
        active

        interactions
        modified

Su value esta controlado por el extra.format para su comportamiento

- controller_value: es otro ExtraValues de format int que puede repetir su nombre y no es de acceso publico, almacena el índice y un indicativo active, que no limita el acceso, pero si indica con que versión se esta trabajando al momento

- interactions: el registro de que interacciones han afectado el value

## Ejemplos

### Valores de Nivel 0

Extra:

    {
        "pk": 1
        "name": "nombre",
        "format": "str"
    }

ExtraValue:

    {
        "pk": 11,
        "member__uid": "123456"
        "extra__pk" 1,
        "valor": "Ricardo"
    }

### Valores nivel 1, Session

Sessions

    [
        {
            "pk": 111,
            "member__uid": "123456",
            "active": true,
            "number": 1
        },
        {
            "pk": 222,
            "member__uid": "123456",
            "active": false,
            "number": 2
        }
    ]

Extra:

    {
        "pk": 2
        "name": "escuela",
        "format": "str"
    }

ExtraValue:

        [
            {
                "pk": 12,
                "member__uid": "123456"
                "extra__pk" 2,
                "session": 111,
                "valor": "UNAM"
            },
            {
                "pk": 13,
                "member__uid": "123456"
                "extra__pk" 2,
                "session": 222,
                "valor": "BUAP"
            }
        ]

### Valores nivel 1, Controler

Extra:

    [
        {
            "pk": 3
            "name": "medicamento",
            "format": "str"
        },
        {
            "pk": 4
            "name": "medicamento__controler",
            "format": "cv"
        }
    ]

ExtraValue:

    # control_values
    [
        {
            "pk": 14,
            "member__uid": "123456"
            "extra__pk" 4,
            "extra__name": "medicamento__controler",
            "valor": 1,
            "active": true
        },
        {
            "pk": 16,
            "member__uid": "123456"
            "extra__pk" 4,
            "extra__name": "medicamento__controler",
            "valor": 2,
            "active": false
        }
    ]

    # values
    [
        {
            "pk": 15,
            "member__uid": "123456"
            "extra__pk" 3,
            "extra__name": "medicamento",
            "controller_value": 14,
            "valor": "Ibuprofeno"
        },
        {
            "pk": 17,
            "member__uid": "123456"
            "extra__pk" 3,
            "extra__name": "medicamento",
            "controller_value": 16,
            "valor": "parasetamol"
        }
    ]

### Valores nivel 2

Sessions

    [
        {
            "pk": 111,
            "member__uid": "123456",
            "active": true,
            "number": 1
        },
        {
            "pk": 222,
            "member__uid": "123456",
            "active": false,
            "number": 2
        }
    ]

Extra:

    [
        {
            "pk": 3
            "name": "medicamento",
            "format": "str"
        },
        {
            "pk": 4
            "name": "medicamento__controler",
            "format": "cv"
        }
    ]

ExtraValue:

    # control_values
    [
        {
            "pk": 14,
            "member__uid": "123456"
            "extra__pk" 4,
            "extra__name": "medicamento__controler",
            "valor": 1,
            "active": true
        },
        {
            "pk": 16,
            "member__uid": "123456"
            "extra__pk" 4,
            "extra__name": "medicamento__controler",
            "valor": 2,
            "active": false
        }
    ]

    # values
    [
        {
            "pk": 15,
            "member__uid": "123456"
            "extra__pk" 3,
            "extra__name": "medicamento",
            "controller_value": 14,
            "session": 111,
            "valor": "Ibuprofeno"
        },
        {
            "pk": 17,
            "member__uid": "123456"
            "extra__pk" 3,
            "extra__name": "medicamento",
            "controller_value": 16,
            "session": 111,
            "valor": "parasetamol"
        },
        {
            "pk": 15,
            "member__uid": "123456"
            "extra__pk" 3,
            "extra__name": "medicamento",
            "controller_value": 14,
            "session": 222,
            "valor": "naproxeno"
        },
        {
            "pk": 17,
            "member__uid": "123456"
            "extra__pk" 3,
            "extra__name": "medicamento",
            "controller_value": 16,
            "session": 222,
            "valor": "penicilina"
        }
    ]
