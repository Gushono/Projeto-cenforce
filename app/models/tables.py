from app import db


class Imovel(db.Model):
    __tablename__ = "imovel"

    matricula = db.Column(db.Integer, primary_key=True)
    tipoImovel = db.Column(db.String)
    areaImovel = db.Column(db.String)
    enderecoUser = db.Column(db.String)
    latUser = db.Column(db.String)
    longUser = db.Column(db.String)


def __init__(self, matricula, tipoImovel, areaImovel, enderecoUser, latUser, longUser):
    self.matricula = matricula
    self.tipoImovel = tipoImovel
    self.areaImovel = areaImovel
    self.enderecoUser = enderecoUser
    self.latUser = latUser
    self.longUser = longUser


def __repr__(self):
    return "<Post %r>" % self.matricula
