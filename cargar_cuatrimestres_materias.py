# cargar_cuatrimestres_materias.py

from web import db, app, Cuatrimestre, Materia

with app.app_context():
    # Borrar materias y cuatrimestres existentes
    db.session.query(Materia).delete()
    db.session.query(Cuatrimestre).delete()
    db.session.commit()

    # Datos de cuatrimestres y materias
    datos = [
        ("Primer Cuatrimestre", [
            "Inglés I", "Desarrollo Humano y Valores", "Fundamentos Matemáticos",
            "Fundamentos de Redes", "Física", "Fundamentos de Programación", "Comunicación y Habilidades Digitales"
        ]),
        ("Segundo Cuatrimestre", [
            "Inglés II", "Habilidades Socioemocionales y Manejo de Conflictos", "Cálculo Diferencial",
            "Conmutación y Enrutamiento de Redes", "Probabilidad y Estadística", "Programación Estructurada", "Sistemas Operativos"
        ]),
        ("Tercer Cuatrimestre", [
            "Inglés III", "Desarrollo del Pensamiento y Toma de Decisiones", "Cálculo Integral",
            "Tópicos de Calidad para el Diseño de Software", "Bases de Datos", "Programación Orientada a Objetos", "Proyecto Integrador I"
        ]),
        ("Cuarto Cuatrimestre", [
            "Inglés IV", "Ética Profesional", "Cálculo de Varias Variables",
            "Aprendizaje Profundo (Deep Learning)", "Metodología con Enfoque de Proyectos",
            "Sistemas de Optimización Inteligente", "Sistemas Embebidos"
        ]),
        ("Quinto Cuatrimestre", [
            "Inglés V", "Liderazgo de Equipos de Alto Rendimiento", "Ecuaciones Diferenciales",
            "Minería de Datos", "Aprendizaje de Máquina", "Fundamentos de Visión por Computadora", "Proyecto Integrador II"
        ]),
        ("Sexto Cuatrimestre", [
            "Estadía (600 HRS)"
        ]),
        ("Séptimo Cuatrimestre", [
            "Inglés VI", "Habilidades Gerenciales", "Formulación de Proyectos de Tecnología",
            "Fundamentos de Inteligencia Artificial", "Legislación en Tecnologías de la Información",
            "Optativa I", "Seguridad Informática"
        ]),
        ("Octavo Cuatrimestre", [
            "Inglés VII", "Electrónica Digital", "Gestión de Proyectos de Tecnología",
            "Programación para Inteligencia Artificial", "Administración de Servidores",
            "Optativa II", "Informática Forense"
        ]),
        ("Noveno Cuatrimestre", [
            "Inglés VIII", "Internet de las Cosas", "Evaluación de Proyectos de Tecnología",
            "Ciencia de Datos", "Tecnologías Disruptivas", "Optativa III", "Proyecto Integrador III"
        ]),
        ("Décimo Cuatrimestre", [
            "Estadía (600 HRS)"
        ]),
    ]

    # Insertar los datos
    for nombre_cuatrimestre, materias in datos:
        cuatrimestre = Cuatrimestre(nombre=nombre_cuatrimestre)
        db.session.add(cuatrimestre)
        db.session.commit()  # Guardamos para tener el ID

        for nombre_materia in materias:
            materia = Materia(nombre=nombre_materia, cuatrimestre_id=cuatrimestre.id)
            db.session.add(materia)

    db.session.commit()

    print("✅ ¡Todos los cuatrimestres y materias fueron cargados correctamente!")

