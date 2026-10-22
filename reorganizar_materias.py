from web import app, db, Cuatrimestre, Materia, Usuario

ESTRUCTURA = {
    "1er Cuatrimestre": {
        "comun": [
            "Inglés I", "Desarrollo Humano y Valores", "Fundamentos Matemáticos",
            "Física", "Fundamentos de Programación", "Fundamentos de Redes",
            "Comunicación y Habilidades Digitales"
        ]
    },
    "2do Cuatrimestre": {
        "comun": [
            "Inglés II", "Habilidades Socioemocionales y Manejo de Conflictos",
            "Cálculo Diferencial", "Probabilidad y Estadística",
            "Programación Estructurada", "Conmutación y Enrutamiento de Redes",
            "Sistemas Operativos"
        ]
    },
    "3er Cuatrimestre": {
        "comun": [
            "Inglés III", "Desarrollo del Pensamiento y Toma de Decisiones",
            "Cálculo Integral", "Tópicos de Calidad para el Diseño de Software",
            "Programación Orientada a Objetos", "Base de Datos",
            "Proyecto Integrador I"
        ]
    },
    "4to Cuatrimestre": {
        "ia": [
            "Inglés IV", "Ética Profesional", "Cálculo de Varias Variables",
            "Aprendizaje Profundo Deep Learning", "Sistemas de Optimización Inteligente",
            "Metodología No Code", "Sistemas Embebidos"
        ],
        "redes": [
            "Inglés IV", "Ética Profesional", "Cálculo de Varias Variables",
            "Escalabilidad de Redes", "Centro de Datos",
            "Infraestructura de Redes de Datos", "Programación de Redes"
        ]
    },
    "5to Cuatrimestre": {
        "ia": [
            "Inglés V", "Liderazgo de Equipos de Alto Desempeño",
            "Ecuaciones Diferenciales", "Minería de Datos",
            "Aprendizaje de Máquina", "Fundamentos de Visión por Computadora",
            "Proyecto Integrador II"
        ],
        "redes": [
            "Inglés V", "Liderazgo de Equipos de Alto Desempeño",
            "Ecuaciones Diferenciales", "Conexión de Redes WAN",
            "Cómputo en la Nube", "Seguridad en Redes", "Proyecto Integrador II"
        ]
    },
    "6to Cuatrimestre": {
        "ia": ["Estadía — Inteligencia Artificial"],
        "redes": ["Estadía — Infraestructura de Redes Digitales"]
    },
    "7mo Cuatrimestre": {
        "ia": [
            "Inglés VI", "Habilidades Gerenciales", "Formulación de Proyectos de Tecnología",
            "Fundamentos de Inteligencia Artificial",
            "Ética y Legislación en Tecnologías de Información",
            "Optativa I (MT)", "Seguridad Informática"
        ],
        "redes": [
            "Inglés VI", "Habilidades Gerenciales", "Formulación de Proyectos de Tecnología",
            "Fundamentos de Inteligencia Artificial",
            "Ética y Legislación en Tecnologías de Información",
            "Optativa I (IAW)", "Seguridad Informática"
        ]
    },
    "8vo Cuatrimestre": {
        "ia": [
            "Inglés VII", "Electrónica Digital", "Gestión de Proyectos de Tecnología",
            "Programación para Inteligencia Artificial",
            "Optativa II (AR)", "Informática Forense", "Administración de Servidores"
        ],
        "redes": [
            "Inglés VII", "Electrónica Digital", "Gestión de Proyectos de Tecnología",
            "Programación para Inteligencia Artificial",
            "Optativa II (ARE)", "Informática Forense", "Administración de Servidores"
        ]
    },
    "9no Cuatrimestre": {
        "ia": [
            "Inglés VIII", "Internet de las Cosas", "Evaluación de Proyectos de Tecnología",
            "Ciencia de Datos", "Optativa III (SI)", "Tecnologías Disruptivas",
            "Proyecto Integrador II"
        ],
        "redes": [
            "Inglés VIII", "Internet de las Cosas", "Evaluación de Proyectos de Tecnología",
            "Ciencia de Datos", "Optativa III (AAS)", "Tecnologías Disruptivas",
            "Proyecto Integrador II"
        ]
    },
}

with app.app_context():
    print("⚠️  Limpiando estructura...")
    Usuario.query.update({Usuario.cuatrimestre_id: None})
    db.session.commit()
    Materia.query.delete()
    db.session.commit()
    Cuatrimestre.query.delete()
    db.session.commit()
    print("   ✓ Limpieza completada")

    print("\n📚 Creando nueva estructura...")
    total = 0

    for cuatri_nombre, especialidades in ESTRUCTURA.items():
        if 'comun' in especialidades:
            # Cuatrimestre común — un solo cuatrimestre
            cuatri = Cuatrimestre(nombre=cuatri_nombre)
            db.session.add(cuatri)
            db.session.flush()
            for m in especialidades['comun']:
                db.session.add(Materia(nombre=m, cuatrimestre_id=cuatri.id))
                total += 1
            print(f"   ✓ {cuatri_nombre} — Común ({len(especialidades['comun'])} materias)")
        else:
            # Cuatrimestre con especialidades — crear dos
            for esp_key, materias in especialidades.items():
                label = "Inteligencia Artificial" if esp_key == "ia" else "Infraestructura de Redes Digitales"
                nombre = f"{cuatri_nombre} — {label}"
                cuatri = Cuatrimestre(nombre=nombre)
                db.session.add(cuatri)
                db.session.flush()
                for m in materias:
                    db.session.add(Materia(nombre=m, cuatrimestre_id=cuatri.id))
                    total += 1
                print(f"   ✓ {nombre} ({len(materias)} materias)")

    db.session.commit()
    cuatris = Cuatrimestre.query.count()
    print(f"\n✅ Listo — {cuatris} cuatrimestres, {total} materias")
