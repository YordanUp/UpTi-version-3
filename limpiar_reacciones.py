from web import app, db, Reaccion
from sqlalchemy import func

with app.app_context():
    subq = db.session.query(
        Reaccion.usuario_id,
        Reaccion.tipo_objeto,
        Reaccion.objeto_id,
        func.max(Reaccion.id).label('max_id')
    ).group_by(Reaccion.usuario_id, Reaccion.tipo_objeto, Reaccion.objeto_id).subquery()

    ids_a_mantener = [r[0] for r in db.session.query(subq.c.max_id).all()]

    eliminados = Reaccion.query.filter(
        ~Reaccion.id.in_(ids_a_mantener)
    ).delete(synchronize_session=False)
    db.session.commit()
    print(f"Eliminadas {eliminados} reacciones duplicadas")
