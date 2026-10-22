from web import app, db, Cuatrimestre, Materia, Tema, Archivo, Comentario

# ══════════════════════════════════════════════
# ESTRUCTURA COMPLETA DE MATERIAS UPTI
# ══════════════════════════════════════════════

ESTRUCTURA = {

    # ── CICLO COMÚN (ambas especialidades) ──
    "1er Cuatrimestre": [
        "Inglés I", "Desarrollo Humano y Valores", "Fundamentos Matemáticos",
        "Física", "Fundamentos de Programación", "Fundamentos de Redes",
        "Comunicación y Habilidades Digitales"
    ],
    "2do Cuatrimestre": [
        "Inglés II", "Habilidades Socioemocionales y Manejo de Conflictos",
        "Cálculo Diferencial", "Probabilidad y Estadística",
        "Programación Estructurada", "Conmutación y Enrutamiento de Redes",
        "Sistemas Operativos"
    ],
    "3er Cuatrimestre": [
        "Inglés III", "Desarrollo del Pensamiento y Toma de Decisiones",
        "Cálculo Integral", "Tópicos de Calidad para el Diseño de Software",
        "Programación Orientada a Objetos", "Base de Datos",
        "Proyecto Integrador I"
    ],

    # ── INTELIGENCIA ARTIFICIAL ──
    "4to Cuatrimestre — IA": [
        "Inglés IV", "Ética Profesional", "Cálculo de Varias Variables",
        "Aprendizaje Profundo Deep Learning", "Sistemas de Optimización Inteligente",
        "Metodología No Code", "Sistemas Embebidos"
    ],
    "5to Cuatrimestre — IA": [
        "Inglés V", "Liderazgo de Equipos de Alto Desempeño",
        "Ecuaciones Diferenciales", "Minería de Datos",
        "Aprendizaje de Máquina", "Fundamentos de Visión por Computadora",
        "Proyecto Integrador II"
    ],
    "6to Cuatrimestre — IA": [
        "Estadía — Técnico Superior Universitario en Inteligencia Artificial"
    ],
    "7mo Cuatrimestre — IA": [
        "Inglés VI", "Habilidades Gerenciales", "Formulación de Proyectos de Tecnología",
        "Fundamentos de Inteligencia Artificial",
        "Ética y Legislación en Tecnologías de Información",
        "Optativa I (MT)", "Seguridad Informática"
    ],
    "8vo Cuatrimestre — IA": [
        "Inglés VII", "Electrónica Digital", "Gestión de Proyectos de Tecnología",
        "Programación para Inteligencia Artificial",
        "Optativa II (AR)", "Informática Forense", "Administración de Servidores"
    ],
    "9no Cuatrimestre — IA": [
        "Inglés VIII", "Internet de las Cosas", "Evaluación de Proyectos de Tecnología",
        "Ciencia de Datos", "Optativa III (SI)", "Tecnologías Disruptivas",
        "Proyecto Integrador II"
    ],

    # ── INFRAESTRUCTURA DE REDES DIGITALES ──
    "4to Cuatrimestre — Redes": [
        "Inglés IV", "Ética Profesional", "Cálculo de Varias Variables",
        "Escalabilidad de Redes", "Centro de Datos",
        "Infraestructura de Redes de Datos", "Programación de Redes"
    ],
    "5to Cuatrimestre — Redes": [
        "Inglés V", "Liderazgo de Equipos de Alto Desempeño",
        "Ecuaciones Diferenciales", "Conexión de Redes WAN",
        "Cómputo en la Nube", "Seguridad en Redes", "Proyecto Integrador II"
    ],
    "6to Cuatrimestre — Redes": [
        "Estadía — Técnico Superior Universitario en Infraestructura de Redes Digitales"
    ],
    "7mo Cuatrimestre — Redes": [
        "Inglés VI", "Habilidades Gerenciales", "Formulación de Proyectos de Tecnología",
        "Fundamentos de Inteligencia Artificial",
        "Ética y Legislación en Tecnologías de Información",
        "Optativa I (IAW)", "Seguridad Informática"
    ],
    "8vo Cuatrimestre — Redes": [
        "Inglés VII", "Electrónica Digital", "Gestión de Proyectos de Tecnología",
        "Programación para Inteligencia Artificial",
        "Optativa II (ARE)", "Informática Forense", "Administración de Servidores"
    ],
    "9no Cuatrimestre — Redes": [
        "Inglés VIII", "Internet de las Cosas", "Evaluación de Proyectos de Tecnología",
        "Ciencia de Datos", "Optativa III (AAS)", "Tecnologías Disruptivas",
        "Proyecto Integrador II"
    ],
}

with app.app_context():
    print("⚠️  Eliminando estructura actual...")

    # Eliminar en orden correcto para respetar foreign keys
    from sqlalchemy import text
    
    # Borrar reacciones, archivos, comentarios, temas
    try:
        from web import Reaccion
        Reaccion.query.delete()
        db.session.commit()
        print("   ✓ Reacciones eliminadas")
    except:
        pass

    Archivo.query.delete()
    db.session.commit()
    print("   ✓ Archivos eliminados")

    Comentario.query.delete()
    db.session.commit()
    print("   ✓ Comentarios eliminados")

    Tema.query.delete()
    db.session.commit()
    print("   ✓ Temas eliminados")

    Materia.query.delete()
    db.session.commit()
    print("   ✓ Materias eliminadas")

    # Limpiar cuatrimestre_id de usuarios antes de borrar cuatrimestres
    from web import Usuario
    Usuario.query.update({Usuario.cuatrimestre_id: None})
    db.session.commit()
    print("   ✓ Cuatrimestre de usuarios limpiado")

    Cuatrimestre.query.delete()
    db.session.commit()
    print("   ✓ Cuatrimestres eliminados")

    print("\n📚 Creando nueva estructura...")

    total_materias = 0
    for cuatri_nombre, materias in ESTRUCTURA.items():
        cuatri = Cuatrimestre(nombre=cuatri_nombre)
        db.session.add(cuatri)
        db.session.flush()  # Para obtener el id

        for materia_nombre in materias:
            db.session.add(Materia(nombre=materia_nombre, cuatrimestre_id=cuatri.id))
            total_materias += 1

        print(f"   ✓ {cuatri_nombre} ({len(materias)} materias)")

    db.session.commit()
    print(f"\n✅ Listo — {len(ESTRUCTURA)} cuatrimestres, {total_materias} materias creadas")
