from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, RadioField
from wtforms.validators import DataRequired

#Classe CadastroFrom
class CadastroForm(FlaskForm):
	matricula = StringField("matricula", validators=[DataRequired()])
	tipoImovel = StringField("tipoImovel", validators=[DataRequired()])
	areaImovel = RadioField("area", choices=[("m2", "M²"), ("ha", "HA")])
	enderecoUser = StringField("enderecoUser", validators=[DataRequired()])
	latUser = StringField("latUser", validators=[DataRequired()])
	longUser = StringField("longUser", validators=[DataRequired()])

		
	
		